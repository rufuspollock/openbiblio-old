"""Pylons environment configuration"""
import os

from mako.lookup import TemplateLookup
from pylons import config
from pylons.error import handle_mako_error

import openbiblio.lib.app_globals as app_globals
import openbiblio.lib.helpers
from openbiblio.config.routing import make_map

import openbiblio.model as model

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='openbiblio', paths=paths)

    config['routes.map'] = make_map()
    config['pylons.app_globals'] = app_globals.Globals()
    config['pylons.h'] = openbiblio.lib.helpers

    # Create the Mako TemplateLoader
    config['pylons.app_globals'].mako_lookup = TemplateLookup(
        paths['templates'],
        error_handler=handle_mako_error,
        module_directory=os.path.join(app_conf['cache_dir'], 'templates'),
        input_encoding='utf-8', default_filters=['escape'],
        imports=['from webhelpers.html import escape'])

    # CONFIGURATIOr OPTIONS HERE (note: all config options will override
    # any Pylons config options)

    store_type = config.get("rdflib.store", "IOMemory")
    store_args = config.get("rdflib.args", [])
    if store_args:
        store_args = [store_args]
    model.init_store(store_type, *store_args)
    model.init_ptree(config["pairtree.root"])
    model.init_handler()
