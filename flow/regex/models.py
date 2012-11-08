#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
"""
regexapp - a simple regex webapp
"""

# model
class Regexable(object):
    @classmethod
    def perform_regex(self, rgxform):
        if not rgxform.validate():
            return { 'errors': rgxform.errors.as_dict() }

        rgxform.after_validation() # port to n-framework event namespace
        rgx = rgxform.rgx

        pattern_match_bool = rgx.match(rgxform.text)

        if rgxform.replace:
            new_string, count = rgx.subn(rgxform.replace, rgxform.text)
            return {'matchbool': pattern_match_bool,
                    'new_string': new_string,
                    'count': count }
        else:
            match_iter = rgx.finditer(rgxform.text)
            return {'matchbool': pattern_match_bool,
                    'pattern_matches': enumerate(match_iter)}

# form
import re
from formsframework import fields
class RegexForm(FormClass):

    action = fields.AutoCompleteSelectField()

    pattern = fields.StringField()
    replace = fields.UnicodeField(optional=True)
    text    = fields.UnicodeField()

    def after_validation(self):
        self.rgx = re.compile(self.pattern)


# view
def regex_view(request):
    return Regexable.perform_regex(RegexForm(request))

# application
def regexapp():
    """
    mainfunc
    """
    settings = {}
    app = framework.Application(settings=settings)
    app.add_route('/', regex_view)
    return app.serve(address='127.0.0.1', port='8080')


import unittest
class Test_regexapp(unittest.TestCase):
    def test_regexapp(self):
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



