try:
    from pkg_resources import get_distribution
    __version__ = get_distribution("openbiblio").version
    del get_distribution
except:
    __version__ = "unknown"

__description__  = 'RDF Open Source Bibliographic Catalogue System'
__license__ = 'AGPL'
__long_description__ = ''

version = __version__
handler = None
