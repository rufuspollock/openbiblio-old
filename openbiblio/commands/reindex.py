from openbiblio.commands import Command
from ordf.namespace import RDF, CS
import logging

class Indexer(Command):
    summary = "Index data stored"
    usage = "[options] config.ini"
    parser = Command.standard_parser(verbose=False)
    parser.add_option("-c", "--changesets",
        dest="changesets",
        action="store_true",
        default=False,
        help="Index Changesets")
    parser.add_option("-i", "--indices",
        dest="indices",
        default=None,
        help="Comma separated list of indices to rebuild")
    def command(self):
        from openbiblio import handler
        log = logging.getLogger(__name__)

        if self.options.indices:
            indices = self.options.indices.split(",")
        else:
            indices = self.config["ordf.indices"].split(",")
        log.info("Reindexing %s changesets: %s" % (indices, self.options.changesets))
        indices = [getattr(handler, x) for x in indices]
        for uuid in handler.pairtree.store.list_ids():
            g = handler.pairtree.get("urn:uuid:" + uuid)
            is_cs = False
            for s,p,o in g.triples((g.identifier, RDF.type, CS.ChangeSet)):
                is_cs = True
                break
            if is_cs and self.options.changesets:
                log.info("Indexing cset %s" % g.identifier)
                for index in indices:
                    index.cset(g)
            elif not is_cs:
                log.info("Indexing graph %s" % g.identifier)
                for index in indices:
                    index.set(g)
