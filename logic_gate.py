from lit import new_lit, global_inv, TRUE, FALSE, l_reset

AND_cached_res_f = dict()
AND_cached_res_b = dict()

def reset():
    l_reset()
    AND_cached_res_f.clear()
    AND_cached_res_b.clear()


def AND(var1, var2, constraints=global_inv, forward=True, backward=True):
    if var1 == var2:
        return var1
    if var1 == TRUE():
        return var2
    if var2 == TRUE():
        return var1
    if var1 == FALSE() or var2 == FALSE():
        return FALSE()
    if var1 == -var2:
        return FALSE()

    if var1 > var2:
        temp = var1
        var1 = var2
        var2 = temp

    predicate_lit = None
    if forward and not backward:
        predicate_lit = AND_cached_res_f.get((var1, var2), None)
    elif backward and not forward:
        predicate_lit = AND_cached_res_b.get((var1, var2), None)
    elif forward and backward:
        p_f = AND_cached_res_f.get((var1, var2), None)
        p_b = AND_cached_res_b.get((var1, var2), None)
        if p_f is not None and p_b is not None:
            predicate_lit = AND(p_f, p_b, constraints)

    if predicate_lit is not None:
        return predicate_lit
    else:
        predicate_lit = new_lit()
        if backward:
            constraints.append([-predicate_lit, var1])
            constraints.append([-predicate_lit, var2])
        if forward:
            constraints.append([-var1, -var2, predicate_lit])

        if forward:
            AND_cached_res_f[(var1, var2)] = predicate_lit
        if backward:
            AND_cached_res_f[(var1, var2)] = predicate_lit

        return predicate_lit

def g_AND(var_body, constraints=global_inv, forward=True, backward=True):
    init = TRUE()
    if var_body == []:
        return TRUE()
    for var in var_body:
        init = AND(init, var, constraints, forward=forward, backward=backward)

    return init

def g_OR(var_body, constraints=global_inv, forward=True, backward=True):
    return -g_AND([-var for var in var_body], constraints, forward=backward, backward=forward)

#a bit unncessary
def NOT(var):
    return -var

def OR(var1, var2, constraints=global_inv, forward=True, backward=True):
    return -AND(-var1, -var2, constraints, forward=backward, backward=forward)

def IMPLIES(var1, var2, constraints=global_inv, forward=True, backward=True):
    return OR(-var1, var2, constraints=constraints, forward=forward, backward=backward)


#NonMonotonic
def IFF(var1, var2, constraints=global_inv):
    return AND(IMPLIES(var1, var2, constraints), IMPLIES(var2, var1, constraints), constraints)

def XOR(var1, var2, constraints=global_inv):
    return -IFF(var1, var2, constraints=constraints)

def ITE(C, var1, var2, constraints=global_inv):
    return AND(IMPLIES(C, var1, constraints), IMPLIES(-C, var2, constraints), constraints)

