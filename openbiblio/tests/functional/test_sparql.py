from openbiblio.tests import *

class TestSparqlController(TestController):
    def test_index(self):
        response = self.app.get(url(controller='sparql', action='index'))
        # Test response...
