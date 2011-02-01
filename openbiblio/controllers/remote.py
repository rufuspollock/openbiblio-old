"""
RDF Graph Controller - see L{ordf.pylons.graph}. 
"""

#from ordf.pylons.graph import GraphControllerFactory
from ordf.onto.controllers.graph import GraphController as _GraphController


from openbiblio.lib import base
from openbiblio.lib.base import render, request, c, response
from openbiblio import handler
from logging import getLogger
log = getLogger(__name__)

# TODO: change this to be more elegant ...
#_RemoteController = _GraphController()

class RemoteController(_GraphController):
    def index(self):
        try:
            return super(RemoteController, self).index()
        except:
            from traceback import format_exc
            log.info(format_exc())
            return self._render()

    def _render(self):
        # stuff other things in c
        return render('graph_fetch.html')
