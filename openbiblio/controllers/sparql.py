"""
SPARQL Endpoint Controller - see L{ordf.pylons.sparql}.
"""
from ordf.pylons.sparql import SparqlControllerFactory
from openbiblio.lib import base
from openbiblio import handler

SparqlController = SparqlControllerFactory(base, handler)
