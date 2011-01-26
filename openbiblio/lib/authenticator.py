from zope.interface import implements
from repoze.who.interfaces import IAuthenticator

from openbiblio.model import Account

class OpenIDAuthenticator(object):
    implements(IAuthenticator)
    
    def authenticate(self, environ, identity):
        if 'repoze.who.plugins.openid.userid' in identity:
            openid = identity.get('repoze.who.plugins.openid.userid')
            user = Account.get_by_openid(openid)
            if user is None:
                username = identity.get('repoze.who.plugins.openid.username')
                if not username or not len(username.strip()) \
                    or not Account.VALID_USERNAME.match(username):
                    username = openid
                # we do not enforce uniqueness of username ...
                user = Account.create(
                    openid=openid,
                    name=identity.get('repoze.who.plugins.openid.fullname'),
                    mbox=identity.get('repoze.who.plugins.openid.email')
                )
#                user = Account(openid=openid,username=username,
#                        fullname=
#                        email=identity.get('repoze.who.plugins.openid.email'))
#                user.save(user=openid, message='New account: %s' % openid)
            return user.accountName[0]
        return None

