from ordf.pylons.proxy import ProxyControllerFactory
from openbiblio.lib import base
from openbiblio import model

ProxyController = ProxyControllerFactory(base, model)
