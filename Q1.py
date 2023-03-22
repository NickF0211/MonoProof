import csv
import numpy as np


def geo_mean_overflow(content):
    return np.exp(np.log(content).mean())


def read_over_head(filename, benchmark_name):
    raws = []
    proofs = []
    with open(filename, 'r') as file:
        spamreader = csv.reader(file, delimiter=',', quotechar='|')
        for row in spamreader:
            raw_solving, solving = float(row[1]), float(row[2])
            if raw_solving <= 3600 and solving <= 3600:
                raws.append(raw_solving)
                proofs.append(solving)

    raws = np.array(raws)
    proofs = np.array(proofs)

    overhead = (proofs - raws) / raws
    print("On {}".format(benchmark_name))
    print("the geometric mean for the overhead of proof ceritificate: {0:.2%}".format(geo_mean_overflow(overhead)))
    print("the worst-case overhead: {0:.2%}".format(max(overhead)))
    return overhead

public_overhead = read_over_head("mono_result/key_flow_bench_new_benchmarks_raw_solving.csv", "Public instances")
#private_overhead = read_over_head("{please hold for the csv}", "Tirso instances")
# total_over_head = np.concatenate((public_overhead, private_overhead))
# print("On the combined instances")
# print("the geometric mean for the overhead of proof ceritificate: {0:.2%}".format(geo_mean_overflow(total_over_head)))
# print("the worst-case overhead: {0:.2%}".format(max(total_over_head)))
