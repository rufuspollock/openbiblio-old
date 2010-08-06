from ordf.namespace import Namespace, register_ns

def init_ns():
    register_ns("obp", Namespace("http://purl.org/okfn/obp#"))
    register_ns("obpl", Namespace("http://purl.org/okfn/obp/lens/"))
    register_ns("nbn", Namespace("http://purl.org/okfn/obp/nbn#"))
    register_ns("scn", Namespace("http://purl.org/okfn/obp/scn#"))
    register_ns("sccs", Namespace("http://purl.org/okfn/obp/sccs#"))
    register_ns("lccls", Namespace("http://purl.org/okfn/obp/lccls#"))

