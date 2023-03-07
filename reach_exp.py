import os.path
import sys

from mono_proof import run_and_prove, reset, Record
from glob import glob

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
            r = Record(os.path.basename(file))
            try:
                run_and_prove(file, r, running_opt=[], witness_reduction=False, backward_check=backward_check,
                              lemma_bitblast=lemma_bitblast, graph_reduction=graph_reduction)
            except:
                pass
            o_file.write("{}\n".format(r.__str__()))
            o_file.flush()
            reset()