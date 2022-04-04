from pysat.solvers import Cadical, Lingeling
from logic_gate import OR, g_OR

def is_sat(cnfs):
    solver = Cadical(bootstrap_with=cnfs)
    return solver.solve()

def get_proof(cnfs, assumptions = None):
    additional_clause = []
    if assumptions is None:
        assumption_lit = None
        final_collection = cnfs
    elif isinstance(assumptions, type([])):
        assumption_lit = g_OR(assumptions, additional_clause)
        final_collection = cnfs + assumptions + [-assumption_lit]
    elif isinstance(assumptions, int):
        assumption_lit = assumptions
        final_collection = cnfs + assumptions + [-assumption_lit]
        assumptions = [assumptions]
    else:
        print("unsupport proof request")
        assert False

    with Lingeling(bootstrap_with=final_collection, with_proof=True) as solver:
        if solver.solve():
            print("assumption invalid")
        else:
            proofs = solver.get_proof()
            if assumption_lit is None:
                return proofs
            else:
                return _proof_cleanup(proofs, assumption_lit, assumptions)



def _proof_cleanup(proof, assumption_lit, assumptions):
    proof.pop(-1)
    return [[assumption_lit] + lemma for lemma in proof if not lemma.startswith("d")] + [assumptions]

