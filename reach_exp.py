import os.path
import sys

from mono_proof import run_and_prove, reset, Record
from glob import glob

if __name__ == "__main__":
    input_directory = sys.argv[1]
    output_csv = sys.argv[2]

    test_files = glob(f"{input_directory}/**/*.gnf", recursive=True)
    with open(output_csv, 'w') as o_file:
        r = Record("test")
        o_file.write("{}\n".format(r.print_header()))
        for file in test_files:
            print(file)
            r = Record(os.path.basename(file))
            try:
                run_and_prove(file, r, running_opt=['-ruc'], witness_reduction=False)
            except:
                pass
            o_file.write("{}\n".format(r.__str__()))
            o_file.flush()
            reset()