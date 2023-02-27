from monosat import *
from cidr import *
from sg import *
from ult import ge


class C_Node():
    def __init__(self, g: Graph, ip: Cidr):
        self.graph = g
        self.cidr = ip
        self.nodes = []
        self.incoming = set()
        self.outgoing = set()

    def get_node(self, i):
        if len(self.nodes) <= i:
            self.nodes.extend([self.graph.addNode() for j in range(i - len(self.nodes) + 1)])
        return self.nodes[i]
        # return self.node

    def process_constraints(self, i, src_ip, dest_ip, src_port, dest_port, processed):
        if self in processed:
            return

        src_node = self.get_node(i)
        for node in self.outgoing:
            tar_node = node.get_node(i)
            e = self.graph.addEdge(src_node, tar_node)
            self.add_outbound_rule(e, src_ip, dest_ip, src_port, dest_port)
            node.add_inbound_rule(e, src_ip, dest_ip, src_port, dest_port)
            if self.graph.hasEdge(tar_node, src_node):
                # one edge at a time
                _, _, reverse_edge, _ = self.graph.getEdge(tar_node, src_node)
                Assert(Not(And(e, reverse_edge)))

        processed.add(self)

        for node in self.outgoing:
            node.process_constraints(i, src_ip, dest_ip, src_port, dest_port, processed)

    def add_inbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        pass

    def add_outbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        pass

    def __str__(self):
        return "{}: {}".format(type(self), str(self.cidr))

LEVEL_PORTS = []
cur_port =0
for i in range(3):
    LEVEL_PORTS.append(Port(cur_port, cur_port+1024))
    cur_port+= 1024+1

LEVEL_PORTS.append(Port(cur_port))

def get_port_level(i):
    if i <= 3:
        return LEVEL_PORTS[i]
    else:
        return LEVEL_PORTS[3]

def level_difference_encode(old_port, new_port, skip_level):
    base = []
    for i in range(len(LEVEL_PORTS)):
        base.append(Implies(get_port_level(i).compile(old_port), get_port_level(i+skip_level).compile(new_port)))

    return And(base)


def create_layering_routing(src_ip, cidr:Cidr, old_port, new_port, level_width):
    cases =[]
    common_prefix_len = 0
    max_level = cidr.prefix_len // level_width
    while common_prefix_len <= cidr.prefix_len:
        if common_prefix_len:
            level = common_prefix_len // level_width
            level_diff = max_level - level
            cases.append(Implies(Not(cidr.extend(common_prefix_len).compile(src_ip)),
                                 level_difference_encode(old_port, new_port, level_diff)))

        common_prefix_len += level_width

    return And(cases)







class TGW(C_Node):
    collections = []

    def __init__(self, g: Graph, cidr: Cidr, real_cidr = None, parent_width = 8):
        super().__init__(g, cidr)
        if not real_cidr:
            real_cidr = cidr
        self.real_cidr = real_cidr
        self.cidr = cidr
        self.receiving_src_ports = []
        self.send_src_port = None

        TGW.collections.append(self)

    def process_constraints(self, i, src_ip, dest_ip, src_port, dest_port, processed):
        if processed:
            if self not in processed:
                self.receiving_src_ports.append((i, src_port, src_ip))
                # self.graph.addEdge(self.get_node(i), self.get_node(i + 1))
                processed.add(self)
                return
            else:
                return
        else:
            self.send_src_port = (i, src_port)
            super().process_constraints(i, src_ip, dest_ip, src_port, dest_port, processed)

    def add_outbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        Assert(Implies(edge, self.real_cidr.compile(src_ip)))
        # the dest port must be greater than the src port
        Assert(Implies(edge, ge(dest_port, src_port)))

    def add_inbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        pass

    def add_internal_edges(self):
        assert self.send_src_port
        i, sender_src_port = self.send_src_port
        for j, receiver_src_port, receive_src_ip in self.receiving_src_ports:
            edge = self.graph.addEdge(self.get_node(j),  self.get_node(i))
            Assert(Implies(edge,  create_layering_routing(receive_src_ip, self.cidr, receiver_src_port,
                                                          sender_src_port, 8)))



# depend on how munch common prefix they share, allow access different dest ports
#
def create_layering_rules(cidr:Cidr, level_width):
    SG_rules =[]
    common_prefix_len = 0
    while common_prefix_len <= 32:
        level = common_prefix_len // level_width
        if common_prefix_len:
            allowed_ports = Port(0, 1024 * level)
            SG_rules.append(SG_rule(cidr.extend(common_prefix_len), allowed_ports))
        common_prefix_len += level_width
    return SG(SG_rules)


class S_Node(C_Node):
    Spokeds = []
    Senders = []
    Receivers = []

    def __init__(self, g: Graph, ip: Cidr, is_sender=True, is_receiver=True, is_internal = False, parent_level=8,
                 on_path = False):
        super().__init__(g, ip)
        S_Node.Spokeds.append(self)
        self.is_sender = is_sender
        self.is_receiver = is_receiver
        self.cidr = ip
        self.is_internal = True
        if is_internal:
            self.sg = create_layering_rules(self.cidr, parent_level)
        else:
            self.sg = SG([accept_all_sg_rules])

        if is_sender:
            S_Node.Senders.append(self)
        if is_receiver and on_path:
            S_Node.Receivers.append(self)

    def add_outbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        # the policy of outbound to a spoke node is that
        # the src is the spoke ip
        # Assert(Implies(edge, match_cidr(self.src, self.cidr)))
        Assert(Implies(edge, self.cidr.compile(src_ip)))

    def add_inbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        # Assert(Implies(edge, match_cidr(self.dest, self.cidr)))
        Assert(Implies(edge, self.cidr.compile(dest_ip)))
        Assert(Implies(edge, self.sg.compile(src_ip, dest_port)))


class H_Node(C_Node):
    def __init__(self, g: Graph, cidr:Cidr):
        super().__init__(g, cidr)
        self.subnets = []
        self.cidr = cidr

    def add_outbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        pass

    def add_inbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        pass


class SubNet(C_Node):
    def __init__(self, g: Graph, cidr: Cidr, root_level = 8):
        super().__init__(g, cidr)
        self.in_SG = SG([SG_rule(cidr.extend(root_level), accept_all_port)])
        self.cidr = cidr
        self.subnets = []

    def add_outbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        pass

    def add_inbound_rule(self, edge, src_ip, dest_ip, src_port, dest_port):
        # ensure it is a traffic in or or out of the subnet
        Assert(Implies(edge, self.in_SG.compile(src_ip, dest_port)))


def connect(node1: C_Node, node2: C_Node, f=True, b=True):
    if isinstance(node1, S_Node):
        f = f and node1.is_sender
        b = b and node1.is_receiver

    if isinstance(node2, S_Node):
        f = f and node2.is_receiver
        b = b and node2.is_sender

    if f:
        node1.outgoing.add(node2)
        node2.incoming.add(node1)
    if b:
        node2.outgoing.add(node1)
        node1.incoming.add(node2)
