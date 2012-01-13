#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
"""
Scan and generate documentation for nx.generators.{ }


"""
import codecs
import sys
import inspect
import StringIO as io
import networkx as nx
from pkg_resources import resource_stream, resource_filename
from itertools import izip, ifilter, repeat
from pprint import pformat

from flow.graphs.models import RSTContext, format_numbered_line_iter
from flow.graphs.utils import grep_file

#from sage.misc.sageinspect import sage_getargspec # ast

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

file_adaptors = (
    (basestring, io.StringIO),
    ((file, io.StringIO), lambda x: x),
    (list, lambda x: io.StringIO(u''.join(x))), # .writelines
)
def to_file(source=None, filename=None):
    """
    adapt input to a _read able file
    """

    def read_file(source):
        print(type(source))
        if source:
            return codecs.open(source, 'r', 'utf-8')
        raise TypeError(source)

    if filename:
        return read_file(filename)

    # otherwise
    for typeset, fn in file_adaptors:
        if isinstance(source, typeset):
            return fn(source)

    raise TypeError(source)


# hrm
import ast
import StringIO as io
from unparse import Unparser
def parse_for_examples_ast(source=None, filename=None, examples=[]):

    f = to_file(source=source, filename=filename)
    ast_tree = ast.parse(f.read())
    walkpath = []
    print("ast")
    for node in ast.walk(ast_tree):
        walkpath.append(node)
        ast.dump(node)

    print("unparsed: ")
    Unparser(walkpath[0])


# yuck
import re
def to_native_type(txt, argname=None):
    """ #! ... """
    if argname == 'create_using':
        if txt.startswith('MultiGraph'):
            return nx.MultiGraph()
        elif txt.startswith('DiGraph'):
            return nx.DiGraph()
        elif txt.startswith('MultiDiGraph'):
            return nx.MultiDiGraph()
    else:
        if txt == u'True':
            return True
        elif txt == u'False':
            return False
        elif txt == u'None':
            return None
        elif re.match('([\d.]+)', txt):
            try:
                if '.' in txt:
                    return float(txt)
                else:
                    return int(txt)
            except ValueError:
                raise Exception("%s, %s" % (txt,argname))
        else:
            return str(txt) # ...

    raise Exception("%s, %s" % (txt, argname))


def parse_for_examples(iterable, func_name, examples=[]):
    """ Q&D """
    filterfunc = lambda nl: ('%s(' % func_name) in nl[1] and '=' in nl[1]
    for nl in iterable:
        if filterfunc(nl):
            n,l = nl
            args=[]
            kwargs=[]


            import re
            l = l.split('=',1)[1].strip()

            #examples.append(sage_getargspec(l))

            argstr = l.split('(', 1)[1].split(')', -1)[0]
            if re.match('.*\[(.*)\].*', argstr ):
                continue
                raise Exception(argstr)
            allargs = [s.strip() for s in argstr.split(',')]
            for arg in allargs:
                arg=arg.strip()
                if '=' in arg:
                    k,v=arg.split('=',1)
                    v=v.strip()
                    try:
                        _v = to_native_type(v, argname=k)
                    except Exception: ######### ...
                        _v = v
                    kwargs.append((k, _v))
                else:
                    try:
                        args.append(to_native_type(arg))
                    except Exception:
                        print(repr(arg))

            examples.append((n, l, (args,kwargs)))

            #('%-79s# %d' % (l, n) ))# ... TODO: parse
        yield nl


def generate_networkx_graph_reference(
        generators='all',
        print=print,
        output=sys.stdout):
    """
    Introspect and iterate over network.generators.<module>.<fn>_graph

    For when sphinx would be too much.

    """
    tests_path = resource_filename('networkx', 'generators/tests')

    sys.path.append(tests_path)

    # generators=('classic', 'small', ...)
    if generators == 'all':
        generatorsrc = resource_stream(
                            'networkx',
                            'generators/__init__.py')
        generatorlist = tuple(
            n.split('.')[2].split()[0]
                for n in generatorsrc
                    if n.startswith('from networkx.generators.'))
    else:
        generatorlist = tuple(generators)


    c = RSTContext(output=output)
    c.title = "networkx reference graphs"
    c.print_rest_title(c.title)
    c.print_rest_meta("Version", nx.__version__)
    c.print_rest_meta("Copyright", "Copyright NetworkX: %s. `<%s>`_\n" % (
                                nx.__license__, "http://networkx.lanl.gov"))
    c.print_rest_meta("SeeAlso", "`<https://github.com/networkx/networkx>`_")

    c.print_rest_directive("contents", depth=2)
    c.print_rest_directive("sectnum")

    generators = OrderedDict()
    for g in generatorlist:
        c.print_rest_header(
            str(g),
            "=")

        Generators = getattr(nx.generators, g)
        generators[g] = []

        if Generators.__doc__:
            c.print_rest_docstring(Generators)

        fn_filter = lambda x: x.endswith('_graph')
        Functions = filter(fn_filter, dir(Generators))
        if Functions:
            c.print(".. Functions:")
            c.print_rest_list(Functions, indentstr=('.. '))

            generators[g] = dict(izip(Functions, repeat([])))

        c.print_rest_directive("contents", local='', depth=1)

        TestsFile, Tests, TestClass, TestFuncs = None, None, None, None
        # nx.generators.tests.test_${g}
        TestsFile = 'test_%s' % g
        TestsFilePath = resource_filename(
                        'networkx',
                        'generators/tests/%s.py' % TestsFile)
        TestClassName = 'TestGenerator%s' % g.capitalize()
        TestMethodFilter  = lambda x: x.startswith("test")

        try:
            Tests = __import__(TestsFile)
        except ImportError:
            pass
        try:
            TestClass = getattr(Tests, TestClassName)
            TestFuncs = filter(TestMethodFilter, dir(TestClass))
        except AttributeError:
            pass

        for graph_fn in Functions:
            graph_fn_path = "%s.%s" % (g, graph_fn)
            GraphFunction = getattr(Generators, graph_fn)

            c.print_rest_header(
                graph_fn_path,
                '-')
            c.print_rest_directive("contents", local='', depth=1)

            if GraphFunction.__doc__:
                c.print_rest_docstring(GraphFunction)

            argspec = inspect.getargspec(GraphFunction)
            # asr.add_argspec(argspec)
            c.print_rest_preformatted(
                inspect.formatargspec(argspec),
                header = "``%s`` argspec" % graph_fn)

            #c.print_rest_argspec(
            #    sage_getargspec(GraphFunction),
            #    header = "``%s`` argspec ast" % graph_fn)

            c.print_rest_header(
                'src: ``%s``' % graph_fn_path,
                '~')
            c.print_rest_source_lines(
                GraphFunction,
                header="source")


            if TestFuncs:
                for fn in ifilter(lambda x: graph_fn in x, TestFuncs): # ...
                    c.print_rest_header("test_function: ``%s``" % fn, "~")
                    c.print_rest_source_lines(
                        getattr(TestClass, fn),
                        header="``%s``" % fn)
            #else:
            #    c.print_rest_preformatted("# No tests found"),

            if Tests:
                c.print_rest_header(
                    'tests grep for ``%s``' % graph_fn,
                    "~")
                test_examples=[]

                c.print_rest_preformatted(
                    format_numbered_line_iter(
                        parse_for_examples(
                            grep_file(
                                filename=TestsFilePath,
                                searchfn=lambda x: graph_fn in x),
                            func_name=graph_fn,
                            examples=test_examples)
                        ),
                    header="``networkx.generators.tests.%s``" % TestsFile)

                c.print_rest_header(
                    'ast examples',
                    '~')

                #c.print_rest_preformatted(
                #    parse_for_examples_ast(
                #        source=inspect.getsourcelines(GraphFunction)[0]),
                #    header='ast examples')

                c.print_rest_header(
                    'test_examples for ``%s``' % graph_fn,
                    "~")
                c.print_rest_preformatted(
                    test_examples,
                    header='examples')

                generators[g][graph_fn] = test_examples

    c.print_rest_args_summary(c.argspecs)

    c.print_rest_header(
        "generators",
        "=")
    c.print_rest_preformatted(
        pformat(dict(generators)))

    return c.file


import unittest
class Test_progname(unittest.TestCase):
    def test_progname(self):
        generate_networkx_graph_reference(output=sys.stdout)


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
    else:
        generate_networkx_graph_reference(output=sys.stdout)
        exit(0)


if __name__=="__main__":
    main()
