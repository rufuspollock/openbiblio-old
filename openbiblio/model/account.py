from .base import *
    
class Account(Class, DomainObject):
    '''User accounts based on openids.
    
    OpenID url is used as identifier for the graph and object.
    '''
    rdfclass = FOAF.OnlineAccount
    accountServiceHomepage = predicate(FOAF.accountServiceHomepage)
    accountName = predicate(FOAF.accountName)
    
    def __init__(self, *av, **kw):
        kwa = kw.copy()
        kwa["skipClassMembership"] = True
        super(Account, self).__init__(*av, **kwa)
        if not kw.get("skipClassMembership"):
            self.type = FOAF.OnlineAccount
        
    @classmethod
    def get_by_openid(cls, openid):
        openid = u(openid)
        q = u"""
        SELECT DISTINCT ?account WHERE {
            ?person foaf:openid %s .
            ?person foaf:account ?account .
        }
        """ % openid.n3()
        for account, in handler.query(q):
            return cls.get_by_uri(account)

    @classmethod
    def get_by_name(cls, name):
        name = l(name)
        q = u"""
        SELECT DISTINCT ?account WHERE {
            ?account foaf:accountName %s
        }
        """ % name.n3()
        for account, in handler.query(q):
            return cls.get_by_uri(account)

    @classmethod
    def create(cls, openid, name=None, mbox=None):
        from uuid import uuid4
        account_name = uuid4() ## can do better than this!
        identifier = URIRef("http://bibliographica.org/account/%s" % account_name)
        graph = handler.get(identifier)
        account = cls(identifier=identifier, graph=graph)
        account.accountName = l(account_name)
        person = Person(graph=graph)
        person.openid = u(openid)
        if name is not None:
            person.name = l(name)
        if mbox is not None:
            if not mbox.startswith("mailto:"):
                mbox = "mailto:" + mbox
            person.mbox = u(mbox)
        person.account = account
        return account
    
    @property
    def owners(self):
        for person,p,o in self.graph.triples((None, FOAF.account, self.identifier)):
            yield Person(person, graph=self.graph)
            

class Person(Class, DomainObject):
    name = predicate(FOAF.name)
    openid = predicate(FOAF.openid)
    nick = predicate(FOAF.nick)
    mbox = predicate(FOAF.mbox)
    account = object_predicate(FOAF.account, Account)
    def __init__(self, *av, **kw):
        kwa = kw.copy()
        kwa["skipClassMembership"] = True
        super(Person, self).__init__(*av, **kwa)
        if not kw.get("skipClassMembership"):
            self.type = FOAF.Person
