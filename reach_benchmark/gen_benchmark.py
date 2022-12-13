import subprocess

for width in [10, 20, 30]:
    constraint_ratio = width * 2
    for i in range(10):
        random_seed = i
        instance = 'reachability_{}_{}_{}.gnf'.format(width, constraint_ratio, random_seed)
        print(instance)
        arugment_list = ["python3", "reachability_benchmark.py", "--width={}".format(width), "--constraints={}".format(constraint_ratio),
                         "--seed={}".format(random_seed), "--output={}".format(instance)]
        process = subprocess.Popen(arugment_list,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()