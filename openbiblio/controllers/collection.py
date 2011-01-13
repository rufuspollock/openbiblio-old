import logging
import uuid
try:
    from json import dumps
except ImportError:
    from simplejson import dumps

from pylons import request, url, wsgiapp
from pylons.decorators import jsonify

from openbiblio.lib.base import BaseController, render, request, c, abort
from openbiblio import handler
log = logging.getLogger(__name__)

collection_query = u"""
SPARQL
PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX bb: <http://bibliographica.org/onto#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX data: <http://bibliographica.org/collection/>

SELECT DISTINCT ?doc ?title ?description ?user_name
WHERE { 
  ?doc a bb:Collection . 
  ?doc bb:user '%(user_name)s' .
  ?doc bb:user ?user_name .
  OPTIONAL { ?doc dc:title ?title } .
  OPTIONAL {  ?doc dc:description ?description }
}
"""

class CollectionController(BaseController):

    def index(self, collection=None):
        if collection is None:
            # return self.render("collection.html")
            return 'Collection API'

    @jsonify
    def create(self):
        if not c.user:
            abort(401)
        values = {}
        collection_uri = create_collection(c.user, values)
        return {'uri': collection_uri}

    def update(self, collection):
        uri = self._uri()
        graph = self.handler.get(uri)
        ctx = handler.context(getuser(), "Initial Data")


    @jsonify
    def search(self):
        user = request.params.get('user', '')
        # collection = collection.replace("-", "").replace(" ", "").replace('"', "").replace("'", "")
        q = collection_query % { "user_name": user}

        # cursor = handler.rdflib.store.cursor()
        cursor = handler.rdflib.store.cursor()
        
        results = {}
        for doc, title, description, username in cursor.execute(q):
            rec = results.setdefault(doc, {})
            rec["uri"] = doc
            rec['user'] = username
            if title: rec["title"] = title
            if description: rec["description"] = description

        cursor.close()

        return {
            'status': 'ok',
            'rows': results.values()
            }

collection_n3 = '''
@prefix bb: <http://bibliographica.org/onto#>.
@prefix owl: <http://www.w3.org/2002/07/owl#>.
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
@prefix data: <http://bibliographica.org/collection/>.
@prefix dc: <http://purl.org/dc/terms/>.

bb:Collection a owl:Class;
    rdfs:label "A collection".

<%(collection_uri)s> a bb:Collection;
    rdfs:label "%(title)s";
    dc:title "%(title)s";
    bb:user "%(user)s".
'''
from ordf.graph import Graph
from ordf.term import URIRef
def create_collection(user, object_dict={}):
    id_ = str(uuid.uuid4())
    collection_uri = 'http://bibliographica.org/collection/' +  id_
    defaults = {
        'title': '',
        'collection_uri': collection_uri,
        'user': user
        }
    values = dict(defaults)
    values.update(object_dict)
    ident = URIRef(collection_uri)
    data = Graph(identifier=ident)
    ourdata = collection_n3 % values
    data.parse(data=ourdata, format='n3')
    ctx = handler.context(user, "Creating collection: %s" % collection_uri)
    ctx.add(data)
    ctx.commit()
    return collection_uri

def find_collection():
    pass

