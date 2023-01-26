import sys

from parser import preprocess_pb

if __name__ == "__main__":
    gnf = sys.argv[1]
    out_gnf = None
    if len(sys.argv) >= 3:
        out_gnf = sys.argv[2]
    preprocess_pb(gnf, out_gnf)