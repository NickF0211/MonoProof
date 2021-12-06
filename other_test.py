from z3 import *

constraints = []
head = 0
head_prime = 0

for i in range(0, 100):
    next = Int("{}".format(i))
    next_prime = Int("{}'".format(i))
    constraints.append(next > next_prime)
    head = head + next
    head_prime = head_prime + next_prime

constraints.append(head < head_prime)
solve(constraints)