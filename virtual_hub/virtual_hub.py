from monosat import *
import random
from cidr import Cidr, extend_cidr_by_oct
from node import C_Node, TGW, H_Node, SubNet, connect, S_Node, LEVEL_PORTS
from random_port_ip_generator import *
from sg import SG


def create_VPC(g:Graph, lb, ub, tgw_prb, single_pred):
    external_node = S_Node(g, Cidr(0, 8), is_internal=False, is_receiver=False)
    central_hub_ip = Cidr(167772160, 8)
    central_hub = H_Node(g, central_hub_ip)
    connect(external_node, central_hub)
    expand_to_child(g, central_hub, lb, ub, tgw_prb, on_path=True)
    target = random.choice(S_Node.Receivers)
    # l1_tgw = TGW.collections[0]
    # c2 = central_hub.subnets[0]
    # c3 = c2.subnets[0]
    # c4 = c3.subnets[0]
    # print(c4)
    r = encode_reach(external_node, target, single_pred=single_pred)
    return r

def expand_to_child(g, parent: C_Node, lb, ub, tgw_prb, on_path = False):
    p_cidr = parent.cidr
    if p_cidr.prefix_len == 32:
        return parent
    else:
        number_of_next_layers = random.randint(lb, ub)
        samples = random.sample(range(255), number_of_next_layers)
        head, tails = samples[0], samples[1:]

        if random.random() <= tgw_prb or on_path:
            tgw_cidr = extend_cidr_by_oct(p_cidr, head)
            tgw = TGW(g, tgw_cidr, tgw_cidr.extend(32))
            # TODO, check if it has an effect here
            connect(parent, tgw)

        should_on_path = on_path
        for sample in tails:
            if p_cidr.prefix_len < 24:
                subnet = SubNet(g, extend_cidr_by_oct(p_cidr, sample))
            else:
                subnet = S_Node(g, ip=extend_cidr_by_oct(p_cidr, sample), is_internal=True, is_sender=False, on_path=should_on_path)


            parent.subnets.append(subnet)
            connect(parent, subnet)
            expand_to_child(g, subnet, lb, ub, tgw_prb, should_on_path)
            should_on_path = False


def encode_reach(src: C_Node, target:C_Node, single_pred = False):
    frame_nums = len(TGW.collections)
    dest_ip = [Var() for _ in range(32)]
    dest_port = [Var() for _ in range(16)]
    processed = set()
    src_ip = [Var() for _ in range(32)]
    src_port = [Var() for _ in range(16)]
    should_consider = set()
    src.process_constraints(0, src_ip, dest_ip, src_port, dest_port, processed)
    if target in processed:
        should_consider.add(0)
    # for every TGW,  spawn a new graph with brand new src ip and src port
    for frame_n in range(1, frame_nums+1):
        processed = set()
        src_ip = [Var() for _ in range(32)]
        src_port = [Var() for _ in range(16)]
        TGW.collections[frame_n-1].process_constraints(frame_n, src_ip, dest_ip, src_port, dest_port, processed)
        if target in processed:
            should_consider.add(frame_n)


    print("adding relational constraints")
    for tgw in TGW.collections:
        tgw.add_internal_edges()

    # forever
    if not single_pred:
        return Or([src.graph.reaches(src.get_node(0), target.get_node(i)) for i in should_consider])
    else:
        final_target = src.graph.addNode("final_target")
        for i in range(frame_nums+1):
            src.graph.addEdge(target.get_node(i), final_target)

        return src.graph.reaches(src.get_node(0), final_target)

def sample_reachability():
    s1 = random.choice(S_Node.Senders)
    s2 = random.choice(S_Node.Receivers)
    return encode_reach(s1, s2)


def tgw_instance(outputFile, lb=5, ub=5, tgw_prb= 1.0, single_pred = False):
    args = []
    Monosat().newSolver(args)

    if outputFile is not None:
        print("Writing output to " + outputFile)
        Monosat().setOutputFile(outputFile)

    g = Graph()
    r = create_VPC(g, lb, ub, tgw_prb, single_pred)
    print("start solving")
    Assert(r)


def reset():
    TGW.collections.clear()
    LEVEL_PORTS.clear()
    S_Node.Receivers.clear()
    S_Node.Senders.clear()
    S_Node.Spokeds.clear()












if __name__ == "__main__":
    outputFile = sys.argv[1]
    children_lb = 3
    children_ub = 3
    tgw_probability = 1.0
    single_pred = True
    if len(sys.argv) >=3:
        children_lb = int(sys.argv[2])
    if len(sys.argv) >= 4:
        children_ub = int(sys.argv[3])
    if len(sys.argv) >= 5:
        tgw_probability = float(sys.argv[4])

    # hubs = sys.argv[2]
    # subnets = sys.argv[3]
    # spokes = sys.argv[4]
    tgw_instance(outputFile, children_lb, children_ub, tgw_probability, single_pred)

