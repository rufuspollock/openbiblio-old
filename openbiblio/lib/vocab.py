import os
import pkg_resources
from getpass import getuser
from logging import getLogger
from ordf.graph import Graph

__import__("openbiblio.lib.namespace", {}, {}, ["unused"])
__import__("ordf.vocab.opmv", {}, {}, ["Process"]).Process.add_distribution("openbiblio")

from ordf.namespace import OBPL

log = getLogger(__name__)

def rdf_data():
    graph_uri = "http://purl.org/okfn/obp#"
    log.info("Loading %s" % graph_uri)

    graph = Graph(identifier=graph_uri)
    fp = pkg_resources.resource_stream("openbiblio", os.path.join("n3", "obp.n3"))
    graph.parse(fp, format="n3")
    fp.close()

    yield graph

    for lens in pkg_resources.resource_listdir("openbiblio", "lenses"):
        if not lens.endswith(".n3"):
            continue
        lens_uri = OBPL[lens[:-3]]
        graph = Graph(identifier=lens_uri)
        fp = pkg_resources.resource_stream("openbiblio", os.path.join("lenses", lens))
        graph.parse(fp, format="n3")
        fp.close()
        yield graph


