from .base import *

register_ns("BIBLIOENTRY", Namespace("http://bibliographica.org/entry/"))
from ordf.namespace import BIBLIOENTRY, FOAF, SKOS, BIO

class Birthdate(AnnotatibleTerms, DomainObject):
    '''A bio:Birth event'''

    date = predicate(BIO.date)
    def __init__(self, *av, **kw): 
        super(Birthdate, self).__init__(*av, **kw)   
        self.type = BIO.Birth

class Deathdate(AnnotatibleTerms, DomainObject):
    '''A bio:Death event'''

    date = predicate(BIO.date)
    def __init__(self, *av, **kw): 
        super(Deathdate, self).__init__(*av, **kw)   
        self.type = BIO.Death

class Entity(AnnotatibleTerms, DomainObject):
    '''An entity - person, organisation and so on.
    '''
    namespace = BIBLIOENTRY

    marc_text = predicate(SKOS.notation)
    name = predicate(FOAF.name)
    birthdate = object_predicate(BIO.event, Birthdate)
    deathdate = object_predicate(BIO.event, Deathdate)
    
    def __init__(self, *av, **kw):
        super(Entity, self).__init__(*av, **kw)
        self.type = FOAF.Agent

    @classmethod
    def find(self, limit=20, offset=0):
        ### should really use a lens (upgrade the bibo lens to
        ### understand about accounts and just display the
        ### account graph in here. no need for this find
        ### method...
        sparql_select = '''
        SELECT DISTINCT ?id
        WHERE {
            ?bnode a %(class_)s .
            ?bnode <http://www.w3.org/2002/07/owl#sameAs> ?id .
        } OFFSET %(offset)s LIMIT %(limit)s
        '''
        params = dict(
            class_='<%s>' % FOAF.Agent,
            limit=limit,
            offset=offset)
        query = sparql_select % params
        def cvt(qresult):
            return URIRef(qresult[0])
        results = map(cvt, handler.query(query))
        results = [self.get_by_uri(uri) for uri in results]
        return results

