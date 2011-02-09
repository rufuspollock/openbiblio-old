import uuid

from ordf.namespace import register_ns, Namespace
register_ns("biblio-ont", Namespace("http://bibliographica.org/onto#"))

import ordf.namespace
from ordf.namespace import FOAF, RDFS, BIBO
from ordf.namespace import BIBLIO_ONT
from ordf.term import URIRef, Node, Literal
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

    @classmethod
    def find(self, limit=20, offset=0):
        q = '''
        SELECT DISTINCT ?id
        WHERE {
            ?id a %(class_)s
        } OFFSET %(offset)s LIMIT %(limit)s
        ''' % dict(
            class_='%s' % self.rdfclass.n3(),
            limit=limit,
            offset=offset)
        # have to do this first otherwise get closed cursor error
        results = [ u(res[0]) for res in handler.query(q) ]
        results = [ self.get_by_uri(uri) for uri in results ]
        return results

    def to_dict(self):
        out = {'id': str(self.identifier)}
        for s,p,o in self.graph.triples((None,None,None)):
            if s == self.identifier:
                if isinstance(o, Literal):
                    val = o.toPython()
                    if o.datatype is None:
                        val = unicode(val)
                else:
                    val = o.n3()
                # convert predicates to nice strings using namespace nicknames
                ourp = str(p)
                for ns_nick, ns_uri in ordf.namespace.namespaces.items():
                    ourns_uri = str(ns_uri) 
                    if ourp.startswith(ourns_uri):
                        ourp = ourp[len(ourns_uri):]
                        break
                out[ourp] = val
        return out


    def from_dict(self,objectdict):
        for key, value in objectdict.items():
# need to distinguish between lits and uris, next commit hopefully!
            self.__setattr__(key, value)


