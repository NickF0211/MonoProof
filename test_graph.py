from graph import *
from reachability import *
from max_flow import *
from z3 import Solver, sat, unsat
from prover import Prover

if __name__ == "__main__":
    constraint = []
    g = Graph()
    mk_node = lambda : Node(g)
    mk_edge = lambda src, target : add_edge(g, src, target)
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
    '''
    reachable_hint = [e01, e13, e35]
    reachable = r05.encode(set(reachable_hint), True, constraint)
    constraint.append([-reachable])
    constraint.append([g_AND([e01.lit, e13.lit, e35.lit], constraint)])
    '''
    '''
    unreachable_hint = [e02, e13]
    reachable = r05.encode(set(unreachable_hint), False, constraint)
    constraint.append([reachable])
    constraint.append([g_AND([-e02.lit, -e13.lit], constraint)])
    '''
    mf05 = Maxflow(g, node0, node5, 20)
    '''
    sat_hint = {e02: 10, e24:10, e43: 5, e45:5, e01:10, e13:10, e35:15}
    mfsat = mf05.encode(sat_hint, True, constraint)
    constraint.append([-mfsat])
    for edge, value in sat_hint.items():
        constraint.append([GE_const(edge.cap, value)])
        constraint.append([edge.lit])
    '''
    unsat_hint = [e02, e13]
    mfunsat = mf05.encode(set(unsat_hint), False, constraint)
    constraint.append([mfunsat])
    constraint.append([LT_const(e02.cap, 6, constraint)])
    constraint.append([LT_const(e13.cap, 15, constraint)])
    #constraint.append([GT_const(add(e13.cap, e02.cap, constraint), 4, constraint)])


    print(len(global_inv) + len(constraint))
    test_file = "test_graph.dimacs"
    write_dimacs(test_file, constraint)
    prover = Prover(get_lits_num(), constraint + global_inv)
    prover.propgate()

    s = Solver()
    s.from_file(test_file)
    res = s.check()
    print(res)
    if res == sat:
        m = s.model()
        print(sorted([(d, m[d]) for d in m], key=lambda x: int(str(x[0])[2:])))
        print("hi")
        assert (False)
