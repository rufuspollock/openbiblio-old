'''Collections API.

Create, view, search and update Collections (i.e. lists of works).
'''
import logging
import uuid
try:
    import json
except ImportError:
    import simplejson as json

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

DATANS = 'http://bibliographica.org/collection/'

class CollectionController(BaseController):
    @jsonify
    def index(self, collection=None):
        if collection is None:
            return {
                'doc': __doc__,
                'doc_url': None
                }
        else:
            uri = DATANS + collection
            collection = get_collection(uri)
            return collection

    def _request_json(self):
        return json.loads(dict(request.params).keys()[0])

    @jsonify
    def create(self):
        if not c.user:
            abort(401)
        values = self._request_json()
        uri = create_collection(c.user, values)
        return {'uri': uri}

    @jsonify
    def update(self, collection):
        if not c.user:
            abort(401)
        uri = DATANS + collection
        newdata = self._request_json()
        values = get_collection(uri)
        values.update(newdata)
        collection = create_collection(uri, values)
        return {'status': 'ok'}

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

<%(uri)s> a bb:Collection;
    rdfs:label "%(title)s";
    dc:title "%(title)s";
    bb:user "%(user)s".

'''
from ordf.graph import Graph
from ordf.term import URIRef
def create_collection(user, object_dict={}):
    defaults = {
        'uri': 'http://bibliographica.org/collection/' + str(uuid.uuid4()),
        'title': 'Untitled',
        'user': user,
        'works': []
        }
    values = dict(defaults)
    values.update(object_dict)
    uri = values['uri']
    ident = URIRef(uri)
    data = Graph(identifier=ident)
    ourdata = collection_n3 % values
    for work in values['works']:
        membership = '<%s> rdfs:member <%s> .\n' % (work, ident)
        ourdata += membership
    data.parse(data=ourdata, format='n3')
    ctx = handler.context(user, "Creating collection: %s" % uri)
    ctx.add(data)
    ctx.commit()
    return uri

get_collection_query = u"""
SPARQL
PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX bb: <http://bibliographica.org/onto#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX data: <http://bibliographica.org/collection/>

SELECT DISTINCT ?title ?description ?user_name
WHERE { 
  %(uri)s bb:user ?user_name .
  OPTIONAL { %(uri)s dc:title ?title } .
  OPTIONAL {  %(uri)s dc:description ?description }
}
"""
def get_collection(collection_uri):
    q = get_collection_query % ( {'uri': '<%s>' % collection_uri} )
    cursor = handler.rdflib.store.cursor()
    rec = {
        'uri': collection_uri
        }
    for title, description, username in cursor.execute(q):
        rec['user'] = username
        if title: rec["title"] = title
        if description: rec["description"] = description
    cursor.close()
    return rec

