r"""
Inspect Python, Sage, and Cython objects.

This module extends parts of Python's inspect module to Cython objects.

AUTHORS:

- originally taken from Fernando Perez's IPython
- William Stein (extensive modifications)
- Nick Alexander (extensions)
- Nick Alexander (testing)
- Simon King (some extension for Cython, generalisation of SageArgSpecVisitor)

SRC::

    http://hg.sagemath.org/sage-main/raw-file/9e29a3d84c48/sage/misc/sageinspect.py

EXAMPLES::

    sage: from sage.misc.sageinspect import *

Test introspection of modules defined in Python and Cython files:

Cython modules::

    sage: sage_getfile(sage.rings.rational)
    '.../rational.pyx'

    sage: sage_getdoc(sage.rings.rational).lstrip()
    'Rational Numbers...'

    sage: sage_getsource(sage.rings.rational)[5:]
    'Rational Numbers...'

Python modules::

    sage: sage_getfile(sage.misc.sageinspect)
    '.../sageinspect.py'

    sage: print sage_getdoc(sage.misc.sageinspect).lstrip()[:40]
    Inspect Python, Sage, and Cython objects

    sage: sage_getsource(sage.misc.sageinspect).lstrip()[5:-1]
    'Inspect Python, Sage, and Cython objects...'

Test introspection of classes defined in Python and Cython files:

Cython classes::

    sage: sage_getfile(sage.rings.rational.Rational)
    '.../rational.pyx'

    sage: sage_getdoc(sage.rings.rational.Rational).lstrip()
    'A Rational number...'

    sage: sage_getsource(sage.rings.rational.Rational)
    'cdef class Rational...'

Python classes::

    sage: import sage.misc.attach
    sage: sage_getfile(sage.misc.attach.Attach)
    '.../attach.py'

    sage: sage_getdoc(sage.misc.attach.Attach).lstrip()
    'Attach a file to a running instance of Sage...'

    sage: sage_getsource(sage.misc.attach.Attach)
    'class Attach:...'

Python classes with no docstring, but an __init__ docstring::

    sage: class Foo:
    ...     def __init__(self):
    ...         'docstring'
    ...         pass
    ...
    sage: sage_getdoc(Foo)
    'docstring\n'

Test introspection of functions defined in Python and Cython files:

Cython functions::

    sage: sage_getdef(sage.rings.rational.make_rational, obj_name='mr')
    'mr(s)'

    sage: sage_getfile(sage.rings.rational.make_rational)
    '.../rational.pyx'

    sage: sage_getdoc(sage.rings.rational.make_rational).lstrip()
    "Make a rational number ..."

    sage: sage_getsource(sage.rings.rational.make_rational, True)[4:]
    'make_rational(s):...'

Python functions::

    sage: sage_getdef(sage.misc.sageinspect.sage_getfile, obj_name='sage_getfile')
    'sage_getfile(obj)'

    sage: sage_getfile(sage.misc.sageinspect.sage_getfile)
    '.../sageinspect.py'

    sage: sage_getdoc(sage.misc.sageinspect.sage_getfile).lstrip()
    "Get the full file name associated to ``obj`` as a string..."

    sage: sage_getsource(sage.misc.sageinspect.sage_getfile)[4:]
    'sage_getfile(obj):...'

Unfortunately, there is no argspec extractable from builtins::

    sage: sage_getdef(''.find, 'find')
    'find( [noargspec] )'

    sage: sage_getdef(str.find, 'find')
    'find( [noargspec] )'

By trac ticket #9976, introspection also works for interactively
defined Cython code, and with rather tricky argument lines::

    sage: cython('def foo(x, a=\')"\', b={not (2+1==3):\'bar\'}): return')
    sage: print sage_getsource(foo)
    def foo(x, a=')"', b={not (2+1==3):'bar'}): return
    sage: sage_getargspec(foo)
    ArgSpec(args=['x', 'a', 'b'], varargs=None, keywords=None, defaults=(')"', {False: 'bar'}))

"""

import ast
import inspect
import functools
import os
import tokenize
EMBEDDED_MODE = False

def isclassinstance(obj):
    r"""
    Checks if argument is instance of non built-in class

    INPUT: ``obj`` - object

    EXAMPLES::

        sage: from sage.misc.sageinspect import isclassinstance
        sage: isclassinstance(int)
        False
        sage: isclassinstance(FreeModule)
        True
        sage: class myclass: pass
        sage: isclassinstance(myclass)
        False
        sage: class mymetaclass(type): pass
        sage: class myclass2:
        ...       __metaclass__ = mymetaclass
        sage: isclassinstance(myclass2)
        False
    """
    return (not inspect.isclass(obj) and \
            hasattr(obj, '__class__') and \
            hasattr(obj.__class__, '__module__') and \
            obj.__class__.__module__ not in ('__builtin__', 'exceptions'))


SAGE_ROOT = "." #os.environ["SAGE_ROOT"]

import re
# Parse strings of form "File: sage/rings/rational.pyx (starting at line 1080)"
# "\ " protects a space in re.VERBOSE mode.
__embedded_position_re = re.compile(r'''
\A                                          # anchor to the beginning of the string
File:\ (?P<FILENAME>.*?)                    # match File: then filename
\ \(starting\ at\ line\ (?P<LINENO>\d+)\)   # match line number
\n?                                         # if there is a newline, eat it
(?P<ORIGINAL>.*)                            # the original docstring is the end
\Z                                          # anchor to the end of the string
''', re.MULTILINE | re.DOTALL | re.VERBOSE)

def _extract_embedded_position(docstring):
    r"""
    If docstring has a Cython embedded position, return a tuple
    (original_docstring, filename, line).  If not, return None.

    INPUT: ``docstring`` (string)

    EXAMPLES::

       sage: from sage.misc.sageinspect import _extract_embedded_position
       sage: import inspect
       sage: _extract_embedded_position(inspect.getdoc(var))[1][-21:]
       'sage/calculus/var.pyx'

    AUTHORS:

    - William Stein
    - Extensions by Nick Alexander
    """
    if docstring is None:
        return None
    res = __embedded_position_re.match(docstring)
    if res is not None:
        #filename = '%s/local/lib/python/site-packages/%s' % (SAGE_ROOT, res.group('FILENAME'))
        filename = '%s/devel/sage/%s' % (SAGE_ROOT, res.group('FILENAME'))
        lineno = int(res.group('LINENO'))
        original = res.group('ORIGINAL')
        return (original, filename, lineno)
    return None


class BlockFinder:
    """
    Provide a tokeneater() method to detect the end of a code block.

    This is the Python library's :class:`inspect.BlockFinder` modified
    to recognize Cython definitions.
    """
    def __init__(self):
        self.indent = 0
        self.islambda = False
        self.started = False
        self.passline = False
        self.last = 1

    def tokeneater(self, type, token, srow_scol, erow_ecol, line):
        srow, scol = srow_scol
        erow, ecol = erow_ecol
        if not self.started:
            # look for the first "(cp)def", "class" or "lambda"
            if token in ("def", "cpdef", "class", "lambda"):
                if token == "lambda":
                    self.islambda = True
                self.started = True
            self.passline = True    # skip to the end of the line
        elif type == tokenize.NEWLINE:
            self.passline = False   # stop skipping when a NEWLINE is seen
            self.last = srow
            if self.islambda:       # lambdas always end at the first NEWLINE
                raise inspect.EndOfBlock
        elif self.passline:
            pass
        elif type == tokenize.INDENT:
            self.indent = self.indent + 1
            self.passline = True
        elif type == tokenize.DEDENT:
            self.indent = self.indent - 1
            # the end of matching indent/dedent pairs end a block
            # (note that this only works for "def"/"class" blocks,
            #  not e.g. for "if: else:" or "try: finally:" blocks)
            if self.indent <= 0:
                raise inspect.EndOfBlock
        elif self.indent == 0 and type not in (tokenize.COMMENT, tokenize.NL):
            # any other token on the same indentation level end the previous
            # block as well, except the pseudo-tokens COMMENT and NL.
            raise inspect.EndOfBlock

def _getblock(lines):
    """
    Extract the block of code at the top of the given list of lines.

    This is the Python library's :func:`inspect.getblock`, except that
    it uses an instance of our custom :class:`BlockFinder`.
    """
    blockfinder = BlockFinder()
    try:
        tokenize.tokenize(iter(lines).next, blockfinder.tokeneater)
    except (inspect.EndOfBlock, IndentationError):
        pass
    return lines[:blockfinder.last]

def _extract_source(lines, lineno):
    r"""
    Given a list of lines or a multiline string and a starting lineno,
    _extract_source returns [source_lines].  [source_lines] is the smallest
    indentation block starting at lineno.

    INPUT:

    - ``lines`` - string or list of strings
    - ``lineno`` - positive integer

    EXAMPLES::

        sage: from sage.misc.sageinspect import _extract_source
        sage: s2 = "#hello\n\n  class f():\n    pass\n\n#goodbye"
        sage: _extract_source(s2, 3)
        ['  class f():\n', '    pass\n']
    """
    if lineno < 1:
        raise ValueError, "Line numbering starts at 1! (tried to extract line %s)" % lineno
    lineno -= 1

    if isinstance(lines, str):
        lines = lines.splitlines(True) # true keeps the '\n'
    if len(lines) > 0:
        # Fixes an issue with getblock
        lines[-1] += '\n'

    return _getblock(lines[lineno:])


class SageArgSpecVisitor(ast.NodeVisitor):
    """
    A simple visitor class that walks an abstract-syntax tree (AST)
    for a Python function's argspec.  It returns the contents of nodes
    representing the basic Python types: None, booleans, numbers,
    strings, lists, tuples, and dictionaries.  We use this class in
    :func:`_sage_getargspec_from_ast` to extract an argspec from a
    function's or method's source code.

    EXAMPLES::

        sage: import ast, sage.misc.sageinspect as sms
        sage: visitor = sms.SageArgSpecVisitor()
        sage: visitor.visit(ast.parse('[1,2,3]').body[0].value)
        [1, 2, 3]
        sage: visitor.visit(ast.parse("{'a':('e',2,[None,({False:True},'pi')]), 37.0:'temp'}").body[0].value)
        {'a': ('e', 2, [None, ({False: True}, 'pi')]), 37.0: 'temp'}
        sage: v = ast.parse("jc = ['veni', 'vidi', 'vici']").body[0]; v
        <_ast.Assign object at ...>
        sage: [x for x in dir(v) if not x.startswith('__')]
        ['_attributes', '_fields', 'col_offset', 'lineno', 'targets', 'value']
        sage: visitor.visit(v.targets[0])
        'jc'
        sage: visitor.visit(v.value)
        ['veni', 'vidi', 'vici']
    """
    def visit_Name(self, node):
        """
        Visit a Python AST :class:`ast.Name` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - None, True, False, or the ``node``'s name as a string.

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit_Name(ast.parse(x).body[0].value)
            sage: [vis(n) for n in ['True', 'False', 'None', 'foo', 'bar']]
            [True, False, None, 'foo', 'bar']
            sage: [type(vis(n)) for n in ['True', 'False', 'None', 'foo', 'bar']]
            [<type 'bool'>, <type 'bool'>, <type 'NoneType'>, <type 'str'>, <type 'str'>]
        """
        what = node.id
        if what == 'None':
            return None
        elif what == 'True':
            return True
        elif what == 'False':
            return False
        return node.id

    def visit_Num(self, node):
        """
        Visit a Python AST :class:`ast.Num` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - the number the ``node`` represents

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit_Num(ast.parse(x).body[0].value)
            sage: [vis(n) for n in ['123', '0.0', str(-pi.n())]]
            [123, 0.0, -3.14159265358979]
        """
        return node.n

    def visit_Str(self, node):
        r"""
        Visit a Python AST :class:`ast.Str` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - the string the ``node`` represents

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit_Str(ast.parse(x).body[0].value)
            sage: [vis(s) for s in ['"abstract"', "u'syntax'", '''r"tr\ee"''']]
            ['abstract', u'syntax', 'tr\\ee']
        """
        return node.s

    def visit_List(self, node):
        """
        Visit a Python AST :class:`ast.List` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - the list the ``node`` represents

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit_List(ast.parse(x).body[0].value)
            sage: [vis(l) for l in ['[]', "['s', 't', 'u']", '[[e], [], [pi]]']]
            [[], ['s', 't', 'u'], [['e'], [], ['pi']]]
         """
        t = []
        for n in node.elts:
            t.append(self.visit(n))
        return t

    def visit_Tuple(self, node):
        """
        Visit a Python AST :class:`ast.Tuple` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - the tuple the ``node`` represents

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit_Tuple(ast.parse(x).body[0].value)
            sage: [vis(t) for t in ['()', '(x,y)', '("Au", "Al", "Cu")']]
            [(), ('x', 'y'), ('Au', 'Al', 'Cu')]
        """
        t = []
        for n in node.elts:
            t.append(self.visit(n))
        return tuple(t)

    def visit_Dict(self, node):
        """
        Visit a Python AST :class:`ast.Dict` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - the dictionary the ``node`` represents

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit_Dict(ast.parse(x).body[0].value)
            sage: [vis(d) for d in ['{}', "{1:one, 'two':2, other:bother}"]]
            [{}, {1: 'one', 'other': 'bother', 'two': 2}]
        """
        d = {}
        for k, v in zip(node.keys, node.values):
            d[self.visit(k)] = self.visit(v)
        return d

    def visit_BoolOp(self, node):
        """
        Visit a Python AST :class:`ast.BoolOp` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - The result that ``node`` represents

        AUTHOR:

        - Simon King

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit(ast.parse(x).body[0].value)
            sage: [vis(d) for d in ['True and 1', 'False or 3 or None', '3 and 4']] #indirect doctest
            [1, 3, 4]

        """
        op = node.op.__class__.__name__
        L = list(node.values)
        out = self.visit(L.pop(0))
        if op == 'And':
            while L:
                next = self.visit(L.pop(0))
                out = out and next
            return out
        if op == 'Or':
            while L:
                next = self.visit(L.pop(0))
                out = out or next
            return out

    def visit_Compare(self, node):
        """
        Visit a Python AST :class:`ast.Compare` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - The result that ``node`` represents

        AUTHOR:

        - Simon King

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit_Compare(ast.parse(x).body[0].value)
            sage: [vis(d) for d in ['1<2==2!=3', '1==1>2', '1<2>1', '1<3<2<4']]
            [True, False, True, False]

        """
        left = self.visit(node.left)
        ops = list(node.ops)
        comparators = list(node.comparators) # the things to be compared with.
        while ops:
            op = ops.pop(0).__class__.__name__
            right = self.visit(comparators.pop(0))
            if op=='Lt':
                if not left<right:
                    return False
            elif op=='LtE':
                if not left<=right:
                    return False
            elif op=='Gt':
                if not left>right:
                    return False
            elif op=='GtE':
                if not left>=right:
                    return False
            elif op=='Eq':
                if not left==right:
                    return False
            elif op=='NotEq':
                if not left!=right:
                    return False
            left = right
        return True

    def visit_BinOp(self, node):
        """
        Visit a Python AST :class:`ast.BinOp` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - The result that ``node`` represents

        AUTHOR:

        - Simon King

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit(ast.parse(x).body[0].value)
            sage: [vis(d) for d in ['(3+(2*4))', '7|8', '5^3', '7/3', '7//3', '3<<4']] #indirect doctest
            [11, 15, 6, 2, 2, 48]
        """
        op = node.op.__class__.__name__
        if op == 'Add':
            return self.visit(node.left)+self.visit(node.right)
        if op == 'Mult':
            return self.visit(node.left)*self.visit(node.right)
        if op == 'BitAnd':
            return self.visit(node.left)&self.visit(node.right)
        if op == 'BitOr':
            return self.visit(node.left) | self.visit(node.right)
        if op == 'BitXor':
            return self.visit(node.left) ^ self.visit(node.right)
        if op == 'Div':
            return self.visit(node.left) / self.visit(node.right)
        if op == 'Eq':
            return self.visit(node.left) == self.visit(node.right)
        if op == 'FloorDiv':
            return self.visit(node.left) // self.visit(node.right)
        if op == 'NotEq':
            return self.visit(node.left) != self.visit(node.right)
        if op == 'NotIn':
            return self.visit(node.left) not in self.visit(node.right)
        if op == 'Pow':
            return self.visit(node.left) ** self.visit(node.right)
        if op == 'RShift':
            return self.visit(node.left) >> self.visit(node.right)
        if op == 'LShift':
            return self.visit(node.left) << self.visit(node.right)
        if op == 'Sub':
            return self.visit(node.left) - self.visit(node.right)
        if op == 'Gt':
            return self.visit(node.left) > self.visit(node.right)
        if op == 'GtE':
            return self.visit(node.left) >= self.visit(node.right)
        if op == 'In':
            return self.visit(node.left) in self.visit(node.right)
        if op == 'Is':
            return self.visit(node.left) is self.visit(node.right)
        if op == 'IsNot':
            return self.visit(node.left) is not self.visit(node.right)
        if op == 'Lt':
            return self.visit(node.left) < self.visit(node.right)
        if op == 'LtE':
            return self.visit(node.left) <= self.visit(node.right)
        if op == 'Mod':
            return self.visit(node.left) % self.visit(node.right)

    def visit_UnaryOp(self, node):
        """
        Visit a Python AST :class:`ast.BinOp` node.

        INPUT:

        - ``node`` - the node instance to visit

        OUTPUT:

        - The result that ``node`` represents

        AUTHOR:

        - Simon King

        EXAMPLES::

            sage: import ast, sage.misc.sageinspect as sms
            sage: visitor = sms.SageArgSpecVisitor()
            sage: vis = lambda x: visitor.visit_UnaryOp(ast.parse(x).body[0].value)
            sage: [vis(d) for d in ['+(3*2)', '-(3*2)']]
            [6, -6]

        """
        op = node.op.__class__.__name__
        if op == 'Not':
            return not self.visit(node.operand)
        if op == 'UAdd':
            return self.visit(node.operand)
        if op == 'USub':
            return -self.visit(node.operand)

def _grep_first_pair_of_parentheses(s):
    """
    Return the first matching pair of parentheses in a code string.

    INPUT:

    A string

    OUTPUT:

    A substring of the input, namely the part between the first
    (outmost) matching pair of parentheses (including the
    parentheses).

    Parentheses between single or double quotation marks do not
    count. If no matching pair of parentheses can be found, a
    ``SyntaxError`` is raised.

    EXAMPLE::

        sage: from sage.misc.sageinspect import _grep_first_pair_of_parentheses
        sage: code = 'def foo(a="\'):", b=4):\n    return'
        sage: _grep_first_pair_of_parentheses(code)
        '(a="\'):", b=4)'
        sage: code = 'def foo(a="%s):", \'b=4):\n    return'%("'")
        sage: _grep_first_pair_of_parentheses(code)
        Traceback (most recent call last):
        ...
        SyntaxError: The given string does not contain balanced parentheses

    """
    out = []
    single_quote = False
    double_quote = False
    escaped = False
    level = 0
    for c in s:
        if level>0:
            out.append(c)
        if c=='(' and not single_quote and not double_quote and not escaped:
            level += 1
        elif c=='"' and not single_quote and not escaped:
            double_quote = not double_quote
        elif c=="'" and not double_quote and not escaped:
            single_quote = not single_quote
        elif c==')' and not single_quote and not double_quote and not escaped:
            if level == 1:
                return '('+''.join(out)
            level -= 1
        elif c=="\\" and (single_quote or double_quote):
            escaped = not escaped
        else:
            escaped = False
    raise SyntaxError, "The given string does not contain balanced parentheses"

def _sage_getargspec_from_ast(source):
    r"""
    Return an argspec for a Python function or method by compiling its
    source to an abstract-syntax tree (AST) and walking its ``args``
    subtrees with :class:`SageArgSpecVisitor`.  We use this in
    :func:`_sage_getargspec_cython`.

    INPUT:

    - ``source`` - a string; the function's (or method's) source code
      definition.  The function's body is ignored.

    OUTPUT:

    - an instance of :obj:`inspect.ArgSpec`, i.e., a named tuple

    EXAMPLES::

        sage: import inspect, sage.misc.sageinspect as sms
        sage: from_ast = sms._sage_getargspec_from_ast
        sage: s = "def f(a, b=2, c={'a': [4, 5.5, False]}, d=(None, True)):\n    return"
        sage: from_ast(s)
        ArgSpec(args=['a', 'b', 'c', 'd'], varargs=None, keywords=None, defaults=(2, {'a': [4, 5.5, False]}, (None, True)))
        sage: context = {}
        sage: exec compile(s, '<string>', 'single') in context
        sage: inspect.getargspec(context['f'])
        ArgSpec(args=['a', 'b', 'c', 'd'], varargs=None, keywords=None, defaults=(2, {'a': [4, 5.5, False]}, (None, True)))
        sage: from_ast(s) == inspect.getargspec(context['f'])
        True
        sage: set(from_ast(sms.sage_getsource(x)) == inspect.getargspec(x) for x in [factor, identity_matrix, Graph.__init__])
        set([True])
    """
    ast_args = ast.parse(source.lstrip()).body[0].args

    visitor = SageArgSpecVisitor()
    args = [visitor.visit(a) for a in ast_args.args]
    defaults = [visitor.visit(d) for d in ast_args.defaults]

    return inspect.ArgSpec(args, ast_args.vararg, ast_args.kwarg,
                           tuple(defaults) if defaults else None)

def _sage_getargspec_cython(source):
    r"""
    inspect.getargspec from source code.  That is, get the names and
    default values of a function's arguments.

    INPUT:

    ``source`` - a string of Cython code

    OUTPUT:

    A tuple (``args``, None, None, ``argdefs``), where ``args`` is the
    list of arguments and ``argdefs`` is their default values (as
    strings, so 2 is represented as '2', etc.).

    EXAMPLES::

        sage: from sage.misc.sageinspect import _sage_getargspec_cython as sgc
        sage: sgc("cpdef double abc(self, x=None, base=0):")
        (['self', 'x', 'base'], None, None, (None, 0))
        sage: sgc("def __init__(self, x=None, unsigned int base=0):")
        (['self', 'x', 'base'], None, None, (None, 0))
        sage: sgc('def o(p, *q, r={}, **s) except? -1:')
        (['p', '*q', 'r', '**s'], None, None, ({},))
        sage: sgc('cpdef how(r=(None, "u:doing?")):')
        (['r'], None, None, ((None, 'u:doing?'),))
        sage: sgc('def _(x="):"):')
        (['x'], None, None, ('):',))
        sage: sgc('def f(z = {(1,2,3): True}):\n    return z')
        (['z'], None, None, ({(1, 2, 3): True},))
        sage: sgc('def f(double x, z = {(1,2,3): True}):\n    return z')
        Traceback (most recent call last):
        ...
        ValueError: Could not parse cython argspec

    AUTHOR:

    - Nick Alexander
    """
    try:
        defpos = source.find('def ')
        assert defpos > -1
        colpos = source.find(':')
        assert colpos > -1
        defsrc = source[defpos:colpos]

        lparpos = defsrc.find('(')
        assert lparpos > -1
        rparpos = defsrc.rfind(')')
        assert rparpos > -1

        argsrc = defsrc[lparpos+1:rparpos]

        # Now handle individual arguments
        # XXX this could break on embedded strings or embedded functions
        args = argsrc.split(',')

        # Now we need to take care of default arguments
        # XXX this could break on embedded strings or embedded functions with default arguments
        argnames = [] # argument names
        argdefs  = [] # default values
        for arg in args:
            # only process arg if it has positive length
            if len(arg) > 0:
                s = arg.split('=')
                argname = s[0]

                # Cython often has type information; we split off the right most
                # identifier to discard this information
                argname = argname.split()[-1]
                # Cython often has C pointer symbols before variable names
                argname.lstrip('*')
                argnames.append(argname)
                if len(s) > 1:
                    defvalue = s[1]
                    # eval defvalue so we aren't just returning strings
                    try:
                        argdefs.append(eval(defvalue))
                    except NameError:
                        argdefs.append(defvalue)

        if len(argdefs) > 0:
            argdefs = tuple(argdefs)
        else:
            argdefs = None

        return (argnames, None, None, argdefs)

    except Exception:
        try:
            # Try to parse the entire definition as Python and get an
            # argspec.
            beg = re.search(r'def([ ]+\w+)+[ ]*\(', source).end() - 1
            proxy = 'def dummy' + source[beg:] + '\n    return'
            return tuple(_sage_getargspec_from_ast(proxy))

        except Exception:
            try:
                # Try to parse just the arguments as a Python argspec.
                proxy = 'def dummy' + _grep_first_pair_of_parentheses(source) + ':\n    return'
                return tuple(_sage_getargspec_from_ast(proxy))

            except Exception:
                raise ValueError, "Could not parse cython argspec"

def sage_getfile(obj):
    r"""
    Get the full file name associated to ``obj`` as a string.

    INPUT: ``obj``, a Sage object, module, etc.

    EXAMPLES::

        sage: from sage.misc.sageinspect import sage_getfile
        sage: sage_getfile(sage.rings.rational)[-23:]
        'sage/rings/rational.pyx'
        sage: sage_getfile(Sq)[-42:]
        'sage/algebras/steenrod/steenrod_algebra.py'

    The following tests against some bugs fixed in trac ticket #9976::

        sage: obj = sage.combinat.partition_algebra.SetPartitionsAk
        sage: obj = sage.combinat.partition_algebra.SetPartitionsAk
        sage: sage_getfile(obj)
        '...sage/combinat/partition_algebra.py'

    And here is another bug, fixed in trac ticket #11298::

        sage: P.<x,y> = QQ[]
        sage: sage_getfile(P)
        '...sage/rings/polynomial/multi_polynomial_libsingular.pyx'

    AUTHORS:

    - Nick Alexander
    - Simon King
    """
    # We try to extract from docstrings, but not using Python's inspect
    # because _sage_getdoc_unformatted is more robust.
    d = _sage_getdoc_unformatted(obj)
    pos = _extract_embedded_position(d)
    if pos is not None:
        (_, filename, _) = pos
        return filename

    # The instance case
    if isclassinstance(obj):
        if isinstance(obj, functools.partial):
            return sage_getfile(obj.func)
        return sage_getfile(obj.__class__) #inspect.getabsfile(obj.__class__)

    # No go? fall back to inspect.
    return inspect.getabsfile(obj)

def sage_getargspec(obj):
    r"""
    Return the names and default values of a function's arguments.

    INPUT:

    ``obj``, any callable object

    OUTPUT:

    An ``ArgSpec`` is returned. This is a named tuple
    ``(args, varargs, keywords, defaults)``.

    - ``args`` is a list of the argument names (it may contain nested lists).

    - ``varargs`` and ``keywords`` are the names of the ``*`` and ``**``
      arguments or ``None``.

    - ``defaults`` is an `n`-tuple of the default values of the last `n` arguments.

    NOTE:

    If the object has a method ``_sage_argspec_`` then the output of
    that method is transformed into a named tuple and then returned.

    If a class instance has a method ``_sage_src_`` then its output
    is  studied to determine the argspec. This is because currently
    the :class:`~sage.misc.cachefunc.CachedMethod` decorator has
    no ``_sage_argspec_`` method.

    EXAMPLES::

        sage: from sage.misc.sageinspect import sage_getargspec
        sage: sage_getargspec(identity_matrix)
        ArgSpec(args=['ring', 'n', 'sparse'], varargs=None, keywords=None, defaults=(0, False))
        sage: sage_getargspec(Poset)
        ArgSpec(args=['data', 'element_labels', 'cover_relations'], varargs=None, keywords=None, defaults=(None, None, False))
        sage: sage_getargspec(factor)
        ArgSpec(args=['n', 'proof', 'int_', 'algorithm', 'verbose'], varargs=None, keywords='kwds', defaults=(None, False, 'pari', 0))

    In the case of a class or a class instance, the ``ArgSpec`` of the ``__new__`` or ``__init__``
    methods are returned::

        sage: P.<x,y> = QQ[]
        sage: sage_getargspec(P)
        ArgSpec(args=['self', 'element'], varargs=None, keywords=None, defaults=None)
        sage: sage_getargspec(P.__class__)
        ArgSpec(args=['self', 'element'], varargs=None, keywords=None, defaults=None)

    The following tests against various bugs that were fixed in
    trac ticket #9976::

        sage: from sage.rings.polynomial.real_roots import bernstein_polynomial_factory_ratlist
        sage: sage_getargspec(bernstein_polynomial_factory_ratlist.coeffs_bitsize)
        ArgSpec(args=['self'], varargs=None, keywords=None, defaults=None)
        sage: from sage.rings.polynomial.pbori import BooleanMonomialMonoid
        sage: sage_getargspec(BooleanMonomialMonoid.gen)
        ArgSpec(args=['self', 'i'], varargs=None, keywords=None, defaults=(0,))
        sage: I = P*[x,y]
        sage: sage_getargspec(I.groebner_basis)
        ArgSpec(args=['self', 'algorithm', 'deg_bound', 'mult_bound', 'prot'],
        varargs='args', keywords='kwds', defaults=('', None, None, False))
        sage: cython("cpdef int foo(x,y) except -1: return 1")
        sage: sage_getargspec(foo)
        ArgSpec(args=['x', 'y'], varargs=None, keywords=None, defaults=None)

    If a ``functools.partial`` instance is involved, we see no other meaningful solution
    than to return the argspec of the underlying function::

        sage: def f(a,b,c,d=1): return a+b+c+d
        ...
        sage: import functools
        sage: f1 = functools.partial(f, 1,c=2)
        sage: sage_getargspec(f1)
        ArgSpec(args=['a', 'b', 'c', 'd'], varargs=None, keywords=None, defaults=(1,))

    TESTS:

    By trac ticket #9976, rather complicated cases work. In the
    following example, we dynamically create an extension class
    that returns some source code, and the example shows that
    the source code is taken for granted, i.e., the argspec of
    an instance of that class does not coincide with the argspec
    of its call method. That behaviour is intended, since a
    decorated method appears to have the generic signature
    ``*args,**kwds``, but in fact it is only supposed to be called
    with the arguments requested by the underlying undecorated
    method. We saw an easy example above, namely ``I.groebner_basis``.
    Here is a more difficult one::

        sage: cython_code = [
        ... 'cdef class MyClass:',
        ... '    def _sage_src_(self):',
        ... '        return "def foo(x, a=\\\')\\\"\\\', b={(2+1):\\\'bar\\\', not 1:3, 3<<4:5}): return\\n"',
        ... '    def __call__(self, m,n): return "something"']
        sage: cython('\n'.join(cython_code))
        sage: O = MyClass()
        sage: print sage.misc.sageinspect.sage_getsource(O)
        def foo(x, a=')"', b={(2+1):'bar', not 1:3, 3<<4:5}): return
        sage: sage.misc.sageinspect.sage_getargspec(O)
        ArgSpec(args=['x', 'a', 'b'], varargs=None, keywords=None, defaults=(')"', {False: 3, 48: 5, 3: 'bar'}))
        sage: sage.misc.sageinspect.sage_getargspec(O.__call__)
        ArgSpec(args=['self', 'm', 'n'], varargs=None, keywords=None, defaults=None)

    ::

        sage: cython('def foo(x, a=\'\\\')"\', b={not (2+1==3):\'bar\'}): return')
        sage: print sage.misc.sageinspect.sage_getsource(foo)
        def foo(x, a='\')"', b={not (2+1==3):'bar'}): return
        <BLANKLINE>
        sage: sage.misc.sageinspect.sage_getargspec(foo)
        ArgSpec(args=['x', 'a', 'b'], varargs=None, keywords=None, defaults=('\')"', {False: 'bar'}))

    AUTHORS:

    - William Stein: a modified version of inspect.getargspec from the
      Python Standard Library, which was taken from IPython for use in Sage.
    - Extensions by Nick Alexander
    - Simon King: Return an ``ArgSpec``, fix some bugs.
    """
    from sage.misc.lazy_attribute import lazy_attribute
    from sage.misc.abstract_method import AbstractMethod
    if isinstance(obj, (lazy_attribute, AbstractMethod)):
        source = sage_getsource(obj)
        return inspect.ArgSpec(*_sage_getargspec_cython(source))
    if not callable(obj):
        raise TypeError, "obj is not a code object"
    try:
        return inspect.ArgSpec(*obj._sage_argspec_())
    except (AttributeError, TypeError):
        pass
    if inspect.isfunction(obj):
        func_obj = obj
    elif inspect.ismethod(obj):
        func_obj = obj.im_func
    elif isclassinstance(obj):
        if hasattr(obj,'_sage_src_'): #it may be a decorator!
            source = sage_getsource(obj)
            # we try to find the definition and parse it by _sage_getargspec_ast
            proxy = 'def dummy' + _grep_first_pair_of_parentheses(source) + ':\n    return'
            return _sage_getargspec_from_ast(proxy)
        elif isinstance(obj,functools.partial):
            base_spec = sage_getargspec(obj.func)
            return base_spec
        return sage_getargspec(obj.__class__.__call__)
    elif inspect.isclass(obj):
        return sage_getargspec(obj.__call__)
    elif (hasattr(obj, '__objclass__') and hasattr(obj, '__name__') and
          obj.__name__ == 'next'):
        # Handle sage.rings.ring.FiniteFieldIterator.next and similar
        # slot wrappers.  This is mainly to suppress Sphinx warnings.
        return ['self'], None, None, None
    else:
        # Perhaps it is binary and defined in a Cython file
        source = sage_getsource(obj, is_binary=True)
        if source:
            return inspect.ArgSpec(*_sage_getargspec_cython(source))
        else:
            func_obj = obj

    # Otherwise we're (hopefully!) plain Python, so use inspect
    try:
        args, varargs, varkw = inspect.getargs(func_obj.func_code)
    except AttributeError:
        try:
            args, varargs, varkw = inspect.getargs(func_obj)
        except TypeError: # arg is not a code object
        # The above "hopefully" was wishful thinking:
            return inspect.ArgSpec(*_sage_getargspec_cython(sage_getsource(obj)))
            #return _sage_getargspec_from_ast(sage_getsource(obj))
    try:
        defaults = func_obj.func_defaults
    except AttributeError:
        defaults = tuple([])
    return inspect.ArgSpec(args, varargs, varkw, defaults)

def sage_getdef(obj, obj_name=''):
    r"""
    Return the definition header for any callable object.

    INPUT:

    - ``obj`` - function
    - ``obj_name`` - string (optional, default '')

    ``obj_name`` is prepended to the output.

    EXAMPLES::

        sage: from sage.misc.sageinspect import sage_getdef
        sage: sage_getdef(identity_matrix)
        '(ring, n=0, sparse=False)'
        sage: sage_getdef(identity_matrix, 'identity_matrix')
        'identity_matrix(ring, n=0, sparse=False)'

    Check that trac ticket #6848 has been fixed::

        sage: sage_getdef(RDF.random_element)
        '(min=-1, max=1)'

    If an exception is generated, None is returned instead and the
    exception is suppressed.

    AUTHORS:

    - William Stein
    - extensions by Nick Alexander
    """
    try:
        spec = sage_getargspec(obj)
        s = str(inspect.formatargspec(*spec))
        s = s.strip('(').strip(')').strip()
        if s[:4] == 'self':
            s = s[4:]
        s = s.lstrip(',').strip()
        # for use with typesetting the definition with the notebook:
        # sometimes s contains "*args" or "**keywds", and the
        # asterisks confuse ReST/sphinx/docutils, so escape them:
        # change * to \*, and change ** to \**.
        if EMBEDDED_MODE:
            s = s.replace('**', '\\**')  # replace ** with \**
            t = ''
            while True:  # replace * with \*
                i = s.find('*')
                if i == -1:
                    break
                elif i > 0 and s[i-1] == '\\':
                    if s[i+1] == "*":
                        t += s[:i+2]
                        s = s[i+2:]
                    else:
                        t += s[:i+1]
                        s = s[i+1:]
                    continue
                elif i > 0 and s[i-1] == '*':
                    t += s[:i+1]
                    s = s[i+1:]
                    continue
                else:
                    t += s[:i] + '\\*'
                    s = s[i+1:]
            s = t + s
        return obj_name + '(' + s + ')'
    except (AttributeError, TypeError, ValueError):
        return '%s( [noargspec] )'%obj_name

def _sage_getdoc_unformatted(obj):
    r"""
    Return the unformatted docstring associated to ``obj`` as a
    string.  Feed the results from this into the
    sage.misc.sagedoc.format for printing to the screen.

    INPUT: ``obj``, a function, module, etc.: something with a docstring.

    If ``obj`` is a Cython object with an embedded position in its
    docstring, the embedded position is stripped.

    EXAMPLES::

        sage: from sage.misc.sageinspect import _sage_getdoc_unformatted
        sage: _sage_getdoc_unformatted(identity_matrix)[5:44]
        'Return the `n \\times n` identity matrix'

    TESTS:

    Test that we suppress useless built-in output (Ticket #3342)

        sage: from sage.misc.sageinspect import _sage_getdoc_unformatted
        sage: _sage_getdoc_unformatted(isinstance.__class__)
        ''

    AUTHORS:

    - William Stein
    - extensions by Nick Alexander
    """
    if obj is None: return ''
    r = None
    try:
        r = obj._sage_doc_()
    except (AttributeError, TypeError): # the TypeError occurs if obj is a class
        r = obj.__doc__

    #Check to see if there is an __init__ method, and if there
    #is, use its docstring.
    if r is None and hasattr(obj, '__init__'):
        r = obj.__init__.__doc__

    if r is None:
        return ''

    # Check if the __doc__ attribute was actually a string, and
    # not a 'getset_descriptor' or similar.
    import types
    if not isinstance(r, types.StringTypes):
        return ''

    from sagenb.misc.misc import encoded_str
    return encoded_str(r)

def sage_getdoc(obj, obj_name='', embedded_override=False):
    r"""
    Return the docstring associated to ``obj`` as a string.

    INPUT: ``obj``, a function, module, etc.: something with a docstring.

    If ``obj`` is a Cython object with an embedded position in its
    docstring, the embedded position is stripped.

    If optional argument ``embedded_override`` is False (its default
    value), then the string is formatted according to the value of
    EMBEDDED_MODE.  If this argument is True, then it is formatted as
    if EMBEDDED_MODE were True.

    EXAMPLES::

        sage: from sage.misc.sageinspect import sage_getdoc
        sage: sage_getdoc(identity_matrix)[3:39]
        'Return the n x n identity matrix ove'
        sage: def f(a,b,c,d=1): return a+b+c+d
        ...
        sage: import functools
        sage: f1 = functools.partial(f, 1,c=2)
        sage: f.__doc__ = "original documentation"
        sage: f1.__doc__ = "specialised documentation"
        sage: sage_getdoc(f)
        'original documentation\n'
        sage: sage_getdoc(f1)
        'specialised documentation\n'

    AUTHORS:

    - William Stein
    - extensions by Nick Alexander
    """
    import sage.misc.sagedoc
    if obj is None: return ''
    r = _sage_getdoc_unformatted(obj)

    if r is None:
        return ''

    s = sage.misc.sagedoc.format(str(r), embedded=(embedded_override or EMBEDDED_MODE))

    # If there is a Cython embedded position, it needs to be stripped
    pos = _extract_embedded_position(s)
    if pos is not None:
        s, _, _ = pos

    # Fix object naming
    if obj_name != '':
        i = obj_name.find('.')
        if i != -1:
            obj_name = obj_name[:i]
        s = s.replace('self.','%s.'%obj_name)

    return s

def sage_getsource(obj, is_binary=False):
    r"""
    Return the source code associated to obj as a string, or None.

    INPUT:

    - ``obj`` - function, etc.
    - ``is_binary`` - boolean, ignored

    EXAMPLES::

        sage: from sage.misc.sageinspect import sage_getsource
        sage: sage_getsource(identity_matrix, True)[4:45]
        'identity_matrix(ring, n=0, sparse=False):'
        sage: sage_getsource(identity_matrix, False)[4:45]
        'identity_matrix(ring, n=0, sparse=False):'

    AUTHORS:

    - William Stein
    - extensions by Nick Alexander
    """
    #First we should check if the object has a _sage_src_
    #method.  If it does, we just return the output from
    #that.  This is useful for getting pexpect interface
    #elements to behave similar to regular Python objects
    #with respect to introspection.
    try:
        return obj._sage_src_()
    except (AttributeError, TypeError):
        pass

    t = sage_getsourcelines(obj, is_binary)
    if not t:
        return None
    (source_lines, lineno) = t
    return ''.join(source_lines)

def sage_getsourcelines(obj, is_binary=False):
    r"""
    Return a pair ([source_lines], starting line number) of the source
    code associated to obj, or None.

    INPUT:

    - ``obj`` - function, etc.
    - ``is_binary`` - boolean, ignored

    OUTPUT: (source_lines, lineno) or None: ``source_lines`` is a list
    of strings, and ``lineno`` is an integer.

    At this time we ignore ``is_binary`` in favour of a 'do our best' strategy.

    EXAMPLES::

        sage: from sage.misc.sageinspect import sage_getsourcelines
        sage: sage_getsourcelines(matrix, True)[1]
        34
        sage: sage_getsourcelines(matrix, False)[0][0][4:]
        'matrix(*args, **kwds):\n'

    TESTS::

        sage: cython('''cpdef test_funct(x,y): return''')
        sage: sage_getsourcelines(test_funct)
        (['cpdef test_funct(x,y): return\n'], 6)

    The following tests that an instance of ``functools.partial`` is correctly
    dealt with (see trac ticket #9976)::

        sage: obj = sage.combinat.partition_algebra.SetPartitionsAk
        sage: sage_getsourcelines(obj)
        (['def create_set_partition_function(letter, k):\n',
        ...
        '    raise ValueError, "k must be an integer or an integer + 1/2"\n'], 31)

    Here are some cases that were covered in trac ticket #11298;
    note that line numbers may easily change, and therefore we do
    not test them::

        sage: P.<x,y> = QQ[]
        sage: I = P*[x,y]
        sage: sage_getsourcelines(P)
        (['cdef class MPolynomialRing_libsingular(MPolynomialRing_generic):\n',
          '\n',
          '    def __cinit__(self):\n',
        ...
          '          M.append(new_MP(self, p_Copy(tempvector, _ring)))\n',
          '          return M\n'], ...)
        sage: sage_getsourcelines(I)
        (['class MPolynomialIdeal( MPolynomialIdeal_singular_repr, \\\n',
        ...
        '        return result_ring.ideal(result)\n'], ...)
        sage: x = var('x')
        sage: sage_getsourcelines(x)
        (['cdef class Expression(CommutativeRingElement):\n',
          '    cpdef object pyobject(self):\n',
        ...
          '        return self / x\n'], ...)


    AUTHORS:

    - William Stein
    - Extensions by Nick Alexander
    - Extension to interactive Cython code by Simon King
    - Simon King: If a class has no docstring then let the class
      definition be found starting from the ``__init__`` method.
    """

    try:
        return obj._sage_src_lines_()
    except (AttributeError, TypeError):
        pass

    # Check if we deal with instance
    if isclassinstance(obj):
        if isinstance(obj,functools.partial):
            obj = obj.func
        else:
            obj=obj.__class__

    # If we can handle it, we do.  We first try Python's inspect, and
    # if that fails then we try _sage_getdoc_unformatted. We can not use
    # the latter right away, since otherwise there is an import problem
    # at sage startup, believe it or not.
    d = inspect.getdoc(obj)
    pos = _extract_embedded_position(d)
    if pos is None:
        d = _sage_getdoc_unformatted(obj)
        pos = _extract_embedded_position(d)
        if pos is None:
            try:
                return inspect.getsourcelines(obj)
            except IOError:
                if obj.__class__ != type:
                    return sage_getsourcelines(obj.__class__)
                raise

    (orig, filename, lineno) = pos
    try:
        source_lines = open(filename).readlines()
    except IOError:
        try:
            from sage.all import SAGE_TMP
            raw_name = filename.split('/')[-1]
            newname = SAGE_TMP+'/spyx/'+'_'.join(raw_name.split('_')[:-1])+'/'+raw_name
            source_lines = open(newname).readlines()
        except IOError:
            return None

    # It is possible that the source lines belong to the __init__ method,
    # rather than to the class. So, we try to look back and find the class
    # definition.
    first_line = source_lines[lineno-1]
    leading_blanks = len(first_line)-len(first_line.lstrip())
    if first_line.lstrip().startswith('def ') and "__init__" in first_line and obj.__name__!='__init__':
        ignore = False
        double_quote = None
        for lnb in xrange(lineno,0,-1):
            new_first_line = source_lines[lnb-1]
            nfl_strip = new_first_line.lstrip()
            if nfl_strip.startswith('"""'):
                if double_quote is None:
                    double_quote=True
                if double_quote:
                    ignore = not ignore
            elif nfl_strip.startswith("'''"):
                if double_quote is None:
                    double_quote=False
                if double_quote is False:
                    ignore = not ignore
            if ignore:
                continue
            if len(new_first_line)-len(nfl_strip)<leading_blanks and nfl_strip:
                # We are not inside a doc string. So, if the indentation
                # is less than the indentation of the __init__ method
                # then we must be at the class definition!
                lineno = lnb
                break
    return _extract_source(source_lines, lineno), lineno

def sage_getvariablename(self, omit_underscore_names=True):
    """
    Attempt to get the name of a Sage object.

    INPUT:

    - ``self`` -- any object.

    - ``omit_underscore_names`` -- boolean, default ``True``.

    OUTPUT:

    If the user has assigned an object ``obj`` to a variable name,
    then return that variable name.  If several variables point to
    ``obj``, return a sorted list of those names.  If
    ``omit_underscore_names`` is True (the default) then omit names
    starting with an underscore "_".

    This is a modified version of code taken from
    http://pythonic.pocoo.org/2009/5/30/finding-objects-names,
    written by Georg Brandl.

    EXAMPLES::

        sage: from sage.misc.sageinspect import sage_getvariablename
        sage: A = random_matrix(ZZ, 100)
        sage: sage_getvariablename(A)
        'A'
        sage: B = A
        sage: sage_getvariablename(A)
        ['A', 'B']

    If an object is not assigned to a variable, an empty list is returned::

        sage: sage_getvariablename(random_matrix(ZZ, 60))
        []
    """
    # first look through variables in stack frames
    result = []
    for frame in inspect.stack():
        for name, obj in frame[0].f_globals.iteritems():
            if obj is self:
                result.append(name)
    if len(result) == 1:
        return result[0]
    else:
        return sorted(result)

__internal_teststring = '''
import os                                  # 1
# preceding comment not include            # 2
def test1(a, b=2):                         # 3
    if a:                                  # 4
        return 1                           # 5
    return b                               # 6
# intervening comment not included         # 7
class test2():                             # 8
    pass                                   # 9
    # indented comment not included        # 10
# trailing comment not included            # 11
def test3(b,                               # 12
          a=2):                            # 13
    pass # EOF                             # 14'''

def __internal_tests():
    r"""
    Test internals of the sageinspect module.

    EXAMPLES::

        sage: from sage.misc.sageinspect import *
        sage: from sage.misc.sageinspect import _extract_source, _extract_embedded_position, _sage_getargspec_cython, __internal_teststring

    If docstring is None, nothing bad happens::

        sage: sage_getdoc(None)
        ''

        sage: sage_getsource(sage)
        "...all..."

    A cython function with default arguments (one of which is a string)::

        sage: sage_getdef(sage.rings.integer.Integer.factor, obj_name='factor')
        "factor(algorithm='pari', proof=None, limit=None, int_=False, verbose=0)"

    This used to be problematic, but was fixed in #10094::

        sage: sage_getsource(sage.rings.integer.Integer.__init__, is_binary=True)
        '    def __init__(self, x=None, unsigned int base=0):\n...'
        sage: sage_getdef(sage.rings.integer.Integer.__init__, obj_name='__init__')
        '__init__(x=None, base=0)'

    Test _extract_source with some likely configurations, including no trailing
    newline at the end of the file::

        sage: s = __internal_teststring.strip()
        sage: es = lambda ls, l: ''.join(_extract_source(ls, l)).rstrip()

        sage: print es(s, 3)
        def test1(a, b=2):                         # 3
            if a:                                  # 4
                return 1                           # 5
            return b                               # 6

        sage: print es(s, 8)
        class test2():                             # 8
            pass                                   # 9

        sage: print es(s, 12)
        def test3(b,                               # 12
                  a=2):                            # 13
            pass # EOF                             # 14

    Test _sage_getargspec_cython with multiple default arguments and a type::

        sage: _sage_getargspec_cython("def init(self, x=None, base=0):")
        (['self', 'x', 'base'], None, None, (None, 0))
        sage: _sage_getargspec_cython("def __init__(self, x=None, base=0):")
        (['self', 'x', 'base'], None, None, (None, 0))
        sage: _sage_getargspec_cython("def __init__(self, x=None, unsigned int base=0):")
        (['self', 'x', 'base'], None, None, (None, 0))

    Test _extract_embedded_position:

    We cannot test the filename since it depends on SAGE_ROOT.

    Make sure things work with no trailing newline::

        sage: _extract_embedded_position('File: sage/rings/rational.pyx (starting at line 1080)')
        ('', '.../rational.pyx', 1080)

    And with a trailing newline::

        sage: s = 'File: sage/rings/rational.pyx (starting at line 1080)\n'
        sage: _extract_embedded_position(s)
        ('', '.../rational.pyx', 1080)

    And with an original docstring::

        sage: s = 'File: sage/rings/rational.pyx (starting at line 1080)\noriginal'
        sage: _extract_embedded_position(s)
        ('original', '.../rational.pyx', 1080)

    And with a complicated original docstring::

        sage: s = 'File: sage/rings/rational.pyx (starting at line 1080)\n\n\noriginal test\noriginal'
        sage: _extract_embedded_position(s)
        ('\n\noriginal test\noriginal', ..., 1080)

        sage: s = 'no embedded position'
        sage: _extract_embedded_position(s) is None
        True
    """
