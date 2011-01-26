from zope.interface import implements
from repoze.who.interfaces import IAuthenticator

from openbiblio.model import Account

class OpenIDAuthenticator(object):
    implements(IAuthenticator)
    
    def authenticate(self, environ, identity):
        if 'repoze.who.plugins.openid.userid' in identity:
            openid = identity.get('repoze.who.plugins.openid.userid')
            # Will always return not None so have to test openid
            user = Account.get(openid)
            if not user.openid:
                username = identity.get('repoze.who.plugins.openid.username')
                if not username or not len(username.strip()) \
                    or not Account.VALID_USERNAME.match(username):
                    username = openid
                # we do not enforce uniqueness of username ...
                user = Account(openid=openid, username=username,
                        fullname=identity.get('repoze.who.plugins.openid.fullname'),
                        email=identity.get('repoze.who.plugins.openid.email'))
                user.save(user=openid, message='New account: %s' % openid)
            return openid
        return None

