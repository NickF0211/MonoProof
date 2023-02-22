from monosat import  *
from ult import *


class Port():
    def __init__(self, lb = None, ub = None):
        self.lb = self.ub = None
        if lb:
            self.lb = N_to_bit_array(lb, 16)
        if ub:
            self.ub = N_to_bit_array(ub, 16)

    def compile(self, port):
        base = true()
        if self.ub:
            base = And(base, ge(self.ub, port))
        if self.lb:
            base  = And(base, ge(port, self.lb))

        return base

accept_all_port = Port(0, 65535)
ssh_port = Port(22, 22)




class Port_Adder():
    def __init__(self, start, end, step):
        self.start = start
        self.end = end
        self.step = step
        self.useful_ports = []
        current = start
        while current < end:
            self.useful_ports.append(Port(current, current+step))
            current += step + 1



    def compile(self, port1, port2):
        base = true()
        for i in range(len(self.useful_ports) -1):
            head = self.useful_ports[i]
            tail = self.useful_ports[i+1]
            base = And(base, Implies(head.compile(port1), tail.compile(port2)))
        return base




