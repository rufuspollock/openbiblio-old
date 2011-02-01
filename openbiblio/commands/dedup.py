from openbiblio.commands import Command
from datetime import datetime
from pylons import config
from pprint import pprint, pformat
from getpass import getuser
from openbiblio.lib import marc
from traceback import format_exc

from ordf.graph import Graph, ConjunctiveGraph
from ordf.term import URIRef, BNode, Literal
from ordf.namespace import *

import logging
import re

class DeDup(Command):
    summary = "Dedup"
    usage = "config.ini"
    parser = Command.standard_parser(verbose=False)

    def count(self, q):
        from openbiblio import handler
        for count, in handler.query(q):
            return count

    def countWorks(self):
        q = """
SELECT DISTINCT COUNT(?s) AS c WHERE
{ ?s a obp:Work }
"""
        return self.count(q)

    def countManifestations(self):
        q = """
SELECT DISTINCT COUNT(?s) AS c WHERE
{ ?s a obp:Work }
"""
        return self.count(q)

    def countProcess(self):
        q = """
SELECT DISTINCT COUNT(?p) AS c WHERE
{ ?m a obp:Manifestation .
  ?m opmv:wasGeneratedBy ?p .
  ?p a opmv:Process }
"""
        return self.count(q)

    def sources(self):
        from openbiblio import handler
        q = """
SELECT DISTINCT ?s WHERE
{ ?m a obp:Manifestation .
  ?m opmv:wasGeneratedBy ?p .
  ?p opmv:used ?s
}
"""
        for source, in handler.query(q):
            yield source

    def sourceCount(self, source):
        q = """
SELECT COUNT(?s) AS c WHERE
{ ?m a obp:Manifestation .
  ?m opmv:wasGeneratedBy ?p .
  ?p opmv:used %s }
""" % source.n3()
        return self.count(q)

    def command(self):
        log = logging.getLogger("ordf.dedup")
        log.info("number of manifestations %s" % self.countManifestations())
        log.info("number of works %s" % self.countWorks())
        log.info("number of opmv:Process %s" % self.countProcess())
        for s in self.sources():
            log.info("source %s: %s records" % (s, self.sourceCount(s)))
