from paste.script.command import Command as PasteCommand, BadCommand
from openbiblio.config.environment import load_environment
from paste.deploy import appconfig
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
    def data(cls):
        obproot = os.path.dirname(os.path.dirname(__file__))
        testdata = os.path.join(obproot, "tests", "data")

        ident = URIRef("http://bibliographica.org/test")
        data = Graph(identifier=ident)
        data.parse(os.path.join(testdata, "fixtures.rdf"))
        yield data

    @classmethod
    def setUp(cls):
        from openbiblio import handler

        if cls.done:
            return

        ctx = handler.context(getuser(), "Initial Data")
        for graph in cls.data():
            ## delete any stale history
            ctx.add(graph)
        ctx.commit()

        cls.done = True

    @classmethod
    def tearDown(cls):
        pass

    def command(self):
        self.setUp()

class Lenses(Command):
    summary = "Load Lenses"
    usage = "config.ini"
    parser = Command.standard_parser(verbose=False)

    def command(self):
        from openbiblio import handler
        obproot = os.path.dirname(os.path.dirname(__file__))
        lenses = os.path.join(obproot, "lenses", "*.n3")
        OB = Namespace("http://bibliographica.org/lens/")
        for filename in glob(lenses):
            ident = OB[os.path.basename(filename)[:-3]]
            data = Graph(identifier=ident)
            data.parse(filename, format="n3")
            filename_rdf = filename[:-3] + ".rdf"
            data.serialize(filename_rdf, format="pretty-xml")
            ## kludge - bnodes have a problem reading directly into the store
            cmd = "4s-import -v -m %s biblio %s" % (ident, os.path.abspath(filename_rdf))
            os.system(cmd)
            handler.pairtree.set(data)
