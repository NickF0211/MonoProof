from lit import *
from logic_gate import *


class BV():
    Bvs = {}

    def __init__(self, width, body, id=None, value=-1):

        assert width == 0 or body is None or len(body) == width
        assert value >= 0 or body is not None

        if body is None and width != 0:
            # this is the case for unassigned BV
            self.assigned = False
        else:
            self.assigned = True

        self.value = value
        self.width = width
        self.body = body
        self.parent = None
        if id == None:
            self.id = len(BV.Bvs)
        else:
            self.id = id
        if id is not None:
            BV.Bvs[self.id] = self

    def assign(self):
        if not self.assigned:
            if self.value >= 0:
                body = N_to_bit_array(self.value)
                body = [ntob(b) for b in body]
                assert len(body) <= self.width
                self.body = [FALSE() for i in range(self.width - len(body))] + body
            else:
                self.body = [new_lit() for _ in range(self.width)]
                self.assigned = True

    def get_body(self):
        self.assign()
        return self.body

    def get_var(self, index):
        self.assign()
        assert (index < self.width)
        return self.body[index]

    def set_var(self, index, var):
        self.assign()
        assert (index < self.width)
        self.get_body()[index] = var

    def extend(self, padding_num, is_zeros=False):
        self.assign()
        if is_zeros:
            return BV(self.width + padding_num, [FALSE() for _ in range(padding_num)] + self.get_body())
        else:
            return BV(self.width + padding_num, [new_lit() for _ in range(padding_num)] + self.get_body())

    def self_extend(self, padding_num, pad=FALSE):
        self.assign()
        self.width = self.width + padding_num
        self.body = [pad() for _ in range(padding_num)] + self.get_body()

    def get_value(self, model):
        value = 0
        for i in range(self.width):
            if self.get_var(i) != FALSE() and model[self.get_var(i) - 1] > 0:
                value += 2 ** (self.width - i - 1)
        return value

    def get_bound(self, model):
        ub, lb = (1 << self.width) - 1, 0
        for i in range(self.width):
            if self.get_var(i) in model:
                lb += (1 << (self.width - i - 1))
            if -self.get_var(i) in model:
                ub -= (1 << (self.width - i - 1))
        return ub, lb

    def __repr__(self):
        return "BV{}".format(self.id)


def get_bv(id):
    return BV.Bvs.get(id)


def sub_bv(bv, start, end):
    return BV(end - start, bv.get_body()[start:end])


def new_bv(width, set_var=True):
    assert width > 0
    if set_var:
        body = [new_lit() for _ in range(width)]
    else:
        body = [0 for _ in range(width)]
    return BV(width, body)


def new_unassigned_bv(width):
    assert width > 0
    return BV(width, None)


def const_bv(id, width, value):
    assert width > 0
    return BV(width, None, id=id, value=value)


def N_to_bit_array(const, width=-1):
    inter = bin(const)[2:]
    if width != -1:
        assert (len(inter) <= width)
        inter = inter.zfill(width)
    return [0 if b == '0' else 1 for b in inter]


def ntob(num):
    if num:
        return TRUE()
    else:
        return FALSE()


def GT_const_strict(bv1, const, constraints=global_inv, equal=False):
    if not equal:
        const = const + 1
    if const > (1 << bv1.width) - 1:
        return FALSE()
    const_bv = N_to_bit_array(const, bv1.width)
    return g_AND([bv1.get_var(i) for i in range(len(const_bv)) if const_bv[i] == 1], constraints)


def LT_const_strict(bv1, const, constraints=global_inv, equal=False):
    if not equal:
        const = const - 1
    const_bv = N_to_bit_array(const, bv1.width)
    return g_AND([-bv1.get_var(i) for i in range(len(const_bv)) if const_bv[i] == 0], constraints)


def cast_bool_to_lit(inbool):
    if isinstance(inbool, bool):
        if inbool is True:
            return TRUE()
        else:
            return FALSE()
    else:
        return inbool


def GT_const(bv1, const, constraints=global_inv, equal=False):
    if isinstance(bv1, int):
        if equal:
            return cast_bool_to_lit(bv1 >= const)
        else:
            return cast_bool_to_lit(bv1 > const)
    if const > (2 ** bv1.width) - 1:
        return FALSE()

    if const >= (2 ** bv1.width) - 1 and not equal:
        return FALSE()

    const_bv = N_to_bit_array(const, bv1.width)
    assert bv1.width == len(const_bv)
    ch_c = TRUE()
    width = bv1.width
    gts = []
    for i in range(width):
        con_bit = const_bv[i]
        if con_bit:
            ch_c = AND(ch_c, bv1.get_var(i), constraints)
        else:
            gt_c = AND(ch_c, bv1.get_var(i), constraints)
            gts.append(gt_c)

    if equal:
        return g_OR(gts + [ch_c], constraints)
    else:
        return g_OR(gts, constraints)


def add(bv1, bv2, constraints=global_inv, input_bv3=None):
    if isinstance(bv1, int):
        bv1 = const_to_bv(bv1)
    if isinstance(bv2, int):
        bv2 = const_to_bv(bv2)

    if bv1.width < bv2.width:
        bv1.self_extend(bv2.width - bv1.width)
    elif bv1.width > bv2.width:
        bv2.self_extend(bv1.width - bv2.width)

    assert bv1.width == bv2.width
    bv3 = new_bv(bv1.width + 1, set_var=False)
    c_i = FALSE()
    for r_i in range(bv1.width):
        i = bv1.width - 1 - r_i
        i_3 = i + 1
        bit1 = bv1.get_var(i)
        bit2 = bv2.get_var(i)
        bit3 = XOR(XOR(bit1, bit2, constraints), c_i, constraints)
        bv3.set_var(i_3, bit3)
        c_i = g_OR([AND(bit1, bit2, constraints), AND(bit1, c_i, constraints), AND(bit2, c_i, constraints)],
                   constraints)
    bv3.set_var(0, c_i)

    if input_bv3 is not None:
        for i in range(bv3.width):
            r_i = bv3.width - 1
            r_adjusted_i = input_bv3.width - 1 - i
            if r_adjusted_i >= 0:
                constraints.append([IFF(input_bv3.get_var(r_adjusted_i), bv3.get_var(r_i), constraints)])

        if bv3.width < input_bv3.width:
            for i in range(input_bv3.width, bv3.width):
                constraints.append([IFF(input_bv3.get_var(i), FALSE(), constraints)])
    return bv3


'''
Define addition operator that consider only the high bits of bv1 and bv2, the result is constraint
  on the upper bound of bv1 + bv2. 
'''


def add_upper(bv1, bv2, constriant=global_inv, bv3=None, forward=True, backward=False, upper_bound=-1):
    if bv1.width < bv2.width:
        bv1.self_extend(bv2.width - bv1.width)
    elif bv1.width > bv2.width:
        bv2.self_extend(bv1.width - bv2.width)
    assert bv1.width == bv2.width
    if bv3 is None:
        if upper_bound >= 0:
            bv3 = new_bv(min(bv1.width + 1, upper_bound))
        else:
            bv3 = new_bv(bv1.width + 1)
        new_bv3 = bv3
    else:
        diff = (bv1.width + 1) - bv3.width
        if diff > 0:
            new_bv3 = bv3.extend(diff, is_zeros=True)
        elif diff < 0:
            new_bv3 = sub_bv(bv3, bv3.width - bv1.width - 1, bv3.width)
        else:
            new_bv3 = bv3

    except_lit = FALSE()
    if upper_bound > 0:
        except_lits = []
        if bv1.width + 1 > upper_bound:
            except_lits += [bv1.get_var(i) for i in range(bv1.width - upper_bound + 1)]
            bv1 = sub_bv(bv1, bv1.width - (upper_bound - 1), bv1.width)
        if bv2.width + 1 > upper_bound:
            except_lits += [bv2.get_var(i) for i in range(bv2.width - upper_bound + 1)]
            bv2 = sub_bv(bv2, bv2.width - (upper_bound - 1), bv2.width)
        if bv3.width > upper_bound:
            new_bv3 = sub_bv(bv3, bv3.width - upper_bound, bv3.width)
        except_lit = g_OR(except_lits, constriant, backward=forward, forward=backward)

    constriant.append([_add_upper(bv1, bv2, new_bv3, constriant, forward=forward, backward=backward,
                                  over_flows=except_lit)])
    return bv3


def const_to_bv(const):
    body = N_to_bit_array(const)
    return BV(len(body), [ntob(b) for b in body])


def add_mono(bv1, bv2, constraint=global_inv, bv3=None):
    if isinstance(bv1, int):
        bv1 = const_to_bv(bv1)
    if isinstance(bv2, int):
        bv2 = const_to_bv(bv2)

    bv3 = add_lower(bv1, bv2, constraint, bv3)
    add_upper(bv1, bv2, constraint, bv3)
    return bv3


def minus_mono(bv1, bv2, constraint):
    if isinstance(bv1, int):
        bv1 = const_to_bv(bv1)
    if isinstance(bv2, int):
        bv2 = const_to_bv(bv2)

    # ensure bv1 is one more bit than bv2
    if bv1.width <= bv2.width:
        bv1 = bv1.extend(bv2.width + 1 - bv1.width)

    if bv2.width < bv1.width + 1:
        bv2 = bv2.extend(bv1.width - 1 - bv2.width)

    bv3 = new_bv(bv1.width - 1)
    bv1 = add_lower(bv3, bv2, constraint, bv1)
    add_upper(bv2, bv3, constraint, bv1)
    return bv3


def minus(bv1, bv2, constraint, bv3):
    if isinstance(bv1, int):
        bv1 = const_to_bv(bv1)
    if isinstance(bv2, int):
        bv2 = const_to_bv(bv2)

    # ensure bv1 is one more bit than bv2
    if bv1.width <= bv2.width:
        bv1 = bv1.extend(bv2.width + 1 - bv1.width)

    if bv2.width < bv1.width + 1:
        bv2 = bv2.extend(bv1.width - 1 - bv2.width)

    bv3 = new_bv(bv1.width - 1)
    new_bv1 = add(bv3, bv2, constraint)
    return Equal(bv1, new_bv1, constraint)


def bv_and(bv1, bit, constraints):
    if isinstance(bv1, int):
        bv1 = const_to_bv(bv1)
    return BV(bv1.width, [AND(bv1.get_var(id), bit, constraints) for id in range(bv1.width)])


'''
Define addition operator that consider only the high bits of bv1 and bv2, the result is constraint
  on the lower bound of bv1 + bv2. 
'''


def add_lower(bv1, bv2, constriant=global_inv, bv3=None):
    if bv1.width < bv2.width:
        bv1.self_extend(bv2.width - bv1.width)
    elif bv1.width > bv2.width:
        bv2.self_extend(bv1.width - bv2.width)
    assert bv1.width == bv2.width
    if bv3 is None:
        bv3 = new_bv(bv1.width + 1)
        new_bv3 = bv3
    else:
        diff = (bv1.width + 1) - bv3.width
        if diff > 0:
            new_bv3 = bv3.extend(diff, is_zeros=True)
        elif diff < 0:
            new_bv3 = sub_bv(bv3, bv3.width - bv1.width - 1, bv3.width)
        else:
            new_bv3 = bv3

    # constriant.append([_add_lower(bv1,bv2,new_bv3, bv1.width, zeros(bv1.width+1, dtype=int), constriant)])
    constriant.append([_add_lower(bv1, bv2, new_bv3, constriant)])
    return new_bv3


def _get_lower_bound_condition(bv1, bv2, bv3, i, constraint, storage=None):
    res = storage.get(i, None)
    if res is not None:
        return res
    else:
        if i == 0:
            return bv3.get_var(0)
        else:
            b1 = bv1.get_var(i - 1)
            b2 = bv2.get_var(i - 1)
            b3 = bv3.get_var(i)
            acceptance_condition = g_AND([-b1, -b2, b3], constraint, forward=False)
            valid_condition = g_OR([-b1, -b2, b3], constraint, forward=False)
            prev_res = _get_lower_bound_condition(bv1, bv2, bv3, i - 1, constraint, storage)
            result = OR(acceptance_condition, AND(prev_res, valid_condition, constraint, forward=False), constraint,
                        forward=False)

            storage[i] = result
            return result


def _add_lower(bv1, bv2, bv3, constraint=global_inv):
    if (bv1.width == 0):
        return TRUE()

    carry_on = FALSE()
    carries = [carry_on]
    rules = []
    for r_i in range(bv1.width):
        i = bv1.width - 1 - r_i
        bit1 = bv1.get_var(i)
        bit2 = bv2.get_var(i)
        carry_on = OR(AND(carry_on, OR(bit1, bit2, constraint, backward=False), constraint),
                      AND(bit1, bit2, constraint, backward=False), constraint, backward=False)
        carries.append(carry_on)
    carries.reverse()
    cache_storage = dict()
    for r_i in range(bv1.width):
        i = bv1.width - 1 - r_i
        bit1 = bv1.get_var(i)
        bit2 = bv2.get_var(i)
        bit3 = bv3.get_var(i + 1)
        contain_bit = g_OR([bit1, bit2, carries[i + 1]], constraint, backward=False)
        rules.append(
            IMPLIES(g_AND([bit1, bit2, carries[i + 1]], constraint, backward=False), bit3, constraint, forward=False))
        acceptance_condition = _get_lower_bound_condition(bv1, bv2, bv3, i, constraint, storage=cache_storage)
        rules.append(IMPLIES(contain_bit, OR(bit3, acceptance_condition, constraint), constraint, forward=False))

    rules.append(IMPLIES(carries[0], bv3.get_var(0), constraint, forward=False))

    return g_AND(rules, constraint, forward=False)


def _get_upper_bound_condition(bv1, bv2, bv3, Ncarries_overs, i, constraint, storage=None):
    res = storage.get(i, None)
    if res is not None:
        return res
    else:
        if i == bv1.width:
            return FALSE()
        else:
            b1 = bv1.get_var(i)
            b2 = bv2.get_var(i)
            b3 = bv3.get_var(i + 1)
            acceptance_condition = g_AND([b1, b2, -b3], constraint, forward=False)
            valid_condition = AND(IMPLIES(OR(-b1, -b2, constraint, forward=False), -b3, constraint, forward=False),
                                  -Ncarries_overs[i], constraint, forward=False)
            prev_res = _get_upper_bound_condition(bv1, bv2, bv3, Ncarries_overs, i + 1, constraint, storage)
            result = OR(acceptance_condition, AND(prev_res, valid_condition, constraint, forward=False), constraint,
                        forward=False)

            storage[i] = result
            return result


def _add_upper(bv1, bv2, bv3, constraint=global_inv, forward=True, backward=False, over_flows=None):
    index = bv1.width
    t_AND = lambda a, b, constraint: AND(a, b, constraint, forward=forward, backward=backward)
    t_OR = lambda a, b, constraint: OR(a, b, constraint, forward=forward, backward=backward)

    rules = []
    NC = TRUE()
    Ncarries_overs = [NC]
    # calculate the NCR bits
    for r_i in range(index):
        i = index - r_i - 1
        bit1 = bv1.get_var(i)
        bit2 = bv2.get_var(i)
        NC = t_OR(t_AND(NC, t_OR(-bit1, -bit2, constraint), constraint), t_AND(-bit1, -bit2, constraint), constraint)
        Ncarries_overs.append(NC)
    Ncarries_overs.reverse()
    cache_storage = dict()
    for r_i in range(index):
        i = index - r_i - 1
        bit1 = bv1.get_var(i)
        bit2 = bv2.get_var(i)
        bit3 = bv3.get_var(i + 1)
        neither_bit = t_AND(-bit1, -bit2, constraint)
        accepted_condition = _get_upper_bound_condition(bv1, bv2, bv3, Ncarries_overs, i + 1, constraint,
                                                        storage=cache_storage)
        rules.append(IMPLIES(neither_bit, OR(-bit3, accepted_condition, constraint), constraint, forward=False))

    accepted_condition = _get_upper_bound_condition(bv1, bv2, bv3, Ncarries_overs, 0, constraint, storage=cache_storage)
    if over_flows is None:
        over_flows = FALSE()
    rules.append(
        OR(-bv3.get_var(0), OR(accepted_condition, over_flows, constraint, forward=False), constraint, forward=False))

    res = g_AND(rules, constraint, forward=False)
    return res


def GE_const(bv1, const, constraints=global_inv):
    return GT_const(bv1, const, constraints, equal=True)


def LT_const(bv1, const, constraints=global_inv):
    return -GE_const(bv1, const, constraints)


def LE_const(bv1, const, constraints=global_inv):
    return -GT_const(bv1, const, constraints, equal=False)


def nomrailize(bv1, bv2):
    diff = bv1.width - bv2.width
    if diff == 0:
        return bv1, bv2
    elif diff > 0:
        padding_BV = BV(bv1.width, [FALSE() for _ in range(diff)] + bv2.get_body())
        return bv1, padding_BV
    else:
        padding_BV = BV(bv2.width, [FALSE() for _ in range(-diff)] + bv1.get_body())
        return padding_BV, bv2


# assume bv1 and bv2 have the same width
# return the constraint showing bv1 > bv2
def GT(bv1, bv2, constraints=global_inv, equal=False):
    if isinstance(bv2, int):
        return GT_const(bv1, bv2, constraints, equal=equal)
    elif isinstance(bv1, int):
        return -GT_const(bv2, bv1, constraints, equal=not equal)

    bv1, bv2 = nomrailize(bv1, bv2)
    assert bv1.width == bv2.width
    gts = []
    ch_c = TRUE()
    width = bv1.width
    for i in range(width):
        gt_c = g_AND([bv1.get_var(i), -bv2.get_var(i), ch_c], constraints)
        ch_c = AND(ch_c, OR(bv1.get_var(i), -bv2.get_var(i), constraints), constraints)
        gts.append(gt_c)

    if equal:
        return g_OR(gts + [ch_c], constraints)
    else:
        return g_OR(gts, constraints)


def GE(bv1, bv2, constraints=global_inv):
    return GT(bv1, bv2, constraints, equal=True)


def LT(bv1, bv2, constraints=global_inv):
    return GT(bv2, bv1, constraints)


def LE(bv1, bv2, constraints=global_inv):
    return GE(bv2, bv1, constraints)


def Equal(bv1, bv2, constraints=global_inv):
    if isinstance(bv1, int):
        return Equal_const(bv2, bv1, constraints)
    if isinstance(bv2, int):
        return Equal_const(bv1, bv2, constraints)
    else:
        if bv1.width < bv2.width:
            bv1.self_extend(bv2.width - bv1.width)
        elif bv1.width > bv2.width:
            bv2.self_extend(bv1.width - bv2.width)
        assert (bv1.width == bv2.width)
        width = bv1.width
        return g_AND([IFF(bv1.get_var(i), bv2.get_var(i), constraints) for i in range(width)], constraints)


def NEqual(bv1, bv2, constraints=global_inv):
    return NOT(Equal(bv1, bv2, constraints))


def Equal_const(bv1, const, constraints=global_inv):
    if isinstance(bv1, int):
        if bv1 == const:
            return TRUE()
        else:
            return FALSE()
    else:
        const_bv = N_to_bit_array(const, bv1.width)
        width = bv1.width
        return g_AND([IFF(bv1.get_var(i), ntob(const_bv[i]), constraints) for i in range(width)], constraints)


def NEQ_const(bv1, const, constraint=global_inv):
    return NOT(Equal_const(bv1, const, constraint))


def get_bound_sign(op):
    if op == GE or op == GT:
        return False, True
    if op == LE or op == LT:
        return True, False
    else:
        # unsupported
        assert False


def negate(op):
    if op == GE:
        return LT
    if op == GT:
        return LE
    if op == LT:
        return GE
    if op == Equal:
        return NEqual
    if op == NEqual:
        return Equal
    else:
        # unsupport negate
        assert False


def _parse_by_op(instr, op):
    tokens = instr.split(op)
    bv_id, v = tokens[0], tokens[1]
    bv1 = BV.Bvs[int(bv_id)]
    value = int(v)
    return (op, bv1, value)


def op_to_str(op):
    if op == GT:
        return ">"
    elif op == GE:
        return ">="
    elif op == LE:
        return "<="
    elif op == LT:
        return "<"
    elif op == Equal:
        return "=="
    elif op == NEqual:
        return "!="


def parse_bv_compare_signature(hint_str):
    hint_str = hint_str.lstrip("bv ")
    if '>=' in hint_str:
        return _parse_by_op(hint_str, '>=')
    elif '<=' in hint_str:
        return _parse_by_op(hint_str, '<=')


def extract_bv_witness(witness):
    steps, hints = witness
    steps = steps.split(',')
    processed = []
    for i in range(len(steps)):
        s = steps[i]
        refine_s = s.split(';')
        processed.extend(refine_s)

    final_processed = []
    current_step = None
    current_lit_dep = []
    last_dep = 0
    current_dep = 0

    current_addition = None
    for s in processed:
        if s.startswith("bv"):
            if current_step is not None:
                # add what we have recoreded into the collection
                final_processed.append((current_step, current_lit_dep, current_addition))
                last_dep = current_dep
                current_addition = None
            current_step = parse_bv_compare_signature(s)
        elif s.startswith('#'):
            current_dep = int(s.lstrip('#'))
            current_lit_dep = hints[last_dep:current_dep]
        elif s.startswith(":"):
            sub_processed = s.lstrip(':').rstrip('+').split('=')
            sum_id, other_id = sub_processed[0], sub_processed[1]
            current_addition = (sum_id, other_id)
        else:
            print("unrecongized hint, skip")
            continue

    final_processed.append((current_step, current_lit_dep, current_addition))
    return final_processed


class GE_DEP_node:

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
        self.deps = set()
        self.support_lit = []
        self.causes = None
        self.vc = FALSE()

    def add_dep(self, dep):
        assert isinstance(dep, GE_DEP_node)
        self.deps.add(dep)

    def encode(self, constraints):
        # in case what we have is a root
        if not self.deps:
            # in case if both are non-BV
            if isinstance(self.lhs, BV):
                assert not isinstance(self.rhs, BV)
                # in this case, we need to create a new BV
                return GT_const_strict(self.lhs, self.rhs, constraints, equal=True)
            elif isinstance(self.rhs, BV):
                assert  not isinstance(self.lhs, BV)
                return LT_const_strict(self.rhs, self.lhs, constraints, equal=True)
            else:
                return TRUE() if self.lhs >= self.rhs else FALSE()
        else:
            if self.causes == "ADD":
                valid =  g_AND([dep.encode(constraints) for dep in self.deps], constraints)
                return AND(valid, self.vc)

            else:
                #Supported
                return False


def process_bv_addition_hint(cur_ge_node, op, sum_bv, part_bv, ubs, lbs, constraints):
    if op == ">=":
        bv = cur_ge_node.lhs
        constant = cur_ge_node.rhs
        if bv == part_bv:
            # in this case, we have a self addition
            assert lbs[sum_bv].rhs >= constant * 2
            cur_ge_node.deps.add(lbs[sum_bv])
            cur_ge_node.vc = GE(lbs[sum_bv].rhs, constant + constant, constraints)
        else:
            # in this case, we have a non self addition
            assert lbs[sum_bv].rhs - ubs[part_bv].lhs >= constant
            cur_ge_node.deps.add(lbs[sum_bv])
            cur_ge_node.deps.add(ubs[part_bv])
            cur_ge_node.vc = GE(lbs[sum_bv].rhs - ubs[part_bv].lhs, constant, constraints)
    elif op == "<=":
        bv = cur_ge_node.rhs
        constant = cur_ge_node.lhs
        if bv == part_bv:
            assert ubs[sum_bv].lhs <= constant * 2
            cur_ge_node.deps.add(ubs[sum_bv])
            cur_ge_node.vc = LE(ubs[sum_bv].lhs, constant + constant, constraints)
        else:
            # in this case, we have a non-self addition
            assert ubs[sum_bv].lhs - lbs[part_bv].rhs <= constant
            cur_ge_node.deps.add(ubs[sum_bv])
            cur_ge_node.deps.add(lbs[part_bv])
            cur_ge_node.vc = LE(ubs[sum_bv].lhs - lbs[part_bv].rhs, constant, constraints)


def build_dependency_graph(processed_dep, root, lit, constraints):
    root_op, bv1, bv2 = root
    ubs = {}
    lbs = {}

    for i in range(len(processed_dep) - 1, -1, -1):
        op, bv, value = processed_dep[i][0]
        dep = processed_dep[i][1]
        addition_info = processed_dep[i][2]
        if lit in dep:
            # then the step should be  invalidated, skip
            continue
        if op == ">=":
            cur_node = GE_DEP_node(bv, value)
            cur_node.support_lit = dep
            if bv in lbs:
                if cur_node.rhs > lbs[bv].rhs:
                    lbs[bv] = cur_node
            else:
                lbs[bv] = cur_node

            # time to process additional info
            if addition_info is not None:
                sum_bv_id, part_bv_id = addition_info
                sum_bv = BV.Bvs[int(sum_bv_id)]
                part_bv = BV.Bvs[int(part_bv_id)]
                process_bv_addition_hint(cur_node, op, sum_bv, part_bv, ubs, lbs, constraints)
                cur_node.causes = "ADD"

        elif op == "<=":
            cur_node = GE_DEP_node(value, bv)
            if bv in ubs:
                if cur_node.lhs < ubs[bv].lhs:
                    ubs[bv] = cur_node
            else:
                ubs[bv] = cur_node

    if root_op == GE:
        assert lbs[bv1].rhs >= ubs[bv2].lhs
        lc_v = lbs[bv1].encode(constraints)
        rc_v = ubs[bv2].encode(constraints)
        return g_AND([GE( lbs[bv1].rhs, ubs[bv2].lhs, constraints),lc_v, rc_v ],constraints)
    elif root_op == GT:
        assert lbs[bv1].rhs > ubs[bv2].lhs
        lc_v = lbs[bv1].encode(constraints)
        rc_v = ubs[bv2].encode(constraints)
        return g_AND([GT(lbs[bv1].rhs, ubs[bv2].lhs, constraints), lc_v, rc_v], constraints)
    elif root_op == LE:
        assert ubs[bv1].lhs <= lbs[bv2].rhs
        lc_v = ubs[bv1].encode(constraints)
        rc_v = lbs[bv2].encode(constraints)
        return g_AND([LE(ubs[bv1].lhs, lbs[bv2].rhs, constraints), lc_v, rc_v], constraints)
    elif root_op == LT:
        assert ubs[bv1].lhs < lbs[bv2].rhs
        lc_v = ubs[bv1].encode(constraints)
        rc_v = lbs[bv2].encode(constraints)
        return g_AND([LT(ubs[bv1].lhs, lbs[bv2].rhs, constraints), lc_v, rc_v], constraints)


class Comparsion():
    Collection = {}
    Lit_Collection = {}

    def __init__(self, bv1, bv2, op, lit=None):
        self.bv1 = bv1
        self.bv2 = bv2

        if op == ">=":
            self.op = GE
        elif op == ">":
            self.op = GT
        elif op == "<=":
            self.op = LE
        elif op == "<":
            self.op = LT
        elif op == "==":
            self.op = Equal
        elif op == "!=":
            self.op = NEqual
        else:
            print("unsupported comparsion")
            assert (False)

        self.encoded = False
        if lit is None:
            self.lit = new_lit()
        else:
            self.lit = lit
        Comparsion.Collection[(bv1.id, bv2.id, op)] = self
        Comparsion.Lit_Collection[self.lit] = self

    def __repr__(self):
        return "{} {} {}".format(self.bv1.__repr__(), op_to_str(self.op), self.bv2.__repr__())

    def encode(self, constraints=global_inv):
        if self.encoded:
            return self.lit
        else:
            if self.op == Equal:
                term1 = Comparsion.Collection.get((self.bv1.id, self.bv2.id, ">="), None)
                term2 = Comparsion.Collection.get((self.bv1.id, self.bv2.id, "<="), None)
                if term1 and term2:
                    term1.encode(constraints)
                    term2.encode(constraints)
                    constraints.append([IFF(self.lit, AND(term1.lit, term2.lit, constraints), constraints)])
                    self.encoded = True
                    return self.lit
            elif self.op == NEqual:
                term = Comparsion.Collection.get((self.bv1.id, self.bv2, "=="), None)
                if term:
                    term.encode()
                    constraints.append([IFF(self.lit, -term.lit, constraints)])
                    self.encoded = True
                    return self.lit

            result_p = self.op(self.bv1, self.bv2, constraints)
            constraints.append([IFF(self.lit, result_p, constraints)])
            self.encoded = True
            return self.lit

    def encode_witness(self, hints, polarity, constraints, witness=None):

        if not polarity:
            op = negate(self.op)
        else:
            op = self.op

        result = self.lit if polarity else -self.lit

        if witness is not None:
            processed_witness = extract_bv_witness(witness)
            encoded = build_dependency_graph(processed_witness, (op, self.bv1, self.bv2), result, constraints)
            if encoded is not False:
                return encoded

        lhs_bound, rhs_bound = get_bound_sign(op)

        # update bound
        bv1_ub, bv1_lb = self.bv1.get_bound(hints)
        bv2_ub, bv2_lb = self.bv2.get_bound(hints)

        if lhs_bound and not rhs_bound:
            condition1 = op(bv1_ub, bv2_lb, constraints)
            if condition1 == FALSE():
                return False
            # bv1 <= bv1_ub  (not (bv1 > bv1_ub))
            condition2 = NOT(GT_const_strict(self.bv1, bv1_ub, constraints, equal=False))
            condition3 = GT_const_strict(self.bv2, bv2_lb, equal=True)
            constraints.append([IMPLIES(AND([condition1, condition2, condition3], constraints), result)])
        if not lhs_bound and rhs_bound:
            condition1 = op(bv1_lb, bv2_ub, constraints)
            if condition1 == FALSE():
                return False
            # bv1 >= bv1_lb
            condition2 = GT_const_strict(self.bv1, bv1_lb, equal=True)
            # bv2 <= bv2_ub  (not (bv2 > bv2_ub))
            condition3 = NOT(GT_const_strict(self.bv2, bv2_ub, constraints, equal=False))
            constraints.append([IMPLIES(g_AND([condition1, condition2, condition3], constraints), result)])

        return result


def add_compare(bv1, bv2, op, lit, constraints=global_inv):
    if isinstance(bv1, int):
        bv1 = get_bv(bv1)
    if isinstance(bv2, int):
        bv2 = get_bv(bv2)

    compare = Comparsion.Collection.get((bv1.id, bv2.id, op), None)
    if compare is None:
        compare = Comparsion(bv1, bv2, op, lit)
        return compare
    else:
        if compare.lit != lit:
            Delayed_Equality.append((compare.lit, lit))
        return compare


def add_compare_const(bv1, const, op, lit):
    if isinstance(bv1, int):
        bv1 = get_bv(bv1)

    compare = Comparsion_const.Collection.get((bv1.id, const, op), None)
    if compare is None:
        compare = Comparsion_const(bv1, const, op, lit)
        return compare
    else:
        if compare.lit != lit:
            return EQ(compare.lit, lit)
        else:
            return compare


class Comparsion_const():
    Collection = {}
    Lit_Collection = {}

    def __init__(self, bv1, const, op, lit=None):
        self.bv1 = bv1
        self.const = const

        if op == ">=":
            self.op = GE_const
        elif op == ">":
            self.op = GT_const
        elif op == "<=":
            self.op = LE_const
        elif op == "<":
            self.op = LT_const
        elif op == "==":
            self.op = Equal_const
        elif op == "!=":
            self.op = NEQ_const
        else:
            print("unsupported comparsion")
            assert (False)

        self.encoded = False
        if lit is None:
            self.lit = new_lit()
        else:
            self.lit = lit
        Comparsion_const.Collection[(bv1.id, const, op)] = self
        Comparsion_const.Lit_Collection[self.lit] = self

    def encode(self, constraints=global_inv):
        if self.encoded:
            return self.lit
        else:
            if self.op == Equal_const:
                term1 = Comparsion_const.Collection.get((self.bv1.id, self.const, ">="), None)
                term2 = Comparsion_const.Collection.get((self.bv1.id, self.const, "<="), None)
                if term1 and term2:
                    term1.encode(constraints)
                    term2.encode(constraints)
                    constraints.append([IFF(self.lit, AND(term1.lit, term2.lit, constraints), constraints)])
                    self.encoded = True
                    return self.lit
            elif self.op == NEQ_const:
                term = Comparsion_const.Collection.get((self.bv1.id, self.const, "=="), None)
                if term:
                    term.encode()
                    constraints.append([IFF(self.lit, -term.lit, constraints)])
                    self.encoded = True
                    return self.lit

            result_p = self.op(self.bv1, self.const, constraints)
            constraints.append([IFF(self.lit, result_p, constraints)])
            self.encoded = True
            return self.lit


def is_compare_predicate(l):
    if l in Comparsion.Lit_Collection:
        return (Comparsion.Lit_Collection[l], True)
    elif -l in Comparsion.Lit_Collection:
        return (Comparsion.Lit_Collection[-l], False)
    elif l in Comparsion_const.Lit_Collection:
        return (Comparsion_const.Lit_Collection[l], True)
    elif -l in Comparsion_const.Lit_Collection:
        return (Comparsion_const.Lit_Collection[-l], False)
    else:
        return None


def check_compare_lemma(lemma, constraints, sup):
    predicates = []
    others = []
    for l in lemma:
        result = is_compare_predicate(l)
        if result is not None:
            predicates.append(result)
        else:
            others.append(l)
    if len(predicates) == 0:
        return True
    elif len(predicates) < 2:
        main_predicate = predicates[0]
        if isinstance(main_predicate, Comparsion_const):
            return False
        else:
            p, polarity = main_predicate
            # if number of predicates are less one, then we can prove the lemma via DRUP
            result = p.encode_witness(set([-l for l in others]), polarity, constraints, witness=sup)
            if result == False:
                return True
            else:
                return False
    else:
        return True


def check_lemma_out_scope(lemma):
    predicate = lemma[-1]
    if predicate != 0:
        compare = None
        if predicate in Comparsion.Lit_Collection:
            compare = Comparsion.Lit_Collection[predicate]
            inputs = set(compare.bv1.get_body() + compare.bv2.get_body())
        elif -predicate in Comparsion.Lit_Collection:
            compare = Comparsion.Lit_Collection[-predicate]
            inputs = set(compare.bv1.get_body() + compare.bv2.get_body())
        elif predicate in Comparsion_const.Lit_Collection:
            compare = Comparsion_const.Lit_Collection[predicate]
            inputs = set(compare.bv1.get_body())
        elif -predicate in Comparsion_const.Lit_Collection:
            compare = Comparsion_const.Lit_Collection[-predicate]
            inputs = set(compare.bv1.get_body())

        if not compare:
            return False
        else:
            # now we need to ensure everything else is a input to the predicate
            for i in lemma[:-1]:
                if i in inputs or -i in inputs:
                    continue
                else:
                    return True
        return False


class EQ():
    Collection = {}

    def __init__(self, a, b):
        self.a = a
        self.b = b
        EQ.Collection[(a, b)] = self
        EQ.Collection[(b, a)] = self
        self.result = None

    def encode(self, constraints=global_inv):
        if self.result is None:
            self.result = IFF(self.a, self.b, constraints)
            constraints.append([self.result])
        return self.result


class ADD():
    Collection = {}

    def __init__(self, result, bv1, bv2):
        self.result = result
        self.bv1 = bv1
        self.bv2 = bv2
        self.encoded = False
        ADD.Collection[result] = self

    def encode(self, constraints=global_inv):
        if not self.encoded:
            add_mono(self.bv1, self.bv2, constraints, self.result)
            self.encoded = True


def add_Add(result, bv1, bv2):
    if isinstance(bv1, int):
        bv1 = get_bv(bv1)
    if isinstance(bv2, int):
        bv2 = get_bv(bv2)
    if isinstance(result, int):
        result = get_bv(result)
    return ADD(result, bv1, bv2)


def parse_const_comparsion(attributes):
    head = attributes[0]
    if head in [">=", "<=", ">", "<", "==", "!="]:
        assert (len(attributes) == 4)
        op, lit, bv, const = attributes
        add_compare_const(int(bv), int(const), op, add_lit(int(lit)))
    else:
        # add a const bv
        assert len(attributes) == 3
        bv_id, bv_width, bv_value = attributes
        const_bv(int(bv_id), int(bv_width), int(bv_value))

    return True


from sortedcontainers import SortedList


def bv_sum(items, constraints, mono=True, is_dir_specific=True, smart_encoding=-1,
           smart_finishing=False, duo=False, upper_bound=-1, linear=False):
    if linear:
        if upper_bound >= 0:
            base_int = 0
            base_bv = const_to_bv(0)
            reverse_item = reversed(items)
            for item in reverse_item:
                if isinstance(item, int):
                    base_int += items
                else:
                    base_bv = add_upper(base_bv, item, constraints, backward=False, forward=True,
                                        upper_bound=upper_bound)

            if base_int == 0:
                return base_bv
            else:
                return add_upper(base_bv, const_to_bv(base_int), constraints,
                                 backward=False, forward=True, upper_bound=upper_bound)
        else:
            print("unsupported linear mode when the upper bound is not capped")
            assert False
    else:
        # if smart encoding is enabled, then each bv is associated with a depth
        bv_depth = {}
        # organize elements to determine summing order
        base_int = 0
        bv_items = SortedList(key=lambda bv: bv.width)
        for item in items:
            if isinstance(item, int):
                base_int += items
            elif isinstance(item, BV):
                bv_items.add(item)
                if smart_encoding >= 0:
                    bv_depth[item] = 0
            else:
                assert False

        if not bv_items:
            return base_int
        else:
            cur = bv_items.pop(0)
            while bv_items:
                next = bv_items.pop(0)
                if smart_encoding >= 0:
                    cur_depth = bv_depth.get(cur, 0)
                    next_depth = bv_depth.get(next, 0)
                    max_depth = max(cur_depth, next_depth)
                    if max_depth > smart_encoding or (smart_finishing and len(bv_items) <= 1):
                        new_item = add_upper(cur, next, constraints, backward=False, forward=True,
                                             upper_bound=upper_bound)
                    else:
                        new_item = add(cur, next, constraints)
                    bv_depth[new_item] = max_depth + 1
                else:
                    if mono:
                        if is_dir_specific:
                            new_item = add_upper(cur, next, constraints, backward=False, forward=True,
                                                 upper_bound=upper_bound)
                        else:
                            new_item = add_mono(cur, next, constraints)
                    else:
                        if duo:
                            new_item = add(cur, next, constraints)
                            new_item = add_upper(cur, next, constraints, bv3=new_item, backward=False, forward=True,
                                                 upper_bound=upper_bound)
                        else:
                            new_item = add(cur, next, constraints)

                bv_items.add(new_item)
                cur = bv_items.pop(0)
            if base_int == 0:
                return cur
            else:
                if mono:
                    if is_dir_specific:
                        return add_upper(cur, const_to_bv(base_int), constraints, backward=False, forward=True,
                                         upper_bound=upper_bound)
                    else:
                        return add_mono(cur, const_to_bv(base_int), constraints)
                else:
                    return add(cur, const_to_bv(base_int), constraints)


def parse_comparsion(attributes):
    assert (len(attributes) == 4)
    op, lit, bv1, bv2 = attributes
    add_compare(int(bv1), int(bv2), op, add_lit(int(lit)))
    return True


def parse_addition(attributes):
    assert (len(attributes) == 3)
    result, bv1, bv2 = attributes
    add_Add(int(result), int(bv1), int(bv2))
    return True


def parse_bv(attributes):
    assert (len(attributes) >= 2)
    id = attributes[0]
    width = attributes[1]
    assert (len(attributes) == int(width) + 2)
    BV(int(width), [add_lit(int(i)) for i in (attributes[2:])[::-1]], int(id))
    return True


def check_lemma_bv_reasoning(lemma):
    for l in lemma:
        if (l not in Comparsion.Lit_Collection) and (l not in Comparsion_const.Lit_Collection) and (
                -l not in Comparsion.Lit_Collection) and (-l not in Comparsion_const.Lit_Collection):
            return False

    return True


def reset():
    BV.Bvs = {}
