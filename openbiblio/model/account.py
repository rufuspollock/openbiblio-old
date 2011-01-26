from ordf.namespace import FOAF
from ordf.term import URIRef
from ordf.vocab.owl import AnnotatibleTerms, predicate
from ordf.graph import Graph

from openbiblio import handler


class DomainObject(object):
    @classmethod
    def _uri(self, uri):
        if isinstance(uri, basestring):
            return URIRef(uri)
        else:
            return uri

    @classmethod
    def create(self, uri):
        '''Create an object with uri `uri` and associated to a graph identified
        by same uri'''
        uri = self._uri(uri)
        graph = Graph(identifier=uri)
        out = self(uri, graph=graph)
        return out
    
    def save(self, user, message=''):
        ctx = handler.context(user, message)
        ctx.add(self.graph)
        ctx.commit()

    @classmethod
    def get(self, uri):
        uri = self._uri(uri)
        graph = handler.get(uri)
        obj = self(uri, graph=graph)
        return obj

    @classmethod
    def purge(self, uri):
        uri = self._uri(uri)
        graph = handler.get(uri)
        if graph:
            graph.remove((None, None, None))

    
    # Hand creating sparql is not going to scale!
    # ww recommended alternative requires another dependency (telescope)
    # http://packages.python.org/ordf/odm.html#queries-and-filters
    sparql_select_base = '''
SPAQRL

'''

class Account(AnnotatibleTerms, DomainObject):
    '''User accounts based on openids.
    
    OpenID url is used as identifier for the graph and object.
    '''
    def __init__(self, *av, **kw):
        super(Account, self).__init__(*av, **kw)
        self.type = FOAF.Person
    name = predicate(FOAF.name)
    openid = predicate(FOAF.openid)
    nick = predicate(FOAF.nick) 

    sparql_select = '''
SPARQL

SELECT DISTINCT ?id
WHERE {
    ?id a %(class_)s
} OFFSET %(offset)s LIMIT %(limit)s
'''

    @classmethod
    def find(self, limit=20, offset=0):
        params = dict(
            class_='<%s>' % FOAF.Person,
            limit=limit,
            offset=offset)
        query = self.sparql_select % params
        try:
            cursor = handler.rdflib.store.cursor()
            def cvt(qresult):
                # get a tuple out (id,)
                return URIRef(qresult[0])
            results = map(cvt, cursor.execute(query))
            return results
        finally:
            cursor.close()
