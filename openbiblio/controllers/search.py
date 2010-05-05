import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from openbiblio.lib.base import *
from openbiblio import searchxapian

log = logging.getLogger(__name__)

class SearchController(BaseController):

    def index(self):
        c.q = request.params.get('q', '')
        index = searchxapian.SearchIndex.default_index()

        if c.q:
            c.had_query = True
            c.results, c.size = index.result_list(c.q)


        return render('search')
