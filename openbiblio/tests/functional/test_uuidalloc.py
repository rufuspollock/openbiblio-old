from openbiblio.tests import *

class TestUuidallocController(TestController):
    def test_index(self):
        response = self.app.get(url(controller='uuidalloc', action='index'))
        assert len(response.body) == 38
