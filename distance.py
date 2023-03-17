from graph import *


class Distance_Collector():
    index = {}
    def __init__(self, src, graph):
        self.src = src
        self.graph = graph
        self.max_width = len(N_to_bit_array(len(self.graph.nodes)))
        self.distance = {}
        self.reachable = {}
        self.unary_distance = {}
        self.initialized = False
        self.unary_initialized = False
        self.graph_size = len(self.graph.nodes)
        assert (graph, src) not in  Distance_Collector.index
        Distance_Collector.index[(graph, src)] = self

    def get_unary_distance(self, n, i):
        # in the sense it always possibl
        if i > len(self.graph.nodes):
            return FALSE()
        else:
            if n == self.src:
                return TRUE()
            else:
                if n not in self.unary_distance:
                    self.unary_distance[n] = [FALSE()] + [new_lit() for i in range(self.graph_size)]
                return self.unary_distance[n][i]

    def initialize_unary(self, constraints):
        if not self.unary_initialized:
            for node in self.graph.nodes:
                if node != self.src:
                    #backward constraints:
                    for i in range(1, self.graph_size + 1):
                        gt_constraint = []
                        for target, edge in get_node(self.graph, node).incoming.items():
                            gt_constraint.append(AND(edge, self.get_unary_distance(target, i-1), constraints))
                        constraints.append([IMPLIES(self.get_unary_distance(node, i), g_OR(gt_constraint, constraints),
                                                    constraints)])

                #forward constraints:
                for target, edge in get_node(self.graph, node).outgoing.items():
                    for i in range(0, self.graph_size):
                        constraints.append([IMPLIES(AND(self.get_unary_distance(node, i), edge, constraints),
                                                   self.get_unary_distance(target, i + 1), constraints)])


            # we need to enforce unary distance consistency
            for n, distance in self.unary_distance.items():
                if n != self.src:
                    for i in range(self.graph_size):
                        constraints.append([IMPLIES(distance[i], distance[i+1], constraints)])

            self.unary_initialized = True

    def get_distance(self, node):
        result = self.distance.get(node, None)
        if result is None:
            if node == self.src:
                self.distance[node] = const_to_bv(0)
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

    def initialize(self, constraints, is_mono = True):
        addition = add_mono if is_mono else add
        if not self.initialized:
            if is_mono:
                for node in self.graph.nodes:
                    if node != self.src:
                        #backward constraints:
                        temp_constraints = [-self.get_reachable(node)]
                        for target, edge in get_node(self.graph, node).incoming.items():
                            gt_distance = GT(self.get_distance(node), self.get_distance(target), constraints)
                            temp_constraints.append( g_AND([gt_distance, edge, self.get_reachable(target)], constraints))
                        constraints.append([g_OR(temp_constraints, constraints)])

                    #forward constraints:
                    for target, edge in get_node(self.graph, node).outgoing.items():
                        cond1 = AND(edge, self.get_reachable(node), constraints)
                        constraints.append([IMPLIES(cond1,
                                                   AND(LE(self.get_distance(target),
                                                                addition(self.get_distance(node), 1, constraints), constraints),
                                                                                                self.get_reachable(target),
                                                                                                   constraints),
                                                                constraints)])
            else:
                for node in self.graph.nodes:
                    if node != self.src:
                        temp_constraints = []
                        for target, edge in get_node(self.graph, node).incoming:
                            successor = Equal(self.get_distance(node), add(self.get_distance(target), const_to_bv(1)), constraints)
                            temp_constraints.append(
                                g_AND([successor, edge, self.get_reachable(target)], constraints))
                        constraints.append([IMPLIES(self.get_reachable(node), g_OR(temp_constraints, constraints), constraints)])

                    for target, edge in get_node(self.graph, node).outgoing:
                        constraints.append([IMPLIES(AND(self.get_reachable(node), edge, constraints),
                                                    AND(GE(add(self.get_distance(node), const_to_bv(1), constraints),
                                                           self.get_distance(target), constraints),
                                                        self.get_reachable(target),constraints)
                                                    )])
            self.initialized = True

def get_distance_collector(src, graph):
    res = Distance_Collector.index.get((graph,src), None)
    if res is None:
        Distance_Collector.index[(graph, src)] = Distance_Collector(src, graph)
        return Distance_Collector.index[(graph, src)]
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
        #self.distance = Distance_Collector(src, graph)
        self.encoded = False
        if lit is not None:
            self.lit = lit
        else:
            self.lit = new_lit()

        Distance_LEQ.Collection[lit] = self


    def get_distance(self, node):
        return self.distance.get_distance(node)

    def get_reachable(self, node):
        return self.distance.get_reachable(node)


    def encode(self, constraints):
        if self.encoded:
            return self.lit
        else:
            #for every node in the graph,
            self.distance.initialize(constraints)
            result =  AND(LE_const(self.get_distance(self.sink), self.target_value, constraints),
                          self.get_reachable(self.sink), constraints)
            constraints.append([IFF( self.lit, result, constraints)])
            self.encoded = True
            return self.lit

    def unary_encode(self, constraints):
        if self.encoded:
            return self.lit
        else:
            self.distance.initialize_unary(constraints)
            result = self.distance.get_unary_distance(self.sink, self.target_value)
            constraints.append([IFF(self.lit, result, constraints)])
            self.encoded = True
            return self.lit

def parse_distance(attributes):
    if len(attributes) != 6:
        return False
    else:
        head, gid, src, target, lit, distance = attributes
        gid = int(gid)
        graph = get_graph(gid)
        tail = head.split('_')[-1]
        src = get_node(graph, int(src))
        sink = get_node(graph, int(target))
        distance = int(distance)
        lit = add_lit(int(lit))
        if tail == "leq":
            Distance_LEQ(graph, src, sink, distance, lit)
        elif tail == 'lt':
            Distance_LEQ(graph, src, sink, distance - 1, lit)
        elif tail == 'geq':
            Distance_LEQ(graph, src, sink, distance - 1, -lit)
        elif tail == 'gt':
            Distance_LEQ(graph, src, sink, distance, -lit)
        else:
            return False
        return True