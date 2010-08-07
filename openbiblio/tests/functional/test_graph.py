from openbiblio.tests import *
from ordf.graph import Graph
from cStringIO import StringIO
from urllib import urlencode

class TestGraphController(TestController):
    def test_01_get(self):
        response = self.app.get(url("/graph", uri=test_graph))

    def test_02_n3(self):
        response = self.app.get(url("/graph", uri=test_graph, format="text/n3"))
        data = StringIO(response.body)
        g = Graph()
        g.parse(data, format="n3")

    def test_03_rdfxml(self):
        response = self.app.get(url("/graph", uri=test_graph, format="application/rdf+xml"))
        data = StringIO(response.body)
        g = Graph()
        g.parse(data, format="xml")

    def test_04_autoneg(self):
        response = self.app.get(url("/graph", uri=test_graph), headers={"Accept": "text/n3"})
        data = StringIO(response.body)
        g = Graph()
        g.parse(data, format="n3")

    def test_05_put(self):
        response = self.app.get(url("/graph", uri=test_graph, format="application/rdf+xml"))
        data = StringIO(response.body)
        g = Graph()
        g.parse(data, format="xml")

        ## now put it back
        body = g.serialize(format="pretty-xml")
        response = self.app.put(url("/graph", uri=test_graph), params=body, headers={"Content-type": "application/rdf+xml"})
        assert response.body.startswith("urn:uuid:")
