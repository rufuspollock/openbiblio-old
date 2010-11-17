"""Pylons environment configuration"""
import os
import pkg_resources

from pylons.configuration import PylonsConfig
from genshi.template import TemplateLoader

import openbiblio.lib.app_globals as app_globals
import openbiblio.lib.helpers
from openbiblio.config.routing import make_map

from ordf.handler import init_handler
import openbiblio

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    config = PylonsConfig()
    
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates'),
                            pkg_resources.resource_filename("ordf.onto", "templates")])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf,
                    package='openbiblio',
                    paths=paths)

    config['routes.map'] = make_map(config)
    config['pylons.app_globals'] = app_globals.Globals(config)
    config['pylons.h'] = openbiblio.lib.helpers

    # Setup cache object as early as possible
    import pylons
    pylons.cache._push_object(config['pylons.app_globals'].cache)
    
    # Create the Genshi TemplateLoader
    config['pylons.app_globals'].genshi_loader = TemplateLoader(
        paths['templates'], auto_reload=True)

    # CONFIGURATIOr OPTIONS HERE (note: all config options will override
    # any Pylons config options)
    openbiblio.handler = init_handler(config)
    config['pylons.strict_tmpl_context'] = False

    return config

