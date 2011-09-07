#!/usr/bin/env python

this_file='/media/walrus/workspace/.virtualenvs/movies/bin/activate_this.py'
execfile(this_file, dict(__file__=this_file))

from paste.script.serve import ServeCommand

ServeCommand("serve").run(["development.ini"])
