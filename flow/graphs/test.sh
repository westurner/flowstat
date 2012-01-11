#!/bin/sh
docname="networkxref"
RST="${docname}.rst"
HTML="${docname}.html"
RST_COMMAND="rst2html-highlight.py"
python ./reference.py > $RST
$RST_COMMAND $RST  > $HTML
sensible-browser $HTML &
cat $RST
