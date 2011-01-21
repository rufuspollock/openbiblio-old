"""
RDF Graph Controller - see L{ordf.pylons.graph}. 
"""

from pylons.controllers.util import abort
from openbiblio.lib import base
from openbiblio.lib.base import render, request, c, response
from openbiblio.lib.bibtex import Bibtex
from openbiblio import handler
from ordf.onto.controllers.graph import GraphController as _GraphController
from ordf.graph import Graph
from ordf.term import URIRef

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
        if uri.endswith("bibtex"):
            content_type = "text/x-bibtex"
            format = "bibtex"
            uri_str, _ = uri.rsplit(".", 1)
            uri = URIRef(uri_str)
        graph = handler.get(uri)
        if len(graph) == 0:
            graph.rollback()
            cursor = handler.rdflib.store.cursor()
            cursor.execute("SET result_timeout = 10000")
            q = construct_graph % { "agent" : uri.n3() }
            graph = handler.rdflib.store.sparql_query(q, cursor=cursor)
            graph = Graph(graph.store, identifier=graph.identifier) # ordf extensions
            cursor.close()
            if len(graph) == 0:
                abort(404, "No such graph: %s" % uri)
        if format == "html":
            c.graph = graph
            data = self._render_graph()
        elif format == "bibtex":
            b = Bibtex()
            b.load_from_graph(graph)
            data = b.to_bibtex()
            response.content_type = str(content_type)
            response.headers['Content-Location'] = "%s.bibtex" % b.uniquekey
            response.headers['Location'] = "%s.bibtex" % b.uniquekey
        else:
            data = graph.serialize(format=format)
            response.content_type = str(content_type)
        graph.rollback()
#        log.warn("XXX cursor: %s" % handler.rdflib.store._cursor)
        return data
