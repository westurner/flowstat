flow
========


Library Requirements
--------------------

flow requires SQLite3 bindings.

Debian::

    sudo apt-get install build-essentials
    sudo apt-get install libsqlite3-dev


Installing and Running
----------------------

#. virtualenv --no-site-packages env

#. cd env

#. . bin/activate

#. ____ clone ________

#. cd flow

#. python setup.py develop

#. paster serve --reload development.ini

