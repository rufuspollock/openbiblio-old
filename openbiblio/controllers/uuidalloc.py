import logging

from pylons import response
from openbiblio.lib.base import BaseController
from uuid import uuid1
try: 
    from json import dumps
except ImportError:
    from simplejson import dumps

log = logging.getLogger(__name__)

class UuidallocController(BaseController):
    def index(self):
        response.content_type = "application/javascript"
        return dumps(str(uuid1()))

