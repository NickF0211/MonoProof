from monosat import *
import random


def N_to_bit_array(const, width=-1):
    inter = bin(const)[2:]
    if width != -1:
        assert (len(inter) <= width)
        inter = inter.zfill(width)
    return [false() if b == '0' else true() for b in inter]



def random_cidr_ranges_constraints():
    base_cidr = random.randint(0, 1 << 32)
    cidr_len = random.randint(0, 32)

    def _func(ip, base_cidr=base_cidr):
        base_cidr_array = N_to_bit_array(base_cidr, 32)
        base = true()
        for i in range(cidr_len):
            base = And(base, Eq(base_cidr_array[i], ip[i]))
        return base
    return _func


def random_port_constraints():
    random_lower_bound = random.randint(0, 65535-1)
    random_upper_bound = random.randint(random_lower_bound, 65535)

    def _func(port, random_lower_bound=random_lower_bound, random_upper_bound=random_upper_bound):
        lb_array = N_to_bit_array(random_lower_bound, 16)
        ub_array = N_to_bit_array(random_upper_bound, 16)
        return And(ge(port, lb_array), ge(ub_array, port))
    return _func


def generate_incoming_firewall_rules(entry_lower=0, entry_higher = 3):
    entry_nums = random.randint(entry_lower, entry_higher)
    rules = []
    for i in range(entry_nums):
        rules.append(generate_incoming_firewall_rule())
    if entry_nums:
        return lambda src_ip, dest_ip, src_port, dest_port : \
            Or([rule(src_ip, dest_ip, src_port, dest_port) for rule in rules])
    else:
        return lambda src_ip, dest_ip, src_port, dest_port : true()

def generate_outgoing_firewall_rules(entry_lower=0, entry_higher = 3):
    entry_nums = random.randint(entry_lower, entry_higher)
    rules = []
    for i in range(entry_nums):
        rules.append(generate_outgoing_firewall_rules())

    if entry_nums:
        return lambda src_ip, dest_ip, src_port, dest_port: \
            Or([rule(src_ip, dest_ip, src_port, dest_port) for rule in rules])
    else:
        return lambda src_ip, dest_ip, src_port, dest_port: true()

def generate_incoming_firewall_rule():
    # this is going to be related to the dest port instead of the source port
    return lambda src_ip, dest_ip, src_port, dest_port : And(random_cidr_ranges_constraints()(src_ip),
                                                             random_port_constraints()(dest_port))

def generate_outgoing_firewall_rule():
    return lambda src_ip, dest_ip, src_port, dest_port: And(random_cidr_ranges_constraints()(dest_ip),
                                                            random_port_constraints()(dest_port))