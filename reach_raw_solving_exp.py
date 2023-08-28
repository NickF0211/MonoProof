import os.path
import subprocess
import sys
import time

from mono_proof import reset, monosat_path, launch_monosat, Record
from glob import glob

if __name__ == "__main__":
    input_directory = sys.argv[1]
    output_csv = sys.argv[2]
    options = []

    test_files = glob(f"{input_directory}/**/*.gnf", recursive=True)
    with open(output_csv, 'w') as o_file:
        for file in test_files:
            print(file)
            try:
                arugment_list = [monosat_path, file]
                if isinstance(options, str):
                    arugment_list = arugment_list + options.split()
                elif isinstance(options, type([])):
                    arugment_list += options
                arugment_list.append("-no-reach-underapprox-cnf")
                start_time = time.time()
                process = subprocess.Popen(arugment_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate(timeout=5000)
                raw_run_time = time.time() - start_time
                reset()
            except subprocess.TimeoutExpired:
                raw_run_time = 5000
                reset()
                pass
            print(raw_run_time)

            record = Record(file)
            start = time.time()

            try:
                arugment_list = [monosat_path, file, "-drup-file=test.proof",
                                 "-proof-support=test.support", "-cnf-file=test.ecnf"]
                if isinstance(options, str):
                    arugment_list = arugment_list + options.split()
                elif isinstance(options, type([])):
                    arugment_list += options
                arugment_list.append("-no-reach-underapprox-cnf")
                start_time = time.time()
                process = subprocess.Popen(arugment_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate(timeout=5000)
                solving_with_proof = time.time() - start_time
                reset()
            except subprocess.TimeoutExpired:
                solving_with_proof = 5000
                reset()
                pass


            print("{}, {}, {} \n".format(file, raw_run_time, solving_with_proof))

            o_file.write("{}, {}, {} \n".format(file, raw_run_time, solving_with_proof))




