"""
RDF Graph Controller - see L{ordf.pylons.graph}. 
"""

from ordf.pylons.graph import GraphControllerFactory
from openbiblio.lib import base
from openbiblio import handler

GraphController = GraphControllerFactory(base, handler)
