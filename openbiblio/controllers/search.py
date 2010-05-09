"""
Xapian Full-Text Search - see L{ordf.pylons.xap}.
"""
from ordf.pylons.xap import XapianControllerFactory
from openbiblio.lib import base
from openbiblio import handler

SearchController = XapianControllerFactory(base, handler)
