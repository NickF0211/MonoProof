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
        self.encoded = set()
        if lit is not None:
            self.lit = lit
        else:
            self.lit = new_lit()

        self.unreach_hint_old_explored = None
        self.unreach_hint_old_cut = None
        self.old_t_final = None
        self.old_flow_cut = None

        Reachability.Collection[lit] = self

    def encode(self, constraints, enabling_cond = _default_enabling_condition):
        if enabling_cond in self.encoded:
            return self.lit
        self.reachable[self.src] = TRUE()
        self.reachability_constraint(set(self.graph.edges), constraints, self.lit, enabling_cond)
        self.unreachability_constraint(set(), constraints, self.lit, enabling_cond)
        self.encoded.add(enabling_cond)
        return self.lit


    def encode_with_hint(self, hint, reachable, constraint, enabling_cond=_default_enabling_condition, dynamic= False, flow_cut=None):
        self.reachable[self.src] = TRUE()
        if reachable:
            return self.reachability_constraint(hint, constraint, self.lit, enabling_cond)
        else:
            return self.unreachability_constraint(hint, constraint, self.lit, enabling_cond, dynamic = dynamic, flow_cut=flow_cut)

    def reachability_constraint(self, path, constraint, predicate, enabling_cond = _default_enabling_condition):
        # then the hint is the path from src to the sink
        #current_node = self.src
        explored = set()
        exploring = [self.src]
        while len(exploring) != 0:
            current_node = exploring.pop(0)
            if current_node in explored:
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

    def check_delta_explored(self, add_edges, new_edges):
        touched = set()
        new_explored = set()
        removed = set()
        for e in add_edges:
            head = e.target
            #in case cut-inward
            if head in self.unreach_hint_old_explored:
                #now computes what has being removed
                exploring = [e.src]
                while exploring != []:
                    head = exploring.pop()
                    removed.add(head)
                    for target, edge in get_node(self.graph, head).incoming.items():
                        if not(edge in new_edges) and target in self.unreach_hint_old_explored  and not (target in removed):
                            exploring.append(target)

            else:
                #in case cut-outward
                exploring = [e.target]
                while exploring != []:
                    head = exploring.pop()
                    new_explored.add(head)
                    for target, edge in get_node(self.graph, head).outgoing.items():
                        if not (edge in new_edges) and not (target in new_explored):
                            if not (target in self.unreach_hint_old_explored):
                                exploring.append(target)
                            else:
                                # toched set has a new reason to build
                                touched.add(target)

        touched = touched.union(new_explored)

        return new_explored, removed, touched


    def unreachability_constraint(self, cut, constraint, predicate, enabling_cond = _default_enabling_condition, dynamic = False, flow_cut = None):
        # each node contains two boolean variable, init, and final. init is true for the src,
        # final takes about weather the node will eventually be reachable from the source
        if dynamic:
            if self.unreach_hint_old_explored is None:
                explored = self.compute_unreachable_graph(cut)
                t_final = self.compute_unreachable_graph_by_cut(cut, explored, constraint, self.distance, enabling_cond)
                # the mono_encoding
                constraint.append([IMPLIES(predicate, t_final, constraint)])
            else:
                #now analyze what is the differnce in cut
                removed_flow_cut = self.old_flow_cut.difference(flow_cut)
                add_edges = cut.difference(self.unreach_hint_old_cut)
                add, removed, touched = self.check_delta_explored(add_edges, cut)
                explored = self.unreach_hint_old_explored.difference(removed).union(add)
                for e in removed_flow_cut:
                    touched.add(e.target)
                t_final = AND(self.old_t_final, self.compute_unreachable_graph_by_cut_delta( constraint, touched, explored, enabling_cond), constraint)
                constraint.append([IMPLIES(predicate, t_final, constraint)])

            self.old_t_final = t_final
            self.old_flow_cut = flow_cut
            self.unreach_hint_old_cut = cut
            self.unreach_hint_old_explored = explored
            return predicate
        else:
            explored = self.compute_unreachable_graph(cut)
            # in case unreachable, the hint is a cut that separates the source from the sink
            t_final = self.compute_unreachable_graph_by_cut(cut, explored, constraint, self.distance, enabling_cond)
            # the mono_encoding
            constraint.append([IMPLIES(predicate, t_final, constraint)])
            return predicate

    def compute_unreachable_graph(self, cut):
        explored = set()
        open = [self.sink]
        #explored.add(self.sink)
        while len(open) != 0:
            head = open.pop()
            explored.add(head)
            for target, edge in get_node(self.graph, head).incoming.items():
                if edge not in cut and target not in explored:
                    open.append(target)
        return explored

    def compute_unreachable_graph_by_cut_delta(self, constraints, touched, explored, enabling_cond):
        def get_reachable(node):
            if node == self.src:
                return TRUE()
            elif node in explored:
                return FALSE()
            else:
                return TRUE()

        validity_constraints = []
        for node in touched:
            obligation = []
            for target, edge in get_node(self.graph, node).incoming.items():
                obligation.append(OR(-enabling_cond(edge), -get_reachable(target), constraints))

            validity_constraints.append(
                                       IMPLIES(-get_reachable(node), g_AND(obligation, constraints), constraints))

        return OR(get_reachable(self.sink), NOT(g_AND(validity_constraints, constraints)), constraints)

    def compute_unreachable_graph_by_cut(self, cut, explored, constraint, cache, enabling_cond):
        max_size = len(explored)
        #print(max_size)
        if len(cut) == 0:
            return self._DSF(self.sink, max_size, cut, constraint, cache, enabling_cond)
        else:
            #use the information in the cut to perform the witness encoding
            return self.wtiness_reduced_unreachability(constraint, explored, enabling_cond)


    def wtiness_reduced_unreachability(self, constraints, explored, enabling_cond):
        def get_reachable(node):
            if node == self.src:
                return TRUE()
            elif node in explored:
                return FALSE()
            else:
                return TRUE()
        validity_constraints = []

        for node in explored:
            obligation = []
            for target, edge in get_node(self.graph, node).incoming.items():
                obligation.append(OR(-enabling_cond(edge), -get_reachable(target), constraints))

            validity_constraints.append(
                                       IMPLIES(-get_reachable(node), g_AND(obligation, constraints), constraints))

        return OR(get_reachable(self.sink), NOT(g_AND(validity_constraints, constraints)), constraints)






    def check_cyclic(self, head, cut, path, explored):
        for target, edge in get_node(self.graph, head).incoming.items():
            if edge not in cut and target not in explored:
                if target in path:
                    return True
                else:
                    path.add(target)
                    if self.check_cyclic(target, cut, path, explored):
                        return True
                    else:
                        path.remove(target)

        return False


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
                for d in range(1, depth+1):
                    obligation = []
                    if cache.get((node, d), None) is None:
                        for target, edge in get_node(self.graph, node).incoming.items():
                            if edge not in cut:
                                t_depth_var = self._DSF(target, d - 1, cut, constraint, cache, enabling_cond)
                            else:
                                t_depth_var = TRUE()

                            obligation.append(AND(t_depth_var, enabling_cond(edge), constraint))
                        res = g_OR(obligation, constraint)
                        assert cache.get((node, d), None) is None
                        cache[(node, d)] = res

            return cache[(node, depth)]

def parse_reach(attributes):
    if len(attributes) != 4:
        return False
    else:
        gid, source, target, lit = attributes
        gid = int(gid)
        graph = get_graph(gid)
        Reachability(graph, get_node(graph, int(source)), get_node(graph, int(target)), lit = add_lit(int(lit)))
        return True


