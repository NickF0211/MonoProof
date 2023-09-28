import os.path
import subprocess
import sys

from mono_proof import  Record
from glob import glob

from parser import reextension



instance_timeout = 10


if __name__ == "__main__":
    input_directory = sys.argv[1]
    output_csv = sys.argv[2]

    backward_check=True
    lemma_bitblast = False
    graph_reduction = True

    for i,arg in enumerate(sys.argv):
        if sys.argv[i].startswith("--no-backward-check"):
            backward_check = False
            del(sys.argv[i])
            break

    for i,arg in enumerate(sys.argv):
        if sys.argv[i].startswith("--lemma-bitblast"):
            lemma_bitblast = True
            del(sys.argv[i])
            break

    for i, arg in enumerate(sys.argv):
        if sys.argv[i].startswith("--no-graph-reduction"):
            graph_reduction = False
            del (sys.argv[i])
            break

    test_files = glob("{}/**/*.gnf".format(input_directory), recursive=True)
    with open(output_csv, 'w') as o_file:
        r = Record("test")
        o_file.write("{}\n".format(r.print_header()))
        for file in test_files:
            print(file)
            arugment_list = ["python3", "run_mono_proof.py", file, "--no-backward-check", "--lemma-bitblast", "--no-graph-reduction",
                             "--no-witness-reduction"]

            process = subprocess.Popen(arugment_list, stdout=subprocess.PIPE, universal_newlines=True)

            try:
                stdout, stderr = process.communicate(timeout=instance_timeout)
                o_file.write("{}\n".format(stdout.split('\n')[-1]))
            except subprocess.TimeoutExpired:
                process.kill()
                o_file.write("{}, timeout\n".format(file))
                # o_file.write("{}\n".format(process.communicate()[0]))
            #
            # print(file)
            # r = Record(os.path.basename(file))
            # signal.alarm(instance_timeout)
            # try:
            #     run_and_prove(file, r, running_opt=[], witness_reduction=True, backward_check=backward_check,
            #                   lemma_bitblast=lemma_bitblast, graph_reduction=graph_reduction)
            #     o_file.write(str(r) + '\n')
            # except TimeoutError:
            #     o_file.write("{} timeout ({} secs) \n".format(file, instance_timeout))
            # except Exception as e:
            #     print(e)
            #     o_file.write("{} error) \n".format(file, instance_timeout))
            finally:
                try:
                    if os.path.exists(reextension(file, "proof")):
                        os.remove(reextension(file, "proof"))
                    if os.path.exists(reextension(file, "support")):
                        os.remove(reextension(file, "support"))
                    if os.path.exists(reextension(file, "ecnf")):
                        os.remove(reextension(file, "ecnf"))
                    if os.path.exists(reextension(file, "cnf")):
                        os.remove(reextension(file, "cnf"))
                    if os.path.exists(reextension(file, "obg")):
                        os.remove(reextension(file, "obg"))
                except:
                    pass
                o_file.flush()