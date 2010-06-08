from openbiblio.tests import *

class TestIsbnController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='isbn', action='index'))
        # Test response...
