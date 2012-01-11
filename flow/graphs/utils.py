import codecs
from itertools import izip, count

def grep_file(
        filename=None,
        fileobj=None,
        searchfn=lambda x: x.startswith('G=')):
    """read, iter, searchfn, repeat

    :rtype: generator
    :returns: (linenumber, line)
    """
    if not fileobj:
        fileobj = codecs.open(filename, "r", "utf-8")
    for i, n in izip(count(1), fileobj):
        n = n.lstrip() # ...
        if searchfn(n):
            yield (i, n)

