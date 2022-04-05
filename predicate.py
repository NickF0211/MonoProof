from bv import Comparsion, Comparsion_const, ADD
from reachability import Reachability
from max_flow import Maxflow

predicate_list = [Comparsion, Comparsion_const, ADD, Reachability, Maxflow]


def encode_predicate(predicate_class):
    constraints = []
    for predicate in predicate_class.Collection.values():
        predicate.encode(constraints)

    return constraints

def encode_all():
    result_constraints = []
    for predicate_class in predicate_list:
        result_constraints += encode_predicate(predicate_class)
    return result_constraints
