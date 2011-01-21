from paste.script.command import Command as PasteCommand, BadCommand
from openbiblio.config.environment import load_environment
from paste.deploy import appconfig
from glob import glob
from getpass import getuser
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
    obproot = os.path.dirname(os.path.dirname(__file__))
    testdata = os.path.join(obproot, "tests", "data")

    @classmethod
    def data(cls):
        ident = URIRef("http://bibliographica.org/test")
        data = Graph(identifier=ident)
        data.parse(os.path.join(cls.testdata, "fixtures.rdf"))
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

        ctx = handler.context(getuser(), "Bibtex Graph data")
        ident = URIRef("http://bnb.bibliographica.org/entry/GB9361575")
        data = Graph(identifier=ident)
        data.parse(os.path.join(cls.testdata, "GB9361575.rdf"))
        ctx.add(data)
        ctx.commit()
        
        cls.done = True

    @classmethod
    def tearDown(cls):
        pass

    def command(self):
        self.setUp()
