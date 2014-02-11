from . import dfa, slr


def parse_query(s, mod):
    result = dfa.tokenize(s)

    if not result[0]:
        return result

    ast = slr.parse_query(result[1])
    if ast == False:
        return False, "syntax error in query"

    return True, [ (n, (m or mod, f), a)  for (n,m,f,a) in ast]


def parse_clauses(s, mod):
    if s == "":
        return True, []

    result = dfa.tokenize(s)

    if not result[0]:
        return result

    if len(result[1]) == 1:
        return True, []

    ast = slr.parse_clauses(result[1])
    if ast == False:
        return False, "syntax error in rules"

    return True, [
        (head, [ (n, (m or mod, f), a) for (n,m,f,a) in body ])
        for (head, body) in ast]


def build_db(s, mod):
    clauses = parse_clauses(s,mod)

    if not clauses[0]:
        return False

    db = {}

    for (head, body) in clauses[1]:
        p, a = head
        entry = db.get(p, [])

        entry.append(
            ("rule",
             a,
             [ (x,y) for (pos, x, y) in body if pos == True],
             [ (x,y) for (pos, x, y) in body if pos == False]))

        db[p] = entry

    return db


def is_var(v):
    return isinstance(v, tuple) and len(v) == 2 and v[0] == "var"


def reified(v):
    return is_var(v) and isinstance(v[1], int)


class SubstitutionMethods(object):
    __slots__ = ()


    def __getattr__(self, name):
        return self.subst(("var", name))


    def subst(self, key):
        while is_var(key):
            found = False

            s = self
            while s is not nil:
                if s.key[1] == key[1]:
                    key = s.value
                    found = True
                    break

                s = s.parent

            if not found:
                break

        return key


    def ext(self, key, value):
        v = self.subst(value)

        if is_var(v):
            if key[1] == v[1]:
                return False

        return Substitution(self, key, v)


    def exts(self, l):
        s = self

        for (k,v) in l:
            s = s.ext(k,v)

        return s


    def walk(self, vs):
        return [self.subst(v) for v in vs]


    def unify(self, v1, v2):
        v1 = self.subst(v1)
        v2 = self.subst(v2)

        if is_var(v1):
            if is_var(v2) and (v1[1] == v2[1]):
                return self
            return self.ext(v1, v2)

        if is_var(v2):
            return self.ext(v2, v1)

        if v1 == v2:
            return self

        return False


    def items(self):
        s = self

        while s is not nil:
            yield s.key, s.value

            s = s.parent


nil = SubstitutionMethods()


class Substitution(SubstitutionMethods):
    __slots__ = ('parent', 'key', 'value')


    def __init__(self, parent, key, value):
        self.parent = parent
        self.key = key
        self.value = value


def unify_list(a, b):
    if len(a) != len(b):
        return False

    s = nil

    for x,y in zip(a,b):
        s = s.unify(x,y)

        if s == False:
            return False

    return s


def reify(vs, s=None, c=None):
    if s is None and c is None:
        s = nil
        c = 0

    res = []

    for v in vs:
        value = s.subst(v)

        if not is_var(value):
            res.append(value)

        elif reified(value):
            res.append(value)

        else:
            g = ("var", c)
            res.append(g)
            s = s.ext(value, g)
            c += 1

    return (res, s, c)


def subst_of(answer):
    return nil.exts([ (("var",i), ans) for (i, ans) in enumerate(answer) ])



def query(goals, db):
    posgoals = [(x,y) for (pos,x,y) in goals if pos == True]
    neggoals = [(x,y) for (pos,x,y) in goals if pos == False]

    s = nil
    c = 0

    for g in posgoals:
        res, s, c = reify(g[1], s, c)

    r = nil.exts([(v,k) for (k,v) in s.items()])
    a = tuple(("var", i) for i in range(c))

    table = {}
    table[("root",a)] = [[], [], [], False]

    cont(
        [([ ("rule", [r.subst(x) for x in a], posgoals, neggoals) ] , "root", a)],
        table,
        db)

    answers, _, _, _ = table[("root", a)]

    res = []

    for answer in answers:
        res.append(
            nil.exts(
                [(k, subst_of(answer).subst(v)) for (k,v) in s.items() ]))

    return res


def success(parent, s, posgoals, neggoals, waitings, stack, table, db):
    if len(posgoals) > 0:
        p, a = posgoals[0]
        a1 = s.walk(a)
        a2, r, _ = reify(a1)
        a1 = tuple(a1)
        a2 = tuple(a2)
        poslookup((p, a2), [parent, s, r, posgoals[1:], neggoals], waitings, stack, table, db)

    elif len(neggoals) > 0:
        reifiedgoals = []
        goals = []

        for p,a in neggoals:
            a1 = s.walk(a)
            a2, _, _ = reify(a1)
            a1 = tuple(a1)
            a2 = tuple(a2)
            reifiedgoals.append((p,a2))
            goals.append(((p,a2), (p,a)))

        for g in reifiedgoals:
            neglookup(g, [parent, s, goals], waitings, stack, table, db)

    else:
        goal, subst = parent
        items = [(k,s.subst(v)) for k,v in subst.items()]
        s1 = nil.exts(items)
        answer = [s1.subst(("var",i)) for i in range(len(items))]

        answers,poslookups,neglookups,completed = table[goal]

        if answer not in answers:
            answers.append(answer)

            for frame in poslookups:
                waitings.append((answer, frame))


def poslookup(goal, frame, waitings, stack, table, db):
    p, a = goal
    entry = table.get(goal, None)

    if entry is not None:
        answers, poslookups, neglookups, completed = entry

        if not completed:
            poslookups.append(frame)

        for answer in answers:
            waitings.append((answer, frame))
    else:
        table[goal] = [[], [frame], [], False]
        choices = db[p]
        stack.append((choices, p, a))


def neglookup(goal, frame, waitings, stack, table, db):
    p, a = goal
    entry = table.get(goal, None)

    if entry is not None:
        answers, poslookups, neglookups, completed = entry

        if not completed:
            neglookups.append(frame)

    else:
        table[goal] = [[], [], [frame], False]
        choices = db[p]
        stack.append((choices, p, a))


def trace(found, table):
    delta = [ g for g in found]

    while len(delta) > 0:
        nextdelta = []

        for goal in delta:
            _,poss,_,_ = table[goal]

            for (parent, _, _, _, _) in poss:
                g, _ = parent
                if g not in found:
                    found.append(g)
                    nextdelta.append(g)

        delta = nextdelta

    return found


def remove_neglookup(goal, frame, table):
    entry = table[goal]
    negs = entry[2]
    entry[2] = [neg for neg in negs if neg != frame]


def complete(goal, waitings, stack, table, db):
    entry = table[goal]
    answers, _, negs, _ = entry
    entry[1] = []
    entry[2] = []
    entry[3] = True

    empty = len(answers) == 0

    for frame in negs:
        parent, s, goals = frame

        for (reifiedgoal, _) in goals:
            if goal == reifiedgoal:
                continue

            remove_neglookup(reifiedgoal, frame, table)

        neggoals = [g for (r,g) in goals if r != goal]

        if empty:
            success(parent, s, [], neggoals, waitings, stack, table, db)


def cont(stack, table, db):
    while True:
        while len(stack) > 0:
            top = stack.pop()

            if len(top[0]) == 0:
                continue

            head = top[0][0]
            p = top[1]
            a = top[2]

            stack.append((top[0][1:], p, a))
            waitings = []
            call(head, p, a, waitings, stack, table, db)
            proceed(waitings, stack, table, db)


        active = []
        negtargets = []
        
        for goal, frame in table.items():
            _,_,negs,completed = frame

            if completed == True:
                continue

            active.append(goal)

            for parent, _, _ in negs:
                g, _ = parent
                if g not in negtargets:
                    negtargets.append(g)


        negreachable = trace(negtargets, table)
        completed = [g for g in active if g not in negreachable]

        for goal in completed:
            complete(goal, waitings, stack, table, db)

        if len(negreachable) == 0:
            return

        if len(completed) == 0:
            raise Exception("negative loop")

        proceed(waitings, stack, table, db)


def proceed(waitings, stack, table, db):
    while len(waitings) > 0:
        answer, frame = waitings.pop()
        parent, s, r, posgoals, neggoals = frame

        s1 = subst_of(answer)
        r1 = s.exts([(k, s1.subst(v)) for (k,v) in r.items()])

        success(parent, r1, posgoals, neggoals, waitings, stack, table, db)


def call(rule, p, a, waitings, stack, table, db):
    _type, head, posgoals, neggoals = rule

    s = unify_list(a, head)

    if s == False:
        return None

    s1 = nil.exts([(k,v) for (k,v) in s.items() if reified(k)])
    s2 = nil.exts([(k,v) for (k,v) in s.items() if not reified(k)])

    success(((p,a),s1), s2, posgoals, neggoals, waitings, stack, table, db)


class SingleFileContext(object):

    def __init__(self, s):
        self.db = build_db(s, "main")


    def __getitem__(self, key):
        m,f = key

        if m == "main":
            return self.db.get(f, [])

        return []


    def query(self, s):
        goals = parse_query(s, "main")

        if goals[0] == False:
            return False

        return query(goals[1], self)


# ctx = SingleFileContext(
#     "p(a). p(b). q(X,Y): p(X), p(Y), not same(X,Y). same(X,X): p(X).")

# answers = ctx.query("q(X,Y).")

# ctx = SingleFileContext(
#     "c(X,Y): c(X,Z), e(Z,Y). c(X,Y): e(X,Y). e(a,b). e(b,c).")

# answers = ctx.query("c(X,Y).")

# for answer in answers:
#     print answer.X, answer.Y
