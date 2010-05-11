"""
RDF Graph Controller - see L{ordf.pylons.graph}. 
"""

from ordf.pylons.graph import GraphControllerFactory
from openbiblio.lib import base
from openbiblio.lib.base import render, request, c, response
from openbiblio import handler

from ordf.pylons.serialiser import graph_format

# TODO: change this to be more elegant ...
_GraphController = GraphControllerFactory(base, handler)

class GraphController(_GraphController):
    def index(self):
        accept, format = graph_format(request)
        graph = self._index(accept, format)
        if format == "html":
            c.triples = graph.triples((None, None, None))
            data = render('graph_fresnel.html')
        else:
            data = graph.serialize(format=format)
            response.content_type = str(accept)
        return data

    def test(self):
        return render('home/index.html')

