from bv import *

class Graph():
    Graphs = []

    def __init__(self, id=-1):
        if id == -1:
            id = len(Graph.Graphs)
        self.id = id
        self.nodes =[]
        self.edges=[]
        Graph.Graphs.append(self)


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


class Edge():
    def __init__(self, graph, src, target, cap=new_bv(8), id=-1):
        self.graph = graph
        if id == -1:
            id = len(graph.edges)
        self.id = id
        self.src = src
        self.target = target
        self.cap = cap
        self.lit = new_lit()
        graph.edges.append(self)

    def __str__(self):
        return "e:{}_{}".format(self.src.id, self.target.id)

def get_node(graph, node):
    if isinstance(node, Node):
        return node
    elif isinstance(node, int):
        assert node < len(graph.nodes)
        return graph.nodes[node]
    else:
        #unsupported node type
        raise AssertionError



def add_edge(graph, src, target, weight =None ):
    if weight is None:
        weight = new_bv(8)
    src = get_node(graph, src)
    target = get_node(graph, target)
    edge = src.outgoing.get(target, None)
    if edge is not None:
        assert target.incoming.get(src) == edge
        return edge
    else:
        edge = Edge(graph, src, target, weight)
        src.outgoing[target] = edge
        target.incoming[src] = edge
        return edge


