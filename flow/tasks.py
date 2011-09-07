#!/usr/bin/env python
# encoding: utf-8
"""
progname
"""

import datetime
from BeautifulSoup import BeautifulSoup as BS


def netflix_watch_instantly_history(html):
    bs = BS(html)
    tbl = bs.find('table')
    movies = tbl.findAll('tr')[1:]
    for m in movies:
        movie = [a.getText() for a in m.findChildren('td')][:-1]
        movie[1] = movie[1].startswith('You rated') and int(float(movie[1][22:25])) or 0
        movie[2] = datetime.datetime.strptime(movie[2], '%m/%d/%y')
        h,m,s = [int(s) for s in movie[3].split(':')]
        movie[3] = (60*60*h) + (60*m) + s
        yield movie


def main():
    """
    mainfunc
    """
    pass


if __name__ == "__main__":
    import optparse
    import logging

    prs = optparse.OptionParser(usage="./")

    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    prs.add_option('-f', '--file',
                    dest='file',
                    action='store')

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

    if opts.file:
        f = open(opts.file, 'rb')
        movies = list( netflix_watch_instantly_history(f.read()) )
        for m in sorted(movies, key=lambda x: x[3]):
            print m


    #main()

