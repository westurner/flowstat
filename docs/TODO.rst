===================
untitled todo list
===================

intentions
===========
code
-----
commit more often
per-feature
with tests
and docs
hg qseries
hg qdiff
hg qnew <name>.patch
hg qrefresh


flow app
=========


models.Context Tests
---------------------
"NumbersContext"

request object
---------------
is_logged_in request lazyproperty
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- add request.is_logged_in attribute
- update templates to reflect
http://readthedocs.org/docs/pyramid/en/latest/api/request.html#pyramid.request.Request.set_property


app: security
--------------------
???: auth 
~~~~~~~~~~~


tests
~~~~~~
TODO: /login logout

app: graphs
------------
generate reference graph documentation pages
from networkx.generators

TODO: cleanup
STORY: algorithm attr set
STORY: persist at least the graph set
FIXME: graphs form
TODO: remove extra routes


app: numbers
--------------
imports alot from graphs ...
TODO: numbers form
TODO: cache?
FIXME: numbers form


app: shootout
----------------
idea
~~~~~
description
tags
title

upstream?

fix tag cloud
~~~~~~~~~~~~~~
TODO: shootout: tag cloud :find and remove the extra loop


TODO: restler port
~~~~~~~~~~~~~~~~~~~
TODO: ideas context wrapper
TODO: comments context wrapper (...)
TODO: ideas rest views
TODO: comments rest views
TODO: extend test templates

XXX: Context, View Test Templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from pyramid_restler.tests

TODO: templates
----------------
TODO: h5bp less django -> jinja

less
~~~~~


sass
~~~~~



TODO: js/css/img asset manager
-------------------------------
expand, compile, transform, compress


django-assetmanager
~~~~~~~~~~~~~~~~~~~~

django-mediagenerator
~~~~~~~~~~~~~~~~~~~~~~

assetgen / pyramid_assetgen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
https://github.com/thruflo/pyramid_assetgen
https://github.com/tav/assetgen.git

STORY: jquery ?
----------------

TODO: mustache templates .js
-----------------------------
portable minimal-logic templates
? with autoescaping

TODO: backbone js
------------------
proper application layers

and REST views to support


TODO: Bookmarks, History, Events
----------------------------------
stories
~~~~~~~~~
story _: fulltext search of objects and standard* properties
highlight-match bookmarks and/or history and/or events

story _: sortable gui

search: |_______________________________|
highlight-match bookmarks and/or history and/or events


hours app
~~~~~~~~~~
binds sqlalchemy to various [copies of] sqlite
TODO: celery tasks

TODO: task: add_event(s)
TODO: task: (re)index_events

.. note::

    datetime files are non-unique due to
    time resolution, disparity, NTP, etc


TODO: whoosh or solr? (...)
----------------------------
whoosh
~~~~~~~
easy
plain python
minimal build compilation
testing: TODO

solr
~~~~~
full-featured
collective.recipe.solrinstance
testing: TODO


object::


    {{ object.name }} {{ object.typetag[s] }} {{ object.tags }}
    <a href="<title>
    <url>
    <a href="{{ request.get_view('get_events_collection',
    object.timecode }}">context</a>


TODO: SVG viewer
-----------------
rescale

TODO: tasks
------------
pyrtm syllabus parser


tools
========
vim
----
NERDTree minimalization
~~~~~~~~~~~~~~~~~~~~~~~~~
 - Bookmark path shortening
 - Removed "Press ? for help"
 - Shortened '.. (up a dir)' to '..'
 - Removed extra newlines
 - >------- Boookmarks ------- to
   = bookmarks

TODO: colorscheme
~~~~~~~~~~~~~~~~~~
cterm:
    highlight lines
    easymotion text color
gui:
    voom highlight line
    -> setl nofoldenable VOoM patch

added vimrc documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~
vimrc documentation convention::

    " <heading, text>
    "  <shortcut>   --  <shortcut desc>

function ListMappings()::

    lvimgrep '\s*"\s\{2,}'

repos.py
---------
docs
_____
utility to find git, hg, bzr, svn repositories
 - repository origin (<tool> ~config)
 - commit logs (<tool> log)
 -  outstanding changes (<tool> status)

ex::

    repos.py -s .
    repos.py -s . -v

TODO: better logging
TODO: generate pip/buildout/makefile for replicating repositories


ranger
-------
cli filebrowser
IDEA: add libacl support to ranger


dependency graph flattener
---------------------------
easy enough to easy_install <appname>
and pull eggs from the

    1. buildout cache
    2. eggproxy cache

cycles are averted, but then the source paths are all different
and scattered e.g. in error messages /<virtualenv>/lib/python2.6/site-packages/*
    - easy-install.pth
    - <*>.pth
    - ./<*>

example
~~~~~~~~
 /-----B
A------C_____/_____/H
 \-----D    /F
  \----E---/---G

source install optimal ordering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
required to install dependencies from source checkouts
instead of pypi mirror

::

    { H, G }, F -> { C, E }, { B, D }, A

where, if there weren't write contention (?) for easy-install.pth,
and the dependency graph information is complete,
the sets in {brackets} could be parallelized.

solutions
~~~~~~~~~~
common problem
similar to async/parallel js loading
python 3 stdlib includes a dependency graph model

http://docs.python.org/dev/library/packaging.depgraph.html

<http://code/docs>
===================
source documentation
-------------------------------

sphinx: build_docs.py
~~~~~~~~~~~~~~~~~~~~~~
Find and attempt to build sphinx configuration from every
``conf.py`` file

algorithm::

    toc=[('label', 'path')]
    for p in `grindd conf.py`;
        conf_dir=`dirname $p`
        append link to toc
        cd $conf_dir;
        make html
        toc.append(dest_dir)
        # which is usually
        # ( [...] sphinx-build [...]  $conf_dir $dest_path )

        # TODO: trace failing build errors
        # TODO: detect nested conf sets
        # TODO: 

TODO: detect & configure nested documentation sets in ``build_docs.py``
TODO: opted for manual installs of remaining packages for now

sphinx: custom builds
~~~~~~~~~~~~~~~~~~~~~
Usually some combination of

    make html
    python ./docs/build.py
    python ./docs/make.py
    sphinx-build ./docs ./_build/html
    or .build/html
    or build/html


Paths
------
::

    /srv/repos/src/<name>
    /srv/repos/var/www/docs/<name>

ReadTheDocs
------------
awesome.

https://github.com/rtfd/readthedocs.org

 - project login support
 - repo polling
 - webhooks
 - full config sample

<http://code>
==============
hgweb configuration
~~~~~~~~~~~~~~~~~~~~~
For now, configured to recursively scan for all .hg repos
on every request

TODO: generate the hgwebconf programmatically::

    HGWEBCONF=""
    for p in `repos.py -s . -type hg -q';
        P=`dirname $p`
        echo $P = $p >> HGWEBCONF

hgweb WSGI entrypoint patch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 - Add paste entrypoint to mercurial 2.0.2
   allows for use with the cadre of WSGI servers and
   WSGI middlewares that
   can execute and/or be configured through Paste
   (<10 lines of code)
 - Posibility to combine the paster.ini and hgweb.conf file
 - way simpler than most of whats in the wiki

TODO: submit patch ?
there's a .wsgi file for mod_wsgi in contrib

hgweb templates
~~~~~~~~~~~~~~~~
modified gitweb templates
added docs, files, graph, and log links to the repo index
added docs link to header links bar
changed top-right link to read 'code/' and point to http://code

# TODO: split/ hg qrefresh

hgweb README
~~~~~~~~~~~~~
would be real nice to preview README{.rst, .txt} in the repo summary
view

fetching '/README' from tip is a little more complicated then file.read
https://bitbucket.org/birkenfeld/hgchangelog

<http://build/>
================
reverse proxied CI server

TODO: configure jenkins
TODO:

local configuration management
================================
port puppet policies to ubuntu
take a look at juju

pull ubuntu mirrors
--------------------
cobbler + debmirror
updated cobbler json

take a look at gentoo, arch
take a look at lxc

lxc
----

webhost migration
==================

this document
==============

FIXME:  it's broken
TODO:   do this later
XXX:    hey look at this, importantly
STORY:  story / usecase title
DESIGN: design phase
MODEL:  modelling phase
TEST:   test phase
DOCS:   documentation phase

STORY: blanknode labeling pass (goedel)
STORY: web-view
STORY: web-editor

TODO: vcs-journal it
