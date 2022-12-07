import glob
import subprocess

from parser import reextension

outfile = "pb_mono.csv"

instance_timeout = 1200
instances = glob.glob("normalized-PB06\**\*.opb", recursive=True)

with open(outfile, 'a') as out:
    for ins in instances[7:]:
        if ins == "normalized-PB06\\SATUNSAT-SMALLINT\\submitted\\aloul\\FPGA_SAT05\\normalized-chnl15_16_pb.cnf.cr.opb":
            continue
        print(ins)
        try:
            mono_cnf = reextension(ins, "mdcnf")
            arugment_list = ["python", "pb.py", ins, "true"]
            process = subprocess.Popen(arugment_list,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate(timeout=instance_timeout)
            out.write("{}".format(stdout))
        except subprocess.TimeoutExpired:
            out.write("{}, Timeout, {} \n".format(mono_cnf, -1))

        try:
            mono_cnf = reextension(ins, "mcnf")
            arugment_list = ["python", "pb.py", ins, "true", "false"]
            process = subprocess.Popen(arugment_list,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate(timeout=instance_timeout)
            out.write("{}".format(stdout))
        except subprocess.TimeoutExpired:
            out.write("{}, Timeout, {} \n".format(mono_cnf, -1))

        try:
            non_mono_cnf = reextension(ins, "cnf")
            arugment_list = ["python", "pb.py", ins, "false"]
            process = subprocess.Popen(arugment_list,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate(timeout=instance_timeout)
            out.write("{} \n".format(stdout))
        except subprocess.TimeoutExpired:
            out.write("{}, Timeout, {}\n".format(mono_cnf, -1))

        out.flush()



