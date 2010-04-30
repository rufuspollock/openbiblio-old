from ordf.pylons.graph import GraphControllerFactory
from openbiblio.lib import base
from openbiblio import model

GraphController = GraphControllerFactory(base, model)
