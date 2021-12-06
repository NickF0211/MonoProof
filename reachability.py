from logic_gate import *
class Reachability():

    def __init__(self, graph, src, target):
        self.graph = graph
        self.src = src
        self.target = target
        self.reachable = {}
        self.reachable[src] = TRUE()

        self.distance = {}
        self.distance[src] = 0


    def encode(self, hint, reachable, constraint, predicate=0):
        if predicate == 0:
            predicate = new_lit()

        if reachable:
            max_size = len(hint)
            step = 0
            #then the hint is the path from src to the target
            assert self.target in reachable
            current_node = self.src
            while current_node != hint and step < max_size:
                old_current = current_node
                current_reach = self.reachable[current_node]
                for next, edge in current_node.outgoing.items():
                    if next in hint:
                        next_reachable = self.reachable.get(next, 0)
                        if next_reachable == -1:
                            next_reachable = new_lit()
                            self.reachable[next] = next_reachable
                        constraint.append([IMPLIES(AND(current_reach, edge.lit, constraint), next_reachable, constraint)])
                        current_node = next
                        break
                assert current_node != old_current

            return IMPLIES(self.reachable[self.target], predicate, constraint)
        else:
            #in case unreachable, the hint is a cut that separates the source from the target
            isolated_graph, edge_nodes = self.compute_unreachable_graph_by_cut(hint)
            #constraint.append([IMPLIES(predicate, )])



    def compute_unreachable_graph_by_cut(self, cut):
        #perform BFS on the graph and stops at the cut
        open = set()
        explored = set()
        edge_nodes = set()
        open.add(self.target)
        while len(open) != 0:
            head = open.pop()
            explored.add(head)
            for target, edge in head.outgoing.items():
                if edge not in cut:
                    open.add(target)
                else:
                    edge_nodes.add(head)

        return explored, edge_nodes



