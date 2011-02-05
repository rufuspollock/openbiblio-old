from .base import *
from .entry import Entry
from .account import Account
    
class Collection(AnnotatibleTerms, DomainObject):
    '''Collections of entries (books, articles etc).
    '''
    rdfclass = BIBO.Collection
    label = predicate(RDFS.label)
    # owner = object_predicate(
    entries = object_predicate(RDFS.member, Entry)
    namespace = 'http://bibliographica.org/collection/'
    owner = object_predicate(BIBLIO_ONT.owner, Account)

    def __init__(self, *av, **kw):
        super(Collection, self).__init__(*av, **kw)
        self.type = BIBO.Collection

    @classmethod
    def by_user(cls, user):
        q = u"""
        PREFIX bb: <http://bibliographica.org/onto#>

        SELECT DISTINCT ?doc
        WHERE { 
          ?doc a bibo:Collection . 
          ?doc bb:owner %s
        }
        """ % user.n3()
        for collection, in handler.query(q):
            return cls.get_by_uri(collection)

