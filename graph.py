from bv import *
from collections import namedtuple

# Edge = namedtuple('Edge', 'cap lit')

class Graph():
    Graphs = {}

    def __init__(self, id=-1):
        if id == -1:
            id = len(Graph.Graphs)
        self.id = id
        self.nodes =[]
        self.edges=[]
        Graph.Graphs[self.id] = self



def add_graph(id):
    graph = Graph.Graphs.get(id, None)
    if graph is None:
        graph = Graph(int(id))
    return graph


def get_graph(id):
    return Graph.Graphs.get(id)



class Node():

    def __init__(self, graph, id =-1):
        self.graph = graph
        if id == -1:
            id = len(graph.nodes)
        self.id = id
        self.incoming = {}
        self.outgoing = {}
        graph.nodes.append(self)

    def __str__(self):
        return "n:{}".format(self.id)

def Edge(cap=None, lit=None):
    if lit is None:
        lit = new_lit()
    return lit, cap

class Edge():
    def __init__(self, src, target, cap=None, lit= None):
        self.src = src
        self.target = target
        self.cap = cap

        if lit is None:
            self.lit = new_lit()
        else:
            assert isinstance(lit, type(0))
            self.lit = lit


def get_node(graph, node):
    if isinstance(node, Node):
        return node
    elif isinstance(node, int):
        while node >= len(graph.nodes):
            Node(graph)
        return graph.nodes[node]
    else:
        #unsupported node type
        raise AssertionError



def add_edge(graph, src, target, lit = None, weight =None):
    if isinstance(graph, int):
        graph = Graph.Graphs.get(graph, None)
        assert graph is not None
    assert isinstance(graph, Graph)
    src = get_node(graph, src)
    target = get_node(graph, target)
    edge = src.outgoing.get(target, None)
    if edge is not None:
        assert target.incoming.get(src) == edge
        return edge
    else:
        edge = Edge(src, target,weight, lit)
        src.outgoing[target] = edge
        target.incoming[src] = edge
        graph.edges.append(edge)
        return edge

def get_edge(graph, src, target):
    if isinstance(graph, int):
        graph = Graph.Graphs.get(graph, None)
        assert graph is not None
    assert isinstance(graph, Graph)
    src = get_node(graph, src)
    target = get_node(graph, target)
    edge = src.outgoing.get(target, None)
    assert edge is not None
    return edge


def parse_graph(attributes):
    #arg1, nodes, #arg2 edges, #arg3 id
    assert (len(attributes) >= 3)
    id = attributes[2]
    add_graph(int(id))
    return True

def parse_edge(attributes):
    #graph id, source, target, lit
    if (len(attributes) == 4):
        gid, source, target, lit = attributes
        add_edge(int(gid), int(source), int(target), lit = add_lit(int(lit)))
    elif len(attributes) == 5:
        gid, source, target, lit, weight = attributes
        add_edge(int(gid), int(source), int(target), lit = add_lit(int(lit)), weight=int(weight))
    return True

def parse_weighted_edge(attributes):
    assert (len(attributes) == 5)
    gid, source, target, lit, width = attributes
    bv = new_unassigned_bv(int(width))
    add_edge(int(gid), int(source), int(target), lit = add_lit(int(lit)), weight=bv)
    return True

def reset():
    Graph.Graphs ={}




