import subprocess
import sys
import time

import logic_gate
from lit import write_dimacs
from mono_proof import verify_full_proof, Record, reset, launch_monosat
from parser import parse_file, Reachability, reextension
from predicate import pre_encode

solver_path = "./kissat/build/kissat"
drat_trim_orig = "./drat-trim-orig"

def run_solver_with_proof(cnf, proof):
    arugment_list = [solver_path, cnf, proof, "-q", "--time=60000"]
    process = subprocess.Popen(arugment_list,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    # print(stdout)
    res = "s UNSATISFIABLE" in stdout
    if res:
        return res
    else:
        return stdout

def get_model(result):
    assert isinstance(result, str)
    models = []
    res = result.split('\n')
    for line_res in res:
        if line_res.startswith('v'):
            line_model = line_res.split()
            models += line_model[1:]
        else:
            continue
    return models

def parse_encode_solve_prove(gnf, record):
    reset()
    if record is None:
        record = Record("test")
    cnf = parse_file(gnf)
    encoding_start = time.time()
    logic_gate.process_delayed_equality(cnf)
    cnf += pre_encode()
    for r in Reachability.Collection.values():
        r.binary_encode(cnf)
    encoding_time = time.time() - encoding_start
    record.set_proof_preparing_time(encoding_time)
    print("done encoding")
    output_cnf = reextension(gnf, 'xextcnf', suffix="complete")
    write_dimacs(output_cnf, cnf)
    print("start solving")
    proof_file = reextension(output_cnf, "proof")
    solving_start = time.time()
    res = run_solver_with_proof(output_cnf, proof_file)
    if isinstance(res, str):
        record.set_verification_result("SAT")
        print("SAT")
    #     models = get_model(res)
    #     model_checking_gnf = reextension(gnf, "modelgnf")
    #     with open(model_checking_gnf, 'w') as output_gnf:
    #         print(model_checking_gnf)
    #         with open(gnf, 'r') as input_gnf:
    #             output_gnf.write(input_gnf.read())
    #
    #         for assign in models:
    #             if assign != '0':
    #                 output_gnf.write("{} 0 \n".format(assign))
    #
    #     assert not launch_monosat(model_checking_gnf, "ok.proof", "ok.support", record=Record)
    else:
        record.set_verification_result("UNSAT")
        solving_time = time.time() - solving_start
        record.set_solving_time(solving_time)
        proving_start = time.time()
        res = verify_full_proof(output_cnf, proof_file)
        if res:
            print("Verified")
            record.set_verification_result(True)
        else:
            record.set_verification_result(False)
        proving_time = time.time() - proving_start
        record.set_proof_verification_time(proving_time)
        print("{},{},{},{}".format(gnf, encoding_time, solving_time, proving_time))
        record.set_proof_preparing_time(0)


if __name__ == "__main__":
    # gnf = "/Users/nickfeng/mono_encoding/routing/UNSAT_gnf_mid_new/instances_N_5_M_4_C_800_id_OeBjeskxuS_atp_1.gnf"
    if len(sys.argv) >= 2:
        gnf = sys.argv[1]
    # gnf = "example.gnf"
    parse_encode_solve_prove(gnf, None)