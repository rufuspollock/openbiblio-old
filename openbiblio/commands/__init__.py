from paste.script.command import Command as PasteCommand, BadCommand
from openbiblio.config.environment import load_environment
from paste.deploy import appconfig
from uuid import uuid3, NAMESPACE_URL
from ordf.changeset import ChangeSet
from ordf.graph import Graph
from ordf.term import URIRef

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
    @classmethod
    def data(cls):
        obproot = os.path.dirname(os.path.dirname(__file__))
        testdata = os.path.join(obproot, "tests", "data")

        ident = URIRef("http://example.org/")

        data = Graph(identifier=ident)
        data.parse(os.path.join(testdata, "fixtures.rdf"))
        return data

    identifier = None
    @classmethod
    def setUp(cls):
        from openbiblio.model import store

        if cls.identifier is not None:
            return ## already done

        new = cls.data()
        orig = Graph(identifier=new.identifier)
        cs = ChangeSet("fixtures", "fixtures")
        cs.diff(orig, new)
        cs.commit(store)

        cls.identifier = cs.identifier

        cs.commit()

    @classmethod
    def tearDown(cls):
        from openbiblio.model import store

        if cls.identifier is not None:
            cursor = store.cursor()
            cursor.delete_model(cls.identifier)
            cursor.delete_model("http://example.org/")
