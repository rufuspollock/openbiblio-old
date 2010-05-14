from openbiblio.tests import *

class TestHomeController(TestController):
    def test_index(self):
        response = self.app.get(url('home'))
        assert 'Welcome to' in response, response
        assert 'Search' in response, response
        # rather hacky test for search box
        assert 'Search by name' in response, response

