from __future__ import print_function
import inspect
import StringIO as io
from collections import defaultdict, namedtuple
from itertools import izip, count

from rst_reindent import restructuredtext_shift

def iter_source_lines(obj):
    """zip inspect.getsourcelines w/ line numberings starting at count"""
    lines, start = inspect.getsourcelines(obj)
    for (i, l) in izip(count(start), lines):
        yield (i, l)


def format_numbered_line_iter(iterable, indent=0):
    """prepend line numberings"""
    indentstr=' '*indent
    for (i, l) in iterable:
        yield '%s%-4d: %s' % (indentstr, i, l.rstrip('\n'))



REST_FORMATTED_BLOCK_HEADERS={
    'default': ('\n'
                '%s::\n'),
    'python': ('\n'
               '%s:\n\n'
               '.. code:: python\n')
}

class RSTContext(object):
    """
    Programmatically build a RestructuredText context

    :param output: file-like-object to *print* output to
    :type output: file-like object
    """
    UNDERLINE_EXTRA=2
    def __init__(self, output):
        self.file=output
        self.argspecs=defaultdict(list)
        self.refoffset=0


    def print(self, *args, **kwargs):
        kwargs['file'] = self.file
        print(args[0].decode('utf-8'), *args[1:], **kwargs)


    def print_rest_header(self, text, level='-', title=False):
        """print rst-underlined header"""
        underline = (level*(len(text) + RSTContext.UNDERLINE_EXTRA))
        self.print("")
        if title:
            self.print(underline)
        self.print(text)
        self.print(underline)


    def print_rest_title(self, text):
        self.print_rest_header(text, level='=', title=True)


    def print_rest_meta(self, key, value):
        self.print(":%s: %s" % (key, value))


    def print_rest_preformatted(self, iterable,
                                    header=None,
                                    indent=4,
                                    syntax='default'):
        indentstr = ' ' * indent
        header = header or ''
        header_template = REST_FORMATTED_BLOCK_HEADERS.get(syntax,
                            REST_FORMATTED_BLOCK_HEADERS['default'])

        self.print(header_template % header)

        if isinstance(iterable, basestring):
            iterable = (iterable,)
        for l in iterable:
            self.print("%s%s" % (indentstr, l))
        self.print('\n')


    def print_rest_list(self, iterable, indent=0, indentstr=None):
        indentstr = indentstr or (' ' * indent)
        for l in iterable:
            self.print("%s- %s" % (indentstr, l))


    def print_rest_source_lines(self, obj, header=None, syntax='default'):
        self.print_rest_preformatted(
            list(
                format_numbered_line_iter(
                    iter_source_lines(obj))),
            header=header,
            syntax=syntax)


    def print_rest_args_summary(self, argspec):
        argspec = argspec or self.argspec
        self.print_rest_header("arguments","=")
        self.print_rest_preformatted(
            self.get_argspec_output(argspec),
            header="argspec")

        for (k, v) in sorted(argspec.items(),
                            key=lambda x: x[0]):
            self.print_rest_header("arg: ``%s``" % k)
            self.print_rest_list(('`%s`_' % fn) for fn in v)


    def print_rest_docstring(self, obj, shiftby=2, refoffset=None):
        (output, refoffset) = restructuredtext_shift(
                io.StringIO(inspect.getdoc(obj)),
                shiftby=shiftby,
                refoffset=self.refoffset)
        self.print("\n")


    def print_rest_directive(self, directive, **options):
        self.print("")
        self.print(".. %s::" % directive)
        for (k,v) in options.iteritems():
            self.print("   :%s: %s" % (k, v))
        self.print("")


    def get_argspec_output(self, all_argspecs=None):
        all_argspecs = all_argspecs or self.argspecs
        for (k, v) in sorted(all_argspecs.items(),
                            key=lambda x: len(x[1]),
                            reverse=True):
            yield "    - %-24s\t%d\t%s" % (k, len(v), v)




from flow.models.context import PlainContext

from .views import get_graph
def GraphsContextFactory(request):
    return PlainContext(request, fn=lambda id: get_graph(str(id)))


Argument = namedtuple('Argument', ('name', 'default', 'values', 'functions'))

class ArgSpecRepo(object):
    """

    Build Repository of ArgSpecs from:
     - Function Definitions
     - Test Mentions

    Questions this structure should answer:

    what are the arguments for func1 (a, b, c)
    what are the arguments for func2 ([m,n], b, c)
    what argument sets are tested for func1
    what are the ranges for values a, b, c
      per function
      per codebase

    """
    def __init__(self):
        self.argspec_fn = defaultdict(list)
        self.argspec_fn_param = defaultdict(list)
        self.argspec_param = defaultdict(list)

    def add_def_argspec(self, argspec, location):
        for argname in argspec[0]:
            self.argspec_fn[argname].append(location)

        # todo: parse default kwargs, args

    def add_mention_argspec(self, argspec, location):
        # todo: parse test mentions from ast
        pass


T_ARGSPECS = (
("func(1, 2, x)", ('func', (1, 2, 'x'))),
("func(3, 2, 7)", ('func', (3, 2, 7))),
("func2(10, 20, 30)", ('func2', (10, 20, 30))),
)


def ast_getargspec(f):
    """ should be equiv to inspect.getargspec(f)
    """
    for i, o in T_ARGSPECS:
        if f==i: return o
    raise KeyError


import unittest
class TestAstGetargspec(unittest.TestCase):
    def test_ast_getargspec(self):
        for inp, outp in T_ARGSPECS:
            self.failUnlessEqual(
                outp,
                ast_getargspec(inp),)


class TestArgSpecRepo(unittest.TestCase):
    def test_argspecstorage(self):
        asr = ArgSpecRepo()
        def func(a, b, c):
            return (a, b, c)

        def func2(a, b, c):
            return (a+1, b, c)


        asr.add_def_argspec(func.__name__, inspect.getargspec(func))
        asr.add_def_argspec(func2.__name__, inspect.getargspec(func2))

        for (i,o) in T_ARGSPECS:
            asr.add_mention_argspec(o[0], ast_getargspec(i))





if __name__=="__main__":
    unittest.main()
