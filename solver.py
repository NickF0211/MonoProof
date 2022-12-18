from pysat.solvers import Cadical, Lingeling, Minisat22, Maplesat
from logic_gate import OR, g_OR, g_AND
from lit import write_proofs, write_dimacs
import subprocess
import os
from uuid import uuid4
from prover import Prover
from lit import get_lits_num

drat_path = "./drat-trim"


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

def get_blocked_proof(cnfs, block_assumptions, optimize=False, useProver=False):
    additional_clause = []
    assumption_lits  = [g_OR(ass, additional_clause, forward=False) for ass in block_assumptions]
    top_level_assumption = g_AND(assumption_lits, additional_clause, forward=False)
    final_collection = cnfs + additional_clause + [[-top_level_assumption]]

    # try prover first
    if useProver:
        p = Prover(get_lits_num(), final_collection)
        if not p.propgate():
            return block_assumptions

    with Lingeling(bootstrap_with=final_collection, with_proof=True) as solver:
        if solver.solve():
            print("assumption invalid")
            assert False
        else:
            proofs = solver.get_proof()
            if optimize:
                proofs = optimize_proof(final_collection, proofs)

            return additional_clause + _proof_block_cleanup(proofs, top_level_assumption, block_assumptions)


def get_proof(cnfs, assumptions = None, optimize = False, useProver=False):
    additional_clause = []
    if assumptions is None:
        assumption_lit = None
        final_collection = cnfs
    elif isinstance(assumptions, type([])):
        assumption_lit = g_OR(assumptions, additional_clause)
        final_collection = cnfs + additional_clause + [[-assumption_lit]]
    elif isinstance(assumptions, int):
        assumption_lit = assumptions
        final_collection = cnfs + additional_clause + [[-assumption_lit]]
        assumptions = [assumptions]
    else:
        print("unsupport proof request")
        assert False

    #try prover first
    if useProver:
        p = Prover(get_lits_num(), final_collection)
        if not p.propgate():
            return [assumptions]

    with Lingeling(bootstrap_with=final_collection, with_proof=True) as solver:
        if solver.solve():
            print("assumption invalid")
            assert False
        else:
            proofs = solver.get_proof()
            if optimize:
                proofs = optimize_proof(final_collection, proofs)

            if assumption_lit is None:
                return proofs
            else:
                return _proof_cleanup(proofs, assumption_lit, assumptions)

def _proof_block_cleanup(proof, assumption_lit, assumption_block):
    proof.pop(-1)
    if len(proof) == 0:
        return assumption_block
    else:
        format_proof = [[int(l) for l in lemma.split()[:-1]] for lemma in proof if not lemma.startswith("d")]
        step1 =  [[assumption_lit] + lemma for lemma in format_proof]  + assumption_block
        return step1

def _proof_cleanup(proof, assumption_lit, assumptions):
    proof.pop(-1)
    if len(proof) == 0:
        return [assumptions]
    else:
        format_proof = [[int(l) for l in lemma.split()[:-1]] for lemma in proof if not lemma.startswith("d")]
        return [assumptions + lemma for lemma in format_proof] + [assumptions]


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



