import os.path
import subprocess
import sys
import time

from mono_proof import reset, monosat_path
from glob import glob

if __name__ == "__main__":
    input_directory = sys.argv[1]
    output_csv = sys.argv[2]

    test_files = glob(f"{input_directory}/**/*.gnf", recursive=True)
    with open(output_csv, 'w') as o_file:
        options = ["ruc"]
        for file in test_files:
            try:
                arugment_list = [monosat_path, file]
                if isinstance(options, str):
                    arugment_list = arugment_list + options.split()
                elif isinstance(options, type([])):
                    arugment_list += options
                start_time = time.time()
                process = subprocess.Popen(arugment_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate(timeout=5000)
                run_time = time.time() - start_time
                o_file.write("{}, {} \n".format(file, run_time))
                o_file.flush()
                reset()
            except subprocess.TimeoutExpired:
                o_file.write("{}, {} \n".format(file, "timeout=5000"))
                o_file.flush()
                reset()
                pass
