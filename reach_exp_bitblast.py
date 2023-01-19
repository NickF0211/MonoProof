import os.path
import signal
import sys

from bit_blaster import parse_encode_solve_prove
from glob import glob

from mono_proof import Record, reset, reextension


def signal_handler(signum, frame):
    if signum == signal.SIGALRM:
        print("timeout {}".format(frame))
        raise TimeoutError

if __name__ == "__main__":
    input_directory = sys.argv[1]
    output_csv = sys.argv[2]
    instance_timeout = 5000

    test_files = glob(f"{input_directory}/**/*.gnf", recursive=True)
    with open(output_csv, 'w') as o_file:
        r = Record("test")
        o_file.write("{}\n".format(r.print_header()))
        for file in test_files:
            print(file)
            r = Record(os.path.basename(file))
            signal.alarm(instance_timeout)
            try:
                parse_encode_solve_prove(file, r)
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