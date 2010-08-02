from openbiblio.commands import Command
from datetime import datetime
from pylons import config
from pprint import pprint, pformat
from getpass import getuser
from openbiblio.lib import marc
from traceback import format_exc

from ordf.graph import Graph, ConjunctiveGraph
from ordf.namespace import *
from ordf.term import URIRef, BNode, Literal
from hashlib import md5
from uuid import UUID

import logging
import swiss
import sys
import os
import re

MARC = Namespace("marc:")
namespaces["marc"] = MARC
ISBN = Namespace("urn:isbn:")
ISSN = Namespace("urn:issn:")

class Loader(Command):
    summary = "Load MARC File"
    usage = "config.ini file.mrc"
    parser = Command.standard_parser(verbose=False)
    parser.add_option("-s", "--source",
        dest="source",
        default=None,
        help="Source for provenance purposes"
    )
    parser.add_option("-b", "--base",
                      dest="base",
                      default="http://localhost:5000/",
                      help="RDF base for entities (default http://localhost:5000/)")
    parser.add_option("-x", "--remove",
                      dest="remove",
                      action="store_true",
                      default=False,
                      help="Remove old triples")
    parser.add_option("-c", "--count",
                      dest="count",
                      default="-1",
                      help="Import N records")
    parser.add_option("-n", "--skip",
                      dest="skip",
                      default="0",
                      help="Skip first N records")
    def command(self):
        self.cache = swiss.Cache(self.config.get("cache_dir", "data"))
        self.log = logging.getLogger("marc_loader")

        if len(self.args) != 1:
            self.log.error("please specify the location of the gutenberg marc file" )
            sys.exit(1)
        self._total = 0
        self._titles_found = 0
        self._authors_found = 0
        self.filename = self.args[0]
        self.log.info("loading records from %s" % (self.filename,))
        skip = int(self.options.skip)
        count = int(self.options.count)
        self.recno = -1
        for record in marc.Parser(self.filename):
            self.recno += 1
            if self.recno < skip:
                continue
            if (self.recno - skip) == count:
                break
            items = record
            try:
                items = dict(record.items())
                self.load(items)
            except:
                self.log.error("Exception processing record %s" % self.recno)
                self.log.error("Record:\n%s" % pformat(items))
                self.log.error("Traceback:\n%s" % format_exc())
                sys.exit(1)
            if self._total % 1000 == 0:
                self.report()
        self.report()

    def report(self):
        self.log.info("total: %s titles found: %s authors found: %s" %
                (self._total, self._titles_found, self._authors_found))

    def get(self, identifier):
        from openbiblio import handler
        return Graph(identifier=identifier) if self.options.remove else handler.get(identifier)

    def toGraph(self, d, subj):
        g = self.get(subj)
        def dict_to_graph(s, d):
            for k in d:
                ns, term = k.split(":")
                pred = namespaces[ns][term]
                for obj in d[k]:
                    if isinstance(obj, dict):
                        o = BNode()
                        g.add((s, pred, o))
                        dict_to_graph(o, obj)
                    else:
                        g.add((s, pred, obj))
        if not g:
            dict_to_graph(subj, d)
            if self.options.source:
                source = URIRef(self.options.source)
            else:
                source = URIRef("file://%s/%s" % (os.uname()[1], os.path.abspath(self.filename)))
            self.provenance(g, source)
        return g

    def provenance(self, g, source):
        from openbiblio import version
        g.add((g.identifier, RDF.type, OPMV["Artifact"]))
        g.add((source, RDF.type, OPMV["Artifact"]))
        p = BNode()
        g.add((g.identifier, OPMV["wasGeneratedBy"], p))
        g.add((p, RDF.type, OPMV["Process"]))
        g.add((p, RDFS.comment, Literal("openbiblio load_marc v%s" % version)))
        g.add((p, OPMV["used"], source))
        g.add((p, OBP["record"], Literal(self.recno)))
        t = BNode()
        g.add((t, RDF.type, TIME["Instant"]))
        g.add((t, TIME["inXSDDateTime"], Literal(datetime.now())))
        g.add((g.identifier, OPMV["wasGeneratedAt"], t))
        g.add((p, OPMV["wasPerformedAt"], t))

    def dictuuid(self, d):
        def values(v):
            for k in v:
                for x in v[k]:
                    if isinstance(x, dict):
                        for y in values(x):
                            yield y
                    else:
                        yield [(k, x)]
        v = reduce(lambda x,y: list(x)+list(y), values(d))
        v.sort()
        def tostr(l):
            def _f():
                for k,v in l:
                    yield u"%s=%s" % (k,v)
            return "\n".join(_f())
        s = tostr(v)
        h = md5(s.encode("utf-8"))
        return UUID(h.hexdigest())
        
    def load(self, record):
        from openbiblio import handler
        ctx = handler.context(getuser(), "command line import of %s" % (self.filename,))

        contributors = record.get("dc:contributor", [])
        cgraphs = {}

        for k in range(len(contributors)):
            c = contributors[k]
            cuuid = self.dictuuid(c)
            subj = URIRef("%sperson/%s" % (self.options.base, cuuid))
            contributors[k] = subj

            graph = cgraphs.setdefault(subj, self.toGraph(c, subj))
            graph.uuid = cuuid
            graph.add((subj, RDF.type, FOAF.Person))
            graph.add((subj, RDF.type, DC.Agent))
            for s,p,o in graph.triples((subj, FOAF.name, None)):
                graph.add((subj, RDFS.label, o))
            cgraphs[subj] = graph
        
        uuid = self.record_uuid(record)
        m = URIRef("%smanifestation/%s" % (self.options.base, uuid))
        w = URIRef("%swork/%s" % (self.options.base, uuid))

        ## add linkage from authors and other contributors to the work
        for c in cgraphs:
            g = cgraphs[c]
            g.add((g.identifier, OBP.contribution, w))

        manif = self.toGraph(record, m)
        manif.add((m, RDF.type, OBP.Manifestation))
        manif.add((m, OBP.work, w))

        publishers = {}
        for s,p,o in manif.triples((m, MARC["publisher"], None)):
            loc = [c for (a, b, c) in manif.triples((m, MARC["publoc"], None))]
            puuid = self.dictuuid({ DC["publisher"]: [o], DC["spatial"]: loc})
            pubid = URIRef("%sperson/%s" % (self.options.base, puuid))
            manif.add((m, DC["publisher"], pubid))
            pub = publishers.setdefault(pubid, self.get(pubid))
            pub.uuid = puuid
            pub.add((pubid, RDF["type"], DC["Agent"]))
            pub.add((pubid, FOAF["name"], o))
            pub.add((pubid, RDFS["label"], o))
            for l in loc:
                pub.add((pubid, DC["spatial"], l))
        manif.remove((m, MARC["publisher"], None))
        manif.remove((m, MARC["publoc"], None))

        for pubid in publishers:
            g = publishers[pubid]
            g.add((pubid, OBP["published"], m))

        self.clean(manif)

        work = self.get(w)
        work.add((w, RDF.type, OBP.Work))
        work.add((w, OBP.hasItem, m))
        self.provenance(work, manif.identifier)

        self.move(manif, work, DC.contributor)
        self.move(manif, work, DC.subject)

        for s,p,o in manif.triples((m, DC["title"], None)):
            manif.add((m, RDFS.label, o))
            work.add((w, DC["title"], o))
            work.add((w, RDFS.label, o))
            
        aggid = URIRef("%saggregate/work/%s" % (self.options.base, uuid))
        agg = self.get(aggid)
        agg.add((aggid, RDF["type"], ORE["Aggregation"]))
        agg.add((aggid, ORE["aggregates"], w))
        agg.add((aggid, ORDF["lens"], URIRef("%slens/work" % self.options.base)))
        work.add((w, ORE["isAggregatedBy"], aggid))
        for c in cgraphs:
            g = cgraphs[c]
            agg.add((aggid, ORE["aggregates"], g.identifier))
            g.add((g.identifier, ORE["isAggregatedBy"], aggid))
        labels = [o for s,p,o in work.triples((w, RDFS.label, None))]
        labels.sort()
        label = u", ".join(labels)
        label = Literal(u"Work: %s" % label)
        agg.add((aggid, RDFS.label, label))
        agg.add((aggid, DC["title"], label))
        ctx.add(agg)

        aggid = URIRef("%saggregate/manifestation/%s" % (self.options.base, uuid))
        agg = self.get(aggid)
        agg.add((aggid, RDF["type"], ORE["Aggregation"]))
        agg.add((aggid, ORE["aggregates"], m))
        manif.add((m, ORE["isAggregatedBy"], aggid))
        agg.add((aggid, ORDF["lens"], URIRef("%slens/manifestation" % self.options.base)))
        for p in publishers:
            g = publishers[p]
            agg.add((aggid, ORE["aggregates"], g.identifier))
            g.add((g.identifier, ORE["isAggregatedBy"], aggid))
        labels = [o for s,p,o in manif.triples((m, RDFS.label, None))]
        labels.sort()
        label = u", ".join(labels)
        label = Literal(u"Manifestation: %s" % label)
        agg.add((aggid, RDFS.label, label))
        agg.add((aggid, DC["title"], label))
        ctx.add(agg)

        for c in cgraphs:
            g = cgraphs[c]
            aggid = URIRef("%saggregate/person/%s" % (self.options.base, g.uuid))
            agg = self.get(aggid)
            agg.add((aggid, RDF["type"], ORE["Aggregation"]))
            agg.add((aggid, ORE["aggregates"], w))
            agg.add((aggid, ORE["aggregates"], g.identifier))
            g.add((g.identifier, ORE["isAggregatedBy"], aggid))
            work.add((w, ORE["isAggregatedBy"], aggid))
            agg.add((aggid, ORDF["lens"], URIRef("%slens/contributor" % self.options.base)))
            labels = [o for s,p,o in g.triples((g.identifier, RDFS.label, None))]
            labels.sort()
            label = u", ".join(labels)
            label = Literal(u"Contributor: %s" % label)
            agg.add((aggid, RDFS.label, label))
            agg.add((aggid, DC["title"], label))
            ctx.add(g)
            ctx.add(agg)

        for p in publishers:
            g = publishers[p]
            aggid = URIRef("%saggregate/person/%s" % (self.options.base, g.uuid))
            agg = self.get(aggid)
            agg.add((aggid, RDF["type"], ORE["Aggregation"]))
            agg.add((aggid, ORE["aggregates"], m))
            agg.add((aggid, ORE["aggregates"], g.identifier))
            agg.add((aggid, ORDF["lens"], URIRef("%slens/publisher" % self.options.base)))
            g.add((g.identifier, ORE["isAggregatedBy"], aggid))
            manif.add((m, ORE["isAggregatedBy"], aggid))
            labels = [o for s,p,o in g.triples((g.identifier, RDFS.label, None))]
            labels.sort()
            label = u", ".join(labels)
            label = Literal(u"Publisher: %s" % label)
            agg.add((aggid, RDFS.label, label))
            agg.add((aggid, DC["title"], label))
            ctx.add(g)
            ctx.add(agg)

        ctx.add(manif)
        ctx.add(work)

        g = ConjunctiveGraph(store=ctx.store)
        for s,p,o in g.triples((None, None, None)):
            if str(p).startswith("marc:"):
                print g.serialize(format="n3")

        cs = ctx.commit()
#        print cs.serialize(format="n3")

    	self._total += 1

    def move(self, src, dst, pred):
        for s,p,o in src.triples((src.identifier, pred, None)):
            dst.add((dst.identifier, pred, o))
            ## and one level down, should really do bnode closure or something
            for ss,pp,oo in src.triples((o, None, None)):
                dst.add((ss,pp,oo))
                src.remove((ss,pp,oo))
        src.remove((src.identifier, pred, None))

    def record_uuid(self, record):
        v = record["dc:title"] + record.get("dc:contributor", []) + record.get("dc:date", []) \
            + record.get("dc:identifier", [])
        v.sort()
        uniq = reduce(lambda x,y: x+y, v)
        h = md5(uniq.encode("utf-8"))
        return UUID(h.hexdigest())

    def clean(self, manif):
        """
        Clean out marc: pseudo-namespace
        """
        i = manif.identifier
        for s,p,o in manif.triples((i, BIBO["isbn"], None)):
            manif.add((i, OWL.sameAs, URIRef("urn:isbn:%s" % o)))
            manif.add((i, OWL.sameAs, URIRef("http://purl.org/NET/book/isbn/%s#book" % o)))
            manif.add((i, OWL.sameAs, URIRef("http://www4.wiwiss.fu-berlin.de/bookmashup/books/%s" % o)))

        for s,p,o in manif.triples((i, BIBO["issn"], None)):
            manif.add((i, OBP["issn"], o))
            manif.add((i, OWL.sameAs, URIRef("urn:issn:%s" % o)))

        for s,p,o in manif.triples((i, MARC["lccn"], None)):
            lccn = o.strip(" -")
            manif.add((i, OWL.sameAs, URIRef(u"http://lccn.loc.gov/" + lccn)))
            manif.add((i, OBP["lccn"], lccn))
        manif.remove((i, MARC["lccn"], None))

        for s,p,o in manif.triples((i, MARC["nlm"], None)):
            manif.add((i, OBP["nlmcn"], o.strip(" -")))
        manif.remove((i, MARC["nlm"], None))

        for s,p,o in manif.triples((i, MARC["lcsh"], None)):
            b = BNode()
            manif.add((i, DC["subject"], b))
            manif.add((b, DCAM["member"], DC["LCSH"]))
            manif.add((b, RDF.value, o))
        manif.remove((i, MARC["lcsh"], None))

        for s,p,o in manif.triples((i, MARC["edition"], None)):
            manif.add((i, OBP["edition"], o))
        manif.remove((i, MARC["edition"], None))

        for s,p,o in manif.triples((i, MARC["pubseq"], None)):
            manif.add((i, RDFS.comment, o))
        manif.remove((i, MARC["pubseq"], None))

        # as much as I hate to remove... marc:scc usually contains
        # one letter things...
        manif.remove((i, MARC["scc"], None))

        ## dewey decimal system is encumbered
        manif.remove((i, MARC["ddc"], None))

        ## charset... hmmm
        manif.remove((i, MARC["charset"], None))

        for s,p,o in manif.triples((i, MARC["pubnum"], None)):
            manif.add((i, OBP["issue"], o))
        manif.remove((i, MARC["pubnum"], None))

        ## clean out "[by] foo bar" in title
        bad_titles = []
        for s,p,o in manif.triples((i, DC["title"], None)):
            if o.startswith(u"[by]"):
                bad_titles.append(o)
        [manif.remove((i, DC["title"], x)) for x in bad_titles]
