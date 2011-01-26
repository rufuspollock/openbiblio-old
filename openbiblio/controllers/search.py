"""
Xapian Full-Text Search - see L{ordf.pylons.xap}.
"""
from ordf.pylons.xap import XapianControllerFactory
from openbiblio.lib import base
from openbiblio import handler
from pylons import tmpl_context as c, request, session
from openbiblio.lib.helpers import Page
from openbiblio.lib.base import BaseController, render

where = u"""
   ?uri a bibo:Document .
    { ?uri dcterms:title ?s . ?s bif:contains '"%(query)s"' } UNION
    { ?uri dcterms:description ?s . ?s bif:contains '"%(query)s"' } UNION
    { ?uri dcterms:contributor ?author .
      ?author foaf:name ?s . ?s bif:contains '"%(query)s"'  }"""

search = u"""
SPARQL
PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT DISTINCT ?uri ?title ?name ?series_title ?description
WHERE {""" + where + """ .
    OPTIONAL { ?uri dcterms:title ?title }
    OPTIONAL { ?uri dcterms:description ?description }
    OPTIONAL {
        ?uri dcterms:isPartOf ?series .
        ?series a bibo:Series .
        ?series dcterms:title ?series_title
    }
    OPTIONAL { ?uri dcterms:contributor ?author . ?author foaf:name ?name }
} ORDER BY ?uri OFFSET %(offset)s LIMIT %(limit)s
"""

count = u"""
SPARQL
PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT COUNT (DISTINCT ?uri)
WHERE {""" + where + "}"


class SearchController(BaseController):
    
    def _render(self):
        """Paginated version instead of superclass _render(),
        specialised for handling the result, received as
        a set of Xapian results"""
        c.page = Page(list(c.results), 
                      page=c.reqpage if hasattr(c, 'reqpage') else 1,
                      item_count=c.item_count,
                      presliced_list=True,
                      q=c.query)
        return self.render("search_paginated.html")
   
    def index(self):
        if c.query:
            c.query = c.query.replace(u"'", u"").replace(u'"', u"")
            vars = { "query": c.query, "offset": c.offset, "limit": c.items_per_page }

            cursor = handler.rdflib.store.cursor()

            query = count % vars
            for c.item_count, in cursor.execute(query): pass

            query = search % vars
            def _rdict(row):
                d = dict(zip(("uri", "title", "name", "series", "description"), row))
                if d["title"]:
                    d["label"] = d["title"]
                elif d["name"]:
                    d["label"] = d["name"]
                else:
                    d["label"] = "Unknown"
                return d
            c.results = [_rdict(x) for x in cursor.execute(query)]
            cursor.close()
        else:
            c.results, c.item_count = [], 0


        return self._render()
