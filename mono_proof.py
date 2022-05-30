from uuid import uuid4
import time
from parser import *
import subprocess
import os
from solver import drat_path
import sys
import graph
import bv
import predicate
import logic_gate
import lit
sys.setrecursionlimit(10000)

monosat_path =  "/Users/nickfeng/monosat/monosat"
drat_trim_orig_path = '/Users/nickfeng/mono_encoding/drat-trim-orig'

def verify_theory(cnf_file, proof_file, obligation_file):
    temp_file = str(uuid4())

    process = subprocess.Popen([drat_path, cnf_file, proof_file, "-p", "-l", temp_file, "-T", obligation_file],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, _ = process.communicate()
    assert "s VERIFIED" in stdout
    return temp_file

def launch_monosat(gnf_file, proof_file, support_file, extra_cnf = None, options = None, record = None):
    arugment_list = [monosat_path, gnf_file, "-drup-file={}".format(proof_file), "-proof-support={}".format(support_file),  "-no-reach-underapprox-cnf"]
    if extra_cnf is not None:
        arugment_list.append("-cnf-file={}".format(extra_cnf))
    if options is not None:
        arugment_list = arugment_list + options.split()
    process = subprocess.Popen(arugment_list,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    res =  "s UNSATISFIABLE" in stdout

    if record is not None:
        if res:
            record.set_solving_result("UNSAT")
        elif "s UNSATISFIABLE" in stdout:
            record.set_solving_result("SAT")
        else:
            record.set_solving_result("Unknown/Error")

    return res


def verify_full_proof(cnf, proof_file):

    process = subprocess.Popen([drat_trim_orig_path, cnf, proof_file],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    result = "s VERIFIED" in stdout
    if not result:
        print(stdout)
    return result

def verify_proof(gnf_file, proof_file, support_file, output_encoding, output_proof, debug=False,
                 extra_cnf = None, record = None):
    start_time = time.time()
    cnf = parse_file(gnf_file)
    if extra_cnf is not None:
        extra_cnf = parse_file(extra_cnf)
        cnf += extra_cnf
    cnf_file = extract_cnf(gnf_file)
    parsing_time_end = time.time()
    print("cnf reading time {}".format(parsing_time_end - start_time))
    start_time = parsing_time_end
    scan_proof(proof_file, record)
    parsing_time_end = time.time()
    print("proof reading time {}".format(parsing_time_end - start_time))
    start_time = parsing_time_end
    cnf += pre_encode()
    obligation_file = reextension(gnf_file, "obg")
    parsing_time_end = time.time()
    print("parsing + pre_encoding {}".format(parsing_time_end - start_time))
    start_time = parsing_time_end
    write_dimacs(cnf_file, cnf)
    optimizied_proof = verify_theory(cnf_file, proof_file, obligation_file)
    #optimizied_proof = proof_file
    parsing_time_end = time.time()
    print("theory processing time {}".format(parsing_time_end - start_time))
    start_time = parsing_time_end
    hint_map = parse_support(support_file)
    addition_encoder = CNFWriter(cnf_file)
    proofs = scan_proof_obligation(obligation_file, cnf, addition_encoder, hint_map, record)

    parsing_time_end = time.time()
    print("theory verification time {}".format(parsing_time_end - start_time))
    addition_encoder.content += global_inv
    addition_encoder.flush()
    addition_encoder.close()
    rewrite_header(cnf_file, output_encoding, cnf, addition_encoder)
    reformat_proof(optimizied_proof, output_proof, proofs)
    #write_dimacs(output_encoding, cnf + global_inv)
    if not debug:
        if os.path.exists(obligation_file):
            os.remove(obligation_file)
        if os.path.exists(optimizied_proof):
            os.remove(optimizied_proof)

    return

def load_record(record_string):
    new_record = Record("test")
    new_record.load(record_string)
    return new_record

class Record():


    def __init__(self, name):
        self.name = name
        self.solving_result = "unknown"
        self.solving_time = -1
        self.proof_preparing_time = -1
        self.proof_verification_time = -1
        self.lemma = 0
        self.theory_lemma = 0
        self.theory_obligation = 0
        self.verification_result = "unknown"

        self.attribute_names = ["name", "solving_result", "solving_time",
                           "proof_preparing_time", "proof_verification_time",
                           "lemma", "theory_lemma", "theory_obligation",
                           "verification_result"]

        self.header_names = ["Name", "Solving result", "Solving time",
                                "Proof preparing time, Proof verification time",
                                "Lemmas", "Theory lemmas", "Theory obligations",
                                "Verification result"]

    def get_attributes(self):
        return [self.name, self.solving_result, self.solving_time,
                           self.proof_preparing_time, self.proof_verification_time,
                           self.lemma, self.theory_lemma, self.theory_obligation,
                           self.verification_result]

    def set_solving_result(self, result):
        self.solving_result = result

    def set_solving_time(self, solving_time):
        self.solving_time = solving_time

    def set_proof_preparing_time(self, proof_preparing_time):
        self.proof_preparing_time = proof_preparing_time

    def set_proof_verification_time(self, proof_verification_time):
        self.proof_verification_time = proof_verification_time

    def set_lemma(self, lemma):
        self.lemma = lemma

    def set_theory_lemma(self, theory_lemma):
        self.theory_lemma = theory_lemma

    def set_theory_obligation(self, theory_obligation):
        self.theory_obligation = theory_obligation

    def set_verification_result(self, verification_result):
        self.verification_result = verification_result

    def __str__(self):
        return ','.join([str(ele) for ele in self.get_attributes()])

    def print_header(self):
        return ','.join(self.header_names)

    def load(self, input):
        tokens = input
        assert len(tokens) == len(self.get_attributes())
        for i in range(len(self.attribute_names)):
            setattr(self, self.attribute_names[i], tokens[i])

def prove(gnf, proof_file, support_file, extra_cnf = None, record = None):
    assert os.path.exists(support_file)
    assert os.path.exists(proof_file)
    start_time = time.time()
    output_cnf = reextension(gnf, 'cnf', suffix="complete")
    verify_proof(gnf, proof_file, support_file, output_cnf, proof_file, extra_cnf=extra_cnf, record=record)
    tick = time.time()
    solving_time = tick - start_time
    start_time = tick
    record.proof_preparing_time = (solving_time)
    print("proof preparing time: {}".format(solving_time))
    res = verify_full_proof(output_cnf, proof_file)
    if res:
        record.set_verification_result(True)
        print("Verified")
    else:
        record.set_verification_result(False)
    tick = time.time()
    solving_time = tick - start_time
    record.set_proof_verification_time(solving_time)
    print("proof checking time: {}".format(solving_time))
    return res


def run_and_prove(gnf, record = None):
    if record is None:
        record = Record(gnf)

    start_time = time.time()
    assert os.path.exists(gnf)
    proof_file = reextension(gnf, "proof")
    support_file = reextension(gnf, "support")
    extra_cnf = reextension(gnf, "ecnf")
    print("start solving")
    unsat = launch_monosat(gnf, proof_file, support_file, record = record, extra_cnf = extra_cnf )
    tick = time.time()
    solving_time = tick - start_time
    start_time = tick
    record.set_solving_time(solving_time)
    print("solving with certificate time: {}".format(solving_time))
    if unsat:
        prove(gnf, proof_file, support_file, record=record, extra_cnf = extra_cnf)
    else:
        print("monosat decided the instance is SAT")
        return False

def reset():
    graph.reset()
    bv.reset()
    predicate.reset()
    logic_gate.reset()
    l_reset()




if __name__ == "__main__":
    gnf = "test.gnf"
    #proof_file = "ti_amk52e04.proof"
    #support_file = "ti_amk52e04.support"
    #output_cnf = reextension(gnf, 'cnf', suffix="_complete")
    #parse_support(support_file)
    #verify_proof(gnf, proof_file, support_file, output_cnf, proof_file, record=None)
    #run_and_prove("/Users/nickfeng/mono_encoding/mx_benchmark/1-nodag-nodiff-trvs-altera_10ax048_780.gnf")
    #run_and_prove("max_flow.gnf")
    run_and_prove(gnf)
