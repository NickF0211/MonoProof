import string
import subprocess

from instances.generate_pcrt import make_pcrt
import random
import os

#make_pcrt(args.filename,args.N, args.M, args.constraints, args.seed)
#route(filename, monosat_args,use_maxflow=False, draw_solution=True, outputFile = None)

start_seed = 10
increment = 10
upper_bound = 200
attempts = 2
monosat_time_out = 1500
target_unsat_threshold = 10
monosat_dir = "monosat"

def random_id():
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(10))

N = 20
M = 3

if __name__ == "__main__":
    cur = start_seed
    id = random_id()
    total_unsat = 0
    while cur < upper_bound:
        found_unsat = False
        apt = 0
        while apt < attempts:
            filename = "instances_N_{}_M_{}_C_{}_id_{}_atp_{}".format(N, M, cur, id, apt)
            with open(filename, 'w') as file:
                make_pcrt(file, N, M, cur, seed=None)

            arugment_list = ["timeout", "{}s".format(monosat_time_out), "python3", "router_orig.py", filename]
            process = subprocess.Popen(arugment_list,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate()
            if "s UNSATISFIABLE" in stdout:
                print("UNSAT")
                found_unsat = True
                total_unsat += 1
                if total_unsat >= target_unsat_threshold:
                    exit(20)
            else:
                if "s SATISFIABLE" in stdout:
                    print("SAT")
                else:
                    print("timeout")
                os.remove(filename)

            apt += 1

        if not found_unsat:
            cur += increment

