from random import random

from monosat import *
def N_to_bit_array(const, width=-1):
    inter = bin(const)[2:]
    if width != -1:
        assert (len(inter) <= width)
        inter = inter.zfill(width)
    return [false() if b == '0' else true() for b in inter]


def gt(bv1, bv2):
    return ge(bv1, bv2)

def ge(bv1, bv2, eq=True):
    ge = true()
    gt = false()
    for i in range(len(bv1)):
        bit1 = bv1[i]
        bit2 = bv2[i]
        l_gt = And(bit1, Not(bit2))
        l_ge = Or(bit1, Not(bit2))
        gt = Or(gt, And(ge, l_gt))
        ge = And(ge, l_ge)

    if eq:
        return Or(gt, ge)
    else:
        return gt



def match_cidr_and_extra(bv, cidrs, suf):
    constraints = []
    for i in range(len(cidrs)):
        oct = cidrs[i]
        constraints.append(eq_ip(bv[i * 8: (i + 1) * 8], oct))
    ge = random.getrandbits(1)

    if ge:
        constraints.append(ge_ip(bv[len(cidrs) * 8: (len(cidrs) + 1) * 8], suf))
    else:
        constraints.append(le_ip(bv[len(cidrs) * 8: (len(cidrs) + 1) * 8], suf))

    return And(constraints)


# def match_cidr(bv, cidrs):
#     constraints = []
#     for i in range(len(cidrs)):
#         oct = cidrs[i]
#         constraints.append(eq_ip(bv[i * 8: (i + 1) * 8], oct))
#     return And(constraints)


def ge_ip(bv, ip):
    ip_value = ip
    constraints = []
    for i in range(len(bv) - 1, 0, -1):
        if ip_value & 1:
            constraints.append(bv[i])
        ip_value = ip_value >> 1
    return And(constraints)


def le_ip(bv, ip):
    ip_value = ip
    constraints = []
    for i in range(len(bv) - 1, 0, -1):
        if ip_value & 0:
            constraints.append(Not(bv[i]))
        ip_value = ip_value >> 1
    return And(constraints)


def eq_ip(bv, ip):
    ip_value = ip
    constraints = []
    for i in range(len(bv) - 1, 0, -1):
        if ip_value & 1:
            constraints.append(bv[i])
        else:
            constraints.append(Not(bv[i]))
        ip_value = ip_value >> 1
    return And(constraints)


def assert_random_bits(edge, bv, nl, nh):
    number_of_bits = random.randint(nl, nh)
    samples_bits = random.sample(bv, number_of_bits)
    for bit in samples_bits:
        if random.getrandbits(1):
            Assert(Implies(edge, bit))
        else:
            Assert(Implies(edge, Not(bit)))


def assert_edge_ge_bits(edge, src, target, start, end):
    Assert(Implies(edge, assert_ge_bits(src, target, start, end)))

def assert_ge_bits(src, target, start, end):
    constraints =[]
    for i in range(start, end):
        constraints.append(Implies(src[i], target[i]))
    return And(constraints)


