from .base import *
from entity import Entity
from subject import Concept
from misc import Label

register_ns("BIBLIOENTRY", Namespace("http://bibliographica.org/entry/"))
register_ns("OV", Namespace("http://open.vocab.org/terms/"))
register_ns("ISBD", Namespace("http://iflastandards.info/ns/isbd/elements/"))
from ordf.namespace import BIBLIOENTRY, DC, FOAF, BIBO, OV, RDFS, ISBD

class Entry(AnnotatibleTerms, DomainObject):
    '''A catalogue entry (or record).
    
    In an FRBR sense this is probably best thought of as a manifestation.
    '''
    namespace = BIBLIOENTRY

    label = predicate(RDFS.label)
    title = predicate(DC.title)
    bnb_id = predicate(BIBO.identifier)
    isbn = predicate(BIBO.isbn)
    bl_id = predicate(OV.blid)
    creators = object_predicate(DC.contributor, Entity) 
    publishers = object_predicate(DC.publisher, Entity) 
    subjects = object_predicate(DC.subject, Concept)
    issued = predicate(DC.issued)
    seealso = predicate(RDFS.seeAlso)
    descriptions = predicate(DC.description)
    edition = predicate(ISBD.hasEditionStatement)
    language = object_predicate(DC.language, Label)
    extent = object_predicate(DC.extent, Label)

    def __init__(self, *av, **kw):
        super(Entry, self).__init__(*av, **kw)
        self.type = BIBO.Document

    @classmethod
    def find(self, limit=20, offset=0):
        ### should really use a lens (upgrade the bibo lens to
        ### understand about accounts and just display the
        ### account graph in here. no need for this find
        ### method...
        sparql_select = '''
        SELECT DISTINCT ?id
        WHERE {
            ?id a %(class_)s
        } OFFSET %(offset)s LIMIT %(limit)s
        '''
        params = dict(
            class_='<%s>' % FOAF.OnlineCollection,
            limit=limit,
            offset=offset)
        query = sparql_select % params
        def cvt(qresult):
            return URIRef(qresult[0])
        results = map(cvt, handler.query(query))
        results = [self.get_by_uri(uri) for uri in results]
        return results


