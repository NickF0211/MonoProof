import subprocess

from virtual_hub import tgw_instance, reset

if __name__ == "__main__":
    for size_lb in range(6, 10):
        for size_ub in range(size_lb, size_lb+2):
            for prob in range(5, 11):
                prob = prob / 10
                file_name = "key_flow_{}_{}_{}.gnf".format(size_lb, size_ub, prob)
                print("start {}".format(file_name))
                try:
                    arugment_list = ["python3", "virtual_hub.py", file_name, str(size_lb), str(size_ub), str(prob)]
                    process = subprocess.Popen(arugment_list,
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    stdout, stderr = process.communicate(timeout=5000)
                except subprocess.TimeoutExpired:
                    print("{} timeout".format(file_name))
                print("done {}".format(file_name))