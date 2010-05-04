from paste.script.command import Command as PasteCommand, BadCommand
from openbiblio.config.environment import load_environment
from paste.deploy import appconfig
from uuid import uuid3, NAMESPACE_URL
from glob import glob
from getpass import getuser
from ordf.changeset import ChangeSet
from ordf.graph import Graph
from ordf.term import URIRef
from ordf.namespace import Namespace

import os

class Command(PasteCommand):
    group_name = "openbiblio"
    def parse_args(self, *av, **kw):
        super(Command, self).parse_args(*av, **kw)
        if not self.args:
            raise BadCommand("please specify a configuration file")
        config = self.args[0]
        self.args = self.args[1:]
        self.parse_config(config)

    def parse_config(self, config_file):
        ### parse the config file
        if not config_file.startswith("/"):
            context = { "relative_to": os.getcwd() }
        else:
            context = {}
        self.logging_file_config(config_file)
        self.config = appconfig('config:' + config_file, **context)
        load_environment(self.config.global_conf, self.config.local_conf)

class Fixtures(Command):
    summary = "Load Fixtures"
    usage = "config.ini"
    parser = Command.standard_parser(verbose=False)
    done = False

    @classmethod
    def data(cls, store="IOMemory"):
        obproot = os.path.dirname(os.path.dirname(__file__))
        testdata = os.path.join(obproot, "tests", "data")

        ident = URIRef("http://bibliographica.org/test")
        data = Graph(store, identifier=ident)
        data.parse(os.path.join(testdata, "fixtures.rdf"))
        yield data

        lenses = os.path.join(obproot, "lenses", "*.n3")
        OB = Namespace("http://bibliographica.org/lens/")
        for filename in glob(lenses):
            ident = OB[os.path.basename(filename)[:-3]]
            data = Graph(store, identifier=ident)
            data.parse(filename, format="n3")
            filename_rdf = filename[:-3] + ".rdf"
            data.serialize(filename_rdf, format="pretty-xml")
            ## kludge - bnodes have a problem reading directly into the store
            cmd = "4s-import -v -m %s biblio %s" % (ident, os.path.abspath(filename_rdf))
            os.system(cmd)
            from openbiblio.model import ptree
            ptree[ident] = data
#            yield data

    @classmethod
    def setUp(cls):
        from openbiblio.model import store, ptree

        if cls.done:
            return

        cs = ChangeSet(getuser(), "Initial Data")
        for graph in cls.data():
            ## delete any stale history
#            cursor = store.cursor()
#            for change in graph.history(store):
#                cursor.delete_model(change)
            orig = Graph(identifier=graph.identifier)
            cs.diff(orig, graph)
            ptree[graph.identifier] = graph
            if len(cs):
                ptree[cs.identifier] = cs
        cs.commit(store)

        cls.done = True

    @classmethod
    def tearDown(cls):
        from openbiblio.model import store

        if cls.done:
            cursor = store.cursor()
            for graph in cls.data(store):
                for change in graph.history():
                    cursor.delete_model(change)
                cursor.delete_model(graph)

    def command(self):
        self.setUp()
