from openbiblio.commands import Command
from datetime import datetime
from pprint import pprint, pformat
from getpass import getuser
from openbiblio.lib import marc
from traceback import format_exc

from ordf.changeset import ChangeSet
from ordf.graph import Graph, ConjunctiveGraph
from ordf.term import URIRef, BNode, Literal
from ordf.vocab.ore import Aggregation
from ordf.vocab.opmv import Agent, Process
from ordf.utils import get_identifier
from ordf.namespace import *

import logging
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
    parser.add_option("--noload",
                      dest="load",
                      default=True,
                      action="store_false",
                      help="Do not load MARC records")
    parser.add_option("--noevolve",
                       dest="evolve",
                       default=True,
                       action="store_false",
                       help="Do not evolve Work/Manifestation/etc.")
    parser.add_option("--sanity",
                      default=False,
                      dest="sanity",
                      action="store_true",
                      help="Sanity Check Input")
    parser.add_option("--dryrun",
                      default=False,
                      dest="dryrun",
                      action="store_true",
                      help="Dry run -- do not save to store")
    def command(self):
        self.log = logging.getLogger("marc_loader")

        if len(self.args) != 1:
            self.log.error("please specify the location of the marc file" )
            sys.exit(1)
        self.filename = self.args[0]
        self.log.info("loading records from %s" % (self.filename,))
        skip = int(self.options.skip)
        count = int(self.options.count)
        self.recno = -1
        self.total = 0
        self.agent = Agent()
        self.agent.nick(getuser())

        for record in marc.Parser(self.filename):
            self.recno += 1
            if self.recno < skip:
                continue
            if (self.recno - skip) == count:
                break
            try:
                if self.options.load:
                    marc_rdf = self.load(record)
                else:
                    from openbiblio import handler
                    marc_rdf = handler.get(self.record_id())
                if self.options.evolve:
                    self.evolve(marc_rdf)
                self.total += 1
            except:
                self.log.error("Exception processing record %s" % self.recno)
                self.log.error("Record:\n%s" % pformat(record))
                self.log.error("Traceback:\n%s" % format_exc())
                self.report()
                sys.exit(1)
        self.report()

    def report(self):
        self.log.info("total records: %s total processed: %s" %
                      (self.recno+1, self.total))

    def source(self):
        if self.options.source:
            return URIRef(self.options.source)
        else:
            return URIRef("file://" + os.path.abspath(self.filename))

    def uuid(self):
        from uuid import uuid5, NAMESPACE_URL
        return str(uuid5(NAMESPACE_URL, str(self.source())))

    def record_id(self):
        return URIRef(self.options.base + self.uuid() + "/%s" % self.recno)

    def get(self, identifier):
        return Graph(identifier=identifier)

    def load(self, record):
        if self.options.sanity:
            record.sanity()

        ident = self.record_id()

        proc = Process()
        proc.agent(self.agent)
        proc.use(self.source())

        marc = record.rdf(identifier = ident)
        marc.add((ident, OBP["record"], Literal(self.recno)))
        marc.add((ident, DC["source"], self.source()))

        proc.result(marc)

        if not self.options.dryrun:
            from openbiblio import handler
            ctx = handler.context(getuser(), "command line import of %s" % (self.source()))
            ctx.add(marc)
            ctx.commit()

        self.log.info("import: %s" % marc.identifier)

        return marc

    def rewrite(self, src, dst, pred):
        return src.bnc((src.identifier, pred, None)
                       ).replace(
            (src.identifier, None, None), (get_identifier(dst), None, None))

    def evolve(self, marc):
        from openbiblio import handler
        self.context = handler.context(getuser(), "evolution of %s" % marc.identifier)

        self.work(marc)

        if not self.options.dryrun:
            self.context.commit()

    def work(self, marc):
        proc = Process()
        proc.agent(self.agent)
        proc.use(marc.identifier)
        proc.start()

        work = Graph(identifier = URIRef(marc.identifier + "/work"))
        work.add((work.identifier, RDF["type"], OBP["Work"]))
        work += self.rewrite(marc, work, DC["title"])
        work += self.rewrite(marc, work, DC["description"])
        work += self.rewrite(marc, work, BIBO["lccn"])

        contributors = self.contributors(marc)
        for c in contributors:
            work.add((work.identifier, DC["contributor"], c.identifier))
        subjects = self.subjects(marc)
        for s in subjects:
            work.add((work.identifier, DC["subject"], s.identifier))
            if not s.exists((s.identifier, RDF["type"], FOAF["Person"])):
                work += s

        manif = self.manifestation(marc)
        work.add((work.identifier, OBP["hasManifestation"], manif.identifier))

        proc.result(work)
        self.context.add(work)

    def contributors(self, marc):
        result = []
        i = 0
        for s,p,o in marc.triples((marc.identifier, DC["contributor"], None)):
            proc = Process()
            proc.agent(self.agent)
            proc.use(marc.identifier)

            identifier = URIRef(marc.identifier + "/contributor/%d" % i)
            contributor = Graph(identifier=identifier)
            contributor += marc.bnc((o, None, None)
                                    ).replace(
                (o, None, None), (identifier, None, None))
            proc.result(contributor)
            self.context.add(contributor)
            result.append(contributor)
            i += 1
        return result

    def subjects(self, marc):
        result = []
        i = 0
        for s,p,o in marc.triples((marc.identifier, DC["subject"], None)):
            if marc.exists((o, RDF["type"], FOAF["Person"])):
                proc = Process()
                proc.agent(self.agent)
                proc.use(marc.identifier)
                identifier = URIRef(marc.identifier + "/subject/%d" % i)
                subject = Graph(identifier=identifier)
                subject += marc.bnc((o, None, None)
                                    ).replace(
                    (o, None, None), (identifier, None, None))
                proc.result(subject)
                self.context.add(subject)
                i += 1
            else:
                subject = Graph(identifier=o)
                subject += marc.bnc((o, None, None))
            result.append(subject)
        return result

    def manifestation(self, marc):
        proc = Process()
        proc.agent(self.agent)
        proc.use(marc.identifier)

        manif = Graph(identifier = URIRef(marc.identifier + "/manifestation"))
        manif.add((manif.identifier, RDF["type"], OBP["Manifestation"]))

        publisher = self.publisher(marc)
        manif.add((manif.identifier, DC["publisher"], publisher.identifier))
        for _s,_p,o in marc.triples((marc.identifier, DC["publisher"], None)):
            for s,p,loc in marc.triples((o, DC["spatial"], None)):
                manif.add((manif.identifier, DC["spatial"], loc))

        manif += self.rewrite(marc, manif, BIBO["isbn"])
        manif += self.rewrite(marc, manif, BIBO["isbn10"])
        manif += self.rewrite(marc, manif, BIBO["isbn13"])
        manif += self.rewrite(marc, manif, DC["date"])
        manif += self.rewrite(marc, manif, DC["extent"])
        manif += self.rewrite(marc, manif, OBP["dimensions"])
        manif += self.rewrite(marc, manif, OBP["edition"])
        manif += self.rewrite(marc, manif, OBP["nbn"])
        manif += self.rewrite(marc, manif, OBP["scn"])
        manif += self.rewrite(marc, manif, OWL["sameAs"])
        
        proc.result(manif)
        self.context.add(manif)

        return manif

    def publisher(self, marc):
        proc = Process()
        proc.agent(self.agent)
        proc.use(marc.identifier)

        publisher = Graph(identifier = URIRef(marc.identifier + "/publisher"))
        for s,p,o in marc.triples((marc.identifier, DC["publisher"], None)):
            publisher += marc.bnc((o, None, None)
                                  ).replace(
                (o, None, None), (publisher.identifier, None, None))
        publisher.remove((publisher.identifier, DC["spatial"], None))

        proc.result(publisher)
        self.context.add(publisher)

        return publisher
