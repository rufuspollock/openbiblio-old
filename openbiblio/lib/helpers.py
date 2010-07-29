# coding=UTF-8
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
from webhelpers.html.tags import checkbox, password, text, submit, literal, \
    link_to
from webhelpers import paginate
from openbiblio.utils import rdf_getstr, render_html
from routes import url_for, redirect_to
from pylons import url

from genshi import XML
from genshi.builder import tag
from formencode import validators
from pylons.controllers.util import abort

class Page(paginate.Page):
    
    # Curry the pager method of the webhelpers.paginate.Page class, so we have
    # our custom layout set as default.
    def pager(self, *args, **kwargs):
        pagerformat = """<div class='pager'>$link_previous ~2~ $link_next \
                 (Page $page of $page_count)</div>"""
        kwargs.update(format=pagerformat, 
                      symbol_previous=u'« Prev', symbol_next=u'Next »'
        )
        return super(Page, self).pager(*args, **kwargs)

def numberwang(s, minn=1, maxn=500):
    """Rough and ready number guard, (see:
    http://en.wikipedia.org/wiki/Numberwang#Recurring_sketches)
    """
    uv = """Unsupported value: %s is not a integer in the range %s to %s"""
    try:
        n = validators.Int().to_python(s)
    except:
        abort(400, detail=uv % (s, minn, maxn))
    if n < minn or n > maxn: 
        abort(400, detail=uv % (n, minn, maxn))
    return n
