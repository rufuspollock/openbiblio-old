import openbiblio.model as model

class TestEntry:
    label = 'my-test-entry'

    @classmethod
    def setup_class(self):
        entry = model.Entry.create()
        entry.label = self.label
        self.entry_id = entry.identifier
        entry.bl_id = "123456789"
        entry.isbn = "urn:isbn:123456789"
        current_user = 'ouruser'
        entry.save(current_user, 'xyz')

    @classmethod
    def teardown_class(self):
        model.Entry.purge(self.entry_id)

    def test_01_get(self):
        entry = model.Entry.get_by_uri(self.entry_id)
        assert entry.label[0] == self.label, entry.label
        assert entry.isbn[0] == "urn:isbn:123456789", entry.isbn
        assert entry.bl_id[0] == "123456789", entry.bl_id

    def test_02_get_real_data(self):
        entry = model.Entry.get_by_uri("http://bnb.bibliographica.org/entry/GB9361575")
        assert entry.isbn[0] == "0575055774", entry.isbn
        assert entry.bl_id[0] == "010078938", entry.bl_id
        assert entry.title[0] == "Rama revealed", entry.title
        creator_names = set([x.name[0] for x in entry.creators])
        assert creator_names == set(["Clarke, Arthur C. (Arthur Charles)", "Lee, Gentry."]), creator_names
        for author in entry.creators:
            if author.name[0] == "Clarke, Arthur C. (Arthur Charles)":
                bday = author.birth.next()
                assert bday.date[0] == "1917", bday.date[0]



class TestEntity:
    @classmethod
    def setup_class(self):
        entity = model.Entity.create()
        self.entity_id = entity.identifier
        entity.name = "Smith, John,"
        entity.marc_text = "Smith, John, b1990"
        entity.save('entityuser','xyz')
    
    @classmethod
    def teardown_class(self):
        model.Entity.purge(self.entity_id)

    def test_01_get(self):
        entity = model.Entity.get_by_uri(self.entity_id)
        assert entity.name[0] == "Smith, John,", entity.name
        assert entity.marc_text[0] == "Smith, John, b1990", entity.marc_text

