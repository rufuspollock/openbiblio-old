"""
RDF Graph Controller - see L{ordf.pylons.graph}. 
"""

from pylons.controllers.util import abort
from openbiblio.lib import base
from openbiblio.lib.base import render, request, c, response
from openbiblio import handler
from ordf.onto.controllers.graph import GraphController as _GraphController

class GraphController(_GraphController):
    def _render_graph(self):
        if len(c.graph) == 0:
            abort(404, "No such graph: %s" % c.graph.identifier)
        self._label_graph()
        return render('graph_fresnel.html')
