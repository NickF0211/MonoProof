from logic_gate import *
from graph import *

def _default_enabling_condition(edge):
    return edge.lit


def on_cut(edge, cut, is_edge_lit):
    if is_edge_lit:
        return edge.lit in cut
    else:
        return edge in cut


def update_max_distance(max_distance, node, cur_dis):
    max_dis = max_distance.get(node, 0)
    if cur_dis > max_dis:
        max_distance[node] = cur_dis

def get_max_distance(max_distance, node):
    return max_distance.get(node, 0)

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
        self.old_flow_cut = None
        self.old_edge_cut = None
        self.old_node_obligations = {}

        Reachability.Collection[lit] = self

    def encode_unreach_residual(self, constraints, flow_assignment):
        reachability = {}
        def get_reachable(node):
            if node in reachability:
                return reachability[node]

            if node == self.src:
                return TRUE()
            else:
                res = new_lit()
                reachability[node] = res
                return res

        validity_constraints = []

        for node in self.graph.nodes:
            obligation = []
            for target, edge in get_node(self.graph, node).incoming.items():
                flow = flow_assignment.get(edge, 0)
                obligation.append(OR(-GT(edge.cap, flow), -get_reachable(target), constraints))

            for target, edge in get_node(self.graph, node).outgoing.items():
                flow = flow_assignment.get(edge, 0)
                rflow = minus_mono(edge.cap, flow, constraints)
                obligation.append(OR(Equal_const(rflow, 0), -get_reachable(target), constraints))

            validity_constraints.append(
                                       IMPLIES(-get_reachable(node), g_AND(obligation, constraints), constraints))

        return OR(get_reachable(self.sink), NOT(g_AND(validity_constraints, constraints)), constraints)


    def encode(self, constraints, enabling_cond = _default_enabling_condition, reach_cond = True, unreach_cond = True, force_witness = False):
        if enabling_cond in self.encoded:
            return self.lit
        print("we are here")
        self.reachable[self.src] = TRUE()
        if reach_cond:
            print("encode reach")
            self.reachability_constraint(set(self.graph.edges), constraints, self.lit, enabling_cond)
        if unreach_cond:
            print("encode unreach")
            self.unreachability_constraint(set(), constraints, self.lit, enabling_cond, force_witness=force_witness)
        print("done")
        self.encoded.add(enabling_cond)
        return self.lit

    def encode_with_hint(self, hint, reachable, constraint, enabling_cond=_default_enabling_condition, dynamic= False, flow_cut=None, edge_cut=None):
        self.reachable[self.src] = TRUE()
        if reachable:
            return self.reachability_constraint(hint, constraint, self.lit, enabling_cond)
        else:
            return self.unreachability_constraint(hint, constraint, self.lit, enabling_cond, dynamic = dynamic, flow_cut=flow_cut, edge_cut = edge_cut)

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
                if e.src in self.unreach_hint_old_explored:
                    exploring = [e.src]
                    while exploring != []:
                        head = exploring.pop()
                        if head in removed:
                            continue
                        else:
                            removed.add(head)
                            for target, edge in get_node(self.graph, head).incoming.items():
                                if not(edge in new_edges) and target in self.unreach_hint_old_explored  and not (target in removed):
                                    exploring.append(target)

            else:
                #in case cut-outward
                exploring = [e.target]
                while exploring != []:
                    head = exploring.pop()
                    if head in new_explored:
                        continue
                    else:
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


    def unreachability_constraint(self, cut, constraint, predicate, enabling_cond = _default_enabling_condition, dynamic = False, flow_cut = None, edge_cut = None, force_witness = False):
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
                removed_cut = self.old_flow_cut.difference(flow_cut).union(self.old_edge_cut.difference(edge_cut))
                explored, touched = self.compute_unreachable_delta(cut)
                for e in removed_cut:
                    touched.add(e.target)
                t_final = self.compute_unreachable_graph_by_cut_delta( constraint, touched, explored, enabling_cond)
                constraint.append([IMPLIES(predicate, t_final, constraint)])

            #self.old_t_final = t_final
            self.old_edge_cut = edge_cut
            self.old_flow_cut = flow_cut
            self.unreach_hint_old_cut = cut
            self.unreach_hint_old_explored = explored
            return predicate
        else:
            explored = self.compute_unreachable_graph(cut)
            # in case unreachable, the hint is a cut that separates the source from the sink
            t_final = self.compute_unreachable_graph_by_cut(cut, explored, constraint, self.distance, enabling_cond, force_witness=force_witness)
            # the mono_encoding
            constraint.append([IMPLIES(predicate, t_final, constraint)])
            return predicate

    def compute_unreachable_graph(self, cut):
        explored = set()
        open = [self.sink]

        is_edge_lit = False
        for e in cut:
            is_edge_lit = isinstance(e, int)
            break

        #explored.add(self.sink)
        while len(open) != 0:
            head = open.pop()
            if head in explored:
                continue
            else:
                explored.add(head)
                for target, edge in get_node(self.graph, head).incoming.items():
                    if (not on_cut(edge, cut, is_edge_lit)) and (target not in explored):
                        open.append(target)
        return explored

    def compute_unreachable_delta(self, cut):
        explored = set()
        touched = set()
        open = [self.sink]
        # explored.add(self.sink)
        is_edge_lit = False
        for e in cut:
            is_edge_lit = isinstance(e, int)
            break

        while len(open) != 0:
            head = open.pop()
            if head in explored:
                continue
            else:
                explored.add(head)
                if head not in self.unreach_hint_old_explored:
                    touched.add(head)
                for target, edge in get_node(self.graph, head).incoming.items():
                    if not on_cut(edge, cut, is_edge_lit) and target not in explored:
                        open.append(target)
                        if edge in self.unreach_hint_old_cut:
                            touched.add(head)

        return explored, touched


    def compute_unreachable_graph_by_cut_delta(self, constraints, touched, explored, enabling_cond):
        def get_reachable(node):
            if node == self.src:
                return TRUE()
            elif node in explored:
                return FALSE()
            else:
                return TRUE()

        validity_constraints = []
        new_obligations = {}
        for node, obligations in self.old_node_obligations.items():
            if node in explored:
                if node not in touched:
                    new_obligations[node] = self.old_node_obligations[node]
                    validity_constraints.append(self.old_node_obligations[node])

        for node in touched:
            obligation = []
            for target, edge in get_node(self.graph, node).incoming.items():
                obligation.append(OR(-enabling_cond(edge), -get_reachable(target), constraints))

            node_obligation = IMPLIES(-get_reachable(node), g_AND(obligation, constraints), constraints)
            new_obligations[node] = node_obligation
            validity_constraints.append(
                                       node_obligation)
        self.old_node_obligations = new_obligations
        return OR(get_reachable(self.sink), NOT(g_AND(validity_constraints, constraints)), constraints)

    def compute_unreachable_graph_by_cut(self, cut, explored, constraint, cache, enabling_cond, force_witness=False):
        max_size = len(explored)
        #print(max_size)
        if len(cut) == 0 and not force_witness:
            max_distance = dict()
            return self._DSF(self.sink, max_size, cut, constraint, cache, enabling_cond, max_distance)
        else:
            #use the information in the cut to perform the witness encoding
            return self.wtiness_reduced_unreachability(constraint, explored, enabling_cond, is_forced = force_witness)


    def wtiness_reduced_unreachability(self, constraints, explored, enabling_cond, is_forced = False):
        reachability = {}
        def get_reachable(node):
            if node == self.src:
                return TRUE()
            elif node in explored:
                return FALSE()
            else:
                if is_forced:
                    if node in reachability:
                        return reachability[node]
                    else:
                        res = new_lit()
                        reachability[node] = res
                        return res
                else:
                    return TRUE()
        validity_constraints = []

        for node in explored:
            obligation = []
            for target, edge in get_node(self.graph, node).incoming.items():
                obligation.append(OR(-enabling_cond(edge), -get_reachable(target), constraints))

            node_obg = IMPLIES(-get_reachable(node), g_AND(obligation, constraints), constraints)
            self.old_node_obligations[node] = node_obg
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



    def _DSF(self, node, depth, cut, constraint, cache, enabling_cond, max_distance):
        res = cache.get((node, depth), None)
        if res is not None:
            update_max_distance(max_distance, node, depth)
            return res
        else:
            cur_distance = get_max_distance(max_distance, node)
            if node == self.src:
                return TRUE()
            else:
                if depth == 0:
                    return FALSE()
                for d in range(cur_distance+1, depth+1):
                    obligation = []
                    if cache.get((node, d), None) is None:
                        for target, edge in get_node(self.graph, node).incoming.items():
                            if edge not in cut:
                                t_depth_var = self._DSF(target, d - 1, cut, constraint, cache, enabling_cond, max_distance)
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


