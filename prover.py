from fact import Fact
from watch import Watch
from clause import Clause
class Prover():

   def __init__(self, lit_num, cnfs):
      self.lit_num = lit_num


      self.fact = Fact(lit_num)
      self.watch = Watch(lit_num)
      self.Clauses = []
      self.conflict = False
      for c in cnfs:
         if not self.add_clause(c):
            print("conflict by unit propagation")
            self.conflict = True
            break



   def add_clause(self, clause):
      if len(clause) == 0:
         print("empty clause in the input")
         return
      elif (len(clause) == 1):
         return self.fact.add_fact_and_propgate(clause[0])
      else:
         self.Clauses.append(Clause(clause))
         return True


   def propgate(self):
      if not self.fact.unit_propgate():
         print("conflict by unit propagation")
         return False
      else:
         print("no conflict detect by unit propagation")
         return True





