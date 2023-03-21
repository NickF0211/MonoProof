import numpy as np
import matplotlib.pyplot as plt

a = [1,2,3,4,5]
b = [5,6,7,8]


def plt_cactus(monosat_solving, bit_blast_solving, image_name = "solving_cactus.png"):
    plt.title("Solving instances")
    monosat_solving = np.sort(np.array(monosat_solving, dtype=int))
    bit_blast_solving = np.sort(np.array(bit_blast_solving, dtype=int))
    plt.yscale("log")
    plt.ylim([1, 3600])
    plt.scatter(range(len(monosat_solving)), monosat_solving, marker='o', edgecolors = 'r', facecolors= 'none',
                alpha=0.8, label = "Monosat Solving")
    plt.plot(range(len(monosat_solving)), monosat_solving, c='r')
    plt.scatter( range(len(bit_blast_solving)), bit_blast_solving , marker='v', edgecolors='b', facecolors= 'none',
                 alpha=0.8, label = "BitBlasting Solving")
    plt.plot(range(len(bit_blast_solving)), bit_blast_solving , c= 'b')
    plt.legend()
    plt.title("Catcus plot Solving")
    plt.savefig(image_name)

def plt_cactus_proving(monosat_total, bit_blast_total, image_name ="proving_cactus.png"):
    plt.title("Solving instances")
    monosat_solving = np.sort(np.array(monosat_total, dtype=int))
    bit_blast_solving = np.sort(np.array(bit_blast_total, dtype=int))
    plt.yscale("log")
    plt.ylim([1, 3600])
    plt.scatter(range(len(monosat_solving)), monosat_solving, marker='o', edgecolors = 'r', facecolors= 'none',
                alpha=0.8, label = "Monosat proving")
    plt.plot(range(len(monosat_solving)), monosat_solving, c='r')
    plt.scatter( range(len(bit_blast_solving)), bit_blast_solving , marker='v', edgecolors='b', facecolors= 'none',
                 alpha=0.8, label = "BitBlasting proving")
    plt.plot(range(len(bit_blast_solving)), bit_blast_solving , c= 'b')
    plt.legend()
    plt.title("Catcus plot Proving")
    plt.savefig(image_name)


def plt_cactus_total(monosat_total, bit_blast_total, image_name ="total_cactus.png"):
    plt.title("Solving instances")
    monosat_solving = np.sort(np.array(monosat_total, dtype=int))
    bit_blast_solving = np.sort(np.array(bit_blast_total, dtype=int))
    plt.yscale("log")
    plt.ylim([1, 3600])
    plt.scatter(range(len(monosat_solving)), monosat_solving, marker='o', edgecolors = 'r', facecolors= 'none',
                alpha=0.8, label = "Monosat solving + proving")
    plt.plot(range(len(monosat_solving)), monosat_solving, c='r')
    plt.scatter( range(len(bit_blast_solving)), bit_blast_solving , marker='v', edgecolors='b', facecolors= 'none',
                 alpha=0.8, label = "BitBlasting solving + proving")
    plt.plot(range(len(bit_blast_solving)), bit_blast_solving , c= 'b')
    plt.legend()
    plt.title("Catcus plot Solving + Proving")
    plt.savefig(image_name)
