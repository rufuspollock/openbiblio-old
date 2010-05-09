"""
RDF Proxy Controller - see L{ordf.pylons.sparql}.
"""
from ordf.pylons.proxy import ProxyControllerFactory
from openbiblio.lib import base
from openbiblio import model

ProxyController = ProxyControllerFactory(base, model)
