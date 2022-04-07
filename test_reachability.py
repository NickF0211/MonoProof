from max_flow import *
from prover import Prover
from solver import is_sat, get_proof, optimize_proof, is_rat

if __name__ == "__main__":
    constraint = []
    g = Graph()
    mk_node = lambda : Node(g)
    mk_edge = lambda src, target : add_edge(g, src, target, weight = new_bv(8))
    node0 = mk_node()
    node1 = mk_node()
    node2 = mk_node()
    node3 = mk_node()
    node4 = mk_node()
    node5 = mk_node ()

    e01 = mk_edge(0 ,1)
    e02 = mk_edge(0, 2)
    e13 = mk_edge(1, 3)
    e21 = mk_edge(2, 1)
    e24 = mk_edge(2, 4)
    e43 = mk_edge(4, 3)
    e45 = mk_edge(4, 5)
    e32 = mk_edge(3, 2)
    e35 = mk_edge(3, 5)

    r05 = Reachability(g, node0, node5)

    #reachable_hint = [e01, e13, e35]

    reachable = r05.encode(constraint)

    push(constraint)
    constraint.append([-reachable])
    constraint.append([g_AND([e01.lit, e13.lit, e35.lit], constraint)])
    assert(not is_sat(constraint + global_inv))
    assert (is_rat(constraint + global_inv))
    pop(constraint)



    #unreachable_hint = [e02, e13]
    #reachable = r05.encode(set(unreachable_hint), False, constraint)
    #reachable = r05.encode(constraint)
    push(constraint)
    constraint.append([-reachable])
    constraint.append([g_AND([-e01.lit, e02.lit, e13.lit, e21.lit, e24.lit, e43.lit, e32.lit, e35.lit, -e45.lit], constraint)])
    assert (not is_sat(constraint + global_inv))
    assert (is_rat(constraint + global_inv))
    pop(constraint)



