from max_flow import *
from z3 import Solver, sat, unsat
from prover import Prover
from solver import is_sat, get_proof, optimize_proof, get_model

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


    mf05 = Maxflow(g, node0, node5, 20)
    '''
    sat_hint = {e02: 10, e24:10, e43: 5, e45:5, e01:10, e13:10, e35:15}
    #mfsat = mf05.encode_with_hint(sat_hint, True, constraint)
    mfsat = mf05.encode(constraint)
    constraint.append([-mfsat])
    for edge, value in sat_hint.items():
        constraint.append([GE_const(edge.cap, value)])
        constraint.append([edge.lit])

    '''
    constraint.append([LT_const(add_mono(e02.cap, e21.cap, constraint), 11, constraint)])
    unsat_hint = ([e02, e13],[])
    # mfunsat = mf05.encode_with_hint(unsat_hint, False, constraint)
    mfunsat = mf05.encode(constraint)
    constraint.append([mfunsat])
    #constraint.append([LT_const(e02.cap, 200, constraint)])
    constraint.append([LT_const(e13.cap, 10, constraint)])
    #constraint.append([GT_const(add(e13.cap, e02.cap, constraint), 4, constraint)])
    print(len(global_inv) + len(constraint))


    model = get_model(constraint + global_inv)
    if model:
        print(model)
        assert False
    else:
        proofs = get_proof(constraint + global_inv, optimize=True)
        #proofs = optimize_proof(constraint + global_inv, proofs)
        print(len(proofs))
        print("unsat")


