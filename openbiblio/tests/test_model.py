from ordf.term import URIRef
# from openbiblio.tests import 
import openbiblio.model as model

class TestAccount:
    openid = 'http://myopen.id'
    ident = URIRef(openid)

    @classmethod
    def teardown_class(self):
        model.Account.purge(self.openid)

    def test_01(self):
        ## TODO: always returns True.
        ## Need to implement a check for graphs existence
        # out = model.Account.get(self.openid)
        # assert out == None, out

        user = model.Account.create(self.openid)
        assert user.identifier == self.ident
        user.openid = self.openid
        name = 'Mr Jones and me'
        user.name = name
        current_user = 'ouruser'
        user.save(current_user, 'xyz')

        out = model.Account.get(self.openid)
        # print [(s,p,o) for (s,p,o) in out.graph.triples((None,None,None))]
        assert out.identifier == self.ident
        assert out.name[0] == name, out.name
        assert out.openid[0] == self.openid, out

