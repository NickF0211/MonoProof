import numpy as np
from watch import Watch

class Fact():
    fact = None

    def __init__(self, lit_num):
        self.facts = np.zeros(lit_num+1, dtype=int)
        self.propgate_lits = []
        Fact.fact = self

    def add_fact(self, lit):
        assert (lit != 0)
        cur_val = self.lit_val(lit)
        if lit > 0:
            if cur_val == -1:
                return False
            else:
                self.facts[lit] = 1
                return True
        else:
            if cur_val == 1:
                return False
            else:
                self.facts[-lit] = -1
                return True


    def lit_val(self, lit):
        if lit > 0:
            return self.facts[lit]
        else:
            return self.facts[-lit]

    def is_sat(self, lit):
        value = self.lit_val(lit)
        if value == 0:
            return value
        else:
            if np.sign(lit) == np.sign(value):
                return 1
            else:
                return -1

    def add_fact_and_propgate(self, lit):
        if self.add_fact(lit):
            self.propgate_lits.append(lit)
            return True
        else:
            return False


    def unit_propgate(self):
        while (self.propgate_lits != []):
            first = self.propgate_lits.pop(0)
            #print(first)
            if not Watch.watch.notify_change(first):
                return False

        return True





