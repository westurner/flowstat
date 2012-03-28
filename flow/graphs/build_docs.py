#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
"""
build_docs
"""


import os
import sys
import subprocess

def cmd(*args, **kwargs):
    kwargs['output'] = True
    return subprocess.call(*args, **kwargs)


def build_docs(output=sys.stdout):
    #toc=[('label', 'path')]
    toc=[]

    here=os.getcwd()
    for p in cmd("find . -type f -name conf.py"):
        P=os.path.dirname(p)
        #echo "$p $P" >> $index
        os.setcwd(P)
        cmd("ls -al")
        # update build target
        if os.path.exists("Makefile"):
            has_makefile=True
            output.write(P)
            toc.append((p.split(os.path.sep)[0], P, p, ))
            cmd("make html")

        os.setcwd(here)

def build_doc_index():

    for p in cmd("find . -type d -name html | grep -v '.hg' | grep doc"):
        print(p)
        #cmd("cp -Rv %r" % os.path.join(p))



import unittest
class Test_build_docs(unittest.TestCase):
    def test_build_docs(self):
        pass


def main():
    import optparse
    import logging

    prs = optparse.OptionParser(usage="./%prog : args")

    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    (opts, args) = prs.parse_args()

    if not opts.quiet:
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    if opts.run_tests:
        import sys
        sys.argv = [sys.argv[0]] + args
        import unittest
        exit(unittest.main())

    build_docs(output=file('docsindex.rst'))

if __name__ == "__main__":
    main()
