import os.path
import signal
import sys

from mono_proof import run_and_prove, reset, Record, reextension
from glob import glob

def signal_handler(signum, frame):
    if signum == signal.SIGALRM:
        print("timeout {}".format(frame))
        raise TimeoutError

if __name__ == "__main__":
    input_directory = sys.argv[1]
    output_csv = sys.argv[2]
    instance_timeout = 5000
    backward_check=True
    for i,arg in enumerate(sys.argv):
        if sys.argv[i].startswith("--no-backward-check"):
            backward_check = False
            del(sys.argv[i])
            break

    test_files = glob("{}/**/*.gnf".format(input_directory), recursive=True)
    with open(output_csv, 'w') as o_file:
        r = Record("test")
        o_file.write("{}\n".format(r.print_header()))
        for file in test_files:
            print(file)
            r = Record(os.path.basename(file))
            signal.alarm(instance_timeout)
            try:
                run_and_prove(file, r, running_opt=[], witness_reduction=False, backward_check=backward_check)
            except TimeoutError:
                pass
            except Exception as e:
                pass
            finally:
                # reset alarm
                os.remove(reextension(file, "proof"))
                os.remove(reextension(file, "support"))
                os.remove(reextension(file, "ecnf"))
                os.remove(reextension(file, "cnf"))
                os.remove(reextension(file, "obg"))
                signal.alarm(0)
            o_file.write("{}\n".format(r.__str__()))
            o_file.flush()
            reset()