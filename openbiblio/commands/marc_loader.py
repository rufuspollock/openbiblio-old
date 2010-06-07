from openbiblio.commands import Command
from datetime import datetime
from pylons import config
from pprint import pprint
from getpass import getuser
from openbiblio.lib import marc

from ordf.changeset import ChangeSet
from ordf.graph import Graph, ConjunctiveGraph
from ordf.namespace import namespaces, Namespace, DC, DCAM, RDF, FOAF, OBP, ORDF, ORE, OWL, RDFS
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
        for record in marc.Parser(self.filename):
            self.load(dict(record.items()))
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
        if not g:
            for k in d:
                ns, term = k.split(":")
                pred = namespaces[ns][term]
                for obj in d[k]:
                    g.add((subj, pred, obj))
            if self.options.source:
                source = URIRef(self.options.source)
            else:
                source = URIRef("file://%s/%s" % (os.uname()[1], os.path.abspath(self.filename)))
            g.add((subj, DC.source, source))
        return g

    def load(self, record):
        from openbiblio import handler
        ctx = handler.context(getuser(), "command line import of %s" % (self.filename,))

        contributors = record.get("dc:contributor", [])
        cgraphs = {}
        for i in range(len(contributors)):
            c = contributors[i]
            v = reduce(lambda x,y: x+y, c.values())
            v.sort()
            uniq = reduce(lambda x,y: x+y, v)
            h = md5(uniq.encode("utf-8"))
            cuuid = UUID(h.hexdigest())
            subj = URIRef("%sperson/%s" % (self.options.base, cuuid))
            contributors[i] = subj

            graph = cgraphs.setdefault(subj, self.toGraph(c, subj))
            graph.uuid = cuuid
            graph.add((subj, RDF.type, FOAF.Person))
            graph.add((subj, RDF.type, DC.Agent))
            for s,p,o in graph.triples((subj, FOAF.name, None)):
                graph.add((subj, RDFS.label, o))
            cgraphs[subj] = graph

        uuid = self.record_uuid(record)
        i = URIRef("%sitem/%s" % (self.options.base, uuid))
        w = URIRef("%swork/%s" % (self.options.base, uuid))

        ## add linkage from authors and other contributors to the work
        for c in cgraphs:
            g = cgraphs[c]
            g.add((g.identifier, OBP.contribution, w))

        item = self.toGraph(record, i)
        item.add((i, RDF.type, OBP.Item))
        item.add((i, OBP.work, w))

        publishers = {}
        for s,p,o in item.triples((i, MARC["publisher"], None)):
            loc = [c for (a, b, c) in item.triples((i, MARC["publoc"], None))]
            v = [o] + loc
            v.sort()
            uniq = reduce(lambda x,y: x+y, v)
            h = md5(uniq.encode("utf-8"))
            puuid = UUID(h.hexdigest())
            pubid = URIRef("%sperson/%s" % (self.options.base, puuid))
            item.add((i, DC["publisher"], pubid))
            pub = publishers.setdefault(pubid, self.get(pubid))
            pub.uuid = puuid
            pub.add((pubid, RDF["type"], DC["Agent"]))
            pub.add((pubid, FOAF["name"], o))
            pub.add((pubid, RDFS["label"], o))
            for l in loc:
                pub.add((pubid, DC["spatial"], l))
        item.remove((i, MARC["publisher"], None))
        item.remove((i, MARC["publoc"], None))

        for pubid in publishers:
            g = publishers[pubid]
            g.add((pubid, OBP["published"], i))

        self.clean(item)

        work = self.get(w)
        work.add((w, RDF.type, OBP.Work))
        work.add((w, OBP.hasItem, i))

        self.move(item, work, DC.contributor)
        self.move(item, work, DC.subject)

        for s,p,o in item.triples((i, DC["title"], None)):
            item.add((i, RDFS.label, o))
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

        aggid = URIRef("%saggregate/item/%s" % (self.options.base, uuid))
        agg = self.get(aggid)
        agg.add((aggid, RDF["type"], ORE["Aggregation"]))
        agg.add((aggid, ORE["aggregates"], i))
        item.add((i, ORE["isAggregatedBy"], aggid))
        agg.add((aggid, ORDF["lens"], URIRef("%slens/item" % self.options.base)))
        for p in publishers:
            g = publishers[p]
            agg.add((aggid, ORE["aggregates"], g.identifier))
            g.add((g.identifier, ORE["isAggregatedBy"], aggid))
        labels = [o for s,p,o in item.triples((i, RDFS.label, None))]
        labels.sort()
        label = u", ".join(labels)
        label = Literal(u"Item: %s" % label)
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
            agg.add((aggid, ORE["aggregates"], i))
            agg.add((aggid, ORE["aggregates"], g.identifier))
            agg.add((aggid, ORDF["lens"], URIRef("%slens/publisher" % self.options.base)))
            g.add((g.identifier, ORE["isAggregatedBy"], aggid))
            item.add((i, ORE["isAggregatedBy"], aggid))
            labels = [o for s,p,o in g.triples((g.identifier, RDFS.label, None))]
            labels.sort()
            label = u", ".join(labels)
            label = Literal(u"Publisher: %s" % label)
            agg.add((aggid, RDFS.label, label))
            agg.add((aggid, DC["title"], label))
            ctx.add(g)
            ctx.add(agg)

        ctx.add(item)
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

    def clean(self, item):
        """
        Clean out marc: pseudo-namespace
        """
        i = item.identifier
        for s,p,o in item.triples((i, MARC["isbn"], None)):
            isbn = o.strip(" -")
            item.add((i, OBP["isbn"], isbn))
            item.add((i, OWL.sameAs, URIRef("urn:isbn:%s" % isbn)))
            item.add((i, OWL.sameAs, URIRef("http://purl.org/NET/book/isbn/%s#book" % isbn)))
            item.add((i, OWL.sameAs, URIRef("http://www4.wiwiss.fu-berlin.de/bookmashup/books/%s" % isbn)))
        item.remove((i, MARC["isbn"], None))
        for s,p,o in item.triples((i, MARC["issn"], None)):
            issn = o.strip(" -")
            item.add((i, OBP["issn"], issn))
            item.add((i, OWL.sameAs, URIRef("urn:issn:%s" % issn)))
        item.remove((i, MARC["issn"], None))
        for s,p,o in item.triples((i, MARC["lccn"], None)):
            lccn = o.strip(" -")
            item.add((i, OWL.sameAs, URIRef(u"http://lccn.loc.gov/" + lccn)))
            item.add((i, OBP["lccn"], lccn))
        item.remove((i, MARC["lccn"], None))

        for s,p,o in item.triples((i, MARC["nlm"], None)):
            item.add((i, OBP["nlmcn"], o.strip(" -")))
        item.remove((i, MARC["nlm"], None))

        for s,p,o in item.triples((i, MARC["lcsh"], None)):
            b = BNode()
            item.add((i, DC["subject"], b))
            item.add((b, DCAM["member"], DC["LCSH"]))
            item.add((b, RDF.value, o))
        item.remove((i, MARC["lcsh"], None))

        for s,p,o in item.triples((i, MARC["edition"], None)):
            item.add((i, OBP["edition"], o))
        item.remove((i, MARC["edition"], None))

        for s,p,o in item.triples((i, MARC["pubseq"], None)):
            item.add((i, RDFS.comment, o))
        item.remove((i, MARC["pubseq"], None))

        # as much as I hate to remove... marc:scc usually contains
        # one letter things...
        item.remove((i, MARC["scc"], None))

        ## dewey decimal system is encumbered
        item.remove((i, MARC["ddc"], None))

        ## charset... hmmm
        item.remove((i, MARC["charset"], None))

        for s,p,o in item.triples((i, MARC["pubnum"], None)):
            item.add((i, OBP["issue"], o))
        item.remove((i, MARC["pubnum"], None))
