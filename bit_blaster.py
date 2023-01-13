import subprocess
import time

from lit import write_dimacs
from mono_proof import verify_full_proof, Record
from parser import parse_file, Reachability, reextension
from predicate import pre_encode

cadical_path = "./cadical"
drat_trim_orig = "./drat-trim-orig"

def run_cadical_with_proof(cnf, proof):
    arugment_list = [cadical_path, cnf, proof, "-q", "-t", "60000"]
    process = subprocess.Popen(arugment_list,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    res = "s UNSATISFIABLE" in stdout
    return res

def parse_encode_solve_prove(gnf, record):
    if record is None:
        record = Record("test")
    cnf = parse_file(gnf)
    encoding_start = time.time()
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
    print(run_cadical_with_proof(output_cnf, proof_file))
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
    print("{},{},{},{}".format(gnf, encoding_start, solving_time, proving_time))


if __name__ == "__main__":
    gnf = "/Users/nickfeng/mono_encoding/routing/UNSAT_gnf_mid_new/instances_N_5_M_4_C_800_id_OeBjeskxuS_atp_1.gnf"
    parse_encode_solve_prove(gnf, None)