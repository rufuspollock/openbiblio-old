import logging

from pylons import request, url, wsgiapp
from openbiblio.lib.base import BaseController, render
try:
    from json import dumps
except ImportError:
    from simplejson import dumps

log = logging.getLogger(__name__)

isbn_query = u"""
SPARQL
PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX dc: <http://purl.org/dc/terms/>

SELECT DISTINCT ?doc ?title ?description ?contributor_name ?issued ?publisher_name
WHERE { 
  ?doc a bibo:Document . 
  ?doc bibo:isbn <urn:isbn:%(isbn)s> .
  ?doc dc:title ?title .
  OPTIONAL { ?doc dc:description ?description } .
  OPTIONAL { ?doc dc:issued ?issued } .
  OPTIONAL { ?doc dc:publisher ?publisher . ?publisher skos:notation ?publisher_name }
  OPTIONAL { ?doc dc:contributor ?contributor . ?contributor skos:notation ?contributor_name }
}
"""

class IsbnController(BaseController):

    def index(self, isbn=None):
        if isbn is None:
            return self.render("isbn.html")

        isbn = isbn.replace("-", "").replace(" ", "")
        q = isbn_query % { "isbn": isbn }

        cursor = self.handler.rdflib.store.cursor()
        
        results = {}
        for doc, title, description, cname, issued, pubname in cursor.execute(q):
            rec = results.setdefault(doc, {})
            rec["uri"] = doc
            if title: rec["title"] = title
            if description: rec["description"] = description
            if cname:
                clist = rec.setdefault("contributors", [])
                clist.append({ "name": cname })
            if issued: rec["issued"] = issued
            if pubname: rec["publisher"] = { "name": pubname }

        return dumps(results.values())
