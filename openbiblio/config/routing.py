"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper

def make_map(config):
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE

    map.connect('home', '/', controller='home', action='index')
    # proxied items
    map.connect('about', '/about', controller='home', action='about')
    map.connect('get-involved', '/get-involved', controller='home',
            action='get_involved')

    map.connect('proxy', '/proxy', controller='proxy', action='index')
    map.connect('sparql', '/sparql', controller='sparql', action='index')
    map.connect('search', '/search', controller='search', action='index')
    map.connect('graph', '/graph', controller='graph', action='index')
    map.connect('graph', '/add', controller='graph', action='add')
    map.connect('import', '/import', controller='remote', action='index')
    map.connect('uuid', '/api/uuidalloc', controller='uuidalloc', action='index')

    map.connect("isbn", "/isbn/:isbn", controller="isbn", action="index")
    map.connect("isbn", "/isbn", controller="isbn", action="index")

    # for the time being catch everything but soon we will be more specific
    # e.g. restrict to work|person|entity ...
    map.connect('/*path', controller='graph', action='index')

    return map
