from ordf.pylons.sparql import SparqlControllerFactory
from openbiblio.lib import base
from openbiblio import model

SparqlController = SparqlControllerFactory(base, model)
