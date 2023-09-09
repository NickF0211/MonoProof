import glob
from mono_proof import launch_raw_monosat, launch_monosat, Record, reextension
import signal
import os


def signal_handler(signum, frame):
    if signum == signal.SIGALRM:
        print("timeout {}".format(frame))
        raise TimeoutError


signal.signal(signal.SIGALRM, signal_handler)
instance_timeout = 5000
Attempts = 5

instances = glob.glob("gnfs/*.gnf")
solver_location = "/Users/nickfeng/monosat_orig/monosat/monosat"
with open("maxflow_overhead.csv", 'w') as outfile:
    outfile.write(Record("test").print_header() + '\n')
    for instance in instances:
        print(instance)
        record = Record(instance)
        # set timeout for three hours
        try:
            acc_raw_solving = 0
            for i in range(Attempts):
                raw = launch_raw_monosat(instance, options=["-no-check-solution", "-verb=1", "-theory-order-vsids", "-no-decide-theories",
                                                                   "-vsids-both", "-decide-theories",
                                                                   "-no-decide-graph-rnd",
                                                                   "-lazy-maxflow-decisions", "-conflict-min-cut",
                                                                   "-adaptive-history-clear=5"], record=record, solver_location=solver_location)
                acc_raw_solving += record.raw_solving_time
            record.raw_solving_time =  acc_raw_solving / Attempts

            acc_solving = 0
            for i in range(Attempts):
                res = launch_monosat(instance, reextension(instance, "proof"),
                                     reextension(instance, "support"),
                                     reextension(instance, "ecnf"),
                                    options=["-no-check-solution", "-verb=1", "-theory-order-vsids", "-no-decide-theories",
                                                                   "-vsids-both", "-decide-theories",
                                                                   "-no-decide-graph-rnd",
                                                                   "-lazy-maxflow-decisions", "-conflict-min-cut",
                                                                   "-adaptive-history-clear=5"], record=record)
                acc_solving += record.solving_time
            record.solving_time = acc_solving / Attempts
            outfile.write(str(record) + '\n')

        except TimeoutError:
            outfile.write("{} timeout ({} secs) \n".format(instances, instance_timeout))
        except Exception as e:
            print(e)
            outfile.write("{} error) \n".format(instances, instance_timeout))
        finally:
            # reset alarm
            try:
                os.remove(reextension(instance, "proof"))
                os.remove(reextension(instance, "support"))
                os.remove(reextension(instance, "ecnf"))
                os.remove(reextension(instance, "cnf"))
                os.remove(reextension(instance, "obg"))
            except:
                pass
            outfile.flush()

    # inputs = file.readlines()
    # pre_content = ''.join(inputs[:-2])
    # post_content = inputs[-1]
    # declare = inputs[-2]
    # if declare.startswith("maximum_flow_geq"):
    #     declare_token = declare.split()
    #     others = declare_token[:-1]
    #     current_value = int(declare_token[-1])
    #     proof_file = reextension(new_file_name, 'proof')
    #     support_file  =reextension(new_file_name, 'support')
    #     while True:
    #         with open(new_file_name, 'w') as new_file:
    #             new_value_column = others + [str(current_value)]
    #             new_file.write(pre_content + '\n' + ' '.join(new_value_column) + '\n' + post_content )
    #             if run_and_prove(new_file_name, record, running_opt=["-no-check-solution", "-verb=1", "-theory-order-vsids",
    #                         "-vsids-both", "-decide-theories", "-no-decide-graph-rnd",
    #                         "-lazy-maxflow-decisions", "-conflict-min-cut",
    #                         "-conflict-min-cut-maxflow", "-adaptive-history-clear=5"]):
    #                 print("find UNSAT instances with flow {}".format(current_value))
    #                 break
    #             else:
    #                 current_value += 2
    #                 print("increase flow target to {}".format(current_value))
    #
    # else:
    #     continue
