from bv import *
from graph import *
from reachability import Reachability

class Maxflow():

    def __init__(self, graph, src, sink, target_flow):
        self.graph = graph
        self.src = src
        self.sink = sink
        self.target_flow = target_flow

    def encode(self, hint, satisifed, constraint, predicate=0):
        if predicate == 0:
            predicate = new_lit()

        if satisifed:
            #in case of max-flow is satisfied, the hint is a dict that maps flows in each edge
            #the verification encoding checks:

            #cond1: the conservation of flows for each node
            cond1 = self._encode_conservation(hint, constraint)
            #cond2:  flow doesn't exceed the edge capacity
            cond2 = self._encode_capacity_check(hint, constraint)
            #cond3 the flow in the target is larger then the said target
            cond3 = GE(self._encode_in_flow(self.sink, hint, constraint), self.target_flow, constraint)
            constraint.append([g_AND([cond1, cond3, cond2], predicate, constraint)])
            return predicate
        else:
            #in case max-flow constraint is not satisfied, then the hint is the min-cut
            # the verification encoding checks:
            #cond 1, the cut is indeed a cut, such that the sinks is unreachable under the cut
            rch = Reachability(self.graph, self.src, self.sink)
            #if an edge is in the cut, assume the edge is disabled
            def _cut_assignment(edge):
                if edge in hint:
                    return FALSE()
                else:
                    return AND(TRUE(), edge.lit, constraint)

            reachability = rch.encode(hint, False, constraint, enabling_cond=_cut_assignment)
            #cond 2: the sum of cut's cap must be less than the target flow
            cond2 = self.check_cut_caps(hint, constraint)
            constraint.append([IMPLIES(g_AND([cond2], constraint), -predicate, constraint)])
            return predicate




    def check_cut_caps(self, cut, constraint):
        sum_cap = 0
        for edge in cut:
            sum_cap = add_mono(sum_cap, edge.cap, constraint)

        return  LT(sum_cap, self.target_flow, constraint)

    def _encode_in_flow(self, node, flows, constraint):
        in_flow = 0
        for _, in_edge in node.incoming.items():
            flow = flows.get(in_edge, 0)
            if flow > 0:
                in_flow = add(in_flow, flow, constraint)

        return in_flow

    def _encode_out_flow(self, node, flows, constraint):
        out_flow = 0
        for _, out_edge in node.outgoing.items():
            flow = flows.get(out_edge, 0)
            if flow > 0:
                out_flow = add(out_flow, flow, constraint)

        return out_flow

    def _encode_capacity_check(self, flows, constraint):
        conditions = []
        for edge, flow_amount in flows.items():
            if flow_amount > 0:
                # the cap must be at least the flow amount
                conditions.append(GE(edge.cap, flow_amount, constraint))
                # the edge must be enabled
                conditions.append(edge.lit)

        return g_AND(conditions, constraint)

    def _encode_conservation(self, flows, constraint):
        considered_node = set()
        conservation = []
        for edge, _ in flows.items():
            #check incoming node conservation
            in_node = edge.src
            if in_node not in considered_node and in_node != self.src:
                #now check each the conservation of the flows
                conservation.append(self._encode_node_conservation(in_node, flows, constraint))
                considered_node.add(in_node)

            out_node = edge.target
            if out_node not in considered_node and out_node != self.sink:
                conservation.append(self._encode_node_conservation(out_node, flows, constraint))
                considered_node.add(out_node)

        return g_AND(conservation)

    def _encode_node_conservation(self, node, flows, constraint):
        in_flow = self._encode_in_flow(node, flows, constraint)
        out_flow = self._encode_out_flow(node, flows,constraint)
        return Equal(in_flow, out_flow, constraint)


