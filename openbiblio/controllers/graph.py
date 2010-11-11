"""
RDF Graph Controller - see L{ordf.pylons.graph}. 
"""

from pylons.controllers.util import abort
from openbiblio.lib import base
from openbiblio.lib.base import render, request, c, response
from openbiblio import handler
from ordf.onto.controllers.graph import GraphController as _GraphController
from ordf.graph import Graph

construct_graph = """
CONSTRUCT {
    %(agent)s a foaf:Person .
    %(agent)s ?a_p ?a_o .
    %(agent)s <http://dbpedia.org/property/creator> ?work .
    ?work dc:title ?title
} WHERE {
    %(agent)s ?a_p ?a_o .
    ?work a bibo:Document .
    ?work dc:title ?title .
    { ?work dc:contributor %(agent)s } UNION
    { ?work dc:publisher %(agent)s }
}    
"""

class GraphController(base.BaseController, _GraphController):
    def _get_graph(self):
        content_type, format = self._accept()
        uri = self._uri()
        graph = self.handler.get(uri)
        if len(graph) == 0:
            q = construct_graph % { "agent" : uri.n3() }
            graph = self.handler.query(q)
            graph = Graph(graph.store, graph.identifier)
            if len(graph) == 0:
                abort(404, "No such graph: %s" % uri)
        if format == "html":
            c.graph = graph
            data = self._render_graph()
        else:
            data = graph.serialize(format=format)
            response.content_type = str(content_type)
        return data
