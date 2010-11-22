"""
RDF Graph Controller - see L{ordf.pylons.graph}. 
"""

from pylons.controllers.util import abort
from openbiblio.lib import base
from openbiblio.lib.base import render, request, c, response
from openbiblio import handler
from ordf.onto.controllers.graph import GraphController as _GraphController
from ordf.graph import Graph

construct_graph = """\
DEFINE input:same-as "yes"
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
CONSTRUCT {
    %(agent)s a foaf:Person .
    %(agent)s ?a_p ?a_o .
    ?work a bibo:Document .
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
        uri = self._uri()
        content_type, format = self._accept(uri)
        graph = self.handler.get(uri)
        if len(graph) == 0:
            cursor = self.handler.rdflib.store.cursor()
            cursor.execute("SET result_timeout = 10000")
            q = construct_graph % { "agent" : uri.n3() }
            graph = self.handler.rdflib.store.sparql_query(q, cursor=cursor)
            graph = Graph(graph.store, identifier=graph.identifier) # ordf extensions
            cursor.close()
            if len(graph) == 0:
                abort(404, "No such graph: %s" % uri)
        if format == "html":
            c.graph = graph
            data = self._render_graph()
        else:
            data = graph.serialize(format=format)
            response.content_type = str(content_type)
        self._set_location(uri, format)
        return data
