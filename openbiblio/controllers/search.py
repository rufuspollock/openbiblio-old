"""
Xapian Full-Text Search - see L{ordf.pylons.xap}.
"""
from ordf.pylons.xap import XapianControllerFactory
from openbiblio.lib import base
from openbiblio import handler
from pylons import tmpl_context as c, request, session
from openbiblio.lib.helpers import Page, numberwang
from openbiblio.lib.base import BaseController, render

head = u"""
SPARQL PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX foaf: <ttp://xmlns.com/foaf/0.1/>
PREFIX dc: <http://purl.org/dc/terms/>
"""

where = """
    {
        ?uri a bibo:Document . 
        { ?uri dc:title ?s . ?s bif:contains '"%(query)s"' } UNION
        { ?uri dc:description ?s . ?s bif:contains '"%(query)s"' }
    } UNION {
        ?uri a foaf:Agent .
        ?uri foaf:name ?s . ?s bif:contains '"%(query)s"'
    }"""

search = head + """
SELECT DISTINCT ?uri ?title ?name ?series_title ?description
WHERE {""" + where + """ .
    OPTIONAL { ?uri dc:title ?title }
    OPTIONAL { ?uri dc:description ?description }
    OPTIONAL {
        ?uri dc:isPartOf ?series .
        ?series a bibo:Series .
        ?series dc:title ?series_title
    }
    OPTIONAL { ?uri foaf:name ?name }
} ORDER BY ?uri OFFSET %(offset)s LIMIT %(limit)s
"""

count = head + """
SELECT COUNT (?uri)
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
        vars = { "query": c.query, "offset": c.offset, "limit": c.items_per_page }

        cursor = self.handler.rdflib.store.cursor()

        query = count % vars
        #print query
        for c.item_count, in cursor.execute(query): pass
        #print "XXX", c.item_count

        query = search % vars
        #print query
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

        return self._render()
