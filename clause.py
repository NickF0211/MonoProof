import gc

from watch import Watch
from fact import Fact
class Clause():
    CNFS = set()
    def __init__(self, literals, register=True):
        assert(len(literals)  >= 2)
        self.lits = literals
        self.w1 = 0
        self.w2 = 1
        self.watch = Watch.watch
        self.fact = Fact.fact

        if register:
            self.watch.add_watch(self.lits[0], self)
            self.watch.add_watch( self.lits[1], self)
            Clause.CNFS.add(self)

    def register(self):
        self.watch.add_watch(self.lits[0], self)
        self.watch.add_watch(self.lits[1], self)
        Clause.CNFS.add(self)

    def rewatch(self):
        if (not self.find_new_watch()):
            return self.fact.add_fact_and_propgate(self.lits[0])
        else:
            return True

    def detch(self):
        self.watch.remove_watch(self.w1, self)
        self.watch.remove_watch(self.w2, self)
        Clause.CNFS.remove(self)

    def find_new_watch(self):
        if len(self.lits) <= 1:
            self.watch.remove_watch(self.lits[0], self)
            return False
        lit = self.lits[1]
        while not lit is None:
            sat_res = self.fact.is_sat(lit)
            if (sat_res == 0):
                self.watch.add_watch(lit, self)
                return True
            elif (sat_res == 1):
                self.watch.remove_watch(self.lits[0], self)
                return True
            else:
                self.lits.pop(1)
                if len(self.lits) > 1:
                    lit = self.lits[1]
                else:
                    self.watch.remove_watch(self.lits[0], self)
                    return False



    def notify_change(self, lit):
        w1 = self.lits[self.w1]
        w2 = self.lits[self.w2]
        if lit == w1 or lit == w2:
            self.watch.remove_watch(w1, self)
            self.watch.remove_watch(w2, self)
            return True
        elif lit == -w1:
            self.lits.pop(self.w1)
            self.watch.remove_watch(w1, self)
        elif lit == -w2:
            self.watch.remove_watch(w2, self)
            self.lits.pop(self.w2)
        else:
            assert (False)


        result = self.rewatch()

        return result



def resolve(c1, c2, lit):
    new_lits = c1.lits + c2.lits
    new_lits.remove(lit)
    new_lits.remove(-lit)
    return Clause(new_lits, register=False)

def RUP(c1):
    for l in c1.lits:
        Fact.fact.add_fact_and_propgate(l)
    if not Fact.fact.unit_propgate():
        c1.register()
        return True
    else:
        return False

def RAT(c1, i=1):
    for l in c1.lits:
        is_l_blocking  = True
        for c in Clause.CNFS:
            if -l in c.lits:
                res = resolve(c1, c, l)
                if RAT(res, i -1):
                    continue
                else:
                    is_l_blocking = False
                    break
        if is_l_blocking:
            return True
        else:
            continue
    return False











