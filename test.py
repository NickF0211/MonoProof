from bv import *
from z3 import Solver, sat, unsat
from prover import Prover
from random import randint
from logic_gate import reset
from pysat.solvers import Cadical, Lingeling

'''
    bv1 = new_bv(bits)
    bv2 = new_bv(bits)
    constraints = []
    val_1 = 255
    val_2 = 0
    val_3 = 510
    print(val_1)
    print(val_2)
    print(val_3)
    bv3 = add_lower(bv1, bv2, constraints)
    constraints += [ [GE_const(bv1, val_1, constraints)], [GE_const(bv2, val_2, constraints)], [LE_const(bv3, val_3, constraints)]]

    test_file = "test.dimacs"
    write_dimacs(test_file, constraints)

    prover = Prover(get_lits_num(), constraints+global_inv)
    prover.propgate()

    s = Solver()
    s.from_file(test_file)
    res = s.check()
    print(res)
    '''

def test_propgation(attempts=100):
    print("test prop")
    for bits in range(1,16):
        for _ in range(attempts):
            bv1 = new_bv(bits)
            val_1 = randint(0, 2 ** bits - 1)
            val_2 = randint(val_1, 2 ** bits - 1)
            constraints = [[GE_const(bv1, val_2)], [LT_const(bv1, val_1)]]
            print(val_1)
            print(val_2)
            print(len(global_inv) + len(constraints))
            test_file = "test.dimacs"
            write_dimacs(test_file, constraints)

            prover = Prover(get_lits_num(), constraints + global_inv)
            if not prover.conflict:
                if prover.propgate():
                    assert (False)

            reset()


def test_upper(bits, attempts= 100):
    print("test upper")
    for _ in range(attempts):
        bv1 = new_bv(bits)
        bv2 = new_bv(bits)
        constraints = []
        val_1 = randint(0, 2 ** bits - 1)
        val_2 = randint(0, 2 ** bits - 1)
        val_3 = randint(0, val_1 + val_2)
        print(val_1)
        print(val_2)
        print(val_3)
        bv3 = add_mono(bv1, bv2, constraints)
        constraints += [[GE_const(bv1, val_1, constraints)], [GE_const(bv2, val_2, constraints)],
                        [GE_const(bv3, val_3, constraints)]]

        print(len(global_inv) + len(constraints))
        test_file = "test.dimacs"
        write_dimacs(test_file, constraints)

        prover = Prover(get_lits_num(), constraints + global_inv)
        if not prover.conflict:
            prover.propgate()

        solver = Cadical(bootstrap_with= constraints + global_inv)

        if not solver.solve():
            assert (False)

        reset()

    for _ in range(attempts):
        bv1 = new_bv(bits)
        bv2 = new_bv(bits)
        constraints = []
        val_1 = randint(0, 2 ** bits - 1)
        val_2 = randint(0, 2 ** bits - 1)
        val_3 = randint(val_1 + val_2 + 1, 2 ** (bits + 1) - 1)
        print(val_1)
        print(val_2)
        print(val_3)
        bv3 = add_mono(bv1, bv2, constraints)
        left1 = LE_const(bv1, val_1, constraints)
        left2 = LE_const(bv2, val_2, constraints)
        right = LE_const(bv3, val_3, constraints)
        lemma = IMPLIES(AND(left1, left2, constraints),
                        right, constraints)
        constraints.append([-lemma])
        '''
        constraints += [[-GT_const(bv1, val_1, constraints)], [-GT_const(bv2, val_2, constraints)],
                        [GT_const(bv3, val_3, constraints)]]
        '''

        print(len(global_inv) + len(constraints))
        test_file = "test.dimacs"
        write_dimacs(test_file, constraints)

        prover = Prover(get_lits_num(), constraints + global_inv)

        result =prover.propgate()
        solver = Lingeling(bootstrap_with= constraints + global_inv, with_proof=True)

        if solver.solve():
            assert (False)
        else:
            proof = [clause for clause in solver.get_proof() if not clause.startswith("d")]
            assert ( result or proof == [])
            print(proof)


        reset()


def test_lower(bits, attempts=100):
    for _ in range(attempts):
        bv1 = new_bv(bits)
        bv2 = new_bv(bits)
        constraints = []
        val_1 = randint(0, 2 ** bits -1)
        val_2 = randint(0, 2 ** bits -1)
        val_3 = randint(val_1 + val_2+1, 2 ** (bits+1) -1)
        print(val_1)
        print(val_2)
        print(val_3)
        bv3 = add_lower(bv1, bv2, constraints)
        #add_upper(bv1,bv2,constraints,bv3)
        constraints += [ [Equal_const(bv1, val_1, constraints)], [Equal_const(bv2, val_2, constraints)], [LE_const(bv3, val_3, constraints)]]
        print(len(global_inv) +len(constraints))
        test_file = "test.dimacs"
        write_dimacs(test_file, constraints)

        prover = Prover(get_lits_num(), constraints+global_inv)
        prover.propgate()

        s = Solver()
        s.from_file(test_file)
        res = s.check()
        if res == sat:
            print(sat)
        else:
            assert (False)

        reset()

    for _ in range(attempts):
        bv1 = new_bv(bits)
        bv2 = new_bv(bits)
        constraints = []
        val_1 = randint(0, 2 ** bits -1)
        val_2 = randint(0, 2 ** bits -1)
        val_3 = randint(0, val_1  + val_2)
        print(val_1)
        print(val_2)
        print(val_3)
        bv3 = add_lower(bv1, bv2, constraints)
        #add_upper(bv1,bv2,constraints,bv3)
        constraints += [ [GT_const(bv1, val_1, constraints)], [GT_const(bv2, val_2, constraints)], [-GT_const(bv3, val_3, constraints)]]
        print(len(global_inv) +len(constraints))
        test_file = "test.dimacs"
        write_dimacs(test_file, constraints)

        prover = Prover(get_lits_num(), constraints+global_inv)
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


        reset()


def add_performance_test(bits, layers):
    sample_layer = layers
    constraints = []
    cur_value = 0
    bottom_layers = []
    for i in range(2 ** sample_layer):
        bv = new_bv(bits)
        lower_bound = randint(0, 2 ** bits - 1)
        cur_value += lower_bound
        constraints.append([GE_const(bv, lower_bound, constraints)])
        bottom_layers.append(bv)

    while len(bottom_layers) > 1:
        cur_layers = []
        for i in range(len(bottom_layers) // 2):
            first = bottom_layers[i]
            second = bottom_layers[i + 1]
            new_bv1 = add_lower(first, second, constraints)
            cur_layers.append(new_bv1)

        bottom_layers = cur_layers

    assert (len(bottom_layers) == 1)
    sum_res = bottom_layers[0]
    constraints.append([LT_const(sum_res, cur_value, constraints)])

    # bv1 = new_bv(bits)
    # bv2 = new_bv(bits)

    # bv3 = add(bv1, bv2, constraints)
    # bv3_prime = add(bv1, bv2, constraints)
    # bv5 = add_lower(bv1, bv2, constraints)
    # constraints +=[  [GT_const(bv1, 10224, constraints)], [GT_const(bv2, 89862, constraints)], [-GT_const( bv3, 10224+89862, constraints)] ]
    print(len(global_inv) + len(constraints))
    test_file = "test_mono.dimacs"
    write_dimacs(test_file, constraints)

def add_performance_test2(bits, layers, is_momnotoinc = True):
    sample_layer = layers
    constraints = []
    bottom_layers = []
    compare_layers = []
    for i in range(2 ** sample_layer):
        bv = new_bv(bits)
        bv_prime = new_bv(bits)
        bottom_layers.append(bv)
        compare_layers.append(bv_prime)
        constraints.append([GT(bv, bv_prime, constraints)])


    while len(bottom_layers) > 1:
        cur_layers = []
        cur_compare_layers = []
        for i in range(len(bottom_layers) // 2):
            first = bottom_layers[i]
            second = bottom_layers[i + 1]
            if is_momnotoinc:
                new_bv1 = add_mono(first, second, constraints)
            else:
                new_bv1 = add(first, second, constraints)
            cur_layers.append(new_bv1)

            first_compare = compare_layers[i]
            second_compare = compare_layers[i + 1]
            if is_momnotoinc:
                compare_bv1 = add_mono(first_compare, second_compare, constraints)
            else:
                compare_bv1 = add(first_compare, second_compare, constraints)
            cur_compare_layers.append(compare_bv1)

        bottom_layers = cur_layers
        compare_layers = cur_compare_layers

    assert (len(bottom_layers) == 1)
    assert (len(compare_layers) == 1)
    sum_res = bottom_layers[0]
    compare_sum_res = compare_layers[0]

    constraints.append([GE(compare_sum_res, sum_res, constraints)])

    print(len(global_inv) + len(constraints))
    if is_momnotoinc:
        test_file = "test_mono_simplfied.dimacs"
    else:
        test_file = "test_mixed_simplified.dimacs"
    write_dimacs(test_file, constraints)

def add_performance_sequential_test():
    bits = 8

    trails = 200
    constraints = []
    val = 0
    cur = new_bv(bits)
    new_val = randint(0, 2 ** bits - 1)
    print(new_val)
    val += new_val
    constraints.append([GT_const_strict(cur, new_val, constraints, equal=True)])
    for i in range(trails):
        next = new_bv(bits)
        next_val = randint(0, 2 ** bits - 1)
        print(next_val)
        val += next_val
        constraints.append([GT_const_strict(next, next_val, constraints, equal=True)])
        cur = add_lower(cur, next, constraints)
        bits += 1

    print(val)
    constraints.append([LT_const_strict(cur, val, constraints, equal=False)])
    print(len(global_inv) + len(constraints))
    test_file = "test.dimacs"
    write_dimacs(test_file, constraints)



if __name__ == "__main__":
    width = 16
    layers = 3
    test_upper(8)
    #add_performance_test2(width, layers, is_momnotoinc=True)
    #reset()
    #add_performance_test2(width, layers, is_momnotoinc=False)



