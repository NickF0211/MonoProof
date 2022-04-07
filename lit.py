lits = 0

true_lit = 0
false_lit = 0
global_inv = []

stack = []

def push(target):
    assert stack == [] or len(target) >= stack[-1]
    stack.append(len(target))

def pop(target):
    if len(stack) == 0:
        del target[:]
    else:
        f_len = stack.pop(-1)
        del target[f_len:]




def add_lit(num):
    global lits
    if num < 0:
        max_num = -num
    else:
        max_num = num

    if lits < max_num:
        lits = max_num

    return num

def new_lit():
    global lits
    target = lits+1
    lits += 1
    return target

def TRUE():
    global true_lit
    global false_lit
    if true_lit == 0:
        true_lit = new_lit()
        false_lit = -true_lit
        global_inv.append([true_lit])
    return true_lit

def FALSE():
    global false_lit
    global true_lit
    if false_lit == 0:
        false_lit = new_lit()
        true_lit = -false_lit
        global_inv.append([-false_lit])
    return false_lit

def get_lits_num():
    global lits
    return lits

def write_dimacs(filename, clauses):
    global lits
    all_clauses = clauses + global_inv
    with open(filename, 'w') as outfile:
        outfile.write("p cnf {} {} \n".format(str(lits), str(len(all_clauses))))

        for clause in all_clauses:
            outfile.write("{} 0 \n".format(' '.join([str(b) for b in clause])))

def write_proofs(filename, proofs):
    with open(filename, 'w') as outfile:
        for lemma in proofs:
            outfile.write("{} \n".format(lemma))

def l_reset():
    global true_lit, false_lit, lits
    true_lit = 0
    false_lit = 0
    lits = 0
    global_inv.clear()