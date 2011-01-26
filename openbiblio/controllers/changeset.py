import logging

from pylons import request, url, tmpl_context as c
from pylons.controllers.util import abort
from openbiblio.controllers.sparql import SparqlController
from openbiblio.lib.helpers import Page

log = logging.getLogger(__name__)

changeset_query = """
PREFIX cs: <http://purl.org/vocab/changeset/schema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?changeset ?date ?reason ?creator ?precedingchange ?changed
WHERE 
{?changeset a cs:ChangeSet .
 ?changeset cs:createdDate ?date .
 ?changeset cs:changeReason ?reason .
 ?changeset cs:creatorName ?creator .
 ?changeset cs:precedingChangeSet ?precedingchange .
 ?changeset cs:subjectOfChange ?changedthing .
 ?changedthing a ?changed 
} 
ORDER BY DESC(?date) %s
"""

class SPARQLResultObject(object):
    """Avoid undue disruption to existing code."""
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

class ChangesetController(SparqlController):
    def _render(self, reqformat):
        """Paginated version instead of superclass _render(),
        specialised for handling the changesets, received as
        a set of results in standard SPARQL XML result format"""
        if reqformat == 'json':
            return self.render("sparql_%s.html" % reqformat)
        else:
            seq = [SPARQLResultObject(
                        **dict(zip(c.bindings,res))) 
                            for res in c.results]
            npp = 2 if request.environ.get('paste.testing', False) else 20
            c.page = Page(seq, page=c.reqpage,
                          item_count=len(c.results),
                          items_per_page=npp)
            return self.render("sparql_paginated_%s.html" % reqformat)
    
    def index(self):
        """Skip to page 1, 
        """
        return self.page()
    
    def page(self):
        """Render the changesets, re-using existing pagination code"""
        reqformat = request.params.get('format', '')
        if reqformat == 'json':
            request.GET["format"] = "application/sparql-results+json"
        q = changeset_query % ("OFFSET %s LIMIT 50" % (c.reqpage * 50))
        log.info(q)
        request.GET["query"] = q
        return super(ChangesetController, self).index()
