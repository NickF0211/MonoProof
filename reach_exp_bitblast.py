import os.path
import sys

from bit_blaster import parse_encode_solve_prove
from glob import glob

from mono_proof import Record, reset

if __name__ == "__main__":
    input_directory = sys.argv[1]
    output_csv = sys.argv[2]


    test_files = glob("{}/**/*.gnf".format(input_directory), recursive=True)
    with open(output_csv, 'w') as o_file:
        r = Record("test")
        o_file.write("{}\n".format(r.print_header()))
        for file in test_files:
            print(file)
            r = Record(os.path.basename(file))
            try:
                parse_encode_solve_prove(file, r)
            except:
                pass
            o_file.write("{}\n".format(r.__str__()))
            o_file.flush()
            reset()