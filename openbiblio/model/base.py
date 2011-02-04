import uuid

from ordf.namespace import register_ns, Namespace
register_ns("BIBLIO_ONT", Namespace("http://bibliographica.org/onto#"))

from ordf.namespace import FOAF, RDFS, BIBO
from ordf.namespace import BIBLIO_ONT
from ordf.term import URIRef, Node
from ordf.vocab.owl import Class, AnnotatibleTerms, predicate, object_predicate
from ordf.graph import Graph


from openbiblio import handler
from openbiblio.lib.utils import coerce_uri as u, coerce_literal as l

class DomainObject(object):
    namespace = 'http://bibliographica.org/'
    @classmethod
    def new_identifier(cls):
        '''Creates new identifiers in this domain objects namespace using
        uuids'''
        return cls.namespace + str(uuid.uuid4())

    @classmethod
    def create(cls, uri=None):
        '''Create an object with uri `uri` and associated to a graph identified
        by same uri'''
        if uri is None:
            uri = cls.new_identifier()
        uri = u(uri)
        graph = Graph(identifier=uri)
        out = cls(uri, graph=graph)
        return out

    @classmethod
    def get_by_uri(cls, uri):
        uri = u(uri)
        graph = handler.get(uri)
        obj = cls(uri, graph=graph)
        return obj

    @classmethod
    def purge(self, uri):
        uri = u(uri)
        handler.remove(Graph(identifier=uri))
    
    def save(self, user, message=''):
        if not isinstance(self.graph.identifier, URIRef):
            raise TypeError(self.graph.identifier, type(self.graph.identifier), "graph identifier must be URIRef")
        ctx = handler.context(user, message)
        ctx.add(self.graph)
        ctx.commit()
    
    def __str__(self):
        return self.graph.serialize(format='n3')

