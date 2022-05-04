from bv import *
from graph import *
from reachability import Reachability

class Maxflow():
    Collection = {}

    def __init__(self, graph, src, sink, target_flow, lit = None):
        if isinstance(graph, int):
            graph = Graph.Graphs[graph]
        self.graph = graph
        self.src = get_node(self.graph, src)
        self.sink = get_node(self.graph, sink)
        self.target_flow = target_flow
        self.encoded = False
        if lit is None:
            self.lit = new_lit()
        else:
            self.lit = lit
        self.reachability = None
        Maxflow.Collection[lit] = self

    def encode(self, constraint):
        if self.encoded:
            return self.lit

        predicate = self.lit

        #max flow ge encoding
        graph = self.graph
        #recreate the flow assignment
        flows = {}
        for edge in graph.edges:
            if edge.cap is None:
                flows[edge] = 0
            else:
                flows[edge] = new_bv(edge.cap.width)

        cond1 = self._encode_conservation(flows, constraint)
        cond2 = self._encode_capacity_check(flows, constraint)
        cond3 = GE(self._encode_in_flow(self.sink, flows, constraint), self.target_flow, constraint)
        constraint.append([IMPLIES(predicate, g_AND([cond1, cond3, cond2],  constraint), constraint)])

        #max flow lt encoding
        cuts = {}
        for edge in graph.edges:
            if edge.cap is None:
                cuts[edge] = FALSE()
            else:
                cuts[edge] = new_lit()




        rch = Reachability(self.graph, self.src, self.sink)
        def _cut_assignment(edge):
            return AND(edge.lit, -cuts[edge], constraint)

        reachability = rch.encode(constraint, enabling_cond=_cut_assignment)
        # cond 2: the sum of cut's cap must be less than the target flow
        cond2 = self.check_cut_constraint_unhint(cuts,constraint)
        #print(cond2)
        #print(-reachability)
        constraint.append([IMPLIES(-predicate, g_AND([AND(cond2, -reachability, constraint)], constraint), constraint)])
        self.encoded = True
        return self.lit



    def encode_with_hint(self, hint, satisifed, constraint, dynamic= False):
        predicate = self.lit

        if satisifed:
            #in case of max-flow is satisfied, the hint is a dict that maps flows in each edge
            #the verification encoding checks:

            #cond1: the conservation of flows for each node
            cond1 = self._encode_conservation(hint, constraint)
            #cond2:  flow doesn't exceed the edge capacity
            cond2 = self._encode_capacity_check(hint, constraint)
            #cond3 the flow in the target is larger then the said target
            cond3 = GE(self._encode_in_flow(self.sink, hint, constraint), self.target_flow, constraint)
            constraint.append([IMPLIES(g_AND([cond1, cond3, cond2], constraint), predicate, constraint)])
            return predicate
        else:
            bv_cut, edge_cut = hint
            bv_cut = set(bv_cut)
            edge_cut = set(edge_cut)
            all_cut = bv_cut.union(edge_cut)
            #in case max-flow constraint is not satisfied, then the hint is the min-cut
            # the verification encoding checks:
            #cond 1, the cut is indeed a cut, such that the sinks is unreachable under the cut
            if self.reachability is None:
                self.reachability = Reachability(self.graph, self.src, self.sink)

            rch = self.reachability
            #if an edge is in the cut, assume the edge is disabled
            def _cut_assignment(edge):
                if edge in bv_cut:
                    return FALSE()
                else:
                    return edge.lit

            reachability = rch.encode_with_hint(all_cut, False, constraint, enabling_cond=_cut_assignment, dynamic=dynamic, flow_cut=bv_cut)
            #cond 2: the sum of cut's cap must be less than the target flow
            cond2 = self.check_cut_caps(bv_cut, constraint)
            constraint.append([IMPLIES(g_AND([AND(cond2, -reachability, constraint)], constraint), -predicate, constraint)])
            return predicate


    def check_cut_constraint_unhint(self, cuts, constraint):
        sum_cap = 0
        for edge in self.graph.edges:
            if edge.cap is not None:
                sum_cap = add_mono(sum_cap, bv_and(edge.cap, cuts[edge],constraint), constraint)
        return LT(sum_cap, self.target_flow, constraint)

    def check_cut_caps(self, cut, constraint):
        sum_cap = 0
        sum_cap_bv = 0

        for edge in cut:
            if isinstance(edge.cap, int):
                sum_cap += edge.cap
            else:
                sum_cap_bv = add_mono(sum_cap_bv, edge.cap, constraint)

        sum_cap = add_mono(sum_cap, sum_cap_bv, constraint)

        return  LT(sum_cap, self.target_flow, constraint)

    def _encode_in_flow(self, node, flows, constraint):
        in_flow = 0
        for _, in_edge in get_node(self.graph, node).incoming.items():
            flow = flows.get(in_edge, 0)
            if isinstance(flow, BV) or  flow > 0:
                in_flow = add_mono(in_flow, flow, constraint)

        return in_flow

    def _encode_out_flow(self, node, flows, constraint):
        out_flow = 0
        for _, out_edge in get_node(self.graph, node).outgoing.items():
            flow = flows.get(out_edge, 0)
            if isinstance(flow, BV)  or flow > 0:
                out_flow = add_mono(out_flow, flow, constraint)

        return out_flow

    def _encode_capacity_check(self, flows, constraint):
        conditions = []
        for edge, flow_amount in flows.items():
            if isinstance(flow_amount, BV) or flow_amount > 0:
                # the cap must be at least the flow amount
                conditions.append(GE(edge.cap, flow_amount, constraint))
                # the edge must be enabled
                conditions.append(IMPLIES(GT(flow_amount, 0, constraint), edge.lit, constraint))

        return g_AND(conditions, constraint)

    def _encode_conservation(self, flows, constraint):
        considered_node = set()
        conservation = []
        for edge, _ in flows.items():
            #check incoming node conservation
            in_node = edge.src
            if in_node not in considered_node and in_node != self.src and in_node != self.sink:
                #now check each the conservation of the flows
                conservation.append(self._encode_node_conservation(in_node, flows, constraint))
                considered_node.add(in_node)

            out_node = edge.target
            if out_node not in considered_node and out_node != self.sink and out_node != self.src:
                conservation.append(self._encode_node_conservation(out_node, flows, constraint))
                considered_node.add(out_node)

        return g_AND(conservation)

    def _encode_node_conservation(self, node, flows, constraint):
        in_flow = self._encode_in_flow(node, flows, constraint)
        out_flow = self._encode_out_flow(node, flows,constraint)
        return Equal(in_flow, out_flow, constraint)

    def find_cut(self, pseudo_cut, bv_cut):
        explored = set()
        exploring = {self.src}
        while len(exploring) > 0:
            node = exploring.pop()
            for target, edge in get_node(self.graph, node).outgoing.items():
                if target == node:
                    continue
                elif edge in pseudo_cut:
                    continue
                else:
                    if target not in explored and target not in exploring:
                        exploring.add(target)

            #now trace with backedge
            for target, edge in get_node(self.graph, node).incoming.items():
                if target == node:
                    continue
                elif edge not in bv_cut:
                    continue
                else:
                    #backedge
                    if target not in explored and target not in exploring:
                        exploring.add(target)

            explored.add(node)

        assert self.sink not in explored
        small_cut = []
        for edge in bv_cut:
            if edge.src in explored and edge.target not in explored:
                small_cut.append(edge)

        return small_cut


def parse_maxflow(attributes):
    if len(attributes) != 6:
        return False
    else:
        signature, gid, source, target, lit, targetflow = attributes
        lit = add_lit(int(lit))
        if "bv" in signature:
            targetflow = get_bv(int(targetflow))
        else:
            targetflow = int(targetflow)

        if signature.endswith("geq"):
            Maxflow(int(gid), int(source), int(target), targetflow, lit = lit)
        elif signature.endswith("gt"):
            Maxflow(int(gid), int(source), int(target), targetflow+1, lit=lit)
        elif signature.endswith("lt"):
            Maxflow(int(gid), int(source), int(target), targetflow, lit=-lit)
        elif signature.endswith("le"):
            Maxflow(int(gid), int(source), int(target), targetflow+1, lit=-lit)
        return True