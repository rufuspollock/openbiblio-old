from ordf.term import URIRef

from openbiblio.tests import delete_all
from openbiblio import handler
import openbiblio.model as model

class TestAccount:
    openid = 'http://myopen.id'
    ident = URIRef(openid)
    name = 'Mr Jones and me'
    email = 'xyz@openbiblio.net'

    @classmethod
    def setup_class(self):
        account = model.Account.create(self.openid, self.name, self.email)
        self.account_id = account.identifier
        current_user = 'ouruser'
        account.save(current_user, 'xyz')

    @classmethod
    def teardown_class(self):
        delete_all()

    def test_01_get_null(self):
        out = model.Account.get_by_openid(self.openid + 'madeup')
        assert out == None, out

    def test_02_get(self):
        acc = model.Account.get_by_uri(self.account_id)
        acc = model.Account.get_by_openid(self.openid)
        assert acc.identifier == self.account_id, acc.identifier
        out = [x for x in acc.owners][0]
        for (s,p,o) in out.graph.triples((None,None,None)):
            print s,p,o
        # print [(s,p,o) for (s,p,o) in out.graph.triples((None,None,None))]
        assert out.name[0] == self.name, out.name
        assert str(out.openid[0]) == self.openid, out.openid[0]

    def test_03_find(self):
        out = model.Account.find()
        assert len(out) == 1, out
        assert self.account_id == out[0].identifier, out

