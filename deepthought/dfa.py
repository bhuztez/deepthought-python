#!/usr/bin/env python2


class CODE(object):
    START = 0

    MATCH = {
      0: [],
      1: [0],
      2: [8],
      3: [9],
      4: [10],
      5: [1],
      6: [2],
      7: [3],
      8: [4],
      9: [5],
      10: [6],
      11: [7]}

    DFA = {
      0: {0: 1, 1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10, 7: 11, 8: 2, 9: 3, 10: 4},
      1: {0: 1},
      2: {8: 2, 9: 2, 10: 2},
      3: {8: 3, 9: 3, 10: 3},
      4: {10: 4},
      5: {},
      6: {},
      7: {},
      8: {},
      9: {},
      10: {},
      11: {}}


class QUOTE(object):
    START = 1

    MATCH = {
      0: [],
      1: [],
      2: [0]}

    DFA = {
      0: {0: 1, 1: 1, 2: 1},
      1: {0: 2, 1: 0, 2: 1},
      2: {}}


CODE_MAP = [-1,-1,-1,-1,-1,-1,-1,-1,-1,0,0,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,2,-1,-1,-1,-1,1,6,7,-1,-1,4,-1,5,-1,10,10,10,10,10,10,10,10,10,10,3,-1,-1,-1,-1,-1,-1,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,-1,-1,-1,-1,8,-1,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,-1,-1,-1,-1,-1]

SINGLE_QUOTE_MAP = [-1,-1,-1,-1,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,2,2,2,2,2,2,2,0,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,-1]

DOUBLE_QUOTE_MAP = [-1,-1,-1,-1,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,2,2,0,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,-1]


MODE = [
    [CODE, CODE_MAP],
    [QUOTE, SINGLE_QUOTE_MAP],
    [QUOTE, DOUBLE_QUOTE_MAP]]


def next_mode(match, mode):
    if match == 1 and mode == 0:
        return 1
    elif match == 2 and mode == 0:
        return 2
    elif match == 0 and mode > 0:
        return 0
    else:
        return mode


def finish(state, dfa):
    return (dfa.MATCH.get(state, []) or [-1])[0]


def tokens(s, found, state, mode):
    result = []

    while s:
        code = ord(s[0])
        dfa, charmap = MODE[mode]
        code = -1 if code > 127 else charmap[code]
        next_state = dfa.DFA.get(state, {}).get(code, -1)

        if next_state >= 0:
            found += s[0]
            state = next_state
            s = s[1:]
        else:
            match = finish(state, dfa)
            if match < 0:
                return False, mode, found

            result += [(mode, match, found)]

            mode = next_mode(match, mode)
            found = ''
            state = MODE[mode][0].START

    match = finish(state, dfa)
    if match < 0:
        return False, mode, found

    result += [(mode, match, found)]
    return True, result


def convert_tokens(tokens):
    for mode, match, s in tokens:
        if mode == 0 and match in [0,1,2]:
            continue

        if mode == 0:
            if match == 9 and s == 'not':
                yield 11, s
            else:
                yield match, s
        elif mode == 1:
            yield 9, s[:-1]
        elif mode == 2:
            yield 2, s[:-1]

    yield -1, None


def tokenize(s):
    result = tokens(s, '', MODE[0][0].START, 0)

    if result[0]:
        return (True, list(convert_tokens(result[1])))
    else:
        return result

