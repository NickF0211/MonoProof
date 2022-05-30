from graph import *


class Distance_Collector():
    index = {}
    def __init__(self, src, graph):
        self.src = src
        self.graph = graph
        self.max_width = len(N_to_bit_array(len(self.graph.nodes)))
        self.distance = {}
        self.reachable = {}
        self.initialized = False
        assert src not in  Distance_Collector.index
        Distance_Collector.index[src] = self

    def get_distance(self, node):
        result = self.distance.get(node, None)
        if result is None:
            if node == self.src:
                self.distance[node] = const_bv(None, self.max_width, 0)
            else:
                self.distance[node] = new_bv(self.max_width, True)
            return self.distance[node]
        else:
            return result

    def get_reachable(self, node):
        result = self.reachable.get(node, None)
        if result is None:
            if node == self.src:
                self.reachable[node] = TRUE()
            else:
                self.reachable[node] = new_lit()
            return self.reachable[node]
        else:
            return result

    def initialize(self, constraints):
        if not self.initialized:
            for node in self.graph.nodes:
                if node != self.src:
                    #backward constraints:
                    temp_constraints = [-self.get_reachable(node)]
                    for target, edge in get_node(self.graph, node).incoming.items():
                        gt_distance = GT(self.get_distance(node), self.get_distance(target), constraints)
                        temp_constraints.append( g_AND([gt_distance, edge.lit, self.get_reachable(target)], constraints))
                    constraints.append(g_OR(temp_constraints, constraints))


                #forward constraints:
                for target, edge in get_node(self.graph, node).outgoing.items():
                    constraints.append(IMPLIES(AND(edge.lit, self.get_reachable(node), constraints),
                                               AND(LE(self.get_distance(target),
                                                            add_mono(self.get_distance(node), 1, constraints)),
                                                                                            self.get_reachable(target),
                                                                                               constraints),
                                                            constraints))

            self.initialized = True

def get_distance_collector(src, graph):
    res = Distance_Collector.index.get(src, None)
    if res is None:
        Distance_Collector.index[src] = Distance_Collector(src, graph)
        return Distance_Collector.index[src]
    else:
        return res

class Distance_LEQ():
    Collection = {}

    def __init__(self, graph, src, sink, target_value, lit=None):
        if isinstance(graph, int):
            graph = Graph.Graphs[graph]
        self.graph = graph
        self.src = src
        self.sink = sink
        self.target_value = target_value
        self.distance = get_distance_collector(src, graph)
        self.encoded = set()
        if lit is not None:
            self.lit = lit
        else:
            self.lit = new_lit()

        Distance_LEQ.Collection[lit] = self


    def get_distance(self, node):
        return self.distance.get_distance(node)


    def encode(self, constraints):
        if self.encoded:
            return self.lit
        else:
            #for every node in the graph,
            self.distance.initialize(constraints)
            result =  LE_const(self.get_distance(self.sink), self.target_value, constraints)
            constraints.append(IFF(result, self.lit, constraints))
            return self.lit

def parse_distance(attributes):
    if len(attributes) != 6:
        return False
    else:
        head, gid, src, target, lit, distance = attributes
        gid = int(gid)
        graph = get_graph(gid)
        head, tail = head.split('_')
        src = get_node(graph, int(src))
        sink = get_node(graph, int(target))
        distance = int(distance)
        lit = add_lit(int(lit))
        if tail == "leq":
            Distance_LEQ(graph, src, sink, distance, lit)
        elif tail == 'lt':
            Distance_LEQ(graph, src, sink, distance+1, lit)
        elif tail == 'geq':
            Distance_LEQ(graph, src, sink, distance + 1, -lit)
        elif tail == 'gt':
            Distance_LEQ(graph, src, sink, distance, -lit)
        else:
            return False
        return True