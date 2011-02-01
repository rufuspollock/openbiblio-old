from openbiblio.tests import Fixtures

from openbiblio import handler
from openbiblio.lib.bibtex import Bibtex

def setup():
   Fixtures.setUp() 

class TestBibtex:
    def test_get_blank_instance(self):
        b = Bibtex()
        assert b.uri == None

    def test_load_from_uri(self):
        b = Bibtex()
        assert b.uri == None # make sure it's None
        g = handler.get("http://bnb.bibliographica.org/entry/GB9361575")
        b.load_from_graph(g)
        assert b.uri != None # make sure it's not None
        print b
        #assert False 

