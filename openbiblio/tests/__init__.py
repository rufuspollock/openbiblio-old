"""Pylons application test package

This package assumes the Pylons environment is already loaded, such as
when this script is imported from the `nosetests --with-pylons=test.ini`
command.

This module initializes the application via ``websetup`` (`paster
setup-app`) and provides the base testing objects.
"""
from unittest import TestCase

from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand
from pylons import url
from routes.util import URLGenerator
from webtest import TestApp

import pylons.test

from openbiblio.commands import Fixtures

__all__ = ['environ', 'url', 'test_graph', 'TestController', 'delete_all']

# Invoke websetup with the current config file
SetupCommand('setup-app').run([pylons.test.pylonsapp.config['__file__']])

test_graph = "http://bnb.bibliographica.org/entry/GB5006595"

# ensure cache_dir exists as we use it for e.g. pairtree
# and pair tree falls over if parent dir does not exist
cachedir = pylons.test.pylonsapp.config['app_conf']['cache_dir']
import os
if not os.path.exists(cachedir):
    os.makedirs(cachedir)


environ = {}

class TestController(TestCase):

    def __init__(self, *args, **kwargs):
        wsgiapp = pylons.test.pylonsapp
        config = wsgiapp.config
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
        TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        Fixtures.setUp()

    def tearDown(self):
        Fixtures.tearDown()

def delete_all():
    '''Remove all openbiblio related graphs from the store.
    
    '''
    # TODO: not working properly and not all graphs deleted - not sure why
    # TODO: none of changeset graphs get picked up here (not sure why)
    from openbiblio import handler
    from ordf.graph import Graph, ConjunctiveGraph
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

    # virtuoso specific ...
    store.cursor().execute('RDF_GLOBAL_RESET ()')

