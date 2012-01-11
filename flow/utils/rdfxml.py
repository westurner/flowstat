# -*- coding: iso-8859-15 -*-
# (c) Mikael Högqvist, ZIB, AstroGrid-D
# This software is licensed under the software license specified at
# http://www.gac-grid.org/

# this is a work-around of the SPARQL XML-serialization in rdflib which does
# not work on all installation due to a bug in the python sax-parser
# We rely on ElementTree which is only available in Python 2.5

# See: http://code.alcidesfonseca.com/docs/rdflib/addons.html#sparql-xml-serializer 

from cStringIO import StringIO

try:
    from xml.etree.cElementTree import Element, SubElement, \
                                ElementTree, ProcessingInstruction
    import xml.etree.cElementTree as ET
except ImportError:
    from cElementTree import Element, SubElement, ElementTree
    import cElementTree as ET

from rdflib import URIRef, BNode, Literal

SPARQL_XML_NAMESPACE = u'http://www.w3.org/2005/sparql-results#'
XML_NAMESPACE = "http://www.w3.org/2001/XMLSchema#"

name = lambda elem: u'{%s}%s' % (SPARQL_XML_NAMESPACE, elem)
xml_name = lambda elem: u'{%s}%s' % (XML_NAMESPACE, elem)

def variables(results):
    # don't include any variables which are not part of the
    # result set
    #res_vars = set(results.selectionF).intersection(
    #                               set(results.allVariables))


    # this means select *, use all variables from the result-set
    #if len(results.selectionF) == 0:
    #    res_vars = results.allVariables
    #else:
    #    res_vars = [v for v in results.selectionF
    #                        if v in results.allVariables]
    #
    return results['head']['vars']

def header(results, root):
    head = SubElement(root, name(u'head'))

    res_vars = variables(results)
    for var in res_vars:
        v = SubElement(head, name(u'variable'))
        # remove the ?
        v.attrib[u'name'] = var[1:]

def res_iter(results):
    res_vars = variables(results)

    for row in results['results']['bindings']:
        if len(res_vars) == 1:
            row = (row, )

        yield zip(row, res_vars)

def binding(val, var, elem):
    bindingElem = SubElement(elem, name(u'binding'))
    bindingElem.attrib[u'name'] = var

    if isinstance(val,URIRef):
        varElem = SubElement(bindingElem, name(u'uri'))
    elif isinstance(val,BNode) :
        varElem = SubElement(bindingElem, name(u'bnode'))
    elif isinstance(val,Literal):
        varElem = SubElement(bindingElem, name(u'literal'))

        if val.language != "" and val.language != None:
            varElem.attrib[xml_name(u'lang')] = str(val.language)
        elif val.datatype != "" and val.datatype != None:
            varElem.attrib[name(u'datatype')] = str(val.datatype)

    varElem.text = str(val)

def binding_2(k, d, elem):
    bindingElem = SubElement(elem, name(u'binding'))
    bindingElem.attrib[u'name'] = k

    typ = d['type']
    if typ=='uri':
        varElem = SubElement(bindingElem, u'uri')
    elif type=='bnode':
        varElem = SubElement(bindingElem, u'bnode')
    elif type=='literal':
        varElem = SubElement(bindingElem, u'literal')

        if k['language']:
            varElem.attrib[xml_name(u'lang')] = str(d['language'])
        if k['datatype']:
            varElem.attrib[name(u'datatype')] = str(d['datatype'])

    varElem.text = d['value']

def result_list(results, root):
    resultsElem = SubElement(root, name(u'results'))

    ordered = results['results'].get('ordered', False)

    #if ordered == None:
    #    ordered = False

    # removed according to the new working draft (2007-06-14)
    # resultsElem.attrib[u'ordered'] = str(ordered)
    # resultsElem.attrib[u'distinct'] = str(results.distinct)

    for row in results['results']['bindings']:
        resultElem = SubElement(resultsElem, name(u'result'))
        # remove the ? from the variable name
        [binding_2(k, d, resultElem) for (k, d) in row.iteritems()]

def serializeXML(results):
    root = Element(name(u'sparql'))

    header(results, root)
    result_list(results, root)

    out = StringIO()
    tree = ElementTree(root)

    # xml declaration must be written by hand
    # http://www.nabble.com/Writing-XML-files-with-ElementTree-t3433325.html
    out.write('<?xml version="1.0" encoding="utf-8"?>')
    out.write('<?xml-stylesheet type="text/xsl" ' + \
              'href="/static/sparql-xml-to-html.xsl"?>')
    tree.write(out, encoding='utf-8')

    return out.getvalue()
