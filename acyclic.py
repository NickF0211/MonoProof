from graph import *
from logic_gate import *

class Acyclic():
    Collection = {}

    def __init__(self, graph, lit=None):
        if isinstance(graph, int):
            graph = Graph.Graphs[graph]
        self.graph = graph
        self.encoded = False
        if lit is None:
            self.lit = new_lit()
        else:
            self.lit = lit
        self.reachability = None
        Acyclic.Collection[lit] = self
        self.first = {}
        self.second = {}

        self.connect = {}
        self.reconnect = {}
        self.ac_encoded = False

    def get_first(self, root, node):
        reach_dic = self.first.get(root, None)
        if reach_dic is None:
            reach_dic = {}
            self.first[root] = reach_dic

        first_lit = reach_dic.get(node, None)
        if first_lit is None:
            if node == root:
                first_lit = TRUE()
            else:
                first_lit = new_lit()
            reach_dic[node] = first_lit
        return first_lit

    def get_second(self, root, node):

        reach_dic = self.second.get(root, None)
        if reach_dic is None:
            reach_dic = {}
            self.second[root] = reach_dic

        second_lit = reach_dic.get(node, None)
        if second_lit is None:
            first_lit = new_lit()
            reach_dic[node] = first_lit
        return second_lit

    def encode_cyclic_clause(self, cycles, constraints):
        assert len(cycles) > 0
        root_node = cycles[0]
        local_constraints = []
        def get_first(node):
            return self.get_first(root_node, node)

        def get_second(node):
            return self.get_first(root_node, node)

        for node in cycles:
            for next, edge in node.outgoing.items():
                connecting = AND(get_first(node), edge.lit, constraints )
                constraints.append([IMPLIES(connecting,
                                           get_first(next), constraints)])
                constraints.append([IMPLIES(AND(connecting, get_first(next), constraints),
                                           get_second(next), constraints)])

        #if the root is visited the second time, then the graph must be cyclic
        constraints.append([IMPLIES(get_second(root_node),
                                   -self.lit, constraints)])


    def get_connection(self, source, target):
        lit = self.connect.get((source, target), None)
        if lit is None:
            if source == target:
                lit = TRUE()
            else:
                lit = new_lit()

            self.connect[(source, target)] = lit
        return  lit


    def encode_acyclic_clause(self, constraints):
        if self.ac_encoded:
            return
        else:
            new_constraints = []
            for target in self.graph.nodes:
                for source in self.graph.nodes:
                    connect_lit = self.get_connection(source, target)
                    obligation = []
                    if source != target:
                        for prev, edge in target.incoming.items():
                            obligation.append(AND(edge.lit, self.get_connection(source, prev), constraints))

                        new_constraints.append([IMPLIES(connect_lit, g_OR(obligation, constraints), constraints)])

                    for next, edge in target.outgoing.items():
                        new_constraints.append(IMPLIES(AND(connect_lit, edge.lit, constraints),
                                                       self.get_connection(source, next)))


                for prev, edge in target.incoming.items():
                    new_constraints.append([IMPLIES(AND(self.get_connection(target, prev), edge.lit, constraints),
                                                   -self.lit, constraints)])

            constraints.extends(new_constraints)
            self.ac_encoded = True


                                






def parse_acyclic(attributes):
    if len(attributes) != 2:
        return False
    else:
        gid, lit = attributes
        lit = add_lit(int(lit))
        Acyclic(int(gid), lit=lit)
        return True