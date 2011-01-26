from ordf.term import URIRef
# from openbiblio.tests import 
import openbiblio.model as model

class TestAccount:
    openid = 'http://myopen.id'
    ident = URIRef(openid)
    name = 'Mr Jones and me'

    @classmethod
    def setup_class(self):
        user = model.Account.create(self.openid)
        assert user.identifier == self.ident
        user.openid = self.openid
        user.name = self.name
        current_user = 'ouruser'
        user.save(current_user, 'xyz')

    @classmethod
    def teardown_class(self):
        model.Account.purge(self.openid)

    def test_01_get_null(self):
        ## TODO: always returns True.
        ## Need to implement a check for graphs existence
        # out = model.Account.get(self.openid + 'madeup')
        # assert out == None, out
        pass

    def test_02_get(self):
        out = model.Account.get(self.openid)
        # print [(s,p,o) for (s,p,o) in out.graph.triples((None,None,None))]
        assert out.identifier == self.ident
        assert out.name[0] == self.name, out.name
        assert out.openid[0] == self.openid, out

    def test_03_find(self):
        out = model.Account.find()
        assert self.ident == out[0], out
        assert self.ident in out, out

