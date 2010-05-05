"""Pylons environment configuration"""
import os

from pylons import config

import openbiblio.lib.app_globals as app_globals
import openbiblio.lib.helpers
from openbiblio.config.routing import make_map

from ordf.pylons.handler import init_handler
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
    config['pylons.g'] = app_globals.Globals()


    # CONFIGURATIOr OPTIONS HERE (note: all config options will override
    # any Pylons config options)
    openbiblio.handler = init_handler(config)
