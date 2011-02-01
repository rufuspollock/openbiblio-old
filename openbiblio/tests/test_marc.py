from os import path
from openbiblio.lib.marc import Parser
#from pprint import pprint

TESTFILE = "test.mrc"

class TestClass(object):
    def __init__(self):
        self._parser = Parser(self.data_file())
        self._records = iter(self._parser)
    def data_file(self):
        here = path.dirname(__file__)
        data = path.join(here, "data")
        return path.join(data, TESTFILE)
    def record(self):
        return self._records.next()
    def test_00_read(self):
        for record in self._records:
            dict(record.items())
            record.sanity()
