"""
RDF Graph Controller - see L{ordf.pylons.graph}. 
"""

from ordf.pylons.graph import GraphControllerFactory
from openbiblio.lib import base
from openbiblio.lib.base import render, request, c, response
from openbiblio import handler

# TODO: change this to be more elegant ...
_GraphController = GraphControllerFactory(base, handler)

class GraphController(_GraphController):
    def _render(self):
        # stuff other things in c
        return render('graph_fresnel.html')
