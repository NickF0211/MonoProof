from lit import *
from logic_gate import *
from numpy import zeros

class BV():

    def __init__(self, width, body):
        assert width == 0 or len(body) == width
        self.width = width
        self.body = body
        self.parent = None

    def get_var(self, index):
        assert(index < self.width)
        return self.body[index]

    def set_var(self, index, var):
        assert (index < self.width)
        self.body[index] = var

    def extend(self, padding_num):
        return BV(self.width+padding_num, [new_lit() for _ in range(padding_num)] + self.body)

    def self_extend(self, padding_num, pad=FALSE):
        self.width = self.width+padding_num
        self.body = [pad() for _ in range(padding_num)] + self.body

def sub_bv(bv, start, end):
    return BV(end-start, bv.body[start:end])


def new_bv(width, set_var=True):
    assert width > 0
    if set_var:
        body = [new_lit() for _ in range(width)]
    else:
        body = [0 for _ in range(width)]
    return BV(width, body)

def N_to_bit_array(const, width):
    inter = bin(const)[2:]
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


def add_mono(bv1, bv2, constraint=global_inv, bv3 = None):
    bv3 = add_lower(bv1, bv2, constraint, bv3)
    bv3 = add_upper(bv1, bv2, constraint, bv3)
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
        rules.append(IMPLIES(contain_bit, OR(bit3, acceptance_condition, constraint, forward=False), constraint, forward=False))

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
        rules.append(IMPLIES(neither_bit, OR(-bit3, accepted_condition, constraint, forward=False), constraint, forward=False))


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

