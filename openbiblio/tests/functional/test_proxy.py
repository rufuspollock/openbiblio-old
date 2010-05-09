from openbiblio.tests import *
from ordf.graph import Graph
from cStringIO import StringIO
from urllib import urlencode

class TestProxyController(TestController):
    def test_proxy(self):
        params = { "uri": "http://www.w3.org/People/EM/contact#me", "format": "text/n3" }
        response = self.app.get("/proxy?" + urlencode(params))
        data = StringIO(response.body)
        g = Graph()
        g.parse(data, format="n3")
