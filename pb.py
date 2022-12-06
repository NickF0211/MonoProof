# this is encoding scheme for pseudo boolean constraint constraints
from bv import BV, bv_sum, bv_and, const_to_bv, GE
from lit import new_lit, add_lit, TRUE, FALSE, write_dimacs, global_inv
from math import gcd, ceil

from parser import reextension
from solver import is_sat
import sys


class PB:
    collection = set()
    def __init__(self, variables, cofs, target, lit=None):
        assert len(variables) == len(cofs)
        self.variables = variables
        self.cofs = cofs
        self.target = target
        self.bv_init = False
        self.bvs = []
        PB.collection.add(self)

    def __str__(self):
        return "{} >= {}".format(' + '.join(["{} * v:{}".format(c, l) for l, c in zip(self.variables, self.cofs)]),
                                 self.target
                                 )

    def encode(self, constraints, mono=True):
        if not self.bv_init:
            self.bvs = [bv_and(const_to_bv(c), l, constraints) for c, l in zip(self.cofs, self.variables)]

        return GE(bv_sum(self.bvs, constraints, mono=mono), self.target, constraints)


def pb_normalize(cofs, lits, op, target):
    n_cofs, n_lits, n_op, n_target = cofs, lits, op, target
    # pass 1: ≤-constraints are changed into ≥-constraints by negating all constants
    if n_op == ">":
        n_target += 1
        n_op = ">="

    if n_op == "<":
        n_target -= 1
        n_op = "<="

    if n_op == "<=":
        n_op = ">="
        n_cofs = [-c for c in n_cofs]
        n_target = -n_target

    # pass 2: Negative coefficients are eliminated by changing p into ¬p and updating the RHS.
    new_cofs = []
    new_lits = []
    for i in range(len(n_cofs)):
        c = n_cofs[i]
        l = n_lits[i]
        if c < 0:
            n_target -= c
            new_cofs.append(-c)
            new_lits.append(-l)
        elif c == 0:
            continue
        else:
            new_cofs.append(c)
            new_lits.append(l)
    n_cofs = new_cofs
    n_lits = new_lits

    # pass 3: Multiple occurrences of the same variable are merged into one term Cix or Ci¬x
    collection = {}
    for i in range(len(new_cofs)):
        c = n_cofs[i]
        l = n_lits[i]
        stored_cof = collection.get(l, 0)
        collection[l] = c + stored_cof

    # merge x and ¬x
    keys = list(collection.keys())
    for l in keys:
        if l in collection and -l in collection:
            cur_cof = collection[l]
            other_cof = collection[-l]
            if cur_cof > other_cof:
                collection[l] -= collection.pop(-l)
                n_target -= other_cof
            elif other_cof > cur_cof:
                collection[-l] -= collection.pop(1)
                n_target -= cur_cof
            else:
                n_target -= cur_cof

    # pass 4: find out trivially sat or unsat
    if n_target <= 0:
        #print("trivially sat")
        return True

    best_case = sum([c for c in collection.values()])
    if best_case < n_target:
        #print("trivially unsat")
        return False

    # pass 5: Coefficients greater than the RHS are trimmed to (replaced with) the RHS
    for c in collection:
        if collection[c] > n_target:
            collection[c] = n_target

    # The coefficients of the LHS are divided by their greatest common divisor (“gcd”).
    # The RHS is replaced by “RHS/gcd”, rounded upwards
    gcd_val = gcd(*[val for val in collection.values()])
    for c in collection:
        collection[c] = collection[c] // gcd_val
    n_target = ceil(n_target / gcd_val)

    n_lits = list(collection.keys())
    n_lits = sorted(n_lits, key=lambda c: collection[c])
    n_cofs = []
    for l in n_lits:
        n_cofs.append(collection[l])

    return (n_cofs, n_lits, n_op, n_target)


def parse_mps_line(line: str):
    tokens = line.split()
    assert tokens[-1] == ";"
    cur_index = 0
    cofs = []
    lits = []
    while cur_index < len(tokens) - 3:
        cof = int(tokens[cur_index])
        cofs.append(cof)
        var = tokens[cur_index + 1]
        assert var.startswith('x')
        lit_var = add_lit(int(var[1:]))
        lits.append(lit_var)
        cur_index += 2

    op = tokens[-3]
    target = int(tokens[-2])
    res = pb_normalize(cofs, lits, op, target)
    if res is True:
        return True
    elif res is False:
        return False
    else:
        cofs, lits, op, target = res
        return PB(lits, cofs, target)


def parse_mps(filename):
    constraints = []
    with open(filename, 'r') as file:
        line = file.readline()
        assert isinstance(line, str)
        while line:
            if line.startswith('*'):
                line = file.readline()
                continue
            elif line.startswith("min") or line.startswith("max"):
                return False
            parsing_result = parse_mps_line(line.strip())
            if parsing_result is False:
                return [[FALSE()]]

            line = file.readline()

    return constraints


def process_pb_mps(filename, mono=True, out_cnf=None):
    constraints = parse_mps(filename)
    if constraints is False:
        print("Uknown")
        return

    for pb in PB.collection:
        constraints.append([pb.encode(constraints, mono=mono)])

    if not out_cnf:
        cnf_file = reextension(filename, "cnf")
    else:
        cnf_file = out_cnf

    write_dimacs(cnf_file, constraints)
    print("CNF written to {}".format(cnf_file))

    # if is_sat(constraints+global_inv):
    #     print ("SAT")
    # else:
    #     print("UNSAT")

if __name__ == "__main__":
    filename = sys.argv[1]
    mono = True
    if len(sys.argv) >= 3:
        mono = sys.argv[2].lower().startswith('t')

    out_cnf = None
    if len(sys.argv) >= 3:
        out_cnf = sys.argv[3]

    print("filename = {} mono: {}".format(filename, mono))
    process_pb_mps(filename, mono, out_cnf=out_cnf)


