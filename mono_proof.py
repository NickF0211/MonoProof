import re
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
sys.setrecursionlimit(10000)

monosat_path =  "/Users/nickfeng/monosat/monosat"
drat_trim_orig_path = './drat-trim-orig'


def verify_theory(cnf_file, proof_file, obligation_file):
    temp_file = str(uuid4())
    print(' '.join([cnf_file, proof_file,  "-w", "-l", temp_file, "-T", obligation_file]))
    process = subprocess.Popen([drat_path, cnf_file, proof_file, "-w", "-l", temp_file, "-T", obligation_file, "-C"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, _ = process.communicate()
    # print(stdout)
    assert "s VERIFIED" in stdout
    return temp_file

def prepare_proof(proof_file, obligation_file, record):
    temp_file = str(uuid4())
    try:
        with open(obligation_file, 'w') as ob:
            scan_proof(proof_file, record, ob)
    except AssertionError:
        with open(obligation_file, 'w') as ob:
            with open(temp_file, 'wb') as fp:
                scan_binary_proof(proof_file, record, ob, fp)
    except UnicodeDecodeError:
        with open(obligation_file, 'w') as ob:
            with open(temp_file, 'wb') as fp:
                scan_binary_proof(proof_file, record, ob, fp)
    # shutil.move(proof_file, temp_file)
    return temp_file

def  launch_monosat(gnf_file, proof_file, support_file, extra_cnf = None, options = None, record = None):
    arugment_list = [monosat_path, gnf_file, "-drup-file={}".format(proof_file), "-proof-support={}".format(support_file),  "-no-reach-underapprox-cnf"]
    if extra_cnf is not None:
        arugment_list.append("-cnf-file={}".format(extra_cnf))
    if options is not None:
        if isinstance(options, str):
            arugment_list = arugment_list + options.split()
        elif isinstance(options, type([])):
            arugment_list += options
    start_time = time.time()
    process = subprocess.Popen(arugment_list,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    record.set_solving_time(time.time() - start_time)
    res =  "s UNSATISFIABLE" in stdout

    if record is not None:
        if res:
            record.set_solving_result("UNSAT")
        elif "s SATISFIABLE" in stdout:
            record.set_solving_result("SAT")
        else:
            record.set_solving_result("Unknown/Error")

    match = re.search(r"c total var nums: (\d+)\n", stdout)
    if match:
        # Return the number as an integer
        record.set_vars(int(match.group(1)))

    match = re.search(r"c total var tlemmas: (\d+)\n", stdout)
    if match:
        # Return the number as an integer
        record.set_theory_lemma(int(match.group(1)))

    match = re.search(r"c total var lemmas: (\d+)\n", stdout)
    if match:
        # Return the number as an integer
        record.set_lemma(int(match.group(1)))

    return res

def  launch_raw_monosat(gnf_file, options = None, record = None, solver_location = None):
    if not solver_location:
        solver_location = monosat_path
    arugment_list = [solver_location, gnf_file,   "-no-reach-underapprox-cnf"]
    if options is not None:
        if isinstance(options, str):
            arugment_list = arugment_list + options.split()
        elif isinstance(options, type([])):
            arugment_list += options
    process = subprocess.Popen(arugment_list,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    start_time = time.time()
    stdout, stderr = process.communicate()
    record.set_raw_solving_time(time.time() - start_time)
    res =  "s UNSATISFIABLE" in stdout

    if record is not None:
        if res:
            record.set_solving_result("UNSAT")
        elif "s SATISFIABLE" in stdout:
            record.set_solving_result("SAT")
        else:
            record.set_solving_result("Unknown/Error")

    match = re.search(r"c total var nums: (\d+)\n", stdout)
    if match:
        # Return the number as an integer
        record.set_vars(int(match.group(1)))

    match = re.search(r"c total var tlemmas: (\d+)\n", stdout)
    if match:
        # Return the number as an integer
        record.set_theory_lemma(int(match.group(1)))

    match = re.search(r"c total var lemmas: (\d+)\n", stdout)
    if match:
        # Return the number as an integer
        record.set_lemma(int(match.group(1)))

    return res


def verify_full_proof(cnf, proof_file):

    print(' '.join([drat_trim_orig_path, cnf, proof_file, "-w"]))
    process = subprocess.Popen([drat_trim_orig_path, cnf, proof_file, "-w", "-t", "100000"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    result = "s VERIFIED" in stdout
    if not result:
        print(stdout)
    return result

def verify_proof(gnf_file, proof_file, support_file, output_encoding, output_proof, debug=False,
                 extra_cnf = None, record = None, witness_reduction = True, backward_check=True, lemma_bitblast = False,
                 graph_reduction = True):
    start_time = time.time()
    cnf = parse_file(gnf_file)
    if extra_cnf is not None:
        extra_cnf = parse_file(extra_cnf)
        cnf += extra_cnf
    cnf_file = extract_cnf(gnf_file)
    parsing_time_end = time.time()
    print("cnf reading time {}".format(parsing_time_end - start_time))
    start_time = parsing_time_end
    if record is not None and record.vars:
        add_lit(record.vars)
    else:
        try:
            scan_proof(proof_file, record)
        except UnicodeDecodeError:
            scan_binary_proof(proof_file, record)
    # now we can process delayed equality
    logic_gate.process_delayed_equality(cnf)
    parsing_time_end = time.time()
    print("proof reading time {}".format(parsing_time_end - start_time))
    start_time = parsing_time_end
    cnf += pre_encode()
    obligation_file = reextension(gnf_file, "obg")
    parsing_time_end = time.time()
    print("parsing + pre_encoding {}".format(parsing_time_end - start_time))
    start_time = parsing_time_end
    write_dimacs(cnf_file, cnf)
    if backward_check:
        optimizied_proof = verify_theory(cnf_file, proof_file, obligation_file)
    else:
        optimizied_proof = prepare_proof(proof_file, obligation_file, record)
    #optimizied_proof = proof_file
    parsing_time_end = time.time()
    print("theory processing time {}".format(parsing_time_end - start_time), flush=True, file=sys.stderr)
    start_time = parsing_time_end
    hint_map = parse_support(support_file)
    addition_encoder = CNFWriter(cnf_file)
    logic_gate.set_file_writer(addition_encoder)
    cnf_len = len(cnf) + len(global_inv)
    # if not lemma_bitblast:
    #     cnf.clear()
    proofs = scan_proof_obligation(obligation_file, cnf, addition_encoder, hint_map, record,
                                   witness_reduction = witness_reduction,
                                   lemma_bitblast= lemma_bitblast, graph_reduction = graph_reduction)
    parsing_time_end = time.time()
    print("theory verification time {}".format(parsing_time_end - start_time), flush=True)
    addition_encoder.content += global_inv
    addition_encoder.flush()
    addition_encoder.close()
    rewrite_header(cnf_file, output_encoding, cnf_len, addition_encoder)
    # shutil.move(optimizied_proof, proof_file)
    try:
        reformat_proof(optimizied_proof, output_proof, proofs)
    except UnicodeDecodeError:
        reformat_proof_binary(optimizied_proof, output_proof, proofs)
    except AssertionError:
        reformat_proof_binary(optimizied_proof, output_proof, proofs)

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
        self.vars = 0
        self.solving_result = "unknown"
        self.solving_time = -1
        self.raw_solving_time = -1
        self.proof_preparing_time = -1
        self.proof_verification_time = -1
        self.lemma = 0
        self.theory_lemma = 0
        self.theory_obligation = 0
        self.verification_result = "unknown"

        self.attribute_names = ["name", "solving_result", "solving_time", "raw_solving_time"
                           "proof_preparing_time", "proof_verification_time",
                           "lemma", "theory_lemma", "theory_obligation",
                           "verification_result"]

        self.header_names = ["Name", "Solving result", "Solving time", "Raw solving time",
                                "Proof preparing time, Proof verification time",
                                "Lemmas", "Theory lemmas", "Theory obligations",
                                "Verification result"]

    def get_attributes(self):
        return [self.name, self.solving_result, self.solving_time, self.raw_solving_time,
                           self.proof_preparing_time, self.proof_verification_time,
                           self.lemma, self.theory_lemma, self.theory_obligation,
                           self.verification_result]

    def set_solving_result(self, result):
        self.solving_result = result

    def set_solving_time(self, solving_time):
        self.solving_time = solving_time

    def set_raw_solving_time(self, raw_solving_time):
        self.raw_solving_time = raw_solving_time

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

    def set_vars(self, vars):
        self.vars = vars

    def __str__(self):
        return ','.join([str(ele) for ele in self.get_attributes()])

    def print_header(self):
        return ','.join(self.header_names)

    def load(self, input):
        tokens = input
        assert len(tokens) == len(self.get_attributes())
        for i in range(len(self.attribute_names)):
            setattr(self, self.attribute_names[i], tokens[i])

def prove(gnf, proof_file, support_file, extra_cnf = None, record = None, witness_reduction = True, backward_check = True,
          lemma_bitblast=False, graph_reduction = True):
    assert os.path.exists(support_file)
    assert os.path.exists(proof_file)
    start_time = time.time()
    output_cnf = reextension(gnf, 'extcnf', suffix="complete")
    verify_proof(gnf, proof_file, support_file, output_cnf, proof_file, extra_cnf=extra_cnf, record=record,
                 witness_reduction=witness_reduction, backward_check = backward_check,
                 lemma_bitblast = lemma_bitblast, graph_reduction=graph_reduction)
    tick = time.time()
    solving_time = tick - start_time
    start_time = tick
    record.set_proof_preparing_time(solving_time)
    print("proof preparing time: {}".format(solving_time),  flush=True, file=sys.stderr)
    res = verify_full_proof(output_cnf, proof_file)
    if res:
        record.set_verification_result(True)
        print("Verified")
    else:
        record.set_verification_result(False)
    tick = time.time()
    solving_time = tick - start_time
    record.set_proof_verification_time(solving_time)
    print("proof checking time: {}".format(solving_time), flush=True)
    return res



def run_and_prove(gnf, record = None, running_opt=None, witness_reduction = True,
                  backward_check = True, lemma_bitblast = False, graph_reduction = True):
    reset()
    if record is None:
        record = Record(gnf)

    start_time = time.time()
    assert os.path.exists(gnf)
    proof_file = reextension(gnf, "proof")
    support_file = reextension(gnf, "support")
    extra_cnf = reextension(gnf, "ecnf")
    print("start solving for file {}".format(gnf),  flush=True, file=sys.stderr)
    unsat = launch_monosat(gnf, proof_file, support_file, record = record, extra_cnf = extra_cnf, options=running_opt)
    tick = time.time()
    solving_time = tick - start_time
    record.set_solving_time(solving_time)
    print("solving with certificate time: {}".format(solving_time),  flush=True, file=sys.stderr)
    if unsat:
        return prove(gnf, proof_file, support_file, record=record, extra_cnf = extra_cnf,
                     witness_reduction = witness_reduction, backward_check=backward_check,
                     lemma_bitblast = lemma_bitblast, graph_reduction = graph_reduction)
    else:
        print("monosat decided the instance is SAT", file=sys.stderr)
        return False

def reset():
    graph.reset()
    bv.reset()
    predicate.reset()
    logic_gate.reset()
    l_reset()




if __name__ == "__main__":
    # gnf = "/Users/nickfeng/mono_encoding/routing/UNSAT_instances_mid_gnf/instances_N_5_M_6_C_3800_id_FmpzCyNCYY_atp_0.gnf"
    # gnf = "/Users/nickfeng/mono_encoding/routing/UNSAT_gnf_tiny/instances_N_5_M_2_C_40_id_xJEKwjwrkj_atp_1.gnf"
    # gnf = "/Users/nickfeng/mono_encoding/routing/UNSAT_gnf_mid_new/instances_N_5_M_4_C_800_id_OeBjeskxuS_atp_1.gnf"
    gnf = "/Users/nickfeng/mono_encoding/virtual_hub/test.gnf"
    # gnf = "sub_gnf.gnf"
    # gnf = "/Users/nickfeng/mono_encoding/colored_graph/color_graph.gnf"
    # gnf = "reach.gnf"
    # proof_file = "test.proof"
    # support_file = "test.support"
    #proof_file = "ti_amk52e04.proof"
    #support_file = "ti_amk52e04.support"
    #output_cnf = reextension(gnf, 'cnf', suffix="_complete")
    #parse_support(support_file)
    #verify_proof(gnf, proof_file, support_file, output_cnf, proof_file, record=None)
    #run_and_prove("/Users/nickfeng/mono_encoding/mx_benchmark/1-nodag-nodiff-trvs-altera_10ax048_780.gnf")
    #run_and_prove("max_flow.gnf")
    # launch_monosat(gnf, "test.proof", "test.support", options=["-no-check-solution", "-verb=1", "-theory-order-vsids", "-no-decide-theories",
    #                                                             "-vsids-both", "-decide-theories",
    #                                                             "-no-decide-graph-rnd",
    #                                                             "-lazy-maxflow-decisions", "-conflict-min-cut",
    #                                                             "-adaptive-history-clear=5"], record=Record("test"))
    #run_and_prove(gnf, running_opt=["-ruc"], witness_reduction=False)
    running_opt=["-no-check-solution", "-verb=1", "-theory-order-vsids",
                                                                "-vsids-both", "-decide-theories",
                                                                "-no-decide-graph-rnd",
                                                                "-lazy-maxflow-decisions", "-conflict-min-cut",
                                                                "-adaptive-history-clear=5"]
    run_and_prove(gnf, running_opt=[], witness_reduction=True, backward_check=True, lemma_bitblast=False)
    #launch_monosat(gnf, proof_file, support_file, options=running_opt)
    # record = Record(gnf)
    # prove(gnf, proof_file, support_file=support_file, record=record)