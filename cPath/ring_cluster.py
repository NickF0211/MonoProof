from monosat import *
import random

# A graph is divided into n clusters of nodes
# For each cluster, there exists a node that is reachable from every other node, and can
# reach every other nodes in the cluster
# cluster may contain sub-cluster if the cluster layer > 1
# At the top level, there are n cluster forms a ring (n edges)
# We assert at most 1 edge is available
# We form n reach predicate between node in cluster i and node in cluster i+1
# We assert more than 1 reach predicate can hold at the same time
# this is UNSAT. 

def generate_group(size, g: Graph, name, layer=0):
    assert size > 2
    all_nodes = []

    if layer:
        nodes = []
        for i in range(size):
            new_node, sub_nods = generate_group(size, g, "{}_sg_i".format(i), layer=layer-1)
            all_nodes += sub_nods
            nodes.append(new_node)
    else:
        nodes = [g.addNode(name = "{}_n_{}".format(name,i)) for i in range(size)]
    # the last node is a hub node
    hub_node = nodes[-1]
    sender_node = nodes[0]

    for i in range(size):
        if i != size- 1:
            if i > 0:
                nodes_before = random.randint(1, i)
                connections = random.sample(range(i), nodes_before)
                for tar in connections:
                    g.addEdge(nodes[i], nodes[tar])

            if i < size:
                nodes_after = random.randint(1, size-i-1)
                connections = random.sample(range(i+1, size), nodes_after)
                for tar in connections:
                    g.addEdge(nodes[i], nodes[tar])

    new_node = g.addNode("{}_connection_node".format(name))
    g.addEdge(hub_node, new_node)
    g.addEdge(new_node, sender_node)
    nodes.append(new_node)
    return new_node, all_nodes + nodes




def generate_path(monosat_args, outputFile, size=50, n =10):
    args = []
    if(len(monosat_args)>0):
        args = " ".join(monosat_args)
        print("MonoSAT args: " + args)
    Monosat().newSolver(args)

    if outputFile is not None:
        print("Writing output to " + outputFile)
        Monosat().setOutputFile(outputFile)

    g = Graph()
    # at top level, lets create N groups with different level of layers
    nodes_collection = []
    hubs_collection = []
    for i in range(n):
        hub, nodes = generate_group(size,g, "hub_{}".format(i), layer=random.randint(0,1))
        hubs_collection.append(hub)
        nodes_collection.append(nodes)

    # now, form a ring between hubs
    ring_edges = []
    for i in range(n-1):
        ring_edges.append(g.addEdge(hubs_collection[i], hubs_collection[i+1]))
    ring_edges.append(g.addEdge(hubs_collection[n-1], hubs_collection[0]))
    # AssertAtMostOne(ring_edges)
    Assert(Not(moreThanOne(ring_edges)))


    reach_collections = []
    for i in range(n-1):
        reach_collections.append(g.reaches(random.choice(nodes_collection[i]), random.choice(nodes_collection[i+1])))
    reach_collections.append(g.reaches(random.choice(nodes_collection[n-1]), random.choice(nodes_collection[0])))
    Assert(moreThanOne(reach_collections))
    # Assert(reach12)

def moreThanOne(list):
    constraints = []
    for i in range(len(list)):
        for j in range(i+1, len(list)):
            constraints.append(And(list[i], list[j]))
    return Or(constraints)

if __name__ == "__main__":
    outputFile = sys.argv[1]
    size = sys.argv[2]
    generate_path([], outputFile, int(size))