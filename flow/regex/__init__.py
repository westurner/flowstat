#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
"""
regexapp - a simple regex webapp
"""


from pyramid.view import view_config

# model

def regex_view(request):
    rgxform = RegexForm(request)
    return rgxform.do_regex()

# form
import re
from formsframework import fields
class RegexForm(FormClass):

    action = fields.AutoCompleteSelectField()

    pattern = fields.UnicodeField()
    replace = fields.UnicodeField(optional=True)
    text    = fields.UnicodeField()

    def after_validation(self):
        self.rgx = re.compile(self.pattern)

    def do_regex(self, rgxform):
        if not rgxform.validate():
            ret = { 'errors': rgxform.errors.as_dict() }
        else:
            rgxform.after_validation() # port to n-framework event namespace

            pattern_match_bool = self.rgx.match(rgxform.text)

            if rgxform.replace:
                new_string, count = (
                    self.rgx.subn(rgxform.replace, rgxform.text) )
                return {'matchbool': pattern_match_bool,
                        'new_string': new_string,
                        'count': count }
            else:
                match_iter = rgx.finditer(rgxform.text)
                return {'matchbool': pattern_match_bool,
                        'pattern_matches': enumerate(match_iter)}

# view
def regex_view(request):
    return Regexable.perform_regex(RegexForm(request))

# application
from pyramid.config import Configurator
def regexapp(address='127.0.0.1',port='8080'):
    """
    regex application
    """

    config = Configurator()
    config.add_route('regex', '/regex')
    config.add_view(regex_view, route_name='regex')
    app = config.make_wsgi_app()
    server = make_server(address, port, app)
    server.serve_forever()


import unittest
class Test_regexapp(unittest.TestCase):
    def test_regexapp(self):
        try:
            regexapp(serve_forever=False)
        except KeyboardInterrupt:
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

    regexapp()

if __name__ == "__main__":
    main()



