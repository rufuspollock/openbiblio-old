"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons.controllers import WSGIController
from pylons.templating import render_genshi as render
from pylons import tmpl_context as c, request, config, response
from pylons.controllers.util import abort

import openbiblio

class BaseController(WSGIController):

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        return WSGIController.__call__(self, environ, start_response)

    def __before__(self, action, **params):
        c.__version__ = openbiblio.__version__
        c.site_title = config.get('site_title', 'Bibliographica')
        # WARNING: you must use request.GET as request.params appears to alter
        # request.body (it gets url-encoded) upon call to request.params
        c.items_per_page = int(request.GET.get('items_per_page', 20))
        c.deliverance_enabled = bool(config.get('deliverance.enabled', ''))
        self._set_user()

    def _set_user(self):
        # TODO: (?) work out how to use repoze.who.identity stuff
        # identity = request.environ.get('repoze.who.identity') 
        c.user = request.environ.get('REMOTE_USER', None)
        c.remote_addr = request.environ.get('REMOTE_ADDR', 'Unknown IP Address')
        if c.remote_addr == 'localhost' or c.remote_addr == '127.0.0.1':
            # see if it was proxied
            c.remote_addr = request.environ.get('HTTP_X_FORWARDED_FOR',
                    '127.0.0.1')
        if c.user:
            c.author = c.user
        else:
            c.author = c.remote_addr

