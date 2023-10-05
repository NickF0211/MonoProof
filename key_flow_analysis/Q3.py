import csv
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



def geo_mean_overflow(content):
    return np.exp(np.log(content).mean())


def comparsion_study(mono_result, bit_blast_result):

    collections ={}
    with open(mono_result, 'r') as file:
        spamreader = csv.reader(file, delimiter=',', quotechar='|')
        for row in spamreader:
            name, solving, proof_preparing, proof_checking = row[0], float(row[2]), float(row[4]), float(row[5])
            proof_verification = proof_preparing + proof_checking

            if proof_verification > 3600:
                proof_verification = 3600

            collections[name] = np.zeros(4)
            collections[name][0] = solving
            collections[name][1] = proof_verification

    with open(bit_blast_result, 'r') as file:
        spamreader = csv.reader(file, delimiter=',', quotechar='|')
        for row in spamreader:
            name, solving, proof_preparing, proof_checking = row[0], float(row[2]), float(row[4]), float(row[5])
            proof_verification = proof_preparing + proof_checking

            if proof_verification > 3600:
                proof_verification = 3600

            collections[name][2] = solving
            collections[name][3] = proof_verification

    # collections = list(filter(lambda x: x[0] > 10, collections))
    collections = list(collections.values())
    collections = sorted(collections, key = lambda x: x[0])
    names = ["{}".format(i) for i in range(1, len(collections) + 1)]
    print(collections)
    collections = np.array(collections)

    mono_solving = collections[:,0]
    mono_proving = collections[:,1]
    bit_solving = collections[:,2]
    bit_proving = collections[:,3]

    print(np.mean(mono_solving))
    print(np.mean(mono_proving))
    print(np.mean(bit_solving))
    print(np.mean(bit_proving))

    # plt.xlim(0, 3600)
    # plt.ylim(0, 3600)
    plt.title("MonoSAT VS Bit-Blasting Proof Checking")
    # plt.plot(plt.xlim(), plt.ylim(), c=".3")
    # plt.scatter(mono_solving, bit_solving, label = "Solving time", color = 'r', s=10)
    # plt.scatter(mono_proving, bit_proving, label=  "Proof Checking time", color='b', s=10)
    # plt.scatter(mono_proving + mono_proving, bit_solving + bit_proving, label="Total time", color='g', s=10)

    barWidth = 0.4
    r1 = np.arange(len(mono_solving))
    r2 = [x + barWidth for x in r1]
    # r3 = [x + 2*barWidth for x in r1]
    # r4 = [x + 3*barWidth for x in r1]
    plt.bar(r1, mono_proving, color='orange', width=barWidth, edgecolor='white', label='MonoSAT Proof Checking BC')
    plt.bar(r2, bit_proving, color='green', width=barWidth, edgecolor='white', label='MonoSAT Proof Checking W/O BC')
    # plt.bar(r3, mono_proving, color='orange', width=barWidth, edgecolor='white', label='MonoSAT Proof Checking')
    # plt.bar(r4, bit_proving, color='green', width=barWidth, edgecolor='white', label='Bitblasting Proof Checking')
    # plt.bar(r4, bit_proving, color='green', width=barWidth, edgecolor='white', label='Bitblasting Proof Checking')


    plt.xlabel("instances")
    plt.ylabel("Time (s)")
    plt.legend()
    plt.show()
    # plt.xlabel('Instances', fontweight='bold')
    #
    # plt.xticks([r + barWidth for r in range(len(solving))], names)
    # plt.yscale("log")
    # # plt.ylim(0, 3600)
    # plt.title("Performance Network Reachability")
    # plt.ylabel("Time (log scale)")
    # plt.legend()
    # plt.show()
    # max_flow_mono = []
    # max_flow_bb = []
    # with open("maxflow_offical.csv", 'r') as file:
    #     spamreader = csv.reader(file, delimiter=',', quotechar='|')
    #     for row in spamreader:
    #         name, solving, proof_preparing, proof_checking = row[0], float(row[2]), float(row[4]), float(row[5])
    #         proof_verification = proof_preparing + proof_checking
    #
    #         total_time =  solving + proof_verification
    #         if total_time > 3600:
    #             total_time = 7200
    #
    #         max_flow_mono.append(total_time)
    #         max_flow_bb.append(float(3600))
    #
    # max_flow_mono = np.array(max_flow_mono)
    # max_flow_bb = np.array(max_flow_bb)
    # all_time_mono = mono_solving + mono_proving
    # all_time_bb  = bit_solving + bit_proving

    # all_time_mono = np.concatenate((all_time_mono ,max_flow_mono))
    # all_time_bb = np.concatenate((all_time_bb, max_flow_bb))
    # print(all_time_bb.shape)
    # adjust_time_mono= []
    # adjust_time_bb = []
    # for i in range(len(all_time_bb)):
    #     if all_time_bb[i] <= 3600:
    #         adjust_time_mono.append(all_time_mono[i])
    #         adjust_time_bb.append(all_time_bb[i])
    # adjust_time_mono = np.array(adjust_time_mono)
    # adjust_time_bb = np.array(adjust_time_bb)
    # adjust_time_mono = np.array([all_time_mono[i] if all_time_bb[i] >= 3600 for i in range(all_time_bb)])
    # adjust_time_bb = np.array([all_time_bb[i] if all_time_bb[i] >= 3600 for i in range(all_time_bb)])
    # penalized = np.array([2*x if x >= 3600 else 3600 for x in all_time_bb])


    # axes = df.
    overhead = mono_proving / bit_proving
    print("On Comparsion")
    print("the geometric mean for the overhead of proof ceritificate: {0:.2%}".format(geo_mean_overflow(overhead)))
    print("the worst-case overhead: {0:.2%}".format(max(overhead)))
    # return overhead

# public_overhead = comparsion_study("key_flow.csv", "key_flow_simple_no_back_offical.csv")
public_overhead = comparsion_study("maxflow_offical.csv", "maxflow_no_back_offical.csv")

#private_overhead = read_over_head("{please hold for the csv}", "Tirso instances")
# total_over_head = np.concatenate((public_overhead, private_overhead))
# print("On the combined instances")
# print("the geometric mean for the overhead of proof ceritificate: {0:.2%}".format(geo_mean_overflow(total_over_head)))
# print("the worst-case overhead: {0:.2%}".format(max(total_over_head)))