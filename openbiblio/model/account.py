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


class Account(AnnotatibleTerms, DomainObject):
    def __init__(self, *av, **kw):
        super(Account, self).__init__(*av, **kw)
        self.type = FOAF.Person
    name = predicate(FOAF.name)
    openid = predicate(FOAF.openid)
    nick = predicate(FOAF.nick) 
    
