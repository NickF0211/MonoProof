from lit import new_lit, global_inv, TRUE, FALSE, l_reset, Delayed_Equality, CNFWriter

AND_cached_res_f = dict()
AND_cached_res_b = dict()

CNF_writer = None
def set_file_writer(writer:CNFWriter):
    global CNFWriter
    CNFWriter = writer

def flushwriter():
    global CNF_writer
    if CNF_writer is not None:
        if len(CNF_writer.content) > CNF_writer.cap:
            CNF_writer.flush()




cache_lock = False
def lock_cache():
    global cache_lock
    cache_lock = True

def unlock_cache():
    global cache_lock
    cache_lock = False

def is_cache_locked():
    global cache_lock
    return cache_lock

def cache_rest():
    AND_cached_res_f.clear()
    AND_cached_res_b.clear()

def reset():
    l_reset()
    AND_cached_res_f.clear()
    AND_cached_res_b.clear()
    set_file_writer(None)


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

    predicate_lit_f = AND_cached_res_f.get((var1, var2), None)
    predicate_lit_b = AND_cached_res_b.get((var1, var2), None)

    '''
    if forward and not backward:
        if predicate_lit_f is not None:
            return predicate_lit_f
    elif backward and not forward:
        if predicate_lit_b is not None:
            return predicate_lit_b
    elif forward and backward:
        if predicate_lit_f is not None and predicate_lit_b is not None:
            if predicate_lit_f == predicate_lit_b:
                return predicate_lit_f  
    '''

    if predicate_lit_f is not None:
        assert (predicate_lit_b is None or predicate_lit_b == predicate_lit_f)
        predicate_lit = predicate_lit_f
    elif predicate_lit_b is not None:
        assert (predicate_lit_f is None or predicate_lit_b == predicate_lit_f)
        predicate_lit = predicate_lit_b
    else:
        predicate_lit = new_lit()

    assert (predicate_lit_b is None or predicate_lit_f is None or predicate_lit_b == predicate_lit_f)
    if backward and predicate_lit_b is None:
        constraints.append([-predicate_lit, var1])
        constraints.append([-predicate_lit, var2])
    if forward and predicate_lit_f is None:
        constraints.append([predicate_lit, -var1, -var2])

    if not is_cache_locked():
        if forward:
            AND_cached_res_f[(var1, var2)] = predicate_lit
        if backward:
            AND_cached_res_b[(var1, var2)] = predicate_lit

    flushwriter()
    return predicate_lit

def g_AND(var_body, constraints=global_inv, forward=True, backward=True):
    if FALSE() in var_body:
        return FALSE()

    init = TRUE()
    if var_body == []:
        return TRUE()

    var_body = sorted(var_body)

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

def process_delayed_equality(constraints):
    for v1, v2 in Delayed_Equality:
        constraints.append([IFF(v1, v2, constraints)])
    Delayed_Equality.clear()

