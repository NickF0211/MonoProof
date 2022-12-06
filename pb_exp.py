import glob
import subprocess
import time

from parser import reextension

outfile = "pb_mono.csv"

instance_timeout = 20000
instances = glob.glob("/u/fengnick/normalized-PB06/**.opb")

with open(outfile, 'w') as out:
    for ins in instances:
        mono_cnf = reextension(ins, "mcnf")
        arugment_list = ["python3", "pb.py", ins, "true", mono_cnf]
        process = subprocess.Popen(arugment_list,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        process.communicate()

        non_mono_cnf = reextension(ins, "cnf")
        arugment_list = ["python3", "pb.py", ins, "false", non_mono_cnf]
        process = subprocess.Popen(arugment_list,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        process.communicate()

        mono_start_time = time.time()
        arugment_list = ["minisat", mono_cnf]
        try:
            process = subprocess.Popen(arugment_list,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate(timeout=5000)
            mono_time = time.time() - mono_start_time
            if "UNSATISFIABLE" in stdout:
                out.write("{}, UNSAT, {} \n".format(mono_cnf, mono_time))
            else:
                out.write("{}, SAT, {} \n".format(mono_cnf, mono_time))
        except TimeoutError:
            out.write("{}, Timeout, {} \n".format(mono_cnf, -1))

        non_mono_start_time = time.time()
        arugment_list = ["minisat", non_mono_cnf]
        try:
            process = subprocess.Popen(arugment_list,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate(timeout=5000)
            non_mono_time = time.time() - non_mono_start_time
            if "UNSATISFIABLE" in stdout:
                out.write("{}, UNSAT, {} \n".format(non_mono_cnf, non_mono_time))
            else:
                out.write("{}, SAT, {} \n".format(non_mono_cnf, non_mono_time))
        except TimeoutError:
            out.write("{}, Timeout, {} \n".format(non_mono_cnf, -1))


