from setuptools import setup, find_packages

from openbiblio import __description__, __long_description__, __license__

__version__ = "0.3"

try:
    from mercurial import ui, hg, error
    repo = hg.repository(ui.ui(), ".")
    ver = repo[__version__]
except ImportError:
    pass
except error.RepoLookupError:
    tip = repo["tip"]
    __version__ = "hg+%s:%s" % (tip.rev(), tip.hex()[:12])

setup(
    name='openbiblio',
    version=__version__,
    description=__description__,
    author='Open Knowledge Foundation',
    author_email='info@okfn.org',
    url='http://bibliographica.org/',
    license=__license__,
    install_requires=[
        'Pylons>=0.9.7',
        'Genshi>=0.5',
        'Cython',
    	'pymarc',
    	'swiss',
        'ordf',
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'openbiblio': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'openbiblio': [
    #        ('**.py', 'python', None),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = openbiblio.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller

    [paste.paster_command]
    fetch = openbiblio.commands.fetch:Fetch
    fixtures = openbiblio.commands:Fixtures
    lenses = openbiblio.commands:Lenses
    load_marc = openbiblio.commands.marc_loader2:Loader
    dedup = openbiblio.commands.dedup:DeDup

    [ordf.xapian]
    index = openbiblio.lib.xapindex:index_store
    search = openbiblio.lib.xapindex:search
    """,
)
