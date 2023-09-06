import os
import subprocess
import sys
import time

import logic_gate
from lit import write_dimacs, CNFWriter, global_inv, rewrite_header
from mono_proof import verify_full_proof, Record, reset, launch_monosat
from parser import parse_file, Reachability, reextension, Maxflow
from predicate import pre_encode

solver_path = "./kissat/build/kissat"
drat_trim_orig = "./drat-trim-orig"
run_lim = ""
run_lim_v_limit = 32000

def run_solver_with_proof(cnf, proof):
    arugment_list = [solver_path, cnf, proof, "-q", "--time=60000"]
    if run_lim:
        arugment_list = [run_lim, "-v", str(run_lim_v_limit)] + arugment_list

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
    cnf_file =  reextension(gnf, 'xextcnf', suffix="init_complete")
    write_dimacs(cnf_file, cnf)
    addition_encoder = CNFWriter(cnf_file)
    logic_gate.set_file_writer(addition_encoder)
    cnf_len = len(cnf) + len(global_inv)
    for r in Reachability.Collection.values():
        r.binary_encode(addition_encoder)
    print("encode mf")
    for mf in Maxflow.Collection.values():
        # logic_gate.lock_cache()
        mf.encode(addition_encoder, pos = True, neg=False)
        # logic_gate.unlock_cache()
    encoding_time = time.time() - encoding_start
    record.set_proof_preparing_time(encoding_time)
    print("done encoding")
    output_cnf = reextension(gnf, 'xextcnf', suffix="complete")
    # write_dimacs(output_cnf, cnf)
    addition_encoder.content += global_inv
    addition_encoder.flush()
    addition_encoder.close()
    rewrite_header(cnf_file, output_cnf, cnf_len, addition_encoder)
    print("start solving")
    proof_file = reextension(output_cnf, "proof")
    solving_start = time.time()
    res = run_solver_with_proof(output_cnf, proof_file)
    os.remove(cnf_file)
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
        os.remove(proof_file)
    os.remove(output_cnf)

if __name__ == "__main__":
    # gnf = "/Users/nickfeng/mono_encoding/routing/UNSAT_gnf_mid_new/instances_N_5_M_4_C_800_id_OeBjeskxuS_atp_1.gnf"
    if len(sys.argv) >= 2:
        gnf = sys.argv[1]
    # gnf = "example.gnf"
    parse_encode_solve_prove(gnf, None)