#!/usr/bin/env python

import os
this_file='%s/bin/activate_this.py' % os.environ['VIRTUAL_ENV']
execfile(this_file, dict(__file__=this_file))

from paste.script.serve import ServeCommand

ServeCommand("serve").run(["development.ini"])
