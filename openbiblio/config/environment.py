"""Pylons environment configuration"""
import os

from pylons import config
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
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf,
                    package='openbiblio',
                    template_engine='genshi',  
                    paths=paths)

    config['routes.map'] = make_map()
    config['pylons.h'] = openbiblio.lib.helpers
    config['pylons.app_globals'] = app_globals.Globals()

    # Create the Genshi TemplateLoader
    config['pylons.app_globals'].genshi_loader = TemplateLoader(
        paths['templates'], auto_reload=True)

    # CONFIGURATIOr OPTIONS HERE (note: all config options will override
    # any Pylons config options)
    openbiblio.handler = init_handler(config)
