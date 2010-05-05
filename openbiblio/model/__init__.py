store = None
ptree = None
handler = None

## kludge to get rdflib plugin infrastructure to find
## the FourStore if we have it
try:
    import py4s
    del py4s
except ImportError:
    pass

def init_store(store_type, *av, **kw):
    from rdflib import plugin
    from rdflib.store import Store

    cls = plugin.get(store_type, Store)

    global store
    store = cls(*av, **kw)
    return store

def init_ptree(ptree_root, ptree_uri="urn:uuid:"):
    from ordf.handler.pt import PairTree
    global ptree
    ptree = PairTree(store_dir=ptree_root, uri_base=ptree_uri)

def init_handler():
    global handler
    from ordf.handler import Handler
    from ordf.handler.rdf import FourStore
    handler = Handler(ptree)
