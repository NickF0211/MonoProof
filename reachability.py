from logic_gate import *

def _default_enabling_condition(edge):
    return edge.lit

class Reachability():

    def __init__(self, graph, src, sink):
        self.graph = graph
        self.src = src
        self.sink = sink
        self.reachable = {}
        self.reachable[src] = TRUE()
        self.distance = dict()


    def encode(self, hint, reachable, constraint, predicate=0, enabling_cond=_default_enabling_condition):
        if predicate == 0:
            predicate = new_lit()
        if reachable:
            return self.reachability_constraint(hint, constraint, predicate, enabling_cond)
        else:
            return self.unreachability_constraint(hint, constraint, predicate, enabling_cond)

    def reachability_constraint(self, path, constraint, predicate, enabling_cond = _default_enabling_condition):
        max_size = len(path)
        step = 0
        # then the hint is the path from src to the sink
        assert self.sink in self.reachable
        current_node = self.src
        while current_node != path and step < max_size:
            old_current = current_node
            current_reach = self.reachable[current_node]
            for next, edge in current_node.outgoing.items():
                if next in path:
                    next_reachable = self.reachable.get(next, 0)
                    if next_reachable == -1:
                        next_reachable = new_lit()
                        self.reachable[next] = next_reachable
                    constraint.append([IMPLIES(AND(current_reach, enabling_cond(edge), constraint), next_reachable, constraint)])
                    current_node = next
                    break
            assert current_node != old_current
        constraint.append([IMPLIES(self.reachable[self.sink], predicate, constraint)])
        return predicate

    def unreachability_constraint(self, cut, constraint, predicate, enabling_cond = _default_enabling_condition):
        # each node contains two boolean variable, init, and final. init is true for the src,
        # final takes about weather the node will eventually be reachable from the source
        explored = self.compute_unreachable_graph(cut)
        # in case unreachable, the hint is a cut that separates the source from the sink
        t_final = self.compute_unreachable_graph_by_cut(cut, explored, constraint, self.distance, enabling_cond)
        # the mono_encoding
        constraint.append(IMPLIES(predicate, t_final,constraint))
        return predicate

    def compute_unreachable_graph(self, cut):
        explored = set()
        open = [self.sink]
        explored.add(self.sink)
        while len(open) != 0:
            head = open.pop()
            for target, edge in head.incoming.items():
                if edge not in cut and target not in explored:
                    open.append(target)
                explored.add(open)
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
                for target, edge in node.incoming.items():
                    if edge not in cut:
                        t_depth_var = self._DSF(target, depth - 1, cut, constraint, cache, enabling_cond)
                    else:
                        t_depth_var = TRUE()

                    obligation.append(AND(t_depth_var, enabling_cond(edge), constraint))
            res = g_OR(obligation)
            cache[(node, depth)] = res
            return res

