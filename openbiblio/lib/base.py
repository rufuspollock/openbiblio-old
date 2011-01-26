"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons.controllers import WSGIController
from pylons.templating import render_genshi as render
from pylons import tmpl_context as c, request, config, response, session
from pylons.controllers.util import abort

import openbiblio
from openbiblio.lib.helpers import to_int
from ordf.onto.lib.base import BaseController as OBaseController
import pkg_resources

class BaseController(OBaseController):

    def __before__(self, action, **params):
        c.site_title = config.setdefault('site_title', 'Non-Bibliographica')
        # Why doesn't setting strict_c to False avoid this ...?
        for attr, val in {'url':'', 'bindings':[], 'boolean':False, 
                          'warnings': None, 'person_total': 0, 
                          'manif_total': 0, 'work_total': 0, 'results': [],
                          'read_user': '', 'graph':None}.items():
            if not hasattr(c, attr): setattr(c, attr, val)

        super(BaseController, self).__before__(action, **params)

        # WARNING: you must use request.GET as request.params appears to alter
        # request.body (it gets url-encoded) upon call to request.params
        c.q = c.query = request.GET.get("q", None)
        c.reqpage = to_int(request.params.get('page', 1),maxn=50)
        c.limit = to_int(request.GET.get('limit', '500'), maxn=5000)
        c.items_per_page = to_int(request.GET.get('items_per_page', 20))
        c.offset = (c.reqpage-1) * c.items_per_page
        c.deliverance_enabled = bool(config.get('deliverance.enabled', ''))
        self._set_user()
