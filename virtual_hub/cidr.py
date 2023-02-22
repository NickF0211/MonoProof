from monosat import *

from ult import N_to_bit_array

class Cidr():

    def __init__(self, address, prefix_len):
        self.address = address
        self.prefix_len = prefix_len
        self.bit_array = N_to_bit_array(address, 32)

    def compile(self, ip):
        base = true()
        for i in range(self.prefix_len):
            base = And(base, Eq(self.bit_array[i], ip[i]))
        return base

    def extend(self, new_len):
        return Cidr(self.address, new_len)

    def __str__(self):
        return "{}/{}".format(self.address, self.prefix_len)

accept_all_cidrs = Cidr(0,0)

def get_parent_cidr(cidr: Cidr, level=1):
    return Cidr(cidr.address, max(0, cidr.prefix_len-level))

def extend_cidr_by_oct(cidr:Cidr, oct:int):
    assert cidr.prefix_len <= 24
    diff = 32 - cidr.prefix_len
    address = (cidr.address >> diff) << diff
    address = address + (oct << (diff  - 8))
    return Cidr(address, cidr.prefix_len + 8)



