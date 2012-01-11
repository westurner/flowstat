#!/usr/bin/env python
"""
ReStructuredText Utility for modifying ReStructuredText headings by the
specified shift offset.

For example::

    ==========
    Title
    ==========

    Heading 1
    =========
    Heading 2
    ---------
    Heading 3
    ~~~~~~~~~

Shifted by 1::

    Title
    ======
    Heading 1
    ----------
    Heading 2
    ~~~~~~~~~~
    Heading 3
    '''''''''

"""

import re
import optparse
import codecs
from StringIO import StringIO

RE_TITLE = re.compile(r'^([\=|\-|\~]+)\n(.*)\n^([\=|\-|\~]+)\n', re.MULTILINE)
RE_HEADING = re.compile(r'^(?:[\=|\-|\~]?)(?:[\n]?)(.*)\n^([\=|\-|\~]+)\n',
                                                                 re.MULTILINE)
RE_NUMREF = re.compile(r'^.. [(\d+)]\n?', re.MULTILINE)

STANDARD_HEADINGS = {
 0: '==',
 1: '=',
 2: '-',
 3: '~',
 4: "'",
 5: '"',
 6: '`',
 7: '^',
 8: '_',
 9: '*',
 10: '+',
 11: '#',
 12: '<',
 13: '>'}

def restructuredtext_shift(input_file, shiftby, refoffset=None):
    """

    Shift the headings of a restructuredtext document

    :param input_file: ReStructuredText file to read
    :type input_file: str
    :param shiftby: offset to shift headings by
    :type shiftby: signed int
    """

    lines=[]
    if isinstance(input_file, (file, StringIO)):
        lines = input_file.read()
    elif isinstance(input_file, list):
        lines = u''.join(input_file)
    else:
        input_file = codecs.open(input_file,'r+', 'utf-8')
        lines = input_file.read()


    depthcount = 0
    headings = {}
    sections = []

    # Special case for title
    title_obj = RE_TITLE.search(lines)
    if title_obj:
        (overline, title, underline) = title_obj.groups()
        #if len(overline) == len(underline):
        headings[overline[0]*2] = 0

        #print 0, title
        #sections.append((0, '\n'.join([overline, title, underline])))

    # Extract section headings and existing section heading numbering
    for g in RE_HEADING.finditer(lines):
        (text, line) = g.groups()
        underline_char = line[0]
        depth = headings.get(underline_char)
        if not depth:
            depthcount += 1
            headings[underline_char] = depthcount

        heading_level = headings[underline_char]
        sections.append(
            (heading_level, underline_char, '\n'.join((text, line))))
        print heading_level, heading_level * '  ', text

    STD_HEADINGS = STANDARD_HEADINGS.values()

    # Expand headings with elements from STD_HEADINGS
    for char in sorted(headings.keys()):
        STD_HEADINGS.remove(char)
    for n in xrange(len(STD_HEADINGS)):
        dest = depthcount + ((((shiftby > 0) and 1 or -1)) * n)
        headings[STD_HEADINGS[n]] = dest

    headings_by_n = dict(
        (x[1], x[0]) for x in headings.iteritems()
    )

    # Renumber numbered links (.. [n])
    if refoffset:
        for ref in RE_NUMREF.finditer(lines):
            num = ref.groups()[0]
            print '%s --> %s' % (num, refoffset+num)
            refoffset+=1

    #output = copy.copy(lines)
    output = lines

    # Perform underline replacements
    for section in sections:
        (level, char, text) = section
        newlevel = level + shiftby
        newchar = headings_by_n[newlevel]
        section, underline = text.split('\n',1)
        newtext = '\n'.join((section, underline.replace(char, newchar)))

        output = output.replace(text, newtext, 1)

    return output, refoffset

def main():
    prs = optparse.OptionParser()
    prs.add_option('-i','--input-file',dest='input_file',action='store',
        help='ReStructuredText file to reindent')
    prs.add_option('-s','--shiftby',dest='shiftby',action='store',
        help='Degrees to shift ReStructuredText headings by (eg 1, -1)')

    (opts,args) = prs.parse_args()

    if not (opts.input_file and opts.shiftby):
        raise Exception("Must specify both --input-file and --shiftby")
        exit(0)
    print restructuredtext_shift(opts.input_file, int(opts.shiftby))[0]

if __name__=="__main__":
    main()
