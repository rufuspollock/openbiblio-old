This file is for you to describe the openbiblio application.

Installation and Setup
======================

For the moment we only describe installation from source which is in mercurial
repo here:

  https://knowledgeforge.net/pdw/openbiblio

1. Install basics

  * python (>= 2.4)
  * python packages: setuptools, virtualenv>=1.3.4, pip>=0.4

2. Clone the repo:: 

    hg clone https://knowledgeforge.net/pdw/openbiblio

3. Create virtualenv (can change the name)::

    virtualenv pyenv-openbiblio

4. Install the application using pip-requirements.txt (assumes local checkout
   atm)::
    
    # openbiblio is where checkout is
    pip install -E pyenv-openbiblio openbiblio/pip-requirements.txt
    
5. Make a config file as follows::

    paster make-config openbiblio development.ini

6. Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

7. Then you are ready to go.

Loading Data
============

This package adds subcommands to the paster command to download and manipulate
data sets. Source URLs for the data should be in the configuration file. The
sample config lists pdw_archive_20090520 as a dataset. It can be retrieved 
with the following command:

    paster fetch config.ini pdw_archive_20090520

And the data can be loaded into the store with the following two commands:

    paster load_pdw -e config.ini pdw_archive_20090520
    paster load_pdw -l config.ini pdw_archive_20090520

The first one loads the entities (Person, Work, etc.) and the second loads the
links between them.

As workaround for out of memory issues (to be tracked down if necessary) the
load function can also take a -f argument with a list of files to load from
an extracted archive. e.g.:

	for file in /some/where/data/dump/005_WorkPerson_*.js; do
		paster load_pdw -lf $file config.ini
	done

