from ordf.pylons.graph import GraphControllerFactory
from openbiblio.lib import base
from openbiblio import model

GraphController = GraphControllerFactory(base, model)

from openbiblio.commands import Fixtures
Fixtures.setUp()
