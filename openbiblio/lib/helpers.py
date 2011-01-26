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
from urllib import quote_plus

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

def to_int(s, minn=1, maxn=None, default=1):
    """Rough and ready converter to integer (with guard).
    """
    try:
        n = validators.Int().to_python(s)
    except:
        n = default
    n = max(minn, n) 
    if maxn:
        n = min(maxn, n)
    return n

