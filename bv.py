from lit import *
from logic_gate import *
from numpy import zeros

class BV():
    Bvs = {}
    def __init__(self, width, body, id =None):
        assert width == 0 or len(body) == width

        if body is None and width != 0:
            #this is the case for unassigned BV
            self.assigned = False
        else:
            self.assigned = True

        self.width = width
        self.body = body
        self.parent = None
        if id == None:
            self.id = len(BV.Bvs)
        else:
            self.id = id
        BV.Bvs[id] = self

    def assign(self):
        if not self.assigned:
            self.body = [new_lit() for _ in self.width]
            self.assigned = True

    def get_var(self, index):
        self.assign()
        assert(index < self.width)
        return self.body[index]

    def set_var(self, index, var):
        self.assign()
        assert (index < self.width)
        self.body[index] = var

    def extend(self, padding_num):
        self.assign()
        return BV(self.width+padding_num, [new_lit() for _ in range(padding_num)] + self.body)

    def self_extend(self, padding_num, pad=FALSE):
        self.assign()
        self.width = self.width+padding_num
        self.body = [pad() for _ in range(padding_num)] + self.body

def get_bv(id):
    return BV.Bvs.get(id)

def sub_bv(bv, start, end):
    return BV(end-start, bv.body[start:end])


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


def N_to_bit_array(const, width = -1):
    inter = bin(const)[2:]
    if width != -1:
        assert (len(inter) <= width)
        inter = inter.zfill(width)
    return [0  if b == '0' else 1 for b in inter]

def ntob(num):
    if num:
        return TRUE()
    else:
        return FALSE()

def GT_const_strict(bv1, const, constraints=global_inv, equal = False):
    if not equal:
        const = const + 1
    const_bv = N_to_bit_array(const, bv1.width)
    return g_AND([bv1.get_var(i) for i in range(len(const_bv)) if const_bv[i] == 1], constraints)


def LT_const_strict(bv1, const, constraints=global_inv, equal = False):
    if not equal:
        const = const -1
    const_bv = N_to_bit_array(const, bv1.width)
    return g_AND([-bv1.get_var(i) for i in range(len(const_bv)) if const_bv[i] == 0], constraints)

def GT_const(bv1, const, constraints=global_inv, equal = False):
    if isinstance(bv1, int):
        if equal:
            return bv1 >= const
        else:
            return bv1 > const
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

def add(bv1, bv2, constraints=global_inv):
    if isinstance(bv1, int):
        bv1 = const_to_bv(bv1)
    if isinstance(bv2, int):
        bv2 = const_to_bv(bv2)

    if bv1.width < bv2.width:
        bv1.self_extend(bv2.width - bv1.width)
    elif bv1.width > bv2.width:
        bv2.self_extend(bv1.width - bv2.width)

    assert bv1.width == bv2.width
    bv3 = new_bv(bv1.width+1, set_var=False)
    c_i = FALSE()
    for r_i in range(bv1.width):
        i = bv1.width-1-r_i
        i_3 = i  +1
        bit1 = bv1.get_var(i)
        bit2 = bv2.get_var(i)
        bit3 = XOR(XOR(bit1,bit2, constraints), c_i, constraints)
        bv3.set_var(i_3, bit3)
        c_i = g_OR([AND(bit1,bit2, constraints), AND(bit1, c_i, constraints), AND(bit2, c_i, constraints)], constraints)
    bv3.set_var(0, c_i)
    return bv3

'''
Define addition operator that consider only the high bits of bv1 and bv2, the result is constraint
  on the upper bound of bv1 + bv2. 
'''
def add_upper(bv1, bv2, constriant=global_inv, bv3=None):
    if bv1.width < bv2.width:
        bv1.self_extend(bv2.width - bv1.width)
    elif bv1.width > bv2.width:
        bv2.self_extend(bv1.width - bv2.width)
    assert bv1.width == bv2.width
    if bv3 is None:
        bv3 = new_bv(bv1.width+1)
        new_bv3 = bv3
    else:
        assert bv3.width > bv1.width
        new_bv3 = sub_bv(bv3, bv3.width - bv1.width-1, bv3.width)

    constriant.append([_add_upper(bv1,bv2,new_bv3, constriant)])
    return bv3

def const_to_bv(const):
    body = N_to_bit_array(const)
    return BV( len(body), [ntob(b) for b in body])


def add_mono(bv1, bv2, constraint=global_inv, bv3 = None):
    if isinstance(bv1, int):
        bv1 = const_to_bv(bv1)
    if isinstance(bv2, int):
        bv2 = const_to_bv(bv2)

    bv3 = add_lower(bv1, bv2, constraint, bv3)
    add_upper(bv1, bv2, constraint, bv3)
    return bv3


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
        bv3 = new_bv(bv1.width+1)
        new_bv3 = bv3
    else:
        assert bv3.width > bv1.width
        new_bv3 = sub_bv(bv3, bv3.width - bv1.width-1, bv3.width)

    #constriant.append([_add_lower(bv1,bv2,new_bv3, bv1.width, zeros(bv1.width+1, dtype=int), constriant)])
    constriant.append([_add_lower(bv1, bv2, new_bv3, constriant)])
    return bv3

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
            prev_res = _get_lower_bound_condition(bv1, bv2, bv3, i-1, constraint, storage)
            result = OR(acceptance_condition, AND(prev_res, valid_condition, constraint, forward=False), constraint, forward=False)

            storage[i] = result
            return result


def _add_lower(bv1, bv2, bv3, constraint = global_inv):

    if (bv1.width == 0):
        return TRUE()

    carry_on = FALSE()
    carries = [carry_on]
    rules = []
    for r_i in range(bv1.width):
        i = bv1.width - 1 - r_i
        bit1 = bv1.get_var(i)
        bit2 = bv2.get_var(i)
        carry_on = OR(AND(carry_on, OR(bit1, bit2, constraint, backward=False), constraint), AND(bit1, bit2, constraint, backward=False), constraint, backward=False)
        carries.append(carry_on)
    carries.reverse()
    cache_storage = dict()
    for r_i in range(bv1.width):
        i = bv1.width - 1 - r_i
        bit1 = bv1.get_var(i)
        bit2 = bv2.get_var(i)
        bit3 = bv3.get_var(i+1)
        contain_bit = g_OR([bit1, bit2, carries[i+1]], constraint, backward=False)
        rules.append(IMPLIES(g_AND([bit1, bit2, carries[i+1]], constraint, backward=False) , bit3, constraint, forward=False))
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
            b1 = bv1.get_var(i )
            b2 = bv2.get_var(i )
            b3 = bv3.get_var(i+1)
            acceptance_condition = g_AND([b1, b2, -b3], constraint, forward=False)
            valid_condition = AND(IMPLIES(OR(-b1, -b2, constraint, forward=False), -b3, constraint, forward=False),
                                                             -Ncarries_overs[i], constraint, forward=False)
            prev_res = _get_upper_bound_condition(bv1, bv2, bv3, Ncarries_overs, i+1, constraint, storage)
            result = OR(acceptance_condition, AND(prev_res, valid_condition, constraint, forward=False), constraint, forward=False)

            storage[i] = result
            return result

def _add_upper(bv1, bv2, bv3, constraint=global_inv, forward=True, backward=False):

    index = bv1.width
    t_AND = lambda a, b, constraint : AND(a,b,constraint, forward=forward, backward=backward)
    t_OR = lambda a, b, constraint: OR(a, b, constraint, forward=forward, backward=backward)

    rules = []
    NC = TRUE()
    Ncarries_overs = [NC]
    #calculate the NCR bits
    for r_i in range(index):
        i = index-r_i-1
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
        bit3 = bv3.get_var(i+1)
        neither_bit = t_AND(-bit1, -bit2, constraint)
        accepted_condition = _get_upper_bound_condition(bv1, bv2, bv3, Ncarries_overs, i+1, constraint, storage=cache_storage)
        rules.append(IMPLIES(neither_bit, OR(-bit3, accepted_condition, constraint), constraint, forward=False))


    accepted_condition = _get_upper_bound_condition(bv1, bv2, bv3, Ncarries_overs, 0, constraint, storage=cache_storage)
    rules.append( OR(-bv3.get_var(0), accepted_condition, constraint, forward=False))

    res = g_AND(rules, constraint, forward=False)
    return res





def GE_const(bv1, const, constraints=global_inv):
    return GT_const(bv1, const, constraints, equal=True)

def LT_const(bv1, const, constraints=global_inv):
    return -GE_const(bv1, const, constraints)

def LE_const(bv1, const, constraints= global_inv):
    return -GT_const(bv1, const, constraints, equal=False)



def nomrailize(bv1, bv2):
    diff = bv1.width  - bv2.width
    if diff == 0:
        return bv1, bv2
    elif diff > 0:
        padding_BV = BV(bv1.width, [FALSE() for _ in range(diff)] + bv2.body)
        return bv1, padding_BV
    else:
        padding_BV = BV(bv2.width, [FALSE() for _ in range(-diff)] + bv1.body)
        return padding_BV, bv1

#assume bv1 and bv2 have the same width
#return the constraint showing bv1 > bv2
def GT(bv1, bv2, constraints=global_inv, equal = False):
    if isinstance(bv2, int):
        return GT_const(bv1, bv2, constraints, equal=equal)
    elif isinstance(bv1, int):
        return -GT_const(bv2, bv1, constraints, equal= not equal)

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
    if isinstance(bv2, int):
        return Equal_const(bv1, bv2, constraints)
    else:
        if bv1.width < bv2.width:
            bv1.self_extend(bv2.width - bv1.width)
        elif bv1.width > bv2.width:
            bv2.self_extend(bv1.width - bv2.width)
        assert (bv1.width == bv2.width)
        width = bv1.width
        return g_AND([IFF(bv1.get_var(i), bv2.get_var(i), constraints)  for i in range(width)], constraints)

def Equal_const(bv1, const, constraints=global_inv):
    if isinstance(bv1, int):
        if bv1 == const :
             return TRUE()
        else:
            return FALSE()
    else:
        const_bv = N_to_bit_array(const, bv1.width)
        width = bv1.width
        return g_AND([IFF(bv1.get_var(i), ntob(const_bv[i]), constraints)   for i in range(width)], constraints)

class Comparsion():
    comparsions = {}
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
        else:
            print("unsupported comparsion")
            assert (False)

        self.encoded = False
        if lit is None:
            self.lit = new_lit()
        else:
            self.lit = lit
        Comparsion.comparsions[(bv1.id, bv2.id, op)] = self

    def encode(self, constraints=global_inv):
        if self.encoded:
            return self.lit
        else:
            result_p = self.op(self.bv1, self.bv2, constraints)
            constraints.append([IFF(self.lit, result_p)])
            self.encoded = True
            return self.lit

def add_compare(bv1, bv2, op, lit, constraints = global_inv):
    if isinstance(bv1, int):
        bv1 = get_bv(bv1)
    if isinstance(bv2, int):
        bv2 = get_bv(bv2)

    compare = Comparsion.comparsions.get((bv1.id, bv2.id, op), None)
    if compare is None:
        compare = Comparsion(bv1, bv2, op, lit)
        return compare
    else:
        if compare.lit != lit:
            constraints.append([IFF(compare.lit, lit)])
        return compare

def add_compare_const(bv1, const, op, lit):
    if isinstance(bv1, int):
        bv1 = get_bv(bv1)

    compare = Comparsion_const.comparsion_consts.get((bv1.id, const, op), None)
    if compare is None:
        compare = Comparsion_const(bv1, const, op, lit)
        return compare
    else:
        if compare.lit != lit:
            return EQ(compare.lit, lit)
        else:
            return compare


class Comparsion_const():
    comparsion_consts = {}
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
        else:
            print("unsupported comparsion")
            assert (False)

        self.encoded = False
        if lit is None:
            self.lit = new_lit()
        else:
            self.lit = lit
        Comparsion_const.comparsion_consts[(bv1.id, const, op)] = self

    def encode(self, constraints=global_inv):
        if self.encoded:
            return self.lit
        else:
            result_p = self.op(self.bv1, self.const, constraints)
            constraints.append([IFF(self.lit, result_p)])
            self.encoded = True
            return self.lit

class EQ():
    EQs = {}
    def __init__(self, a, b):
        self.a = a
        self.b = b
        EQ.EQs[(a,b)] = self
        EQ.EQs[(b, a)] = self
        self.result = None

    def encode(self, constraints = global_inv):
        if self.result is None:
            self.result = IFF(self.a, self.b, constraints)
            constraints.append([self.result])
        return self.result

class ADD():
    def __init__(self, result, bv1, bv2):
        self.result = result
        self.bv1 = bv1
        self.bv2 = bv2
        self.encoded = False

    def encode(self, constraints = global_inv):
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
    if len(attributes) != 4:
        return False
    else:
        op, lit, bv, const = attributes
        add_compare_const(int(bv), int(const), op, int(lit))
        return True

def parse_comparsion(attributes):
    if len(attributes) != 4:
        return False
    else:
        op, lit, bv1, bv2 = attributes
        add_compare(int(bv1), int(bv2), op, int(lit))
        return True

def parse_addition(attributes):
    if len(attributes) != 3:
        return False
    else:
        result, bv1, bv2 = attributes
        add_Add(int(result), int(bv1), int(bv2))
        return True



def parse_bv(attributes):
    if len(attributes) < 2:
        return False
    else:
        id = attributes[0]
        width = attributes[1]
        if len(attributes) != int(width) + 2:
            return False
        else:
            BV(int(width), [int(i) for i in attributes[2:]], int(id))
            return True