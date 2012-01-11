
===========================
networkx reference graphs
===========================
:Version: 1.7.dev_20120110162918
:Copyright: Copyright NetworkX: BSD. `<http://networkx.lanl.gov>`_

:SeeAlso: `<https://github.com/networkx/networkx>`_

.. contents::
   :depth: 2


.. sectnum::


atlas
=======
Generators for the small graph atlas.


See
"An Atlas of Graphs" by Ronald C. Read and Robin J. Wilson,
Oxford University Press, 1998.

Because of its size, this module is not imported by default.


.. Functions:
.. - make_small_graph

.. contents::
   :depth: 1
   :local: 


atlas.make_small_graph
------------------------

.. contents::
   :depth: 1
   :local: 

Return the small graph described by graph_description.

graph_description is a list of the form [ltype,name,n,xlist]

Here ltype is one of "adjacencylist" or "edgelist",
name is the name of the graph and n the number of nodes.
This constructs a graph of n nodes with integer labels 0,..,n-1.

If ltype="adjacencylist"  then xlist is an adjacency list
with exactly n entries, in with the j'th entry (which can be empty)
specifies the nodes connected to vertex j.
e.g. the "square" graph C_4 can be obtained by

>>> G=nx.make_small_graph(["adjacencylist","C_4",4,[[2,4],[1,3],[2,4],[1,3]]])

or, since we do not need to add edges twice,

>>> G=nx.make_small_graph(["adjacencylist","C_4",4,[[2,4],[3],[4],[]]])

If ltype="edgelist" then xlist is an edge list 
written as [[v1,w2],[v2,w2],...,[vk,wk]],
where vj and wj integers in the range 1,..,n
e.g. the "square" graph C_4 can be obtained by

>>> G=nx.make_small_graph(["edgelist","C_4",4,[[1,2],[3,4],[2,3],[4,1]]])

Use the create_using argument to choose the graph class/type. 



``make_small_graph`` argspec::

    ((graph_description, create_using), None, None, (None,))



``make_small_graph`` argspec ast::

    ['graph_description', 'create_using']
    None
    None
    (None,)



src: ``atlas.make_small_graph``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

source::

    55  : def make_small_graph(graph_description, create_using=None):
    56  :     """
    57  :     Return the small graph described by graph_description.
    58  : 
    59  :     graph_description is a list of the form [ltype,name,n,xlist]
    60  : 
    61  :     Here ltype is one of "adjacencylist" or "edgelist",
    62  :     name is the name of the graph and n the number of nodes.
    63  :     This constructs a graph of n nodes with integer labels 0,..,n-1.
    64  :     
    65  :     If ltype="adjacencylist"  then xlist is an adjacency list
    66  :     with exactly n entries, in with the j'th entry (which can be empty)
    67  :     specifies the nodes connected to vertex j.
    68  :     e.g. the "square" graph C_4 can be obtained by
    69  : 
    70  :     >>> G=nx.make_small_graph(["adjacencylist","C_4",4,[[2,4],[1,3],[2,4],[1,3]]])
    71  : 
    72  :     or, since we do not need to add edges twice,
    73  :     
    74  :     >>> G=nx.make_small_graph(["adjacencylist","C_4",4,[[2,4],[3],[4],[]]])
    75  :     
    76  :     If ltype="edgelist" then xlist is an edge list 
    77  :     written as [[v1,w2],[v2,w2],...,[vk,wk]],
    78  :     where vj and wj integers in the range 1,..,n
    79  :     e.g. the "square" graph C_4 can be obtained by
    80  :  
    81  :     >>> G=nx.make_small_graph(["edgelist","C_4",4,[[1,2],[3,4],[2,3],[4,1]]])
    82  : 
    83  :     Use the create_using argument to choose the graph class/type. 
    84  :     """
    85  :     ltype=graph_description[0]
    86  :     name=graph_description[1]
    87  :     n=graph_description[2]
    88  : 
    89  :     G=empty_graph(n, create_using)
    90  :     nodes=G.nodes()
    91  : 
    92  :     if ltype=="adjacencylist":
    93  :         adjlist=graph_description[3]
    94  :         if len(adjlist) != n:
    95  :             raise NetworkXError("invalid graph_description")
    96  :         G.add_edges_from([(u-1,v) for v in nodes for u in adjlist[v]])
    97  :     elif ltype=="edgelist":
    98  :         edgelist=graph_description[3]
    99  :         for e in edgelist:
    100 :             v1=e[0]-1
    101 :             v2=e[1]-1
    102 :             if v1<0 or v1>n-1 or v2<0 or v2>n-1:
    103 :                 raise NetworkXError("invalid graph_description")
    104 :             else:
    105 :                 G.add_edge(v1,v2)
    106 :     G.name=name
    107 :     return G



tests grep for ``make_small_graph``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``networkx.generators.tests.test_atlas``::




ast examples
~~~~~~~~~~~~~~

test_examples for ``make_small_graph``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

examples::




bipartite
===========
Generators and functions for bipartite graphs.


.. Functions:
.. - bipartite_alternating_havel_hakimi_graph
.. - bipartite_gnmk_random_graph
.. - bipartite_havel_hakimi_graph
.. - bipartite_preferential_attachment_graph
.. - bipartite_random_graph
.. - bipartite_reverse_havel_hakimi_graph

.. contents::
   :depth: 1
   :local: 


bipartite.bipartite_alternating_havel_hakimi_graph
----------------------------------------------------

.. contents::
   :depth: 1
   :local: 

1    Parameters
1    Notes
Return a bipartite graph from two given degree sequences using 
an alternating Havel-Hakimi style construction.

Nodes from the set A are connected to nodes in the set B by
connecting the highest degree nodes in set A to alternatively the
highest and the lowest degree nodes in set B until all stubs are
connected.

Parameters
~~~~~~~~~~
aseq : list or iterator
   Degree sequence for node set A.
bseq : list or iterator
   Degree sequence for node set B.
create_using : NetworkX graph instance, optional
   Return graph of this type.


Notes
~~~~~
The sum of the two sequences must be equal: sum(aseq)=sum(bseq)
If no graph type is specified use MultiGraph with parallel edges.
If you want a graph with no parallel edges use create_using=Graph()
but then the resulting degree sequences might not be exact.

The nodes are assigned the attribute 'bipartite' with the value 0 or 1
to indicate which bipartite set the node belongs to.



``bipartite_alternating_havel_hakimi_graph`` argspec::

    ((aseq, bseq, create_using), None, None, (None,))



``bipartite_alternating_havel_hakimi_graph`` argspec ast::

    ['aseq', 'bseq', 'create_using']
    None
    None
    (None,)



src: ``bipartite.bipartite_alternating_havel_hakimi_graph``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

source::

    248 : def bipartite_alternating_havel_hakimi_graph(aseq, bseq,create_using=None):
    249 :     """Return a bipartite graph from two given degree sequences using 
    250 :     an alternating Havel-Hakimi style construction.
    251 : 
    252 :     Nodes from the set A are connected to nodes in the set B by
    253 :     connecting the highest degree nodes in set A to alternatively the
    254 :     highest and the lowest degree nodes in set B until all stubs are
    255 :     connected.
    256 : 
    257 :     Parameters
    258 :     ----------
    259 :     aseq : list or iterator
    260 :        Degree sequence for node set A.
    261 :     bseq : list or iterator
    262 :        Degree sequence for node set B.
    263 :     create_using : NetworkX graph instance, optional
    264 :        Return graph of this type.
    265 : 
    266 : 
    267 :     Notes
    268 :     -----
    269 :     The sum of the two sequences must be equal: sum(aseq)=sum(bseq)
    270 :     If no graph type is specified use MultiGraph with parallel edges.
    271 :     If you want a graph with no parallel edges use create_using=Graph()
    272 :     but then the resulting degree sequences might not be exact.
    273 : 
    274 :     The nodes are assigned the attribute 'bipartite' with the value 0 or 1
    275 :     to indicate which bipartite set the node belongs to.
    276 :     """
    277 :     if create_using is None:
    278 :         create_using=networkx.MultiGraph()
    279 :     elif create_using.is_directed():
    280 :         raise networkx.NetworkXError(\
    281 :                 "Directed Graph not supported")
    282 : 
    283 :     G=networkx.empty_graph(0,create_using)
    284 : 
    285 :     # length of the each sequence
    286 :     naseq=len(aseq)
    287 :     nbseq=len(bseq)
    288 :     suma=sum(aseq)
    289 :     sumb=sum(bseq)
    290 : 
    291 :     if not suma==sumb:
    292 :         raise networkx.NetworkXError(\
    293 :               'invalid degree sequences, sum(aseq)!=sum(bseq),%s,%s'\
    294 :               %(suma,sumb))
    295 : 
    296 :     G=_add_nodes_with_bipartite_label(G,naseq,nbseq)
    297 : 
    298 :     if max(aseq)==0: return G  # done if no edges
    299 :     # build list of degree-repeated vertex numbers
    300 :     astubs=[[aseq[v],v] for v in range(0,naseq)]  
    301 :     bstubs=[[bseq[v-naseq],v] for v in range(naseq,naseq+nbseq)]  
    302 :     while astubs:
    303 :         astubs.sort()
    304 :         (degree,u)=astubs.pop() # take of largest degree node in the a set
    305 :         if degree==0: break # done, all are zero
    306 :         bstubs.sort()
    307 :         small=bstubs[0:degree // 2]  # add these low degree targets     
    308 :         large=bstubs[(-degree+degree // 2):] # and these high degree targets
    309 :         stubs=[x for z in zip(large,small) for x in z] # combine, sorry
    310 :         if len(stubs)<len(small)+len(large): # check for zip truncation
    311 :             stubs.append(large.pop())
    312 :         for target in stubs:
    313 :             v=target[1]
    314 :             G.add_edge(u,v)
    315 :             target[0] -= 1  # note this updates bstubs too.
    316 :             if target[0]==0:
    317 :                 bstubs.remove(target)
    318 : 
    319 :     G.name="bipartite_alternating_havel_hakimi_graph"
    320 :     return G



tests grep for ``bipartite_alternating_havel_hakimi_graph``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``networkx.generators.tests.test_bipartite``::

    108 : bipartite_alternating_havel_hakimi_graph, aseq, bseq)
