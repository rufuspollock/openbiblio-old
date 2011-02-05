import pprint

from ordf.term import URIRef

from openbiblio.tests import delete_all
from openbiblio import handler
import openbiblio.model as model


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

    def test_04_asdict(self):
        collection = model.Collection.get_by_uri(self.collection_id)
        out = collection.as_dict()
        pprint.pprint(out)
        assert out['rdfs:label'] == self.label
        assert out['id'] == str(self.collection_id)
        assert out['biblio-ont:owner'] == self.account_id.n3()

