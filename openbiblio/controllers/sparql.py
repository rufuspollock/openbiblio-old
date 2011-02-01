"""
SPARQL Endpoint Controller - see L{ordf.pylons.sparql}.
"""
#from ordf.onto.controllers.sparql import SparqlController as _SparqlController
from ordf.onto.controllers.sparql import GraphController as _SparqlController

from openbiblio.lib.base import BaseController

class SparqlController(BaseController, _SparqlController):
    """OpenBiblio SPARQL Controller"""
