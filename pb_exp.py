import glob
import subprocess
import sys

from parser import reextension

if __name__ == "__main__":
    test_index = sys.argv[1]
    outfile = "pb_mono_s_big_{}.csv".format(test_index)

    instance_timeout = 1800
    instances = glob.glob("ins{}/*.opb".format(test_index))

    with open(outfile, 'w') as out:
        for ins in instances:
            print(ins)

            try:
                non_mono_cnf = reextension(ins, "cnf")
                arugment_list = ["python3", "pb.py", ins, "false"]
                process = subprocess.Popen(arugment_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate(timeout=instance_timeout)
                out.write("{}".format(stdout))
            except subprocess.TimeoutExpired:
                out.write("{}, Timeout, {}\n".format(non_mono_cnf, -1))

            try:
                mono_cnf = reextension(ins, "mcnf")
                arugment_list = ["python3", "pb.py", ins, "true"]
                process = subprocess.Popen(arugment_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate(timeout=instance_timeout)
                out.write("{}".format(stdout))
            except subprocess.TimeoutExpired:
                out.write("{}, Timeout, {} \n".format(mono_cnf, -1))

            try:
                mono_cnf = reextension(ins, "s0cnf")
                arugment_list = ["python3", "pb.py", ins, "t", "0"]
                process = subprocess.Popen(arugment_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate(timeout=instance_timeout)
                out.write("{}".format(stdout))
            except subprocess.TimeoutExpired:
                out.write("{}, Timeout, {} \n".format(mono_cnf, -1))

            try:
                mono_cnf = reextension(ins, "s1cnf")
                arugment_list = ["python3", "pb.py", ins, "t", "1"]
                process = subprocess.Popen(arugment_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate(timeout=instance_timeout)
                out.write("{}".format(stdout))
            except subprocess.TimeoutExpired:
                out.write("{}, Timeout, {} \n".format(mono_cnf, -1))

            try:
                mono_cnf = reextension(ins, "s2cnf")
                arugment_list = ["python3", "pb.py", ins, "t", "2"]
                process = subprocess.Popen(arugment_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate(timeout=instance_timeout)
                out.write("{}".format(stdout))
            except subprocess.TimeoutExpired:
                out.write("{}, Timeout, {} \n".format(mono_cnf, -1))

            out.flush()



