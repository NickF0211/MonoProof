from cidr import Cidr, accept_all_cidrs, get_parent_cidr
from port import Port, accept_all_port
from monosat import *


class SG_rule():
    def __init__(self, cidr: Cidr, port: Port ):
        self.cidr = cidr
        self.port = port

    def compile(self, ip, port):
        return And(self.cidr.compile(ip), self.port.compile(port))

accept_all_sg_rules = SG_rule(accept_all_cidrs, accept_all_port)

# rules to accept all traffic that come from the same cidr range of the node
# whose dest port is below the port threshold
def accept_sibling_sg_rule(cidr: Cidr, lb=0, ub= (1<< 16) -1, parent_level=1):
    return SG_rule(get_parent_cidr(cidr, level=parent_level), Port(lb = lb, ub=ub))

def accept_child_sg_rule(cidr: Cidr):
    return SG_rule(cidr, accept_all_port)


class SG():
    def __init__(self, sgs: [SG_rule]):
        self.sgs = sgs

    def add_rule(self, sg_rule):
        self.sgs.append(sg_rule)

    def compile(self, ip, port):
        return Or([rule.compile(ip, port) for rule in self.sgs])

def subnet_SG(cidr: Cidr, parent_level=8):
    return SG([accept_child_sg_rule(cidr), accept_sibling_sg_rule(cidr, parent_level=parent_level)])