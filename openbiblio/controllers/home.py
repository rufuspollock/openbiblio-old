import logging

from pylons import request, tmpl_context as c, config
from pylons.controllers.util import abort

from openbiblio.lib import namespace
from openbiblio.lib.base import BaseController, render
from openbiblio import handler

log = logging.getLogger(__name__)


class HomeController(BaseController):
    def index(self):
        cursor = handler.rdflib.store.cursor()
        q = """
PREFIX bibo: <http://purl.org/ontology/bibo/>
SELECT COUNT(?d) WHERE { ?d a bibo:Document }
"""
        for c.work_total, in handler.rdflib.query(q, cursor): pass
        cursor.close()
        return render('home/index.html')

    def about(self):
        return self._proxy()

    def get_involved(self):
        return self._proxy()

    def _proxy(self):
        if c.deliverance_enabled:
            # wordpress requires trailing '/' (o/w get redirect)
            if not request.environ['PATH_INFO'].endswith('/'):
                request.environ['PATH_INFO'] = request.environ['PATH_INFO'] + '/'
            return self.deliverance(request.environ, self.start_response)
        else:
            abort(404)
    
    @property
    def deliverance(self):
        from swiss.deliveranceproxy import create_deliverance_proxy
        # where we are proxying from
        proxy_base_url = config['deliverance.dest']
        theme_html = render('home/index.html')
        if not hasattr(self, '_deliverance'):
            self._deliverance = create_deliverance_proxy(proxy_base_url, theme_html)
            # self._deliverance = create_deliverance_proxy()
        return self._deliverance

