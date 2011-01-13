import uuid
import pprint
import json
import datetime

from ordf.graph import Graph, ConjunctiveGraph
from ordf.term import URIRef
from openbiblio.controllers import collection
from openbiblio.tests import *
from openbiblio import handler

class TestCollectionController(TestController):
    graphs_to_destroy = []
    @classmethod
    def teardown_class(self):
        store = handler.__writers__[0].store
        cg = ConjunctiveGraph(store)
        for graph in cg.contexts():
            toremove = (graph.identifier.startswith('http://bibliographica.org')
                or # changesets
                graph.identifier.startswith('urn:uuid')
                )
            if toremove:
                store.remove((None, None, None), graph)
        store.commit()

    def test_list_graphs(self):
        store = handler.__writers__[0].store
        cg = ConjunctiveGraph(store)
        count = 0 
        toremovelist = []
        for graph in cg.contexts():
            count += 1
            toremove = (graph.identifier.startswith('http://bibliographica.org')
                or # changesets
                graph.identifier.startswith('urn:uuid')
                )
            if toremove:
                toremovelist.append(graph)
        print 'Total graphs: %s' % count
        print 'Toremove: %s' % len(toremovelist)
        for graph in toremovelist: 
            store.remove((None, None, None), graph)
        totalnow = len([graph for graph in cg.contexts()])
        store.commit()
        assert totalnow == 4, totalnow

    def test_index(self):
        response = self.app.get(url(controller='collection', action='index'))
        assert 'Collection API' in response
    
    # ouruser = 'http://test.org/' + str(uuid.uuid4())
    ouruser = 'http://test.org/me'
    def test_search(self):
        collection_uri = collection.create_collection(self.ouruser)
        collection_uri2 = collection.create_collection(self.ouruser)
        self.graphs_to_destroy.append(collection_uri)
        self.graphs_to_destroy.append(collection_uri2)

        oururl = url(controller='collection', action='search',
                user=self.ouruser)
        response = self.app.get(oururl)

        # print response
        data = json.loads(response.body)
        assert data['status'] == 'ok'
        assert len(data['rows']) == 2, len(data['rows'])
        firstrow = data['rows'][0]
        assert firstrow['user'] == self.ouruser, firstrow


    def test_create(self):
        title = 'mytitle'
        ourlist = {
            'created': datetime.datetime.now(),
            'title': title,
            'works': [
                
                ]
            }
        ournewuser = 'http://test.org/testcreate'
        oururl = url(controller='collection', action='create')
        response = self.app.post(oururl, params=ourlist, status=[401,302])
        if response.status_int == 302:
            response = response.follow()
            assert 'Login' in response, response

        response = self.app.post(oururl, params=ourlist,
                extra_environ=dict(
                    REMOTE_USER=ournewuser
                )
            )
               
        data = json.loads(response.body)
        collection_uri = data['uri']
        self.graphs_to_destroy.append(collection_uri)
        assert data['uri']

        graph = handler.get(collection_uri)
        assert graph, collection_uri
        match = list(graph.triples((URIRef(collection_uri),None,ournewuser)))
        assert match, pprint.pprint([(s,p,o) for s,p,o in graph])

