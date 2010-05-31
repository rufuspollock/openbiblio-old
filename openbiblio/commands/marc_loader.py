from openbiblio.commands import Command
from datetime import datetime
from pylons import config
from pprint import pprint
from getpass import getuser
from openbiblio.lib import marc

from ordf.changeset import ChangeSet
from ordf.graph import Graph, ConjunctiveGraph
from ordf.namespace import namespaces, Namespace, DC, DCAM, RDF, FOAF, OBP, ORE, OWL, RDFS
from ordf.term import URIRef, BNode
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
                      default="http://example.org/",
                      help="RDF base for entities (default http://example.org/)")
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

    def toGraph(self, d, subj):
        from openbiblio import handler
        g = handler.get(subj)
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
            subj = URIRef("%sperson/%s" % (self.options.base, UUID(h.hexdigest()),))
            contributors[i] = subj

            graph = self.toGraph(c, subj)
            graph.add((subj, RDF.type, FOAF.Person))
            for s,p,o in graph.triples((subj, FOAF.name, None)):
                graph.add((subj, RDFS.label, o))
            cgraphs[subj] = graph
            ctx.add(graph)

        uuid = self.record_uuid(record)
        i = URIRef("%sitem/%s" % (self.options.base, uuid))
        w = URIRef("%swork/%s" % (self.options.base, uuid))

        item = self.toGraph(record, i)
        item.add((i, RDF.type, OBP.Item))
        item.add((i, OBP.work, w))

        self.clean(item)

        work = handler.get(w)
        work.add((w, RDF.type, OBP.Work))
        work.add((w, OBP.hasItem, i))

        self.move(item, work, DC.contributor)
        self.move(item, work, DC.subject)

        for s,p,o in item.triples((i, DC["title"], None)):
            item.add((i, RDFS.label, o))
            work.add((w, DC["title"], o))
            work.add((w, RDFS.label, o))
            
        ctx.add(item)
        ctx.add(work)
        
        g = ConjunctiveGraph(store=ctx.store)
        for s,p,o in g.triples((None, None, None)):
            if str(p).startswith("marc:"):
                print g.serialize(format="n3")
                from sys import exit
                exit()

        ctx.commit()

    	self._total += 1

    def move(self, src, dst, pred):
        for s,p,o in src.triples((src.identifier, pred, None)):
            dst.add((dst.identifier, pred, o))
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
            item.add((i, OWL.sameAs, ISBN[o.strip(" -")]))
        item.remove((i, MARC["isbn"], None))
        for s,p,o in item.triples((i, MARC["issn"], None)):
            item.add((i, OWL.sameAs, ISSN[o.strip(" -")]))
        item.remove((i, MARC["issn"], None))
        for s,p,o in item.triples((i, MARC["lccn"], None)):
            item.add((i, OWL.sameAs, URIRef(u"http://lccn.loc.gov/" + o.strip(" -"))))
        item.remove((i, MARC["lccn"], None))

        for s,p,o in item.triples((i, MARC["nlm"], None)):
            item.add((i, DC["identifier"], o))
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
