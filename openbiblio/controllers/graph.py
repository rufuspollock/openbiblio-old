from ordf.pylons.graph import GraphControllerFactory
from openbiblio.lib import base
from openbiblio import handler

GraphController = GraphControllerFactory(base, handler)
