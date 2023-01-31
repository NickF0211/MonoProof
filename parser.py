from graph import parse_graph, parse_edge, parse_weighted_edge, add_edge
from pb import parse_pb, PB
from reachability import parse_reach
from distance import parse_distance, Distance_LEQ
from acyclic import parse_acyclic, Acyclic
from max_flow import parse_maxflow
from bv import parse_bv, parse_addition, parse_comparsion, parse_const_comparsion, get_bv, GE
from lit import add_lit, write_dimacs, global_inv
import os
from predicate import encode_all, pre_encode
from solver import is_sat, get_model, get_proof, get_blocked_proof, is_rat
from bv import BV
from max_flow import *


def parse_edge_bv(attributes):
    assert len(attributes) == 5
    graph_id, source, target, lit, bv_id = attributes
    add_edge(int(graph_id), int(source), int(target), lit=int(lit), weight=get_bv(int(bv_id)))
    return True


def parse_file(file_name):
    with open(file_name, 'r') as file:
        cnfs = []
        assumption = []
        solve_counter = 0
        while True:
            line = file.readline()
            if line:
                new_assumption = []
                if not parse_line(line, cnfs, new_assumption):
                    assert False
                else:
                    if line.startswith("solve"):
                        assumption = new_assumption
                        solve_counter += 1
                        if solve_counter > 1:
                            print("incremental solving mode is not supported")
            else:
                cnfs += assumption
                return cnfs


def parse_clause(attributes):
    results = set()
    for token in attributes:
        # assert (token.isnumeric() or token.startswith('-'))
        if token == "0":
            return list(results)
        else:
            results.add(add_lit(int(token)))


def parse_header(attributes):
    assert len(attributes) == 3
    signautre, lits, clauses = attributes
    add_lit(int(lits))
    return True


ignore_list = ["node", "symbol", "priority"]


def parse_line(line, cnfs, assumptions= None):
    if not line.strip():
        # if there are formatting issue  with the line, skip
        return True
    line_token = line.split()
    if line_token == []:
        return False
    else:
        header = line_token[0]

        if header.isnumeric() or header.startswith('-'):
            cnfs.append(parse_clause(line_token))
            return True
        elif header == "edge":
            return parse_edge(line_token[1:])
        elif header == "bv":
            sub_header = line_token[1]
            if sub_header == "symbol":
                return True
            if sub_header == "lazy":
                return parse_bv(line_token[2:])
            if sub_header.isdigit():
                return parse_bv(line_token[1:])
            elif sub_header == "+":
                return parse_addition(line_token[2:])
            elif sub_header == "const":
                return parse_const_comparsion(line_token[2:])
            elif sub_header in [">=", "<=", ">", "<", "==", "!="]:
                return parse_comparsion(line_token[1:])
            else:
                return False
        elif header == "weighted_edge":
            return parse_weighted_edge(line_token[1:])
        elif header == "edge_bv":
            return parse_edge_bv(line_token[1:])
        elif header == "reach":
            return parse_reach(line_token[1:])
        elif header.startswith("distance_") or header.startswith("weighted_distance_"):
            return parse_distance(line_token)
        elif header.startswith("maximum_flow"):
            return parse_maxflow(line_token)
        elif header == "p":
            return parse_header(line_token[1:])
        elif header in ignore_list:
            return True
        elif header == "c":
            return True
        elif header == "digraph":
            return parse_graph(line_token[1:])
        elif header == "pb":
            return parse_pb(line_token[1:])
        elif header == "acyclic":
            return parse_acyclic(line_token[1:])
        elif header == "amo":
            # at most one, expand on the spot
            # amo 1374 1592 1620 1636 1659 1719 1753 0
            target_lits = [add_lit(int(i)) for i in line_token[1: -1]]
            for i in range(len(target_lits)):
                for j in range(i + 1, len(target_lits)):
                    cnfs.append([-target_lits[i], -target_lits[j]])
            return True
        elif header == "solve":
            target_lits = [add_lit(int(i)) for i in line_token[1:]]
            if assumptions is not None:
                for l in target_lits:
                    assumptions.append([l])
            return True
        else:
            print(line)
            assert False


def parse_support(support_file):
    with open(support_file, 'r') as file:
        hint_map = {}
        while True:
            line = file.readline()
            if line:
                if "MF witness" in line:
                    tokens = line.split("MF witness")
                    assert (len(tokens) == 2)
                    value, key = tokens
                    key = [int(l) for l in key.split()]
                    key.sort()
                    hint_map[' '.join([str(l) for l in key])] = value
                elif "AC witness" in line:
                    tokens = line.split("AC witness")
                    assert (len(tokens) == 2)
                    value, key = tokens
                    key = [int(l) for l in key.split()]
                    key.sort()
                    hint_map[' '.join([str(l) for l in key])] = value
                else:
                    continue
            else:
                return hint_map


def process_cyclic_witness(predicate, sup):
    tokens = sup.split()[:-2]
    nods = [get_node(predicate.graph, int(i)) for i in tokens]
    return nods


def process_flow_witness(predicate, sup):
    tokens = sup.split()[1:-1]
    assert (len(tokens) % 3 == 0)
    i = 0
    witness = {}
    while i < len(tokens):
        edge = get_edge(predicate.graph, int(tokens[i]), int(tokens[i + 1]))
        flow = int(tokens[i + 2])
        witness[edge] = flow
        i += 3
    return witness


def process_cut_witness(predicate, sup):
    tokens = sup.split()[:-2]
    assert (len(tokens) % 3 == 0)
    i = 0
    pesudo_cut_bv = set()
    pesudo_cut_edge = set()
    while i < len(tokens):
        f = int(tokens[i])
        t = int(tokens[i + 1])
        is_bv = tokens[i + 2] == "flow"
        is_edge = tokens[i + 2] == "edge"
        assert is_bv or is_edge
        if is_bv:
            pesudo_cut_bv.add((int(tokens[i]), int(tokens[i + 1])))
        elif is_edge:
            pesudo_cut_edge.add((int(tokens[i]), int(tokens[i + 1])))

        i += 3

    bv_cut = set([get_edge(predicate.graph, f, t) for f, t in pesudo_cut_bv])
    edge_cut = set([get_edge(predicate.graph, f, t) for f, t in pesudo_cut_edge])

    # if isinstance(predicate.target_flow, int) and len(bv_cut) > predicate.target_flow:
    #    cut = bv_cut.union(edge_cut)
    #    bv_cut = predicate.find_cut(cut, Ωafdbv_cut)
    # asz¸¸¸s¸gfvyuhert len(bv_cut) < predicate.target_flow
    return (bv_cut, edge_cut)


def check_pure_cut(cuts):
    for e in cuts:
        if isinstance(e.cap, BV):
            return False
    return True


large_graph_edge_thresh_hold = 3000


def process_theory_lemma(lemmas, support, constraints, new_constraints, verified_lemmas=None, block_process=False,
                         witness_reduction=True,
                         lemma_bitblast=False, graph_reduction =True):
    # now scan the list, and check what has to be done
    if verified_lemmas is None:
        verified_lemmas = []
    orig_lemma = lemmas[:-1]
    lemmas.sort()
    sup = support.get(' '.join([str(i) for i in lemmas]), None)
    processed_witness = set()
    is_drup = True
    for l in lemmas:
        ac = Acyclic.Collection.get(l, None)
        if ac is not None:
            ac.encode_acyclic_clause(new_constraints)
            assert False

        ac = Acyclic.Collection.get(-l, None)
        if ac is not None:
            if sup is not None:
                support_head = int(sup.split()[-2])
                if sup not in processed_witness and support_head == -ac.lit:
                    ac_witness = process_cyclic_witness(ac, sup)
                    ac.encode_cyclic_clause(ac_witness, new_constraints)
                else:
                    print("encoded")
            else:
                print("we need the support for Cyclic clause")
                assert False

        mf = Maxflow.Collection.get(l, None)

        if mf is not None:
            if sup is not None and witness_reduction:
                support_head = int(sup.split()[-2])
                if sup not in processed_witness and support_head == mf.lit:
                    flow_witness = process_flow_witness(mf, sup)
                    mf.encode_with_hint(flow_witness, True, new_constraints, dynamic=True)
                    # processed_witness.add(sup)
                    is_drup = False
                else:
                    print("hi encoded")
            else:
                # TODO, disable false
                mf.encode(new_constraints, pos=True, neg=False)
                is_drup = False

        mf = Maxflow.Collection.get(-l, None)

        if mf is not None:
            if sup is not None and witness_reduction:
                support_head = int(sup.split()[-2])
                if sup not in processed_witness and support_head == -mf.lit:
                    cut = process_cut_witness(mf, sup)
                    mf.encode_with_hint(cut, False, new_constraints, dynamic=True)
                    # assert is_rat(new_constraints + constraints + global_inv + [[-l] for l in orig_lemma])
                    # assert is_sat(new_constraints + constraints + global_inv)
                    # print("checked")
                    # processed_witness.add(sup)
                    is_drup = check_pure_cut(cut[0])
                else:
                    print("hi encoded")
            else:
                # TODO disbale pos
                mf.encode(new_constraints, neg=True, pos=False)
                is_drup = False

        reach = Reachability.Collection.get(l, None)
        if reach is not None:
            if len(reach.graph.edges) > large_graph_edge_thresh_hold:
                hint = sorted(orig_lemma)[:-1]
                reach.encode_with_hint(hint, True, new_constraints)
                # assert is_rat(constraints + new_constraints + global_inv + [[-l] for l in orig_lemma])
                # assert is_sat(constraints + new_constraints + global_inv)
                # reach.encode(new_constraints)
            else:
                reach.encode(new_constraints, unreach_cond=False, reach_cond=True)

        reach = Reachability.Collection.get(-l, None)
        if reach is not None:
            # if witness_reduction:
            #     threshold = 100
            # else:
            #     threshold = large_graph_edge_thresh_hold

            if witness_reduction:
                hint = sorted(orig_lemma)[1:]
                reach.encode_with_hint(hint, False, new_constraints, force_distance=not witness_reduction)
                # assert is_rat(constraints+new_constraints+global_inv + [[-l] for l in orig_lemma])
                # assert is_sat(constraints+new_constraints+global_inv)
            else:
                # reach.encode(new_constraints, reach_cond = False)
                if not lemma_bitblast:
                    if not graph_reduction:
                        reach.encode(new_constraints, unreach_cond=True, reach_cond=False)
                    else:
                        hint = sorted(orig_lemma)[1:]
                        reach.collect_unreach(hint, new_constraints)
                else:
                    # hint = sorted(orig_lemma)[1:]
                    # reachable = reach.compute_unreachable_graph_with_shortest_distance(hint)
                    # print(len(reachable))
                    # assert reach.src not in reachable
                    # reach.binary_encode(new_constraints, mono=False)
                    reach.binary_encode_unreach_with_hint(new_constraints, sorted(orig_lemma)[1:])
                    is_drup = False
                    # assert not is_sat(new_constraints+global_inv+[[-l] for l in orig_lemma])

        distance = Distance_LEQ.Collection.get(l, None)
        if distance is not None:
            distance.unary_encode(new_constraints)

        distance = Distance_LEQ.Collection.get(-l, None)
        if distance is not None:
            distance.unary_encode(new_constraints)

    if block_process:
        return [orig_lemma], is_drup

    else:
        if is_drup:
            proof = [orig_lemma], True
        else:
            print(orig_lemma)
            proof = get_proof(constraints + global_inv + verified_lemmas + new_constraints, orig_lemma, True), True

        return proof


def scan_proof_obligation(obligation_file, constraints, new_constraints, support, record=None, witness_reduction=True,
                          lemma_bitblast=False, graph_reduction = True):
    # cache_rest()
    verified_lemmas = []
    proofs = []
    # the proof obligation need to be proved backwards
    obligations = []
    with open(obligation_file, 'r') as file:
        lemma_confirmed = None
        while True:
            line = file.readline()
            if line:
                tokens = line.split()
                assert len(tokens) > 0
                header = tokens[0]
                if lemma_confirmed is not None and header == 'Y':
                    obligations.append(lemma_confirmed)
                    lemma_confirmed = None
                elif header == 't':
                    lemma_confirmed = [int(l) for l in tokens[1:]]
            else:
                print("finish reading lemmas")
                break

        if record is not None:
            record.set_theory_obligation(len(obligations))

        reverse_obligation = obligations[::-1]
        processed = 0
        block_process = True
        buffer = []
        for lemma_confirmed in reverse_obligation:
            if not block_process:
                sub_proofs, _ = process_theory_lemma(lemma_confirmed, support, constraints, new_constraints.content,
                                                     verified_lemmas, block_process=False,
                                                     witness_reduction=witness_reduction,
                                                     lemma_bitblast=lemma_bitblast, graph_reduction=graph_reduction)
                is_drup = False
                # verified_lemmas += sub_proofs
                proofs.append(sub_proofs)
                processed += 1
                print(processed)
            else:

                sub_proofs, is_drup = process_theory_lemma(lemma_confirmed, support, constraints,
                                                           new_constraints.content,
                                                           verified_lemmas, block_process=True,
                                                           witness_reduction=witness_reduction,
                                                           lemma_bitblast=lemma_bitblast, graph_reduction=graph_reduction)
                if is_drup:
                    proofs.append(sub_proofs)
                    # processed += 1
                    # print(processed)
                else:
                    buffer += sub_proofs
                    if (len(buffer) > 10000 or lemma_confirmed == reverse_obligation[-1]):
                        sub_proofs = get_blocked_proof(global_inv + new_constraints.content, buffer, optimize=True)
                        proofs.append(sub_proofs)
                        processed += len(buffer)
                        buffer.clear()
                        print(processed)

            if not lemma_bitblast and len(new_constraints.content) > new_constraints.cap and is_drup:
                new_constraints.flush()

        # if there is any pending reachability lemmas to encode
        for reach in Reachability.Collection.values():
            reach.encode_union(new_constraints.content)

        return proofs


def process_binary_lit(lit):
    l1, l2, l3, l4 = lit
    unsigned_int = l1 + (l2 << 7) + (l3 << 14) + (l4 << 21)
    lit = unsigned_int >> 2 if unsigned_int ^ 0b1 else -((unsigned_int - 1) >> 2)
    return lit


def scan_binary_proof(proof_file, record=None, theory_obg=None, proof_fp=None):
    lemmas = 0
    theory_lemmas = 0
    buffer_limit = 2 << 18  # read 256MB once
    in_clause = 0
    cur_binary_content = bytearray()
    with open(proof_file, 'rb') as file:
        content = file.read(buffer_limit)
        cur_clause = []
        while content:
            i = 0
            while i < len(content):
                b = content[i]
                cur_binary_content.append(b)
                if not in_clause:
                    if b == 0x61:
                        in_clause = 1
                    elif b == 0x74:
                        in_clause = 2
                    elif b == 0x64:
                        in_clause = 3
                    else:
                        assert False
                else:
                    if b == 0x00:
                        if in_clause == 2:
                            theory_lemmas += 1
                            if theory_obg:
                                theory_obg.write("t {} 0\n".format(' '.join([str(l) for l in cur_clause])))
                                theory_obg.write("Y\n")
                        elif proof_fp:
                            proof_fp.write(cur_binary_content)
                            # if in_clause == 1:
                            #     proof_fp.write("{}\n".format(' '.join([str(l) for l in cur_clause] + ['0'])))
                            # elif in_clause == 3:
                            #     proof_fp.write("d {}\n".format(' '.join([str(l) for l in cur_clause] + ['0'])))
                        cur_binary_content.clear()
                        lemmas += 1
                        in_clause = 0
                        cur_clause.clear()
                    else:
                        cur_l = 0
                        cur_b = b
                        cur_index = 0
                        while cur_b & 0x80:
                            cur_l += (cur_b & 0x7f) << (7 * cur_index)
                            cur_index += 1
                            i += 1
                            if i >= len(content):
                                content = file.read(buffer_limit)
                                i = 0
                            cur_b = content[i]
                            cur_binary_content.append(cur_b)
                        cur_l += (cur_b & 0x7f) << (7 * cur_index)
                        lit = -(cur_l >> 1) if cur_l & 0b1 else cur_l >> 1
                        cur_clause.append(add_lit(lit))
                        i += 1
                        continue
                i += 1
                continue
            content = file.read(buffer_limit)

    if record is not None:
        record.set_lemma(lemmas)
        record.set_theory_lemma(theory_lemmas)


def scan_proof(proof_file, record=None, theory_obg=None):
    lemmas = 0
    theory_lemmas = 0
    with open(proof_file, 'r') as file:
        while True:
            line = file.readline()
            if line:
                tokens = line.split()
                assert (len(tokens) >= 0)
                header = tokens[0]
                if header == 'c' or header == 'd':
                    continue
                elif header.isnumeric() or header.startswith('-') or header == 't':
                    # in this case, the line is a proof statement
                    lemmas += 1
                    if header == 't':
                        theory_lemmas += 1
                        if theory_obg:
                            theory_obg.write(line)
                            theory_obg.write('Y\n')

                    for lit in tokens:
                        if lit.isnumeric() or lit.startswith('-'):
                            add_lit(int(lit))

                else:
                    print("unknown proof format")
                    assert False
            else:
                break
        print("lemmas: {} ".format(lemmas))
        print("theory lemmas: {} ".format(theory_lemmas))
        if record is not None:
            record.set_lemma(lemmas)
            record.set_theory_lemma(theory_lemmas)


def reextension(source, new_ext, suffix=''):
    pre, ext = os.path.splitext(source)
    return pre + suffix + '.' + new_ext


def extract_cnf(source, cnfs=None):
    target = reextension(source, "cnf")
    # if not cnfs:
    #     cnfs = parse_file(source)
    # write_dimacs(target, cnfs)
    return target


def lit_to_binary(l, bytes):
    u = 2 * l if l > 0 else ((l * -2) + 1)
    while (u >> 7):
        res = u & 0x7f | 0x80
        bytes.append(res)
        u = u >> 7
    res = u & 0x7f
    bytes.append(res)


def write_binary_proof(lemmas, fp, chunk_size=2 << 24):
    bytes = bytearray()
    for lemma in lemmas:
        for step in lemma:
            is_del = False
            if isinstance(step, str):
                is_del = step.startswith("d")
                step = [int(l) for l in step.split()[1:-1]]
            if is_del:
                bytes.append(100)
            else:
                bytes.append(97)
            for l in step:
                lit_to_binary(l, bytes)
            bytes.append(0x00)

    if len(bytes) >= chunk_size:
        fp.write(bytes)
        bytes.clear()
    if bytes:
        fp.write(bytes)
        bytes.clear()


def reformat_proof_binary(proof_file, formated_proof, theory_steps):
    chunk_size = 2 << 24
    with open(formated_proof, 'wb') as new_proof:
        write_binary_proof(theory_steps, new_proof)
        with open(proof_file, 'rb') as proof:
            chunk = proof.read(chunk_size)
            while chunk:
                new_proof.write(chunk)
                chunk = proof.read(chunk_size)


def reformat_proof(proof_file, formated_proof, theory_steps):
    with open(formated_proof, 'w') as new_proof:
        # theory steps are played backward
        i = len(theory_steps) - 1
        while i >= 0:
            proof = theory_steps[i]
            for step in proof:
                if isinstance(step, str) and step.startswith("d"):
                    new_proof.write("{}\n".format(step))
                else:
                    new_proof.write("{} 0\n".format(' '.join([str(i) for i in step])))
            i -= 1
        # now write down the main proof
        with open(proof_file, 'r') as proof:
            while True:
                line = proof.readline()
                if line:
                    if not (line.startswith('t') or line.startswith('d') or (line[0].isnumeric()) or (line[0] == '-')):
                        assert False
                    if not line.startswith('t'):
                        new_proof.write(line)
                    else:
                        continue
                else:
                    break

def preprocess_pb(gnf, output_gnf = None):
    if not output_gnf:
        output_gnf = reextension(gnf, "gnf", "_pb_encoded")
    parse_file(gnf)
    additional_cnfs = []
    for pb in PB.collection:
        pb.pre_encode(additional_cnfs)
        pb.unary_encode(additional_cnfs)

    with open(output_gnf, 'w') as outfile:
        with open(gnf, 'r') as infile:
            line = infile.readline()
            while line:
                if not line.startswith("pb"):
                    outfile.write(line)
                line = infile.readline()
            # now write the encoded pb constraint
            all_clauses = additional_cnfs + global_inv
            for clause in all_clauses:
                outfile.write("{} 0 \n".format(' '.join([str(b) for b in clause])))





# if __name__ == "__main__":
#     line = ' '.join(['pb', '<=', '2', '24', '22855', '22856', '22857', '22858', '22859', '22860', '22861', '22862', '22863', '22864', '22865',
#      '22866', '70672', '70673', '70674', '70675', '70676', '70677', '70678', '70679', '70680', '70681', '70682',
#      '70683', '24', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1',
#      '1', '1', '1', '1'])
#     parse_line(line, [])
#     preprocess_pb("/Users/nickfeng/mono_encoding/test_field/reach.gnf")
#     # w1 = Distance_LEQ.Collection
#     # w2 = w1.pop(1906)
#     # constraint = []
#     # w2.encode(constraint)
#     # for c in constraint:
#     #     print()
#     #     "{} 0 \n".format(' '.join([str(b) for b in c]))
#     # print(constraint)
#     # scan_binary_proof("reach.proof")
'''
model = get_model(cnfs + global_inv)
if model:
    for bv in BV.Bvs.values():
        print("bv {}: {}".format(bv.id, bv.get_value(model)))
else:
    print(get_proof(cnfs + global_inv, optimize=True))
'''