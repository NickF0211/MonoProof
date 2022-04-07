from graph import parse_graph, parse_edge, parse_weighted_edge, add_edge
from reachability import parse_reach
from max_flow import parse_maxflow
from bv import parse_bv, parse_addition, parse_comparsion, parse_const_comparsion, get_bv
from lit import add_lit, write_dimacs
import os

def parse_edge_bv(attributes):
    assert len(attributes) == 5
    graph_id, source, target, lit, bv_id = attributes
    add_edge(int(graph_id), int(source), int(target), get_bv(int(bv_id)), int(lit))
    return True

def parse_file(file_name):
    with open(file_name, 'r') as file:
        cnfs = []
        while True:
            line = file.readline()
            if line:
                if not parse_line(line , cnfs):
                    return False
            else:
                return cnfs


def parse_clause(attributes):
    results = []
    for token in attributes:
        assert (token.isnumeric() or token.startswith('-'))
        if token == "0":
            return results
        else:
           results.append(add_lit(int(token)))

def parse_header(attributes):
    assert len(attributes) == 3
    signautre, lits, clauses = attributes
    add_lit(int(lits))
    return True

def parse_line(line, cnfs):
    line_token = line.split()
    if line_token == []:
        return False
    else:
        header = line_token[0]

        if header.isnumeric() or header.startswith('-'):
            cnfs.append(parse_clause(line_token))
            return True
        if header == "c":
            return True
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
        if header == "p":
            return parse_header(line_token[1:])
        else:
            assert False

def reextension(source, new_ext):
    pre, ext = os.path.splitext(source)
    return pre+'.'+new_ext


def extract_cnf(source):
    target = reextension(source, "cnf")
    cnfs = parse_file(source)
    write_dimacs(target, cnfs)


extract_cnf("diorama_reach.gnf")
