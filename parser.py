from graph import parse_graph, parse_edge, parse_weighted_edge
from reachability import parse_reach
from max_flow import parse_maxflow
from bv import parse_bv, parse_addition, parse_comparsion, parse_const_comparsion

def parse_edge_bv(attributes):
   pass

def parse_line(line):
    line_token = line.split()
    if line_token == []:
        return False
    else:
        header = line_token[0]
        if header == "digraph":
            return parse_graph(line_token[1:])
        elif header == "edge":
            return parse_edge(line_token[1:])
        elif header == "weighted_edge":
            return parse_weighted_edge(line_token[1:])
        elif header == "edge_bv":
            return parse_edge_bv(line_token[1:])
        elif header == "reach":
            return parse_reach(line_token[1:])
        elif header.startswith("maximum_flow"):
            return parse_maxflow(line_token)
        elif header == "bv":
            sub_header = line_token[1]
            if sub_header.isdigit():
                return parse_bv(line_token[1:])
            elif sub_header == "+":
                return parse_addition(line_token[2:])
            elif sub_header == "const":
                return parse_const_comparsion(line_token[1:])
            elif sub_header in [">=", "<=", ">", "<"]:
                return parse_comparsion(line_token[1:])
            else:
                return False
        else:
            return False