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

class TestEntry:
    label = 'my-test-entry'

    @classmethod
    def setup_class(self):
        entry = model.Entry.create()
        entry.label = self.label
        self.entry_id = entry.identifier
        current_user = 'ouruser'
        entry.save(current_user, 'xyz')

    @classmethod
    def teardown_class(self):
        model.Entry.purge(self.entry_id)

    def test_01_get(self):
        entry = model.Entry.get_by_uri(self.entry_id)
        assert entry.label[0] == self.label, entry.label


class TestCollection:
    entrylabel = 'my-test-entry'
    label = 'my-test-collection'
    openid = 'http://myopen.id/2'

    @classmethod
    def setup_class(self):
        account = model.Account.create(self.openid)
        self.account_id = account.identifier
        entry = model.Entry.create()
        entry.label = self.entrylabel

        collection = model.Collection.create()
        collection.label = self.label
        collection.entries = [ entry ]
        collection.owner = account

        self.collection_id = collection.identifier
        self.entry_id = entry.identifier

        ctx = handler.context('ouruser', '')
        ctx.add(account.graph)
        ctx.add(collection.graph)
        ctx.add(entry.graph)
        ctx.commit()

    @classmethod
    def teardown_class(self):
        delete_all()

    def test_01_get(self):
        collection = model.Collection.get_by_uri(self.collection_id)
        assert collection.label[0] == self.label, collection.label
        account = list(collection.owner)[0]
        assert account.identifier == self.account_id, account
        entries = list(collection.entries)
        assert len(entries) == 1, entries

    def test_02_by_user(self):
        collection = model.Collection.by_user(self.account_id)
        assert collection.label[0] == self.label, collection

    def test_03_find(self):
        out = model.Collection.find()
        assert len(out) == 1, out
        assert self.collection_id == out[0].identifier, out

    def test_03_asdict(self):
        pass

