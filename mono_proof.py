from uuid import uuid4
import time
from parser import *
import subprocess
import os
from solver import drat_path

monosat_path =  "/Users/nickfeng/monosat/monosat"
drat_trim_orig_path = '/Users/nickfeng/mono_encoding/drat-trim-orig'

def verify_theory(cnf_file, proof_file, obligation_file):
    temp_file = str(uuid4())

    process = subprocess.Popen([drat_path, cnf_file, proof_file, "-p", "-l", temp_file, "-T", obligation_file],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    process.communicate()

    return temp_file

def launch_monosat(gnf_file, proof_file, support_file):
    process = subprocess.Popen([monosat_path, gnf_file, "-drup-file={}".format(proof_file), "-proof-support={}".format(support_file),  "-no-reach-underapprox-cnf"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    res =  "s UNSATISFIABLE" in stdout
    return res


def verify_full_proof(cnf, proof_file):

    process = subprocess.Popen([drat_trim_orig_path, cnf, proof_file],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    result = "s VERIFIED" in stdout
    if not result:
        print(stdout)
    return result

def verify_proof(gnf_file, proof_file, support_file, output_encoding, output_proof, debug=False):
    cnf = parse_file(gnf_file)
    cnf_file = extract_cnf(gnf_file)
    scan_proof(proof_file)
    cnf += pre_encode()
    obligation_file = reextension(gnf_file, "obg")

    optimizied_proof = verify_theory(cnf_file, proof_file, obligation_file)

    hint_map = parse_support(support_file)
    proofs = scan_proof_obligation(obligation_file, cnf, hint_map)


    reformat_proof(optimizied_proof, output_proof, proofs)
    write_dimacs(output_encoding, cnf + global_inv)
    if not debug:
        if os.path.exists(obligation_file):
            os.remove(obligation_file)
        if os.path.exists(optimizied_proof):
            os.remove(optimizied_proof)

    return



def run_and_prove(gnf):
    start_time = time.time()
    assert os.path.exists(gnf)
    proof_file = reextension(gnf, "proof")
    support_file = reextension(gnf, "support")
    unsat = launch_monosat(gnf, proof_file, support_file)
    tick = time.time()
    solving_time = tick - start_time
    start_time = tick
    print("solving with certificate time: {}".format(solving_time))
    if unsat:
        assert os.path.exists(support_file)
        assert os.path.exists(proof_file)
        output_cnf = reextension(gnf, 'cnf')
        verify_proof(gnf, proof_file, support_file, output_cnf, proof_file)
        tick = time.time()
        solving_time = tick - start_time
        start_time = tick
        print("proof preparing time: {}".format(solving_time))
        res = verify_full_proof(output_cnf, proof_file)
        if res:
            print("Verified")
        tick = time.time()
        solving_time = tick - start_time
        print("proof checking time: {}".format(solving_time))
        return res
    else:
        print("monosat decided the instance is SAT")
        return False





run_and_prove("test.gnf")

