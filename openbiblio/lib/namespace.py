from ordf.namespace import Namespace, register_ns

def init_ns():
    register_ns("obp", Namespace("http://purl.org/NET/obp/"))
    register_ns("nbn", Namespace("http://purl.org/NET/obp/nbn/"))
    register_ns("scn", Namespace("http://purl.org/NET/obp/scn/"))
    register_ns("sccs", Namespace("http://purl.org/NET/obp/sccs/"))
    register_ns("lccls", Namespace("http://purl.org/NET/obp/lccls/"))

