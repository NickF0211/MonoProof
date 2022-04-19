from bv import Comparsion, Comparsion_const, ADD
from reachability import Reachability
from max_flow import Maxflow

predicate_list = [Comparsion, Comparsion_const, ADD, Reachability, Maxflow]
pre_predicate_list = [Comparsion, Comparsion_const, ADD]

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

def pre_encode():
    result_constraints = []
    for predicate_class in pre_predicate_list:
        result_constraints += encode_predicate(predicate_class)
    return result_constraints

def reset():
    for predicate_class in predicate_list:
        predicate_class.Collection.clear()