from openbiblio.commands import Command
from datetime import datetime
from pylons import config
from pprint import pprint
from getpass import getuser
from openbiblio.lib import marc

from ordf.changeset import ChangeSet
from ordf.graph import Graph
from ordf.namespace import namespaces, Namespace, DC, FRBR, RDF, FOAF, OWL
from ordf.term import URIRef
from hashlib import md5
from uuid import UUID

import logging
import swiss
import sys
import os
import re

namespaces["marc"] = Namespace("http://bibliographica.org/schema/marc#")

class Loader(Command):
    summary = "Load MARC File"
    usage = "config.ini file.mrc"
    parser = Command.standard_parser(verbose=False)
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
        g = Graph(identifier=subj)
        for k in d:
            ns, term = k.split(":")
            pred = namespaces[ns][term]
            for obj in d[k]:
                g.add((subj, pred, obj))
        g.add((subj, DC.source, URIRef("file://%s/%s" % (os.uname()[1], os.path.abspath(self.filename)))))
        return g

    def load(self, record):
        from openbiblio.model import handler
        ctx = handler.context(getuser(), "command line import of %s" % (self.filename,))

        contributors = record.get("dc:contributor", [])
        for i in range(len(contributors)):
            c = contributors[i]
            v = reduce(lambda x,y: x+y, c.values())
            v.sort()
            uniq = reduce(lambda x,y: x+y, v)
            h = md5(uniq.encode("utf-8"))
            subj = URIRef("urn:uuid:%s" % (UUID(h.hexdigest()),))
            contributors[i] = subj

            graph = self.toGraph(c, subj)
            graph.add((subj, RDF.type, FRBR.Person))
            graph.add((subj, RDF.type, FOAF.Person))
            graph.add((subj, RDF.type, OWL.Thing))
            ctx.add(graph)

        subj = self.record_subject(record)
        graph = self.toGraph(record, subj)
        graph.add((subj, RDF.type, FRBR.Expression))
        graph.add((subj, RDF.type, OWL.Thing))
        ctx.add(graph)

        ctx.commit()

    	self._total += 1

    def record_subject(self, record):
        v = record["dc:title"] + record.get("dc:contributor", []) + record.get("dc:date", []) \
            + record.get("dc:identifier", [])
        v.sort()
        uniq = reduce(lambda x,y: x+y, v)
        h = md5(uniq.encode("utf-8"))
        subj = URIRef("urn:uuid:%s" % (UUID(h.hexdigest()),))
        return subj
