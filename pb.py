# this is encoding scheme for pseudo boolean constraint constraints
import math
import os
import time

from bv import BV, bv_sum, bv_and, const_to_bv, GE, N_to_bit_array
from lit import new_lit, add_lit, TRUE, FALSE, write_dimacs, global_inv
from math import gcd, ceil
from logic_gate import g_OR, g_AND, OR, AND

from solver import is_sat, get_model
import sys

def reextension(source, new_ext, suffix=''):
    pre, ext = os.path.splitext(source)
    return pre + suffix + '.' + new_ext


class PB:
    collection = set()

    def __init__(self, variables, cofs, target, lit=None):
        assert len(variables) == len(cofs)
        self.variables = variables
        self.cofs = cofs
        self.target = target
        self.bv_init = False
        self.bvs = []
        self.suff = []
        self.amo = None
        self.is_pb_sat = True
        self.is_sat = False
        PB.collection.add(self)

    def invalidate(self, lits_to_pb=None, affected=None):
        # invalidate a pb constraint
        if lits_to_pb:
            for l in self.variables:
                res = lits_to_pb.get(l, [])
                if res:
                    res.discard(self)
                    if affected is not None:
                        affected.add(l)

            for l in self.suff:
                res = lits_to_pb.get(l, [])
                if res:
                    res.discard(self)
                    if affected is not None:
                        affected.add(l)

        # self.variables = []
        # self.cofs = []
        # self.target = 0
        # self.bv_init = False
        # self.bvs = []
        # self.suff = []
        # self.amo = None
        # self.is_pb_sat = True
        # self.is_sat = True

    def __str__(self):
        return "{} >= {}".format(' + '.join(["{} * v:{}".format(c, l) for l, c in zip(self.variables, self.cofs)]),
                                 self.target
                                 )

    def find_ge_than(self, LS):
        collections = {}
        if self.is_sat:
            return collections
        var_to_cof = self.build_var_to_cof()
        for lit in var_to_cof:
            for l in LS:
                if l in var_to_cof:
                    if l != lit and var_to_cof[lit] >= var_to_cof[l]:
                        res = collections.get(l, set())
                        res.add(lit)
                        collections[l] = res
        return collections

    def find_le_than(self, LS):
        collections = {}
        if self.is_sat:
            return collections
        var_to_cof = self.build_var_to_cof()
        for lit in var_to_cof:
            for l in LS:
                if l in var_to_cof:
                    if l != lit and var_to_cof[lit] <= var_to_cof[l]:
                        res = collections.get(l, set())
                        res.add(lit)
                        collections[l] = res
        return collections

    def validate(self, model):
        if self.is_sat:
            return True
        else:
            for l in self.suff:
                if l in model:
                    return True

            cur_sum = 0
            for i in range(len(self.cofs)):
                cof = self.cofs[i]
                lit = self.variables[i]
                if lit in model:
                    cur_sum += cof
            return cur_sum >= self.target

    def build_var_to_cof(self):
        var_to_cof = {}
        for i in range(len(self.variables)):
            lit = self.variables[i]
            cof = self.cofs[i]
            var_to_cof[lit] = cof

        for i in self.suff:
            var_to_cof[i] = self.target

        return var_to_cof

    def resolve(self, other, l):
        self_var_to_cof = self.build_var_to_cof()
        other_var_to_cof = other.build_var_to_cof()
        l_cof = self_var_to_cof[l]
        nl_cof = other_var_to_cof[-l]
        m = lcm(l_cof, nl_cof)
        self_ratio = m // l_cof
        other_ratio = m // nl_cof
        total_sum_assumed = 0
        new_collection = {}
        for lit in self_var_to_cof:
            new_collection[lit] = self_var_to_cof[lit] * self_ratio

        for lit in other_var_to_cof:
            lit_val = other_var_to_cof[lit] * other_ratio
            neg_lit_val = new_collection.get(-lit, 0)
            if neg_lit_val > 0:
                if neg_lit_val > lit_val:
                    assumed = lit_val
                    new_collection[-lit] -= assumed
                    total_sum_assumed += assumed
                else:
                    new_collection.pop(-lit)
                    assumed = neg_lit_val
                    if lit_val > neg_lit_val:
                        new_collection[lit_val] = lit_val - neg_lit_val
                    total_sum_assumed += assumed
            else:
                new_collection[lit] = new_collection.get(lit, 0) + lit_val

        target = (self.target * self_ratio) + (other.target * other_ratio) - total_sum_assumed
        lits = list(new_collection.keys())
        cofs = [new_collection[v] for v in new_collection]

        res = pb_normalize(cofs, lits, ">=", target)
        if res is True:
            return True
        elif res is False:
            return False
        else:
            cofs, lits, op, target = res
            return PB(lits, cofs, target)

    def is_at_most_one(self):
        if self.amo is not None:
            return self.amo

        for cof in self.cofs:
            if cof != 1:
                self.amo = False
                return False

        self.amo = (self.target == len(self.cofs) - 1)
        return self.amo


    def pre_encode(self, constraint, assumption=None):
        if self.target <= 0 or self.is_sat:
            # the target is satisified, nothing to worry about
            return []

        forced_lits = []
        if assumption:
            new_cofs = []
            new_vars = []
            for i in range(len(self.cofs)):
                val = self.cofs[i]
                lit = self.variables[i]
                if lit in assumption:
                    # if something is assumed true
                    self.target -= val
                    continue
                if -lit in assumption:
                    continue
                else:
                    new_cofs.append(val)
                    new_vars.append(lit)
            self.cofs = new_cofs
            self.variables = new_vars
            new_suffix = []

            for l in self.suff:
                if l in assumption:
                    # the pb constraint is trivially satisifed
                    self.cofs = []
                    self.lits = []
                    self.suff = []
                    self.is_sat = True
                    return []
                elif -l in assumption:
                    continue
                else:
                    new_suffix.append(l)
            self.suff = new_suffix

        cof_sum = sum(self.cofs)
        new_cofs = []
        new_vars = []
        for i in range(len(self.cofs)):
            val = self.cofs[i]
            lit = self.variables[i]

            if cof_sum - val < self.target and not self.suff:
                # lit has to be true
                constraint.append([lit])
                forced_lits.append(lit)
                self.target -= val
                cof_sum -=val
            else:
                if val >= self.target:
                    self.suff.append(lit)
                else:
                    new_cofs.append(val)
                    new_vars.append(lit)

        self.cofs = new_cofs
        self.variables = new_vars
        if assumption:
            if self.is_pb_sat:
                self.is_pb_sat = (sum(self.cofs) >= self.target)

            if not self.is_pb_sat and len(self.suff) == 1:
                constraint.append([self.suff[0]])
                forced_lits.append(self.suff[0])
                self.is_sat = True

        return forced_lits

    def unary_encode(self, constraints):
        cache = {}
        return g_OR([self._unary_encode(0, self.target, sum(self.cofs), constraints, cache)] + self.suff)

    def _unary_encode(self, start, sub_target, remain_sum, constraints, cache):

        if sub_target <= 0:
            return TRUE()
        elif remain_sum == sub_target:
            return g_AND(self.variables[start:], constraints)
        elif remain_sum < sub_target:
            return FALSE()
        elif start == len(self.variables):
            return FALSE()
        else:
            if (start, sub_target) in cache:
                return cache[(start, sub_target)]
            else:
                head = self.variables[start]
                head_cof = self.cofs[start]

                # case1 , head is aserted
                case1 = AND(head,
                            self._unary_encode(start + 1, sub_target - head_cof, remain_sum - head_cof, constraints,
                                               cache), constraints)
                case2 = self._unary_encode(start + 1, sub_target, remain_sum - head_cof, constraints, cache)
                result = OR(case1, case2, constraints)
                cache[(start, sub_target)] = result
                return result

    def encode(self, constraints, mono=True, dir_specfic=True, smart_encoding=-1, smart_finishing=False, duo=False,
               linear=False):

        if self.is_sat:
            return TRUE()

        if not self.is_pb_sat:
            if self.suff:
                constraints.append(self.suff)
                return TRUE()
            else:
                return FALSE()

        # if self.is_at_most_one() and len(self.variables) <= 6 and not self.suff:
        #     # specialized amp encoding
        #     for i in range(len(self.variables)):
        #         l1 = self.variables[i]
        #         for j in range(i + 1, len(self.variables)):
        #             l2 = self.variables[j]
        #             constraints.append([l1, l2] + self.suff)
        #     return TRUE()

        self.pre_encode(constraints)

        if self.target <= 0:
            return TRUE()
        else:
            if is_card(self.cofs) or len(self.variables) <= 10:
                return self.unary_encode(constraints)
            else:
                if not self.bv_init:
                    self.bvs = [bv_and(const_to_bv(c), l, constraints) for c, l in zip(self.cofs, self.variables)]
                    self.bv_init = True
                return self.binary_encode(constraints, mono, dir_specfic, smart_encoding, smart_finishing, duo, linear)

    def binary_encode(self, constraints, mono=True, dir_specfic=True, smart_encoding=-1, smart_finishing=False, duo=False,
               linear=False):
        return binary_pb_constraint(self.cofs, self.variables, self.target, self.suff, constraints, mono, dir_specfic,
                                    smart_encoding, smart_finishing, duo, linear, bvs = self.bvs, optimized=False)



    def bounded_encode(self, constraints, mono=True, dir_specfic=True, smart_encoding=-1, smart_finishing=False, duo=False,
               linear=False, bound =10):
        if self.is_sat:
            return TRUE()

        if not self.is_pb_sat:
            if self.suff:
                constraints.append(self.suff)
                return TRUE()
            else:
                return FALSE()

        # if self.is_at_most_one() and len(self.variables) <= 6 and not self.suff:
        #     # specialized amp encoding
        #     for i in range(len(self.variables)):
        #         l1 = self.variables[i]
        #         for j in range(i + 1, len(self.variables)):
        #             l2 = self.variables[j]
        #             constraints.append([l1, l2] + self.suff)
        #     return TRUE()

        self.pre_encode(constraints)

        if self.target <= 0:
            return TRUE()
        else:
            if is_card(self.cofs) or len(self.variables) <= bound:
                # if the pb is a cardnaility constraint, then keep going
                return self.unary_encode(constraints)
            else:
                cache = dict()
                return g_OR([_unary_encode(self.variables, self.cofs, 0, self.target, sum(self.cofs),
                                          constraints, cache, token=bound, mono=mono, dir_specfic=dir_specfic,
                                          smart_encoding=-smart_encoding, smart_finishing=smart_finishing, duo=duo,
                                          linear=linear
                                          )] + self.suff, constraints)

    def find_simple_varibale_order(self, EQ):
        cof_to_var = {}
        EQ_order = {}
        for i in range(len(self.variables)):
            cof_col = cof_to_var.get(self.cofs[i], [])
            cof_col.append(self.variables[i])
        for i in range(len(self.variables)):
            cof_col = cof_to_var.get(self.cofs[i], [])
            cur_eq_order = set(cof_col)
            EQ_order[self.variables[i]] = cur_eq_order

        for var in self.variables:

            if var not in EQ:
                EQ[var] = EQ_order[var]
            else:
                EQ[var] = EQ[var].intersection(EQ_order[var])

        return EQ_order

    def register_lits(self, lits_to_pb):
        if self.is_sat:
            return
        if not self.is_pb_sat:
            return

        for l in self.variables:
            pbs = lits_to_pb.get(l, [])
            if isinstance(pbs, set):
                pbs.add(self)
            else:
                pbs.append(self)
            lits_to_pb[l] = pbs


def is_card(cofs):
    res = True
    for c in cofs:
        if c!= 1:
            return False
    return res


def binary_pb_constraint(cofs, variables, target, suff, constraints, mono=True, dir_specfic=True, smart_encoding=-1, smart_finishing=False, duo=False,
               linear=False, bvs= None, optimized = False):
    if optimized:
        res = pb_normalize(cofs, variables, ">=", target)
        if res is True:
            return TRUE()
        elif res is False:
            return FALSE()
        else:
            cofs, variables, op, target = res

    obligations = []
    new_cofs = []
    new_vars = []
    if bvs is None:
        cof_sum = sum(cofs)
        for i in range(len(cofs)):
            val = cofs[i]
            lit = variables[i]

            if cof_sum - val < target and not suff:
                # lit has to be true
                obligations.append(lit)
                target -= val
                cof_sum -= val
            else:
                if val >= target:
                    suff.append(lit)
                else:
                    new_cofs.append(val)
                    new_vars.append(lit)

        cofs = new_cofs
        variables = new_vars
        bvs = [bv_and(const_to_bv(c), l, constraints) for c, l in zip(cofs, variables)]

    compare_result = []
    cap = len(N_to_bit_array(target)) + 1
    if variables:
        compare_result.append(GE(bv_sum(bvs, constraints, mono=mono, is_dir_specific=dir_specfic,
                                        smart_encoding=smart_encoding, smart_finishing=smart_finishing,
                                        duo=duo,
                                        upper_bound=cap, linear=linear), target, constraints))

    return g_AND(obligations + [g_OR(suff + compare_result, constraints)], constraints)

def register_pbs():
    lits_to_pb = {}
    for pb in PB.collection:
        pb.register_lits(lits_to_pb)

    return lits_to_pb


def derive_facts(constraints, scope=None, assumption=None):
    forced = []
    if scope is None:
        scope = PB.collection

    for pb in scope:
        forced += pb.pre_encode(constraints, assumption=assumption)

    return set(forced)


def propagation(lits_to_pb, constraints):
    forced = derive_facts(constraints)
    all_forced = forced
    while forced:
        # for every forced literal, we need to analyze its impact
        to_be_propagated = []
        for l in forced:
            if -l in all_forced:
                return False
            to_be_propagated += lits_to_pb.get(l, [])
            to_be_propagated += lits_to_pb.get(-l, [])
        forced = derive_facts(constraints, set(to_be_propagated), forced)
        all_forced = all_forced.union(forced)

    return all_forced


def binary_resolution(lits_to_pb, rounds=-1, derived_upper_bound=2000):
    resolved = False
    affected = lits_to_pb.keys()
    cur_round = 0
    derived = 0
    for l in lits_to_pb:
        lits_to_pb[l] = set(lits_to_pb[l])

    while affected and (rounds < 0 or cur_round < rounds) and (
            derived_upper_bound < 0 or derived < derived_upper_bound):
        new_affected = set()
        for l in affected:
            if len(lits_to_pb[l]) == 1:
                # then we can resolve it away
                cur_pb = lits_to_pb[l].pop()
                opposite = lits_to_pb.get(-l, [])
                while opposite:
                    pb = opposite.pop()
                    new_pb = pb.resolve(cur_pb, -l)
                    if new_pb is False:
                        return -1
                    else:
                        pb.invalidate(lits_to_pb, new_affected)
                        if isinstance(new_pb, PB):
                            new_pb.register_lits(lits_to_pb)
                            derived += 1
                            if (derived_upper_bound >= 0 and derived >= derived_upper_bound):
                                return 1

                cur_pb.invalidate(lits_to_pb, new_affected)
                resolved = True
        affected = new_affected
        cur_round += 1
    if resolved:
        return 1
    else:
        return 0

def _unary_encode(variables, cofs, start, sub_target, remain_sum, constraints, cache, token= 10, mono=True, dir_specfic=True, smart_encoding=-1, smart_finishing=False, duo=False,
               linear=False, remain_all_ones = False):

    if sub_target <= 0:
        return TRUE()
    elif remain_sum == sub_target:
        return g_AND(variables[start:], constraints)
    elif remain_sum < sub_target:
        return FALSE()
    elif start == len(variables):
        return FALSE()
    else:
        if (start, sub_target) in cache:
            return cache[(start, sub_target)]
        else:
            if not remain_all_ones:
                remain_all_ones = is_card(cofs[start:])
            if token > 0 or remain_all_ones:
                head = variables[start]
                head_cof = cofs[start]

                # case1 , head is aserted
                case1 = AND(head,
                            _unary_encode(variables, cofs, start + 1, sub_target - head_cof, remain_sum - head_cof, constraints,
                                               cache, token -1, mono, dir_specfic, smart_encoding, smart_finishing, duo,
               linear, remain_all_ones), constraints)
                case2 = _unary_encode(variables, cofs, start + 1, sub_target, remain_sum - head_cof, constraints, cache,
                                      token- 1, mono, dir_specfic, smart_encoding, smart_finishing, duo,linear, remain_all_ones)
                result = OR(case1, case2, constraints)
                cache[(start, sub_target)] = result
            else:
                result = binary_pb_constraint(cofs[start:], variables[start:], sub_target, [], constraints , mono, dir_specfic,
                                    smart_encoding, smart_finishing, duo, linear, bvs = None, optimized=True)
                cache[(start, sub_target)] = result
            return result

def find_variable_order(lits, constraints, lit_to_pbs):
    my_collections = {}
    neg_lits = [-lit for lit in lits]
    for pb in PB.collection:
        local = pb.find_ge_than(neg_lits)
        for l in local:
            if l in my_collections:
                my_collections[l] = my_collections[l].intersection(local[l])
            else:
                my_collections[l] = local[l]

    nl_keys = list(my_collections.keys())
    for l in nl_keys:
        if not my_collections[l]:
            my_collections.pop(l)

    pos_lits = [-l for l in my_collections.keys()]
    my_pos_collection = {}
    for pb in PB.collection:
        local = pb.find_le_than(pos_lits)
        for l in local:
            if l in my_pos_collection:
                my_pos_collection[l] = my_pos_collection[l].intersection(local[l])
            else:
                my_pos_collection[l] = local[l]

    merged_collection = {}
    for l in my_pos_collection:
        nl = -l
        less_than_l = my_pos_collection[l]
        greater_than_nl = my_collections[nl]
        if not less_than_l or not greater_than_nl:
            continue

        merged = set()
        for lit in less_than_l:
            if -lit in greater_than_nl:
                merged.add(lit)

        merged_collection[l] = merged

    # print(merged_collection)
    # for each of the element here, we need to ensure:
    ordering = set()
    for l, LE in merged_collection.items():
        l_appeared = set(lit_to_pbs.get(l, set()))
        nl_appeared = set(lit_to_pbs.get(-l, set()))
        for lit in LE:
            lit_appeared = set(lit_to_pbs.get(lit, set()))
            nlit_appeared = set(lit_to_pbs.get(-lit, set()))
            if lit_appeared.difference(l_appeared):
                continue
            if nl_appeared.difference(nlit_appeared):
                continue
            else:
                if (l, lit) not in ordering:
                    ordering.add((lit, l))
                    constraints.append([l, -lit])
                    print((l, lit))

    print(ordering)


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

    assert n_op == ">="

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
        # print("trivially sat")
        return True

    best_case = sum([c for c in collection.values()])
    if best_case < n_target:
        # print("trivially unsat")
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
    n_lits = sorted(n_lits, key=lambda c: collection[c], reverse=True)
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

    if op == "=":
        res1 = pb_normalize(cofs, lits, ">=", target)
        res2 = pb_normalize(cofs, lits, "<=", target)
        if res1 is False or res2 is False:
            return False
        else:
            if res1 is not True:
                cofs, lits, op, target = res1
                PB(lits, cofs, target)
            if res2 is not True:
                cofs, lits, op, target = res2
                PB(lits, cofs, target)
            return True

    else:
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
                line = file.readline()
                continue
            parsing_result = parse_mps_line(line.strip())
            if parsing_result is False:
                return [[FALSE()]]

            line = file.readline()

    return constraints


def sort_tuple(l1, l2):
    if l1 > l2:
        return l2, l1
    else:
        return l1, l2


def pure_literal_removal():
    print("pure_literal_removal")
    literals = []
    for pb in PB.collection:
        literals += pb.variables

    literals = set(literals)
    pos_literals = set()
    neg_literals = set()
    for l in literals:
        if l > 0:
            pos_literals.add(l)
        elif l < 0:
            neg_literals.add(-l)

    pos_pure = pos_literals.difference(neg_literals)
    neg_pure = neg_literals.difference(pos_literals)
    print("prune pos literal {}".format(len(pos_pure)))
    print("prune neg literal {}".format(len(neg_pure)))
    remain = len(literals) - len(pos_pure) - len(neg_pure)
    print("remained {}".format(remain))

    if pos_pure or neg_pure:
        for pb in PB.collection:
            new_literals = []
            new_cof = []
            for i in range(len(pb.variables)):
                if pb.variables[i] in pos_pure or -pb.variables[i] in neg_pure:
                    pb.target -= pb.cofs[i]
                else:
                    new_literals.append(pb.variables[i])
                    new_cof.append(pb.cofs[i])
            pb.variables = new_literals
            pb.cofs = new_cof
    print("done pure literal removal")


def calculate_variable_score():
    scores = {}
    for pb in PB.collection:
        if pb.is_sat:
            continue

        for lit in pb.suff:
            if lit > 0:
                scores[lit] = scores.get(lit, 0) + 1
            else:
                scores[-lit] = scores.get(-lit, 0) - 1

        for i in range(len(pb.variables)):
            lit = pb.variables[i]
            local_score = pb.cofs[i] / pb.target
            if lit > 0:
                scores[lit] = scores.get(lit, 0) + local_score
            else:
                scores[-lit] = scores.get(-lit, 0) - local_score
    return scores


def get_important_variables(scores, threshold=0.1, forced=None):
    if forced:
        key_list = list(scores.keys())
        for l in key_list:
            if l in forced or -l in forced:
                scores.pop(l)
    total_variables = len(scores)
    top_nums = math.ceil(total_variables * threshold)
    sorted_lits = sorted(scores, key=lambda c: abs(scores[c]), reverse=True)

    return [l if scores[l] > 0 else -l for l in sorted_lits[:top_nums + 1]]


def process_pb_mps(filename, mono=True, out_cnf=None, smart_encoding=-1, smart_finishing=False, duo=False,
                   linear=False):
    constraints = parse_mps(filename)
    if constraints is False:
        print("Uknown")
        return
    # pure_literal_removal()

    if not out_cnf:
        if smart_encoding >= 0:
            if smart_finishing:
                cnf_file = reextension(filename, "s{}fcnf".format(smart_encoding))
            else:
                cnf_file = reextension(filename, "s{}cnf".format(smart_encoding))
        else:
            if mono:
                cnf_file = reextension(filename, "mcnf")
            elif linear:
                cnf_file = reextension(filename, "lmcnf")
            else:
                if duo:
                    cnf_file = reextension(filename, "dcnf")
                else:
                    cnf_file = reextension(filename, "cnf")
    else:
        cnf_file = out_cnf

    preprocess_start = time.time()
    lit_to_pbs = register_pbs()
    res_result = binary_resolution(lit_to_pbs)
    if res_result < 0:
        print("{}, UNSAT, resolution, {}, 0 ".format(cnf_file, time.time() - preprocess_start))
        return

    lit_to_pbs = register_pbs()
    p_result = propagation(lit_to_pbs, constraints)
    if p_result is False:
        print("{}, UNSAT, propagation, {}, 0".format(cnf_file, time.time() - preprocess_start))
        return
    preprocess_time = time.time() - preprocess_start

    encode_start = time.time()
    for pb in PB.collection:
        if smart_encoding >= 0:
            constraints.append([pb.bounded_encode(constraints, smart_encoding=smart_encoding, smart_finishing=smart_finishing)])
        elif mono:
            constraints.append([pb.bounded_encode(constraints, mono=True, dir_specfic=True)])
        elif linear:
            constraints.append([pb.bounded_encode(constraints, mono=True, linear=True, dir_specfic=True)])
        else:
            constraints.append([pb.bounded_encode(constraints, mono=False, duo=duo)])
    encode_time = time.time() - encode_start
    # important_lits = get_important_variables(calculate_variable_score(), forced=p_result)
    # find_variable_order(important_lits, constraints, lit_to_pbs)
    # return
    all_constraint = constraints + global_inv
    # write_dimacs(cnf_file, constraints)
    # print("CNF written to {}".format(cnf_file))

    start_time = time.time()
    m = get_model(all_constraint)
    solving_time = time.time() - start_time
    if m:
        print("{}, SAT, {}, {}, {}".format(cnf_file, solving_time, preprocess_time, encode_time))
        # assert check_solution(m, filename)
    else:
        print("{}, UNSAT, {}, {}, {}".format(cnf_file, solving_time, preprocess_time, encode_time))


def check_solution(model, infile):
    PB.collection.clear()
    parse_mps(infile)
    model = set(model)
    for pb in PB.collection:
        if not pb.validate(model):
            print(pb)
            return False
    return True


def lcm(a, b):
    return abs(a * b) // math.gcd(a, b)

# parse a pb constraint from monosat
def parse_pb(tokens):
    op = tokens[0]
    target = int(tokens[1])
    lit_size = int(tokens[2])
    lits = [int(l) for l in tokens[3: 3 + lit_size]]
    weight_index = 3+ lit_size
    weight_size = int(tokens[weight_index])
    if weight_size:
        cofs = [int(l) for l in tokens[weight_index: weight_index + weight_size]]
    else:
        cofs = [0 for _ in range(lit_size)]

    assert op != "!="
    if op == "=" or op == '==':
        res1 = pb_normalize(cofs, lits, ">=", target)
        res2 = pb_normalize(cofs, lits, "<=", target)
        if res1 is False or res2 is False:
            return False
        else:
            if res1 is not True:
                cofs, lits, op, target = res1
                PB(lits, cofs, target)
            if res2 is not True:
                cofs, lits, op, target = res2
                PB(lits, cofs, target)
            return True

    else:
        res = pb_normalize(cofs, lits, op, target)
        if res is True:
            return True
        elif res is False:
            return False
        else:
            cofs, lits, op, target = res
            return PB(lits, cofs, target)



if __name__ == "__main__":
    filename = sys.argv[1]
    mono = True
    duo = False
    linear = False
    if len(sys.argv) >= 3:
        mono = sys.argv[2].lower().startswith('t')
        duo = sys.argv[2].lower().startswith('d')
        linear = sys.argv[2].lower().startswith('l')

    smart_encoding = -1
    if len(sys.argv) >= 4:
        smart_encoding = int(sys.argv[3])

    smart_finishing = False
    if len(sys.argv) >= 5:
        smart_finishing = sys.argv[4].lower().startswith('t')

    out_cnf = None
    if len(sys.argv) >= 6:
        out_cnf = sys.argv[5]

    # print("filename = {} mono: {}".format(filename, mono))
    process_pb_mps(filename, mono, out_cnf=out_cnf, smart_encoding=smart_encoding, smart_finishing=smart_finishing,
                   duo=duo, linear=linear)
