import csv
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def geo_mean_overflow(content):
    return np.exp(np.log(content).mean())


def read_over_head(filename, benchmark_name):

    collections =[]
    with open(filename, 'r') as file:
        spamreader = csv.reader(file, delimiter=',', quotechar='|')
        for row in spamreader:
            raw_solving, solving, proof_preparing, proof_checking =  float(row[3]), float(row[2]), float(row[4]), float(row[5])
            proof_verification = proof_preparing + proof_checking
            if raw_solving <= 3600 and solving <= 3600:
                collections.append((solving, proof_verification, proof_preparing))

    # collections = list(filter(lambda x: x[0] > 10, collections))
    collections = sorted(collections, key = lambda x: x[0])
    names = ["{}".format(i) for i in range(1, len(collections) + 1)]
    print(collections)
    collections = np.array(collections)

    solving = collections[:,0]
    proving = collections[:,1]
    preparing = collections[:,2]

    barWidth = 0.4
    r1 = np.arange(len(solving))
    r2 = [x + barWidth for x in r1]
    plt.bar(r1, solving, color='#cc1414', width=barWidth, edgecolor='white', label='Solving time')
    plt.bar(r2, proving, color='#1457cc', width=barWidth, edgecolor='white', label='Proving time')
    plt.xlabel('Instances', fontweight='bold')

    plt.xticks([r + barWidth for r in range(len(solving))], names)
    plt.yscale("log")
    # plt.ylim(0, 3600)
    plt.title("Performance Network Reachability")
    plt.ylabel("Time (log scale)")
    plt.legend()
    plt.show()

    # axes = df.
    overhead = preparing / proving
    print("On {}".format(benchmark_name))
    print("the geometric mean for the overhead of proof ceritificate: {0:.2%}".format(geo_mean_overflow(overhead)))
    print("the worst-case overhead: {0:.2%}".format(max(overhead)))
    # return overhead

public_overhead = read_over_head("key_flow.csv", "BGA Escape routing instances")
#private_overhead = read_over_head("{please hold for the csv}", "Tirso instances")
# total_over_head = np.concatenate((public_overhead, private_overhead))
# print("On the combined instances")
# print("the geometric mean for the overhead of proof ceritificate: {0:.2%}".format(geo_mean_overflow(total_over_head)))
# print("the worst-case overhead: {0:.2%}".format(max(total_over_head)))