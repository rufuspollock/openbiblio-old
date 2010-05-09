from openbiblio.tests import *
from ordf.graph import Graph
from cStringIO import StringIO
from urllib import urlencode

class TestGraphController(TestController):
    def test_01_get(self):
        response = self.app.get(test_graph)

    def test_02_n3(self):
        params = { "format": "text/n3" }
        response = self.app.get(test_graph + "?" + urlencode(params)) 
        data = StringIO(response.body)
        g = Graph()
        g.parse(data, format="n3")

    def test_03_rdfxml(self):
        params = { "format": "application/rdf+xml" }
        response = self.app.get(test_graph + "?" + urlencode(params)) 
        data = StringIO(response.body)
        g = Graph()
        g.parse(data, format="xml")

    def test_04_uri(self):
        params = { "uri": test_graph, "format": "application/rdf+xml" }
        response = self.app.get("/graph" + "?" + urlencode(params))
        data = StringIO(response.body)
        g = Graph()
        g.parse(data, format="xml")

    def test_05_put(self):
        params = { "uri": test_graph, "format": "application/rdf+xml" }
        response = self.app.get("/graph" + "?" + urlencode(params))
        data = StringIO(response.body)
        g = Graph()
        g.parse(data, format="xml")

        ## now put it back
        response = self.app.put("/graph" + "?" + urlencode(params),
                           g.serialize(format="pretty-xml"))
        assert response.body.startswith("urn:uuid:")
