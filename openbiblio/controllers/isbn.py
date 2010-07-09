import logging

from pylons import request, url, wsgiapp
from openbiblio.controllers.sparql import SparqlController

log = logging.getLogger(__name__)

isbn_query = """
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX obp: <http://purl.org/NET/obp/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT DISTINCT ?book ?title ?authorname ?pubname ?date%s
WHERE {
    ?book obp:isbn %s .
    ?book obp:work ?work .
    ?work dc:title ?title .
    OPTIONAL {
        ?book dc:date ?date
    } .
    OPTIONAL {
        ?book dc:publisher ?publisher .
        ?publisher foaf:name ?pubname
    } .
    OPTIONAL {
        ?work dc:contributor ?author .
        ?author foaf:name ?authorname
    }
}
"""

class IsbnController(SparqlController):
    def index(self, isbn=None):
        if isbn is None:
            q = isbn_query % (" ?isbn", '?isbn') + "LIMIT 10"
        else:
	    if isbn.endswith(".json"):
                request.GET["format"] = "application/sparql-results+json"
                isbn = isbn[:-5]
            q = isbn_query % ("", '"%s"' % isbn.replace("-", "").replace(" ", ""))
        request.GET["query"] = q
        return super(IsbnController, self).index()
