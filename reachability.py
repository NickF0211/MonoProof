from logic_gate import *
from graph import *

def _default_enabling_condition(edge):
    return edge.lit

class Reachability():
    Collection = {}

    def __init__(self, graph, src, sink, lit=None):
        if isinstance(graph, int):
            graph = Graph.Graphs[graph]
        self.graph = graph
        self.src = src
        self.sink = sink
        self.reachable = {}
        self.distance = dict()
        if lit is not None:
            self.lit = lit
        else:
            self.lit = new_lit()
        Reachability.Collection[lit] = self

    def encode(self, constraints, enabling_cond = _default_enabling_condition):
        self.reachable[self.src] = TRUE()
        self.reachability_constraint(set(self.graph.edges), constraints, self.lit, enabling_cond)
        self.unreachability_constraint(set(), constraints, self.lit, enabling_cond)
        return self.lit


    def encode_with_hint(self, hint, reachable, constraint, enabling_cond=_default_enabling_condition):
        self.reachable[self.src] = TRUE()
        if reachable:
            return self.reachability_constraint(hint, constraint, self.lit, enabling_cond)
        else:
            return self.unreachability_constraint(hint, constraint, self.lit, enabling_cond)

    def reachability_constraint(self, path, constraint, predicate, enabling_cond = _default_enabling_condition):
        # then the hint is the path from src to the sink
        #current_node = self.src
        explored = set()
        exploring = [self.src]
        while len(exploring) != 0:
            current_node = exploring.pop(0)
            if  current_node in explored:
                continue
            current_reach = self.reachable[current_node]
            for next, edge in get_node(self.graph, current_node).outgoing.items():
                if edge in path:
                    next_reachable = self.reachable.get(next, 0)
                    if next_reachable == 0:
                        next_reachable = new_lit()
                        self.reachable[next] = next_reachable
                    constraint.append([IMPLIES(AND(current_reach, enabling_cond(edge), constraint), next_reachable, constraint)])

                    if edge not in explored:
                        exploring.append(next)

            explored.add(current_node)
            #print("{} {}".format(current_node, self.reachable[current_node]))




        if  self.sink not in explored:
            self.reachable[self.sink] = new_lit()

        constraint.append([IMPLIES(self.reachable[self.sink], predicate, constraint)])
        return predicate

    def unreachability_constraint(self, cut, constraint, predicate, enabling_cond = _default_enabling_condition):
        # each node contains two boolean variable, init, and final. init is true for the src,
        # final takes about weather the node will eventually be reachable from the source
        explored = self.compute_unreachable_graph(cut)
        # in case unreachable, the hint is a cut that separates the source from the sink
        t_final = self.compute_unreachable_graph_by_cut(cut, explored, constraint, self.distance, enabling_cond)
        # the mono_encoding
        constraint.append([IMPLIES(predicate, t_final, constraint)])
        return predicate

    def compute_unreachable_graph(self, cut):
        explored = set()
        open = [self.sink]
        explored.add(self.sink)
        while len(open) != 0:
            head = open.pop()
            for target, edge in get_node(self.graph, head).incoming.items():
                if edge not in cut and target not in explored:
                    open.append(target)
                explored.add(target)
        return explored

    def compute_unreachable_graph_by_cut(self, cut, explored, constraint, cache, enabling_cond):
        max_size = len(explored)
        return self._DSF(self.sink, max_size, cut, constraint, cache, enabling_cond)

    def _DSF(self, node, depth, cut, constraint, cache, enabling_cond):
        res = cache.get((node, depth), None)
        if res is not None:
            return res
        else:
            if node == self.src:
                return TRUE()
            else:
                if depth == 0:
                    return FALSE()
                obligation = []
                for target, edge in get_node(self.graph, node).incoming.items():
                    if edge not in cut:
                        t_depth_var = self._DSF(target, depth - 1, cut, constraint, cache, enabling_cond)
                    else:
                        t_depth_var = TRUE()

                    obligation.append(AND(t_depth_var, enabling_cond(edge), constraint))
            res = g_OR(obligation, constraint)
            cache[(node, depth)] = res
            return res

def parse_reach(attributes):
    if len(attributes) != 4:
        return False
    else:
        gid, source, target, lit = attributes
        gid = int(gid)
        graph = get_graph(gid)
        Reachability(graph, get_node(graph, int(source)), get_node(graph, int(target)), lit = int(lit))
        return True