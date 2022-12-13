import glob
import os
import subprocess

def reextension(source, new_ext, suffix=''):
    pre, ext = os.path.splitext(source)
    return pre+suffix+'.'+new_ext

if __name__ == "__main__":
    instances = glob.glob("instances/M_3_C_100/*.pcrt", recursive=True)
    for instance in instances:
        output = reextension(instance, "gnf")
        arugment_list = ["python3", "router.py", instance, "--output", output]
        process = subprocess.Popen(arugment_list,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()