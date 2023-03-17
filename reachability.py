from logic_gate import *
from graph import *
from distance import Distance_Collector, get_distance_collector


def _default_enabling_condition(edge):
    return edge


def on_cut(edge, cut, is_edge_lit):
    if is_edge_lit:
        return edge in cut
    else:
        return edge in cut


def on_path(edge, cut, is_edge_lit):
    if is_edge_lit:
        return -edge in cut
    else:
        return edge in cut


def update_max_distance(max_distance, node, cur_dis):
    max_dis = max_distance.get(node, 0)
    if cur_dis > max_dis:
        max_distance[node] = cur_dis


def get_max_distance(max_distance, node):
    return max_distance.get(node, 0)


large_graph_threshold = 400


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
        self.encoded = {}
        if lit is not None:
            self.lit = lit
        else:
            self.lit = new_lit()

        self.unreach_hint_old_explored = None
        self.unreach_hint_old_cut = None
        self.old_flow_cut = None
        self.old_edge_cut = None
        self.old_node_obligations = {}
        self.total_encoded_distance = 0
        self.inscope = None
        self.incoming = {}
        self.outgoing = {}
        self.union_unreachable = set()
        self.cut_max_d = 0

        Reachability.Collection[lit] = self

    def free(self):
        self.graph = None
        self.src = None
        self.sink = None
        self.reachable = {}
        self.distance = dict()
        self.encoded = {}

        self.unreach_hint_old_explored = None
        self.unreach_hint_old_cut = None
        self.old_flow_cut = None
        self.old_edge_cut = None
        self.old_node_obligations = {}
        self.total_encoded_distance = 0
        self.inscope = None
        self.incoming = {}
        self.outgoing = {}
        self.union_unreachable = set()
        self.cut_max_d = 0

    # trim away nodes that can not possible be in path between src and dest
    def trim_unreachable(self):
        source_reachable = set()
        open_nodes = {self.src}
        while open_nodes:
            head = open_nodes.pop()
            source_reachable.add(head)
            if head == self.sink:
                continue
            for target, _ in get_node(self.graph, head).outgoing:
                if target not in source_reachable:
                    open_nodes.add(target)

        sink_reachable_from = set()
        open_nodes = {self.sink}
        while open_nodes:
            head = open_nodes.pop()
            sink_reachable_from.add(head)
            if head == self.src:
                continue
            for target, _ in get_node(self.graph, head).incoming:
                if target not in sink_reachable_from:
                    open_nodes.add(target)

        self.inscope = source_reachable.intersection(sink_reachable_from)

        for node in self.inscope:
            incomings = {}
            for target, edge in get_node(self.graph, node).incoming:
                if target in self.inscope and target != self.sink:
                    incomings[target] = edge
            self.incoming[node] = incomings

            outgoings = {}
            for target, edge in get_node(self.graph, node).outgoing:
                if target in self.inscope and target != self.src:
                    outgoings[target] = edge
            self.outgoing[node] = outgoings

    def get_incoming(self, node):
        if self.inscope is None:
            self.trim_unreachable()
        return self.incoming.get(node, {})

    def get_outgoing(self, node):
        if self.inscope is None:
            self.trim_unreachable()
        return self.outgoing.get(node, {})

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
            for target, edge in self.get_incoming(get_node(self.graph, node)).items():
                flow = flow_assignment.get(edge, 0)
                obligation.append(OR(-GT(edge.cap, flow), -get_reachable(target), constraints))

            for target, edge in self.get_outgoing(get_node(self.graph, node)).items():
                flow = flow_assignment.get(edge, 0)
                rflow = minus_mono(edge.cap, flow, constraints)
                obligation.append(OR(Equal_const(rflow, 0), -get_reachable(target), constraints))

            validity_constraints.append(
                IMPLIES(-get_reachable(node), g_AND(obligation, constraints), constraints))

        return OR(get_reachable(self.sink), NOT(g_AND(validity_constraints, constraints)), constraints)

    def binary_encode_unreach_with_hint(self, constraints, hint):
        explored = self.compute_unreachable_graph(hint)
        bv_size = len(N_to_bit_array(len(explored)))

        def get_distance(node, distance):
            result = distance.get(node, None)
            if result is None:
                if node == self.src or node not in explored:
                    distance[node] = const_to_bv(0)
                else:
                    distance[node] = new_bv(bv_size, True)
                return distance[node]
            else:
                return result

        def get_reachable(node, reachable):
            result = reachable.get(node, None)
            if result is None:
                if node == self.src or node not in explored:
                    reachable[node] = TRUE()
                else:
                    reachable[node] = new_lit()
                return reachable[node]
            else:
                return result

        distance = {}
        reachable = {}

        for node in explored:
            if node != self.src:
                temp_constraints = []
                for target, edge in self.get_incoming(node).items():
                    if on_cut(edge, hint, is_edge_lit=True):
                        temp_constraints.append(edge)
                    else:
                        successor = Equal(get_distance(node, distance),
                                          add(get_distance(target, distance), const_to_bv(1)),
                                          constraints)
                        temp_constraints.append(
                            g_AND([successor, edge, get_reachable(target, reachable)], constraints))
                constraints.append(
                    [IMPLIES(get_reachable(node, reachable), g_OR(temp_constraints, constraints), constraints)])

        constraints.append([IMPLIES(self.lit, get_reachable(self.sink, reachable), constraints)])
        return self.lit

    def binary_encode(self, constraints, mono=False):
        if self.encoded.get(_default_enabling_condition, None) == (True, True):
            return self.lit
        self.encoded[_default_enabling_condition] = (True, True)
        distance_collector = get_distance_collector(self.src, self.graph)
        distance_collector.initialize(constraints, is_mono=mono)
        # result = AND(LE_const(distance_collector.get_distance(self.sink), len(self.graph.nodes), constraints),
        #              distance_collector.get_reachable(self.sink), constraints)
        constraints.append([IFF(self.lit, distance_collector.get_reachable(self.sink), constraints)])
        return self.lit

    def encode(self, constraints, enabling_cond=_default_enabling_condition, reach_cond=True, unreach_cond=True,
               force_witness=False):
        if self.sink == self.src:
            constraints.append([IFF(self.lit, TRUE(), constraints)])
            self.encoded[enabling_cond] = (True, True)
            return self.lit

        if self.inscope is None:
            self.trim_unreachable()

        encoded_reach, encoded_unreach = self.encoded.get(enabling_cond, (False, False))
        to_encode_reach = reach_cond > encoded_reach
        to_encode_unreach = unreach_cond > encoded_unreach
        # print("we are here")
        self.reachable[self.src] = TRUE()
        if to_encode_reach:
            print("encode reach")
            self.reachability_constraint(set(self.graph.edges), constraints, self.lit, enabling_cond)
        if to_encode_unreach:
            print(" encode unreach")
            self.unreachability_constraint(set(), constraints, self.lit, enabling_cond, force_witness=force_witness)
        # print("done")
        self.encoded[enabling_cond] = (encoded_reach or reach_cond, encoded_unreach or unreach_cond)
        return self.lit

    def encode_with_hint(self, hint, reachable, constraint, enabling_cond=_default_enabling_condition, dynamic=False,
                         flow_cut=None, edge_cut=None, force_distance=False):
        if self.sink == self.src:
            constraint.append([IFF(self.lit, TRUE(), constraint)])
            self.encoded[enabling_cond] = (True, True)
            return self.lit

        if self.inscope is None:
            self.trim_unreachable()
        encoded_reach, encoded_unreach = self.encoded.get(enabling_cond, (False, False))

        self.reachable[self.src] = TRUE()
        if reachable and not encoded_reach:
            return self.reachability_constraint(hint, constraint, self.lit, enabling_cond)
        elif not reachable and not encoded_unreach:
            return self.unreachability_constraint(hint, constraint, self.lit, enabling_cond, dynamic=dynamic,
                                                  flow_cut=flow_cut, edge_cut=edge_cut, force_distance=force_distance)
        else:
            return self.lit

    def reachability_constraint(self, path, constraint, predicate, enabling_cond=_default_enabling_condition):
        # then the hint is the path from src to the sink
        # current_node = self.src
        is_edge_lit = False
        for i in path:
            is_edge_lit = isinstance(i, int)
            break

        explored = set()
        exploring = [self.src]
        while len(exploring) != 0:
            current_node = exploring.pop(0)
            if current_node in explored:
                continue
            explored.add(current_node)
            current_reach = self.reachable[current_node]
            for next, edge in self.get_outgoing(get_node(self.graph, current_node)).items():
                if on_path(edge, path, is_edge_lit):
                    next_reachable = self.reachable.get(next, 0)
                    if next_reachable == 0:
                        next_reachable = new_lit()
                        self.reachable[next] = next_reachable
                    constraint.append(
                        [IMPLIES(AND(current_reach, enabling_cond(edge), constraint), next_reachable, constraint)])

                    if next not in explored:
                        exploring.append(next)

        # assert self.sink in explored
        # print("{} {}".format(current_node, self.reachable[current_node]))

        if self.sink not in explored:
            self.reachable[self.sink] = new_lit()

        constraint.append([IMPLIES(self.reachable[self.sink], predicate, constraint)])
        return predicate

    def check_delta_explored(self, add_edges, new_edges):
        touched = set()
        new_explored = set()
        removed = set()
        for e in add_edges:
            head = e.target
            # in case cut-inward
            if head in self.unreach_hint_old_explored:
                # now computes what has being removed
                if e.src in self.unreach_hint_old_explored:
                    exploring = [e.src]
                    while exploring != []:
                        head = exploring.pop()
                        if head in removed:
                            continue
                        else:
                            removed.add(head)
                            for target, edge in self.get_incoming(get_node(self.graph, head)).items():
                                if not (edge in new_edges) and target in self.unreach_hint_old_explored and not (
                                        target in removed):
                                    exploring.append(target)

            else:
                # in case cut-outward
                exploring = [e.target]
                while exploring != []:
                    head = exploring.pop()
                    if head in new_explored:
                        continue
                    else:
                        new_explored.add(head)
                        for target, edge in self.get_outgoing(get_node(self.graph, head)).items():
                            if not (edge in new_edges) and not (target in new_explored):
                                if not (target in self.unreach_hint_old_explored):
                                    exploring.append(target)
                                else:
                                    # toched set has a new reason to build
                                    touched.add(target)

        touched = touched.union(new_explored)

        return new_explored, removed, touched

    def unreachability_constraint(self, cut, constraint, predicate, enabling_cond=_default_enabling_condition,
                                  dynamic=False, flow_cut=None, edge_cut=None, force_witness=False,
                                  force_distance=False):
        # each node contains two boolean variable, init, and final. init is true for the src,
        # final takes about weather the node will eventually be reachable from the source
        if dynamic:
            if self.unreach_hint_old_explored is None:
                explored = self.compute_unreachable_graph(cut)
                t_final = self.compute_unreachable_graph_by_cut(cut, explored, constraint, self.distance, enabling_cond)
                # the mono_encoding
                constraint.append([-predicate, t_final])
            else:
                # now analyze what is the differnce in cut
                removed_cut = self.old_flow_cut.difference(flow_cut).union(self.old_edge_cut.difference(edge_cut))
                added_cut = flow_cut.difference(self.old_flow_cut).union(edge_cut.difference(self.old_edge_cut))
                delta_cut = removed_cut.union(added_cut)
                explored, touched = self.compute_unreachable_delta(cut)
                for e in delta_cut:
                    touched.add(e.target)
                t_final = self.compute_unreachable_graph_by_cut_delta(constraint, touched, explored, enabling_cond)
                constraint.append([-predicate, t_final])

            # self.old_t_final = t_final
            self.old_edge_cut = edge_cut
            self.old_flow_cut = flow_cut
            self.unreach_hint_old_cut = cut
            self.unreach_hint_old_explored = explored
            return predicate
        else:
            if force_distance:
                cyclic = self.is_cyclic(cut)
                distance = self.compute_unreachable_graph_with_shortest_distance(cut)

                if cyclic:
                    max_distance = max(distance.values())
                    if len(self.graph.nodes) > large_graph_threshold or (self.total_encoded_distance +
                                                                         (max_distance * max_distance)) > \
                            (len(self.graph.nodes) * len(self.graph.nodes)):
                        print("lazy encoding do not pay off, switch to eager")
                        return self.encode(constraint, enabling_cond=enabling_cond, unreach_cond=True, reach_cond=False)

                    # print(max_distance, cyclic)
                    for node in distance:
                        distance[node] = (max_distance + 1 - distance[node])

                    t_final = self.unary_reach_cyclic(distance, constraint)
                    self.total_encoded_distance += (max_distance * max_distance)
                else:
                    t_final = self.unary_reach_acyclic(distance, constraint, cut)
            else:
                explored = self.compute_unreachable_graph(cut)
                # in case unreachable, the hint is a cut that separates the source from the sink
                t_final = self.compute_unreachable_graph_by_cut(cut, explored, constraint, self.distance, enabling_cond,
                                                                force_witness=force_witness)
                # the mono_encoding

            constraint.append([-predicate, t_final])
            return predicate

    def unary_reach_cyclic(self, distance, constraints):
        reach_cache = {}

        def get_reach(node, reach_cache):
            if node is self.src or node not in distance:
                return TRUE()
            else:
                if node in reach_cache:
                    return reach_cache[node]
                else:
                    res = new_lit()
                    reach_cache[node] = res
                    return res

        def get_distance(node, d, cache):
            if node == self.src:
                return TRUE()

            if node in distance:
                if node not in cache:
                    distance_collection = (FALSE(), 0)
                    cache[node] = distance_collection

                if d > distance[node]:
                    assert False
                    return TRUE()
                else:
                    assert cache[node][0] != 0
                    return cache[node][0]

            else:
                return TRUE()

        def update_cache(cache, i):
            new_cache = {}
            for node in cache:
                if i <= distance[node]:
                    res = cache[node]
                    new_cache[node] = (res[1], 0)

            return new_cache

        cache = {}
        sink_d = []
        for i in range(1, distance[self.sink] + 1):
            for node in distance:
                if distance[node] < i:
                    continue
                gt_constraint = []
                for target, edge in self.get_incoming(get_node(self.graph, node)).items():
                    gt_constraint.append(AND(edge, get_distance(target, i - 1, cache), constraints, forward=False))
                cache[node] = (get_distance(node, i - 1, cache), g_OR(gt_constraint, constraints, forward=False))

            sink_d.append(get_distance(self.sink, i, cache))

            cache = update_cache(cache, i)

        for node in distance:
            gt_constraint = []
            for target, edge in self.get_incoming(get_node(self.graph, node)).items():
                gt_constraint.append(AND(edge, get_reach(target, reach_cache), constraints, forward=False))
            constraints.append([-get_reach(node, reach_cache), g_OR(gt_constraint, constraints, forward=False)])

        return AND(get_reach(self.sink, reach_cache), g_OR(sink_d, constraints, forward=False), constraints,
                   forward=False)

    def unary_reach_acyclic(self, distance, constraints, cut):
        explored_nodes = sorted(distance.keys(), key=lambda v: distance[v], reverse=True)

        def get_reach(node, cache):
            if node == self.src:
                return TRUE()

            if node in distance:
                if node in cache:
                    return cache[node]
                else:
                    options = []
                    for target, edge in self.get_incoming(get_node(self.graph, node)).items():
                        if edge in cut:
                            options.append(edge)
                        else:
                            options.append(AND(get_reach(target, cache), edge, constraints, forward=False))
                    result = g_OR(options, constraints, forward=False)
                    cache[node] = result
                    return result
            else:
                return TRUE()

        cache = {}
        for node in explored_nodes:
            get_reach(node, cache)
        return get_reach(self.sink, cache)

    def compute_unreachable_graph(self, cut):
        explored = set()
        open = [self.sink]

        is_edge_lit = False
        for e in cut:
            is_edge_lit = isinstance(e, int)
            break

        # explored.add(self.sink)
        while len(open) != 0:
            head = open.pop()
            if head in explored:
                continue
            else:
                explored.add(head)
                for target, edge in self.get_incoming(get_node(self.graph, head)).items():
                    if (not on_cut(edge, cut, is_edge_lit)) and (target not in explored):
                        open.append(target)
        return explored

    def compute_unreachable_graph_with_shortest_distance(self, cut):
        explored = set()
        distance = {}
        open = [self.sink]
        distance[self.sink] = 0

        is_edge_lit = False
        for e in cut:
            is_edge_lit = isinstance(e, int)
            break

        # explored.add(self.sink)
        while len(open) != 0:
            head = open.pop(0)
            if head in explored:
                continue
            else:
                explored.add(head)
                for target, edge in self.get_incoming(get_node(self.graph, head)).items():
                    if (not on_cut(edge, cut, is_edge_lit)) and (target not in explored):
                        if target not in distance:
                            distance[target] = distance[head] + 1
                        open.append(target)

        return distance

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
                for target, edge in self.get_incoming(get_node(self.graph, head)).items():
                    if not on_cut(edge, cut, is_edge_lit) and target not in explored:
                        open.append(target)

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
            if node not in explored:
                continue
            obligation = []
            for target, edge in self.get_incoming(get_node(self.graph, node)).items():
                obligation.append(OR(-enabling_cond(edge), -get_reachable(target), constraints))

            node_obligation = IMPLIES(-get_reachable(node), g_AND(obligation, constraints), constraints)
            new_obligations[node] = node_obligation
            validity_constraints.append(
                node_obligation)
        self.old_node_obligations = new_obligations
        return OR(get_reachable(self.sink), NOT(g_AND(validity_constraints, constraints)), constraints)

    def compute_unreachable_graph_by_cut(self, cut, explored, constraint, cache, enabling_cond, force_witness=False):
        max_size = len(explored)
        # print(max_size)
        if (len(cut) == 0 and not force_witness):
            max_distance = dict()

            return self._DSF(self.sink, max_size, cut, constraint, cache, enabling_cond, max_distance)
        else:
            # use the information in the cut to perform the witness encoding
            return self.wtiness_reduced_unreachability(constraint, explored, enabling_cond, is_forced=force_witness)

    def wtiness_reduced_unreachability(self, constraints, explored, enabling_cond, is_forced=False):
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
            for target, edge in self.get_incoming(get_node(self.graph, node)).items():
                obligation.append(OR(-enabling_cond(edge), -get_reachable(target), constraints))

            node_obg = IMPLIES(-get_reachable(node), g_AND(obligation, constraints), constraints)
            self.old_node_obligations[node] = node_obg
            validity_constraints.append(
                IMPLIES(-get_reachable(node), g_AND(obligation, constraints), constraints))

        return OR(get_reachable(self.sink), NOT(g_AND(validity_constraints, constraints)), constraints)

    def check_cyclic(self, head, cut, path, explored):
        for target, edge in self.get_incoming(get_node(self.graph, head)).items():
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
                for d in range(cur_distance + 1, depth + 1):
                    obligation = []
                    if cache.get((node, d), None) is None:
                        for target, edge in self.get_incoming(get_node(self.graph, node)).items():
                            if edge not in cut:
                                t_depth_var = self._DSF(target, d - 1, cut, constraint, cache, enabling_cond,
                                                        max_distance)
                            else:
                                t_depth_var = TRUE()

                            obligation.append(AND(t_depth_var, enabling_cond(edge), constraint, forward=False))
                        res = g_OR(obligation, constraint, forward=False)
                        assert cache.get((node, d), None) is None
                        cache[(node, d)] = res

            return cache[(node, depth)]

    def _BFS(self, node, cut, constraint, enabling_cond):
        pass

    def record_sub_graph(self, file, distance, cut):
        with open(file, 'w') as outfile:
            written = set()
            outfile.write("digraph 0 0 1 -1\n")
            ext_id = len(self.graph.nodes) + 1
            outfile.write("node 1 {}\n".format(ext_id))
            for node in distance:
                if node not in written:
                    outfile.write("node 1 {} \n".format(node.id))
                    written.add(node)
                for target, edge in self.get_incoming(get_node(self.graph, node)).items():
                    if target not in written:
                        if target in distance:
                            outfile.write("node 1 {} \n".format(target.id))
                            written.add(target)
                            outfile.write("edge 1 {} {} {} 1\n".format(edge.src.id, edge.target.id, edge))
                        else:
                            outfile.write("node 1 {} \n".format(target.id))
                            written.add(target)
                            outfile.write("edge 1 {} {} {} 1\n".format(edge.src.id, edge.target.id, edge))
                            for new_target, new_edge in self.get_incoming(get_node(self.graph, target)).items():
                                outfile.write("edge 1 {} {} {} 1\n".format(ext_id, new_edge.target.id, new_edge))

            outfile.write("reach 1 {} {} {}\n".format(ext_id, self.sink.id, self.lit))
            outfile.write("{} 0\n".format(self.lit))
            for l in cut:
                outfile.write("{} 0\n".format(-l))

    def collect_unreach(self, cut, constraint):
        cyclic = self.is_cyclic(cut)
        unreachable = self.compute_unreachable_graph_with_shortest_distance(cut)
        if not cyclic:
            # self.record_sub_graph("sub_gnf.gnf", unreachable, cut)
            # if not cyclic, encode right the way
            t_final = self.unary_reach_acyclic(unreachable, constraint, cut)
            constraint.append([-self.lit, t_final])
        else:
            self.cut_max_d = max(self.cut_max_d, len(unreachable))
            self.union_unreachable = self.union_unreachable.union(unreachable)

    def encode_union(self, constraints):
        if self.union_unreachable:
            explored = set()
            distance = {}
            open = [self.sink]
            distance[self.sink] = 0

            while len(open) != 0:
                head = open.pop(0)
                if head in explored:
                    continue
                else:
                    explored.add(head)
                    for target, edge in self.get_incoming(get_node(self.graph, head)).items():
                        if target in self.union_unreachable and (target not in explored):
                            if target not in distance:
                                distance[target] = distance[head] + 1
                            # else:
                            #     distance[target] = min(distance[target] , distance[head] + 1)
                            open.append(target)
            # max_distance = len(distance.values())
            op_distance = {}

            print(len(distance), self.cut_max_d)
            for node in distance:
                op_distance[node] = (self.cut_max_d - distance[node])

            t_final = self.unary_reach_cyclic(op_distance, constraints)
            constraints.append([-self.lit, t_final])

    def is_cyclic(self, cut):
        return self._is_cyclic(cut, self.sink, set(), set())

    def _is_cyclic(self, cut, current, prefix, visited):
        if current in prefix and current != self.sink:
            return True
        elif current in visited:
            return False
        else:
            prefix.add(current)
            visited.add(current)
            for target, edge in self.get_incoming(get_node(self.graph, current)).items():
                if edge not in cut:
                    if self._is_cyclic(cut, target, prefix, visited):
                        return True

            prefix.remove(current)
            return False


def parse_reach(attributes):
    if len(attributes) != 4:
        return False
    else:
        gid, source, target, lit = attributes
        gid = int(gid)
        graph = get_graph(gid)
        Reachability(graph, get_node(graph, int(source)), get_node(graph, int(target)), lit=add_lit(int(lit)))
        return True
