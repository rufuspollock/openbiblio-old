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
from pylons import config, url
from routes.util import URLGenerator
from webtest import TestApp

import pylons.test
from openbiblio.commands import Fixtures

__all__ = ['environ', 'url', 'test_graph', 'TestController']

# Invoke websetup with the current config file
SetupCommand('setup-app').run([config['__file__']])

test_graph = "http://bibliographica.org/test"

# ensure cache_dir exists as we use it for e.g. pairtree
# and pair tree falls over if parent dir does not exist
cachedir = config['cache.dir']
import os
if not os.path.exists(cachedir):
    os.makedirs(cachedir)


environ = {}

class TestController(TestCase):

    def __init__(self, *args, **kwargs):
        if pylons.test.pylonsapp:
            wsgiapp = pylons.test.pylonsapp
        else:
            wsgiapp = loadapp('config:%s' % config['__file__'])
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))

        TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        Fixtures.setUp()
    def tearDown(self):
        Fixtures.tearDown()
