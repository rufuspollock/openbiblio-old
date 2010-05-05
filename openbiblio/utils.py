from pylons import config
from urllib import urlencode
from ordf.term import URIRef
from ordf.namespace import RDFS
import cgi

import logging
log = logging.getLogger(__name__)

def render_html(u):
    from openbiblio import handler
    store = handler.fourstore.store
    if not isinstance(u, URIRef):
        return cgi.escape("%s" % u)
    q1 = """SELECT DISTINCT ?l WHERE { %s %s ?l . FILTER( lang(?l) = "EN" ) }""" % \
        (u.n3(), RDFS.label.n3())
    q2 = """SELECT DISTINCT ?l WHERE { %s %s ?l }""" % \
        (u.n3(), RDFS.label.n3())
    r = list(store.query(q1))
    if r:
        label = r[0][0]
    else:
        r = list(store.query(q2))
        if r:
            label = r[0][0]
        else:
            label = str(u)
    return '<a href="%s">%s</a>' % (cgi.escape(u), cgi.escape(label))

def rdf_getstr(request):
    get = [ (k,v) for k,v in request.GET.items() if k != "format" ]
    return "?" + urlencode(get + [ ("format", "application/rdf+xml") ])
