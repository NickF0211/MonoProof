import glob
from mono_proof import launch_monosat, run_and_prove, Record
from parser import reextension

instances = glob.glob("gnfs/*.gnf")
with open("max_flow.csv", 'w') as outfile:
    outfile.write(Record("test").print_header() + '\n')
    for instance in instances:
        record = Record(instance)
        res = run_and_prove(instance, record, running_opt=["-no-check-solution", "-verb=1", "-theory-order-vsids",
                                                              "-vsids-both", "-decide-theories", "-no-decide-graph-rnd",
                                                              "-lazy-maxflow-decisions", "-conflict-min-cut",
                                                              "-conflict-min-cut-maxflow", "-adaptive-history-clear=5"])
        outfile.write(str(record) + '\n')


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