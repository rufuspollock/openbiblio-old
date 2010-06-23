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

... to be redocumented, see "paster load_marc"
