from ordf.namespace import FOAF
from ordf.term import URIRef, Node
from ordf.vocab.owl import AnnotatibleTerms, predicate
from ordf.graph import Graph

from openbiblio import handler

def _uri(x):
    if not isinstance(x, URIRef):
        if isinstance(x, Node):
            raise TypeError(x, type(x), "must be either basestring or URIRef")
        x = URIRef(x)
    return x

class DomainObject(object):
    @classmethod
    def create(cls, uri):
        '''Create an object with uri `uri` and associated to a graph identified
        by same uri'''
        uri = _uri(uri)
        graph = Graph(identifier=uri)
        out = cls(uri, graph=graph)
        return out

    @classmethod
    def get(cls, uri):
        uri = _uri(uri)
        graph = handler.get(uri)
        obj = cls(uri, graph=graph)
        return obj

    @classmethod
    def purge(self, uri):
        uri = _uri(uri)
        handler.remove(Graph(identifier=uri))
    
    def save(self, user, message=''):
        if not isinstance(self.graph.identifier, URIRef):
            raise TypeError(self.graph.identifier, type(self.graph.identifier), "graph identifier must be URIRef")
        ctx = handler.context(user, message)
        ctx.add(self.graph)
        ctx.commit()

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
