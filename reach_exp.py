import glob
import os
import signal
import subprocess
import sys

from mono_proof import Record, run_and_prove
from parser import reextension

def signal_handler(signum, frame):
    if signum == signal.SIGALRM:
        print("timeout {}".format(frame))
        raise TimeoutError

if __name__ == "__main__":
    test_index = sys.argv[1]
    outfile = "reach_{}.csv".format(test_index)

    instance_timeout = 20000
    instances = glob.glob("rech_benchmark/ins{}/*.gnf".format(test_index))

    with open(outfile, 'w') as outfile:
        for ins in instances:
            record = Record(ins)
            # set timeout for three hours
            signal.alarm(instance_timeout)
            try:
                res = run_and_prove(ins, record,
                                    running_opt=["-no-check-solution", "-verb=1", "-theory-order-vsids",
                                                 "-no-decide-theories",
                                                 "-vsids-both", "-decide-theories",
                                                 "-no-decide-graph-rnd",
                                                 "-lazy-maxflow-decisions", "-conflict-min-cut",
                                                 "-adaptive-history-clear=5"], witness_reduction=True)
                outfile.write(str(record) + '\n')
            except TimeoutError:
                outfile.write("{} timeout ({} secs) \n".format(instances, instance_timeout))
            except Exception as e:
                print(e)
                outfile.write("{} error) \n".format(instances, instance_timeout))
            finally:
                # reset alarm
                signal.alarm(0)
                try:
                    os.remove(reextension(ins, "proof"))
                    os.remove(reextension(ins, "support"))
                    os.remove(reextension(ins, "ecnf"))
                    os.remove(reextension(ins, "cnf"))
                    os.remove(reextension(ins, "obg"))
                except:
                    pass



