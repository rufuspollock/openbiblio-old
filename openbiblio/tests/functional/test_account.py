from openbiblio.tests import *

class TestAccountController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='account', action='index'))
        response = response.follow()
        assert 'Account' in response
        assert 'Login' in response

    def test_index_logged_in(self):
        response = self.app.get(url(controller='account', action='index'),
            extra_environ={'REMOTE_USER': 'xyz'})
        assert 'Account' in response, response
        assert 'xyz' in response

