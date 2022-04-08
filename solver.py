from pysat.solvers import Cadical, Lingeling
from logic_gate import OR, g_OR
from lit import write_proofs, write_dimacs
import subprocess
import os
from uuid import uuid4
drat_path = "/Users/nickfeng/mono_encoding/drat-trim"

def is_sat(cnfs):
    solver = Cadical(bootstrap_with=cnfs)
    return solver.solve()

def get_model(cnfs):
    solver = Cadical(bootstrap_with=cnfs)
    if solver.solve():
        return solver.get_model()
    else:
        return False

def is_rat(cnfs):
    return get_proof(cnfs, optimize=True) == ['0']

def get_proof(cnfs, assumptions = None, optimize = False):
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
            if optimize:
                proofs = optimize_proof(final_collection, proofs)

            if assumption_lit is None:
                return proofs
            else:
                return _proof_cleanup(proofs, assumption_lit, assumptions)



def _proof_cleanup(proof, assumption_lit, assumptions):
    proof.pop(-1)
    return [[assumption_lit] + lemma for lemma in proof if not lemma.startswith("d")] + ["{} 0".format(' '.join(assumptions))]


def optimize_proof(input, proofs):
    #note, we assume drat is available via command line
    proof_name = str(uuid4()) + "1"
    input_name = str(uuid4()) + "2"
    temp_file = str(uuid4()) + "3"
    write_proofs(proof_name, proofs)
    write_dimacs(input_name, input)
    try:
        process = subprocess.Popen([drat_path, input_name, proof_name, "-p", "-l",  temp_file],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        process.communicate()
        with open(temp_file, 'r') as optimized_proof:
            proofs = [clause.strip() for clause in optimized_proof.readlines() if not clause.startswith('d')]

            if os.path.exists(proof_name):
                os.remove(proof_name)
            if os.path.exists(input_name):
                os.remove(input_name)
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return proofs

    finally:
        if os.path.exists(proof_name):
            os.remove(proof_name)
        if os.path.exists(input_name):
            os.remove(input_name)
        if os.path.exists(temp_file):
            os.remove(temp_file)



