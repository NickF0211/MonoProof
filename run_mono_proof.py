import sys

from mono_proof import run_and_prove, Record

if __name__ == "__main__":
    input_gnf = sys.argv[1]

    backward_check = True
    lemma_bitblast = False
    graph_reduction = True
    witness_reduction = True
    running_opt = []
    for i, arg in enumerate(sys.argv):
        if sys.argv[i].startswith("--no-backward-check"):
            backward_check = False
            del (sys.argv[i])
            break

    for i, arg in enumerate(sys.argv):
        if sys.argv[i].startswith("--lemma-bitblast"):
            lemma_bitblast = True
            del (sys.argv[i])
            break
    #
    # for i, arg in enumerate(sys.argv):
    #     if sys.argv[i].startswith("--no-graph-reduction"):
    #         graph_reduction = False
    #         del (sys.argv[i])
    #         break

    for i, arg in enumerate(sys.argv):
        if sys.argv[i].startswith("--no-witness-reduction"):
            witness_reduction = False
            del (sys.argv[i])
            break

    for i, arg in enumerate(sys.argv):
        if sys.argv[i].startswith("--solver-opt"):
            options = sys.argv[i][13:]
            options.lstrip('"')
            options.rsplit('"')
            running_opt = options.split()
            del (sys.argv[i])
            break

    r = Record(input_gnf)
    run_and_prove(input_gnf, r, running_opt=running_opt, witness_reduction=witness_reduction, backward_check=backward_check,
                  lemma_bitblast=lemma_bitblast, graph_reduction=graph_reduction)
    print(str(r))