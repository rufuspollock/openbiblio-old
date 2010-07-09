# -*- coding: utf-8 -*-
import re
from openbiblio.tests import *
import htmllib, formatter

import logging
log = logging.getLogger(__name__)

class PaginatedHTMLParser(htmllib.HTMLParser):
    def __init__(self, formatter) :
        htmllib.HTMLParser.__init__(self, formatter)
        self.isa = False
        self.next = self.prev = None
    
    def start_a(self, attrs):
        for attr in attrs:
            if not self.isa and attr[0] == 'class' and attr[1] == 'pager_link':
                self.isa = True
            elif self.isa and attr[0] == 'href':
                self.url = attr[1]
    
    def end_a(self):
        self.isa = False
    
    def handle_data(self, data):
        if self.isa and 'Next' in data:
            self.next = self.url
        elif self.isa and 'Prev' in data:
            self.prev = self.url
    

class TestChangesetController(TestController):
    changesets = True
    skip = False
    parser = PaginatedHTMLParser(formatter.NullFormatter())
    def setUp(self):
        Fixtures.setUp()
        response = self.app.get(url('changesets'))
        assert response.status_int == 200
        if not '''"precedingchange": {"type": "uri"''' in response:
            self.skip = True
        
    def test_index_default(self):
        """Check an index page is returned."""
        if not self.skip:
            response = self.app.get(url('changesets'))
            assert response.status_int == 200
            assert '''"precedingchange": {"type": "uri"''' in response
    
    def test_index_html(self):
        """Check html is returned when requested."""
        if not self.skip:
            response = self.app.get(url('changesets', format='html'))
            assert response.status_int == 200
            assert '''<span class="pager_curpage">1</span>''' in response
    
    def test_index_json(self):
        """Check json is returned when requested."""
        if not self.skip:
            response = self.app.get(url('changesets', format='json'))
            assert response.status_int == 200
            assert '''"precedingchange": {"type": "uri"''' in response
    
    def test_paginate(self):
        """Show paginated changesets."""
        if not self.skip:
            response = self.app.get(url('changesets', format='html', page=2))
            assert response.status_int == 200
            assert '''<span class="pager_curpage">2</span>''' in response
    
    def test_pagination_page_2(self):
        """Show page 2 of paginated results."""
        if not self.skip:
            response = self.app.get(url('changesets', format='html', page=2))
            assert response.status_int == 200
            assert '''<span class="pager_curpage">2</span>''' in response
    
    def test_next_page(self):
        """Check functioning of 'Next' link."""
        if not self.skip:
            response = self.app.get(url('changesets', format='html'))
            assert response.status_int == 200
            self.parser.feed(response.body)
            if self.parser.next:
                newurl = self.parser.next+"&amp;format='html'"
                response = self.app.get(newurl)
            assert '''<span class="pager_curpage">2</span>''' in response
    
    def test_prev_page(self):
        """Check functioning of 'Prev' link."""
        if not self.skip:
            response = self.app.get(
                                url('changesets', page='4', format='html'))
            assert response.status_int == 200
            self.parser.feed(response.body)
            if self.parser.prev:
                newurl = self.parser.prev+"&amp;format='html'"
                response = self.app.get(newurl)
            assert '''<span class="pager_curpage">3</span>''' in response
    



