"""
Xapian Full-Text Search - see L{ordf.pylons.xap}.
"""
from ordf.pylons.xap import XapianControllerFactory
from openbiblio.lib import base
from openbiblio import handler
from pylons import tmpl_context as c, request, session
from openbiblio.lib.helpers import Page, numberwang

XapianSearchController = XapianControllerFactory(base, handler)

class SearchController(XapianSearchController):
    
    def _render(self):
        """Paginated version instead of superclass _render(),
        specialised for handling the result, received as
        a set of Xapian results"""
        c.page = Page(list(c.results), 
                      page=c.reqpage if hasattr(c, 'reqpage') else 1,
                      item_count=len(c.results),
                      q=c.query)
        return self.render("search_paginated.html")
    
    def page(self):
        """Render the search results, re-using existing pagination code"""
        from formencode import validators
        request.GET['limit'] = c.limit 
        request.GET['offset'] = c.offset
        return super(SearchController, self).index()
