#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rdflib
#import FuXi
import surf

from FuXi.Horn.HornRules import HornFromN3

from rdflib.graph import ConjunctiveGraph as Graph
from rdflib import plugin
from rdflib.store import VALID_STORE

#from rdflib import Namespace
#from rdflib import Literal
from rdflib import URIRef
#from rdflib import RDF
#from rdflib import RDFS

from FuXi.Rete.RuleStore import SetupRuleStore
from FuXi.Rete.Util import generateTokenSet


import uuid
import os
import logging
import time


def store_from_virtuoso_connstr(config_string):
    Virtuoso = plugin.get("Virtuoso", rdflib.store.Store)
    return Virtuoso(config_string)

def store_from_connstr(config_string):
    store = plugin.get('MySQL', rdflib.store.Store)('rdfstore')

    ret = store.open(config_string,create=False)
    if ret == 0:
        store.open(config_string,create=True)
    else:
        assert ret == VALID_STORE,"Bad store"

    store._is_new = not bool(ret)
    return store


def store_from_engine(engine, **kwargs):
    store = plugin.get('MySQL', rdflib.store.Store)('rdfstore')

    ret = store.open(engine=engine,create=False)
    if ret == 0:
        store.open(engine=engine,create=True)
    else:
        assert ret == VALID_STORE, "Bad store"

    store._is_new = not bool(ret)
    return store


def get_session_uri(base):
    # Mint a URI for this run
    session_id = str(uuid.uuid4())
    graph_uri = os.path.join(base, session_id)
    logging.debug("Minting session uri: %r" % graph_uri)
    return graph_uri


def initialize_rdflib(engine=None, mysql_connstr=None, virtuoso_connstr=None, clear=False, logging=True):

    #rdflib.plugin.register('MySQL',  rdflib.store.Store,'rdfstorage.MySQL', 'MySQL')
    rdflib.plugin.register('sparql', rdflib.query.Processor,'rdfextras.sparql.processor', 'Processor')
    rdflib.plugin.register('sparql', rdflib.query.Result, 'rdfextras.sparql.query', 'SPARQLQueryResult')

    #if engine:
    #    store = store_from_engine(engine=engine)
    #elif mysql_connstr:
    #    store = store_from_connstr(connstr=mysql_connstr)
    #elif virtuoso_connstr:
    #    store = store_from_virtuoso_connstr(virtuoso_connstr)

    rdf_store = surf.Store(
                        reader='virtuoso_protocol',
                        writer='virtuoso_protocol',
                        endpoint='http://localhost:8890/sparql',
                        default_context='http://default')

    if clear:
        rdf_store.clear()

    #print 'SIZE of STORE : ',rdf_store.size()

    # the surf session
    rdf_session = surf.Session(rdf_store, {})
    rdf_session.enable_logging = logging

    # register the namespace
    # ns.register(myblog=config['myblog.namespace'])

    init_model(rdf_session)


def init_model(session, connstr=None,engine=None, base_uri=None):

    global rdf_session
    rdf_session = session

    #global Blog
    #Blog = rdf_session.get_class(ns.MYBLOG['Blog'])


DEFAULT_RULE_PATHS =(
"rules/rdfs-rules.n3",
#"rules/owl-rules.n3",
)

def build_rule_network(rulesets):
    """
    :param rulesets: iterable of n3 ruleset paths

    :returns: Initialized **in-memory** Rule network
    """
    # Build Rule Network
    rule_store, rule_graph, network = SetupRuleStore(None, None, True)
    network.inferredFacts = Graph(   ) # raptor_world

    for ruleset_path in rulesets:
        logging.debug("Loading rules from: %r" % ruleset_path)

        len_pre = len(network.rules)
        for rule in HornFromN3(ruleset_path):
            network.buildNetworkFromClause(rule)
        len_post = len(network.rules)
        logging.debug("                    %r : %d rules (%d -> %d)" % (
                ruleset_path,
                len_post-len_pre,
                len_pre,
                len_post))
    return network

def infer_triples_from_graph(graph, network):
    """
    :param graph: Data Graph
    :param network: Rule Network

    :returns: Rule network applied to
    """
    #
    logging.debug("inferring from %d triples and %d rules" % (
            len(graph),
            len(network.rules)))

    len_pre = len(network.inferredFacts)

    t_pre = time.time()
    network.feedFactsToAdd(generateTokenSet(graph))
    t_post = time.time()

    len_post = len(network.inferredFacts)
    len_diff = len_post - len_pre
    t_diff = t_post - t_pre
    per_triple_avg = len_diff / t_diff

    logging.debug("Inferred %d facts (%d -> %d) in %f seconds [%.4f t/s]" % (
            len_diff,
            len_pre,
            len_post,
            t_diff,
            per_triple_avg))

    return network#.inferredFacts

def infer_and_merge_triples(graph, network):
    network = infer_triples_from_graph(graph, network)

    graph = merge_inferred_facts_into_graph(graph, network)
    return graph #, network

def merge_inferred_facts_into_graph(graph, network, commit=True):

    logging.debug("Merging %d inferred facts from network into graph" % (len(network.inferredFacts)))

    for fact in network.inferredFacts:
        graph.add(fact)

    if commit:
        graph.commit()

    return graph


def load_uris_into_graph(graph, uris):
    """

    :param graph: graph to load into
    :param uris: iterable of (uri,fmt) tuples
    """
    for uri, fmt in uris:
        import_uri(graph, uri, fmt)

#@task
def import_uri(graph, uri, format, dest=None):
    dest = dest or uri
    logging.debug("Loading %r (%s) into graph" % (uri, fmt))
    len_pre = len(graph)
    t_pre = time.time()

    graph.parse(uri, format=format, publicID=uri)

    t_post = time.time()
    len_post = len(graph)
    len_diff = len_post - len_pre
    t_diff = t_post - t_pre
    per_triple_avg = len_diff / t_diff

    logging.debug(" ... Loaded %d triples in %.4f seconds (%.4f t/s)" %
            (len_diff,
            t_diff,
            per_triple_avg
            ))
    # TODO:
    #job_id = str(datetime.datetime.now()).replace(' ','_') # !
    #job_uri = os.path.join(DEFAULT_JOB_URI, job_id)
    #graph.add( (graph_uri, 'parse_job', job_uri ) )
    #graph.add( (job_uri, 'uri', uri) )
    #graph.add( (job_uri, 'format', format) )
    #graph.add( (job_uri, 'date', datetime.datetime.now() )
    # meta.add( (job_uri, headers_set, ... ) )

    # Add the information into the database
    graph.commit()

    return graph





import unittest
class TestIt(unittest.TestCase):
    def test_query(self):

        initialize_rdflib()
        store = store_from_connstr(DEFAULT_STORE_URI)

        # Create a new named graph
        graph = get_context_graph(store)

        # Load default namespaces
        graph.bind("dc", "http://http://purl.org/dc/elements/1.1/")
        graph.bind("foaf", "http://xmlns.com/foaf/0.1/")
        graph.bind("fb", "http://rdf.freebase.com/ns/")
        graph.bind("owl", "http://www.w3.org/2002/07/owl#")

        # Load Freebase Data
        freebase_labels = ("en.nikola_tesla","en.johann_wolfgang_goethe",)
        slurpq=[("http://rdf.freebase.com/rdf/%s" % label, "xml") for label in freebase_labels]

        if getattr(store,'_is_new'):
            graph = load_uris_into_graph(graph, slurpq)
            network = build_rule_network(rulesets=DEFAULT_RULE_PATHS)
            network = infer_triples_from_graph(graph, network)

            graph = merge_inferred_facts_into_graph(graph, network, commit=True)

        # Execute SPARQL Query
        query =  """ \
            PREFIX test: <http://example.com/test/> \
            PREFIX fb: <http://rdf.freebase.com/ns/> \
            SELECT ?namea ?nameb \
            WHERE { \
                ?a test:was_citizen ?nameb. \
                ?a fb:type.object.name ?namea. \
                FILTER ( lang(?namea)='en' ) \
            }"""

        # Print SPARQL Result Bindings
        result = graph.query(query).serialize('python').result

        for (nameA, nameB) in result:
            print "%s was citizen of %s" % (nameA, nameB)

        assert rdflib.URIRef("http://rdf.freebase.com/ns/en.frankfurt") in (x[1] for x in result)
        #assert len( result.triples((None,None, rdflib.URIRef("http://rdf.freebase.com/ns/en.frankfurt")) ) )


        raise Exception()

def main():
    import optparse
    prs = optparse.OptionParser()

    prs.add_option("-i","--ipython",action="store_true")
    prs.add_option("--print-store",action="store_true")
    prs.add_option("--drop-store",action="store_true")

    (opts,args) = prs.parse_args()

    logging.getLogger().setLevel(logging.DEBUG)

    initialize_rdflib()
    store = store_from_connstr(DEFAULT_STORE_URI)

    if opts.drop_store:
        store.destroy(DEFAULT_STORE_URI)
        exit(0)

    # Create a new named graph
    graph_uri = get_session_uri()
    graph = Graph(store, identifier=URIRef(graph_uri)) # !

    if opts.print_store:
        print store

        cmt="""
        contexts = sorted(set(graph.contexts()))
        print "Contexts:"
        for c in contexts:
            print c
        print ""

        for c in contexts:
            print '\n\n', c
            for t in graph.triples((None,None,None), context=c):
                print t
        """

        print graph.serialize(format='n3')

    if opts.ipython:
        #import sys
        import IPython
        IPython.Shell.IPShellEmbed(argv=args)(local_ns=locals(),global_ns=globals())


if __name__=="__main__":
    main()
