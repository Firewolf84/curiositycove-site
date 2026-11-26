#!/usr/bin/env python3
"""Generate the 100 adventure levels (10 worlds) for Robot Lab Breakout.
Every lock is built by a generator, then re-solved by daily_tool.solve from its data alone.
Outputs: worlds.json (for the page, hashed answers) and specs/world-N.json (plain answers, for printing)."""
import json, random, re, itertools, base64, os
import daily_tool as T
from worlds_content import WORLDS, WIN_TITLES

AB = T.AB; FONT = T.FONT
FINALS = {l[0] for w in WORLDS for l in w["levels"]} | {"REBOOT", "LOGIC", "ORBIT", "BRAIN", "BYTE"}
GENERIC = ["CODE", "LOOP", "BYTE", "WIRE", "GEAR", "SPARK", "LAMP", "BELL", "DOOR", "KEY", "LOCK", "MAP", "BOOK", "STAR", "MOON", "SUN", "ROBOT",
           "LEVER", "MAGIC", "PUZZLE", "HELLO", "CLUE", "CLEVER", "BRAVE", "HAPPY", "QUICK", "SMART", "SUPER", "TEAM", "FRIEND", "GAMES", "PIZZA", "TOAST"]
SKILL = {"binary": "Binary numbers", "binary5": "Binary letters", "grid": "Following instructions", "spiral": "Algorithms with turns", "cipher": "Caesar cipher",
         "caesar5": "Caesar cipher", "atbash": "Mirror cipher", "a1z26": "Number cipher", "binadd": "Binary addition", "bubble": "Sorting algorithms",
         "sequence": "Patterns", "gates": "Logic gates", "loops": "Loops", "sorter": "If / else decisions", "variables": "Variables", "score": "Loops with if",
         "graph": "Networks and paths", "pixels": "Pixels and images", "coords": "Coordinates", "lineup": "Logical thinking", "maze": "Path finding",
         "mastermind": "Deduction", "nonogram": "Picture logic", "sudoku": "Logic grids", "morse": "Morse code", "pigpen": "Symbol cipher",
         "balance": "Algebra with shapes", "pyramid": "Adding patterns", "flowchart": "Flowcharts", "parity": "Error detection", "checkdigit": "Check digits",
         "sortnet": "Sorting networks", "rle": "Data compression", "stack": "Stacks and queues", "wordsearch": "Word search", "clock": "Clock maths",
         "halving": "Binary search"}
TITLES = {"binary": ["The {N} Lights", "{N} Light Panel", "Blinking {N}"], "binary5": ["{N} Letter Lights", "The Binary Name Tag"],
          "grid": ["{N} Trail", "The {N} Path", "Arrow Walk"], "spiral": ["The Rover Run", "{N} Spiral", "Turn and Go"],
          "cipher": ["The {N} Message", "Shifty Letters", "Secret Note"], "caesar5": ["The {N} Scramble", "Shift It Back"],
          "atbash": ["Mirror Message", "The {N} Mirror"], "a1z26": ["Number Letters", "The {N} Numbers"], "binadd": ["Binary Sum", "The {N} Adder"],
          "bubble": ["Bubble Sort", "The {N} Shuffle"], "sequence": ["What Comes Next?", "The {N} Pattern"], "gates": ["Logic Lights", "The {N} Switches"],
          "loops": ["Flash Loop", "The {N} Light Show"], "sorter": ["The Sorting Machine", "{N} Sorter"], "variables": ["Variable Box", "The {N} Counter"],
          "score": ["Score Keeper", "The {N} Score"], "graph": ["Shortest Route", "{N} Map"], "pixels": ["Pixel Picture", "The {N} Screen"],
          "coords": ["Coordinate Map", "Plot the Points"], "lineup": ["Line-Up Logic", "Who's Where?"], "maze": ["The {N} Maze", "Maze Runner"],
          "mastermind": ["Code Cracker", "The {N} Safe"], "nonogram": ["Picture Logic", "Hidden Picture"], "sudoku": ["Mini Sudoku", "Number Square"],
          "morse": ["Dots and Dashes", "The {N} Radio"], "pigpen": ["Pigpen Code", "The {N} Symbols"], "balance": ["Shape Sums", "The {N} Scales"],
          "pyramid": ["Number Pyramid", "Brick Builder"], "flowchart": ["Follow the Flow", "The {N} Flowchart"], "parity": ["The Flipped Card", "Magic Cards"],
          "checkdigit": ["Check Digits", "Parcel Codes"], "sortnet": ["Sorting Network", "The {N} Bridges"], "rle": ["Squashed Picture", "Run Code"],
          "stack": ["Crate Stack", "The {N} Pile"], "queue": ["The {N} Queue", "Line Up!"], "wordsearch": ["Word Hunt", "{N} Word Search"],
          "clock": ["Clock Maths", "The {N} Clock"], "halving": ["Guess in Half", "Higher or Lower"]}
CATS = {"Ciphers": ["cipher", "caesar5", "atbash", "a1z26", "morse", "pigpen", "binary5"],
        "Binary": ["binary", "binadd", "pixels", "rle", "parity"],
        "Logic": ["lineup", "mastermind", "nonogram", "sudoku", "gates", "balance"],
        "Maps and mazes": ["grid", "spiral", "graph", "maze", "coords"],
        "Algorithms": ["loops", "sorter", "variables", "score", "bubble", "sortnet", "stack", "flowchart", "halving"],
        "Patterns and words": ["sequence", "pyramid", "checkdigit", "clock", "wordsearch"]}
NEW = {"maze", "mastermind", "nonogram", "sudoku", "morse", "pigpen", "balance", "pyramid", "flowchart", "parity", "checkdigit", "sortnet", "rle",
       "stack", "wordsearch", "clock", "halving", "coords", "lineup"}
ALLT = [t for v in CATS.values() for t in v]
SHAPE_NAME = {"tri": "triangle", "sq": "square", "cir": "circle", "star": "star"}


def pick(c, lo, hi):
    pool = [w for w in c["world"]["vocab"] + GENERIC if lo <= len(w) <= hi and w.isalpha() and w not in c["used"] and w not in FINALS]
    w = c["r"].choice(pool); c["used"].add(w); return w


def shift(word, n): return "".join(chr((ord(ch) - 65 + n) % 26 + 65) if ch.isalpha() else ch for ch in word)
def font_rows(a, b): return [FONT[a][i] + "0" + FONT[b][i] for i in range(5)]
def two_digits(r): return str(r.randint(1, 9)), str(r.randint(0, 9))


# ---------- generators: each returns dict(type, d, answer, hints, how) ----------
def g_binary(r, df, c):
    n = 4 if df < 6 else 5; digs = [r.randint(0, 9) for _ in range(n)]; rows = [format(v, "04b") for v in digs]
    on = [str([8, 4, 2, 1][i]) for i, ch in enumerate(rows[0]) if ch == "1"]
    h2 = f"Row 1 has lights on under {' and '.join(on)}, so it makes {digs[0]}." if on else "Row 1 has no lights on, so it makes 0."
    return dict(type="binary", d={"rows": rows}, answer="".join(map(str, digs)), hints=["Each row makes one digit. Add up the numbers above the lights that are ON.", h2], how="Rows make " + ", ".join(map(str, digs)) + ".")


def g_binary5(r, df, c):
    w = pick(c, 3, 5 if df < 6 else 6)
    return dict(type="binary5", d={"intro": "Each row is a letter written in binary, where A = 1, B = 2 and so on up to Z = 26. Add the values of the lit lights, then turn each number into a letter.",
                                  "rows": [format(ord(ch) - 64, "05b") for ch in w]}, answer=w,
                hints=["Add the numbers above the lit lights in each row, then use the alphabet strip.", f"Row 1 makes {ord(w[0]) - 64}, which is the letter {w[0]}."], how=f"{', '.join(str(ord(ch) - 64) for ch in w)} = {w}.")


def path_grid(r, word, spiral):
    for _ in range(800):
        g = [[None] * 5 for _ in range(5)]; sr, sc = r.randrange(5), r.randrange(5); g[sr][sc] = "*"; seen = {(sr, sc)}; pos = (sr, sc); prog = []; f = (-1, 0); ok = True
        for ch in word:
            opts = []
            if not spiral:
                for dn, (a, b) in T.DIRS.items():
                    for n in (1, 2, 3):
                        q = (pos[0] + a * n, pos[1] + b * n)
                        if 0 <= q[0] < 5 and 0 <= q[1] < 5 and q not in seen: opts.append(([dn, n], q, f))
            else:
                for turn in (None, "Turn right", "Turn left"):
                    ff = f if turn is None else ((f[1], -f[0]) if turn == "Turn right" else (-f[1], f[0]))
                    for n in (1, 2):
                        q = (pos[0] + ff[0] * n, pos[1] + ff[1] * n)
                        if 0 <= q[0] < 5 and 0 <= q[1] < 5 and q not in seen: opts.append(((turn, n), q, ff))
            if not opts: ok = False; break
            step, q, f = r.choice(opts)
            if spiral:
                if step[0]: prog.append(step[0])
                prog.append(f"Forward {step[1]}")
            else: prog.append(step)
            g[q[0]][q[1]] = ch; seen.add(q); pos = q
        if ok and (not spiral or any(p.startswith("Turn") for p in prog)):
            for i in range(5):
                for j in range(5):
                    if g[i][j] is None: g[i][j] = r.choice(AB)
            return g, prog
    raise RuntimeError("no path")


def g_grid(r, df, c):
    w = pick(c, 4, 5 if df < 5 else 6); g, prog = path_grid(r, w, False)
    return dict(type="grid", d={"grid": g, "program": prog}, answer=w,
                hints=["Count squares from where you are standing each time, not from the star.", f"The first move lands on the letter {w[0]}."], how=f"The stops spell {w}.")


def g_spiral(r, df, c):
    w = pick(c, 4, 5 if df < 6 else 6); g, prog = path_grid(r, w, True)
    return dict(type="spiral", d={"intro": "The rover starts on the star, facing UP. 'Turn right' and 'Turn left' spin it on the spot without moving. Write down the letter after every Forward move.", "grid": g, "program": prog},
                answer=w, hints=["Keep track of which way the rover is facing. A turn doesn't move it.", f"The first Forward move lands on {w[0]}."], how=f"The letters after each Forward spell {w}.")


def g_cipher(r, df, c):
    w = pick(c, 4, 6); n = r.randint(2, 5) if df < 5 else r.randint(3, 9)
    sent = r.choice(["THE PASSWORD IS {}", "BOLT SAYS {}", "THE SECRET WORD IS {}", "OPEN UP WITH {}", "THE KEY IS {}"]).format(w)
    return dict(type="cipher", d={"enc": shift(sent, n), "shift": n}, answer=w,
                hints=[f"Use the alphabet strip. For every letter, count back {n} places.", f"The first word decodes to {sent.split()[0]}. The code is the last word."], how=f"Decoded: {sent}.")


def g_caesar5(r, df, c):
    w = pick(c, 4, 6); n = r.randint(1, 6) if df < 6 else r.randint(5, 12)
    return dict(type="caesar5", d={"intro": f"Every letter has been shifted {n} places forward in the alphabet. Shift each one {n} places back to read the code word.", "enc": shift(w, n), "shift": n},
                answer=w, hints=[f"Count back {n} letters for each one. After A, go round to Z.", f"The first letter, {shift(w, n)[0]}, goes back to {w[0]}."], how=f"Shift back {n}: {w}.")


def g_atbash(r, df, c):
    w = pick(c, 4, 7)
    return dict(type="atbash", d={"intro": "Mirror code: A swaps with Z, B with Y, C with X, and so on. Use the mirror strip to turn each letter back into the real one.", "enc": T.atb(w)},
                answer=w, hints=["Find each code letter in one row of the strip and read the letter next to it in the other row.", f"{T.atb(w)[0]} is the mirror of {w[0]}."], how=f"Mirror letters: {w}.")


def g_a1z26(r, df, c):
    w = pick(c, 4, 8)
    return dict(type="a1z26", d={"intro": "Each number is a letter's place in the alphabet: A = 1, B = 2 ... Z = 26. Turn the numbers into letters to find the code word.", "nums": [ord(ch) - 64 for ch in w]},
                answer=w, hints=["Use the alphabet strip: the small numbers show each letter's place.", f"{ord(w[0]) - 64} is the letter {w[0]}."], how=f"Letters: {w}.")


def g_binadd(r, df, c):
    wd = 4 if df < 4 else 5 if df < 7 else 6
    while True:
        a, b = r.randint(1, 2 ** wd - 1), r.randint(1, 2 ** wd - 1)
        if a + b < 2 ** wd and bin(a & b).count("1") >= 1: break
    A, B = format(a, f"0{wd}b"), format(b, f"0{wd}b"); s = format(a + b, f"0{wd}b"); last = int(A[-1]) + int(B[-1])
    return dict(type="binadd", d={"intro": f"Add the two binary numbers, starting from the right. Remember 1 + 1 = 10: write 0 and carry 1. The code is the answer in binary, with {wd} digits.", "a": A, "b": B},
                answer=s, hints=["Work from the right-hand column to the left, just like normal adding.", f"The right-hand column is {A[-1]} + {B[-1]} = {['0', '1', '10'][last]}, so write {last % 2}{' and carry 1' if last == 2 else ''}."], how=f"{a} + {b} = {a + b}, which is {s} in binary.")


def bubble_count(lst):
    a = list(lst); sw = 0; first = None
    for i in range(len(a)):
        for j in range(len(a) - 1 - i):
            if a[j] > a[j + 1]: a[j], a[j + 1] = a[j + 1], a[j]; sw += 1
        if first is None: first = list(a)
    return sw, first


def g_bubble(r, df, c):
    n = 4 if df < 4 else 5 if df < 7 else 6
    while True:
        lst = r.sample(range(1, 10), n); sw, first = bubble_count(lst)
        if sw >= 3: break
    return dict(type="bubble", d={"intro": "Bubble sort walks along the row comparing neighbours. If the left number is bigger, they swap. Keep making passes until the row goes from smallest to biggest. The code is the total number of swaps.", "list": lst},
                answer=str(sw), hints=["Write the row out again after every swap so you don't lose track.", f"After the first full pass the row is {', '.join(map(str, first))}."], how=f"{sw} swaps in total.")


def g_sequence(r, df, c):
    while True:
        a = r.randint(1, 20); d1 = r.randint(2, 9); d2 = 0 if df < 4 else r.randint(1, 4)
        seq = [a]; step = d1
        for _ in range(6): seq.append(seq[-1] + step); step += d2
        if seq[-1] < 200: break
    show, nxt = seq[:5], seq[5:7]; gaps = [b - a for a, b in zip(show, show[1:])]
    return dict(type="sequence", d={"intro": "Find the pattern in the numbers. The code is the next two numbers, one after the other.", "seq": show},
                answer=f"{nxt[0]}{nxt[1]}", hints=["Look at the gaps between each number and the next.", f"The gaps are {', '.join(map(str, gaps))}. What comes next?"], how=f"Next: {nxt[0]}, {nxt[1]}.")


def g_gates(r, df, c):
    I = {k: r.randint(0, 1) for k in "ABC"}; ops = ["AND", "OR", "NOT"] + (["XOR"] if df >= 6 else []); lines = []
    for i in range(3 if df < 5 else 4):
        op = r.choice(ops)
        if op == "NOT": lines.append(f"Light {i + 1} = NOT {r.choice('ABC')}")
        else: x, y = r.sample("ABC", 2); lines.append(f"Light {i + 1} = {x} {op} {y}")
    d = {"intro": "Each light follows a logic rule. AND is 1 only if both inputs are 1. OR is 1 if at least one input is 1. NOT flips 1 to 0 and 0 to 1." + (" XOR is 1 if exactly one input is 1." if "XOR" in ops else "") + " The code is each light's value, Light 1 first.", "inputs": I, "gates": lines}
    ans = T.solve({"type": "gates", "d": d})
    return dict(type="gates", d=d, answer=ans, hints=["Swap each letter for its number first, then apply the rule.", f"{lines[0].split(' = ')[0]} works out as {ans[0]}."], how=f"Lights: {', '.join(ans)}.")


def g_loops(r, df, c):
    C = r.sample(["RED", "BLUE", "GREEN", "YELLOW"], 4)
    while True:
        a, b, k = r.randint(2, 4), r.randint(2, 3), r.randint(2, 4); tpl = r.randrange(3 if df >= 4 else 2)
        if tpl == 0: lines = [f"REPEAT {a} TIMES:", f"    flash {C[0]}", f"    flash {C[1]}", f"flash {C[2]}", f"REPEAT {k} TIMES:", f"    flash {C[3]}"]
        elif tpl == 1: lines = [f"REPEAT {a} TIMES:", f"    flash {C[0]}", f"    REPEAT {b} TIMES:", f"        flash {C[1]}", f"flash {C[2]}", f"flash {C[3]}", f"flash {C[2]}"]
        else: lines = [f"REPEAT {a} TIMES:", f"    REPEAT {b} TIMES:", f"        flash {C[0]}", f"    flash {C[1]}", f"    flash {C[2]}", f"REPEAT {k} TIMES:", f"    flash {C[3]}", f"    flash {C[1]}"]
        ans = T.solve({"type": "loops", "d": {"program_lines": lines}})
        if all(ch <= "9" for ch in ans) and len(ans) == 4: break
    return dict(type="loops", d={"program_lines": lines}, answer=ans, hints=["A REPEAT block runs everything indented under it that many times.", "If a REPEAT is inside another REPEAT, multiply: 3 times round the outside and 2 inside means 6."],
                how="RED, BLUE, GREEN, YELLOW counts: " + ", ".join(ans) + ".")


def g_sorter(r, df, c):
    while True:
        items = r.sample(range(1, 16), r.randint(6, 8)); t = r.randint(4, 10); v = r.randrange(3)
        cond = [(f"IF number > {t}:", "ELSE IF number is even:"), ("IF number is odd:", f"ELSE IF number > {t}:"), (f"IF number < {t}:", "ELSE IF number is odd:")][v]
        code = ["FOR each number:", "    " + cond[0], "        drop it in bin A", "    " + cond[1], "        drop it in bin B", "    ELSE:", "        drop it in bin C"]
        ans = T.solve({"type": "sorter", "d": {"items": items, "code": code}})
        if "0" not in ans: break
    first = T.exec_pseudo(code, items[:1])["bins"][0]
    return dict(type="sorter", d={"intro": "The sorting machine drops each number into bin A, B or C. Check the rules in order for every number. The code is how many land in bin A, then bin B, then bin C.", "items": items, "code": code},
                answer=ans, hints=["Check the rules from the top. As soon as one is true, drop the number and move on.", f"The first number, {items[0]}, goes in bin {first}."], how=f"Bins A, B, C: {', '.join(ans)}.")


def g_variables(r, df, c):
    while True:
        v = r.randrange(3); a, n, m, k = r.randint(2, 6), r.randint(2, 4), r.randint(2, 3), r.randint(1, 4)
        if v == 0: code = [f"x = {a}", f"REPEAT {n} TIMES:", f"    x = x * {m}", f"    x = x - {k}", "SHOW x"]
        elif v == 1: code = [f"x = {a}", f"y = {k}", f"REPEAT {n + 1} TIMES:", "    x = x + y", "    y = y + 1", "SHOW x"]
        else: code = [f"x = {a}", f"REPEAT {n} TIMES:", f"    x = x + {k}", "    x = x * 2", "SHOW x"]
        env = T.exec_pseudo(code); out = env["out"][0]
        if 0 < out < 400: break
    first = T.exec_pseudo(code[:-1] + ["SHOW x"] if False else code)
    return dict(type="variables", d={"intro": "A variable is a box holding a number that can change. Follow the program line by line and keep track of every variable. The code is the number it shows at the end.", "code": code},
                answer=str(out), hints=["Write the variables down and cross out the old number each time it changes.", "Do the lines inside the REPEAT in order, then go back to the top of the block."], how=f"x ends at {out}.")


def g_score(r, df, c):
    while True:
        nums = [r.randint(1, 12) for _ in range(5 if df < 6 else 6)]; t = r.randint(4, 8); v = r.randrange(2)
        if v == 0: code = ["score = 0", f"FOR each number in [{', '.join(map(str, nums))}]:", f"    IF number > {t}:", "        score = score + number", "    ELSE:", "        score = score - 1", "SHOW score"]
        else: code = ["score = 10", f"FOR each number in [{', '.join(map(str, nums))}]:", "    IF number is even:", "        score = score + 2", f"    ELSE IF number > {t}:", "        score = score - 3", "    ELSE:", "        score = score + 1", "SHOW score"]
        out = T.exec_pseudo(code)["out"][0]
        if 0 < out < 100: break
    return dict(type="score", d={"intro": "This program checks a list of numbers and keeps a score. Follow it number by number. The code is the score at the end.", "code": code},
                answer=str(out), hints=["Do one number at a time and write the new score after each one.", f"Start with the first number, {nums[0]}, and check the IF line."], how=f"Final score {out}.")


LAYOUTS = [([(0, 1), (1, 0), (1, 2), (2, 0), (2, 2), (3, 1)], [(0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 4), (3, 5), (4, 5)]),
           ([(0, 1), (1, 0), (1, 2), (2, 1), (3, 1)], [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (3, 4), (2, 4)]),
           ([(0, 0), (1, 1), (0, 2), (2, 0), (2, 2), (3, 1)], [(0, 1), (0, 3), (2, 1), (1, 3), (1, 4), (2, 4), (3, 5), (4, 5)])]


def g_graph(r, df, c):
    pos, ed = r.choice(LAYOUTS); names = r.sample(c["world"]["places"], len(pos))
    while True:
        edges = [[names[a], names[b], r.randint(1, 9)] for a, b in ed]; d = {"nodes": {names[i]: list(p) for i, p in enumerate(pos)}, "edges": edges}
        try: best = int(T.solve({"type": "graph", "d": d}))
        except AssertionError: continue
        direct = [w for a, b, w in edges if {a, b} == {names[0], names[-1]}]
        if not direct or direct[0] != best: break
    d["intro"] = f"BOLT needs the shortest route from the {names[0]} to the {names[-1]}. Each path shows how many metres long it is. The code is the total length of the shortest route."
    return dict(type="graph", d=d, answer=str(best), hints=["List a few different routes and add up the numbers along each one.", "The route with the fewest paths isn't always the shortest. Check them all."], how=f"Shortest route = {best} m.")


def g_pixels(r, df, c):
    a, b = two_digits(r)
    return dict(type="pixels", d={"pixel_rows": font_rows(a, b)}, answer=a + b, hints=["Tap every square that has a 1 in it.", "The picture shows two numbers side by side, with an empty column in the middle."], how=f"The pixels draw {a}{b}.")


def g_coords(r, df, c):
    a, b = two_digits(r); rows = font_rows(a, b); pts = [[j + 1, 5 - i] for i in range(5) for j in range(7) if rows[i][j] == "1"]; r.shuffle(pts)
    return dict(type="coords", d={"intro": "The map chip stores a picture as coordinates (across, up). Light up every point on the grid to reveal a two-digit number.", "cols": 7, "points": pts},
                answer=a + b, hints=["The first number goes ACROSS, the second goes UP. (1, 5) is the top-left corner.", "Nothing goes in column 4: it's the gap between the two numbers."], how=f"The points draw {a}{b}.")


def g_lineup(r, df, c):
    n = 4 if df < 7 else 5
    crew = [x for x in c["world"]["crew"]]
    while True:
        names = r.sample(crew, n)
        if len({x[0] for x in names}) == n: break
    for _ in range(400):
        perm = list(names); r.shuffle(perm); P = {nm: i + 1 for i, nm in enumerate(perm)}; cands = []
        for x in names:
            cands += [f"{x} is in space {P[x]}.", f"{x} is not in space {r.choice([k for k in range(1, n + 1) if k != P[x]])}."]
            if P[x] == 1: cands.append(f"{x} is first in line.")
            if P[x] == n: cands.append(f"{x} is last in line.")
            if P[x] != 1: cands.append(f"{x} is not first.")
            if P[x] != n: cands.append(f"{x} is not last.")
            for y in names:
                if x == y: continue
                if P[x] == P[y] + 1: cands.append(f"{x} stands directly to the right of {y}.")
                if P[x] < P[y]: cands.append(f"{x} stands somewhere to the left of {y}.")
                if abs(P[x] - P[y]) == 1 and x < y: cands.append(f"{x} and {y} stand next to each other.")
                if abs(P[x] - P[y]) > 1 and x < y: cands.append(f"{x} and {y} do not stand next to each other.")
        cands = [k for k in cands if "space" not in k or r.random() < 0.25]; r.shuffle(cands); clues = []
        for k in cands:
            clues.append(k)
            if len(T.lineup_check(names, clues)) == 1: break
        if len(T.lineup_check(names, clues)) != 1: continue
        for k in list(clues):
            trial = [x for x in clues if x != k]
            if len(T.lineup_check(names, trial)) == 1: clues = trial
        if 3 <= len(clues) <= 6: break
    ans = "".join(x[0] for x in perm)
    d = {"intro": f"{n} friends, {', '.join(names[:-1])} and {names[-1]}, line up in spaces 1 to {n}. Use the clues to work out the order. The code is the first letter of each name, from space 1 to space {n}.", "robots": names, "clues": clues}
    return dict(type="lineup", d=d, answer=ans, hints=["Start with any clue that tells you exactly where someone stands.", f"{perm[0]} ends up in space 1."], how=f"Order: {', '.join(perm)}.")


def perfect_maze(r, w, h):
    cells = [[0] * w for _ in range(h)]; seen = {(0, 0)}; stack = [(0, 0)]
    while stack:
        y, x = stack[-1]; opts = [(b, (y + dy, x + dx), o) for b, (dy, dx), o in ((1, (-1, 0), 4), (2, (0, 1), 8), (4, (1, 0), 1), (8, (0, -1), 2)) if 0 <= y + dy < h and 0 <= x + dx < w and (y + dy, x + dx) not in seen]
        if not opts: stack.pop(); continue
        b, (ny, nx), o = r.choice(opts); cells[y][x] |= b; cells[ny][nx] |= o; seen.add((ny, nx)); stack.append((ny, nx))
    return ["".join(format(v, "x") for v in row) for row in cells]


def g_maze(r, df, c):
    n = 5 if df < 4 else 6 if df < 7 else 7; w = pick(c, 3, 4 if df < 5 else 5)
    while True:
        cells = perfect_maze(r, n, n); d = {"w": n, "h": n, "cells": cells, "start": [0, 0], "goal": [n - 1, n - 1], "letters": []}
        par = {(0, 0): None}; q = [(0, 0)]
        for y, x in q:
            v = int(cells[y][x], 16)
            for bit, (a, b) in ((1, (-1, 0)), (2, (0, 1)), (4, (1, 0)), (8, (0, -1))):
                if v & bit and (y + a, x + b) not in par: par[(y + a, x + b)] = (y, x); q.append((y + a, x + b))
        path, p = [], (n - 1, n - 1)
        while p: path.append(p); p = par[p]
        path.reverse(); inner = path[1:-1]
        if len(inner) >= len(w) + 3: break
    spots = sorted(r.sample(range(len(inner)), len(w))); off = [p for p in par if p not in path]
    d["letters"] = [[inner[i][0], inner[i][1], ch] for i, ch in zip(spots, w)] + [[y, x, r.choice(AB)] for y, x in r.sample(off, min(len(off), 3 + n // 2))]
    d["intro"] = "Guide the robot from the star to the flag. There's only one way through. Collect the letters on your route, in order. Tap squares to mark your path."
    return dict(type="maze", d=d, answer=w, hints=["Try working backwards from the flag. Dead ends are easier to spot that way.", f"The first letter on the route is {w[0]}."], how=f"Route letters: {w}.")


def g_mastermind(r, df, c):
    n = 3 if df < 5 else 4; digs = "123456"
    def fb(code, g): b = sum(x == y for x, y in zip(code, g)); return b, len(set(code) & set(g)) - b
    allc = ["".join(p) for p in itertools.permutations(digs, n)]
    while True:
        sec = r.choice(allc); cands = list(allc); guesses = []
        while len(cands) > 1 and len(guesses) < 7:
            opts = r.sample([g for g in allc if g != sec], 25)
            if len(guesses) < 1: g = opts[0]
            else: g = min(opts, key=lambda g: (sum(1 for x in cands if fb(x, g) == fb(sec, g)), r.random()))
            b, wt = fb(sec, g); guesses.append([g, b, wt]); cands = [x for x in cands if fb(x, g) == (b, wt)]
        if len(cands) == 1 and 3 <= len(guesses) <= 6: break
    zero = [g for g, b, wt in guesses if b == 0 and wt == 0]
    h1 = f"Guess {zero[0]} scored nothing, so none of its digits are in the code." if zero else "Start with the guess that scored the most ●. Which of its digits could be right?"
    d = {"intro": f"BOLT's safe has a {n}-digit code made from the digits 1 to 6, with no digit used twice. For each guess, ● means a right digit in the right place and ○ means a right digit in the wrong place. Work out the code.", "len": n, "digits": 6, "guesses": guesses}
    return dict(type="mastermind", d=d, answer=sec, hints=[h1, f"The first digit of the code is {sec[0]}."], how=f"The only code that fits every guess is {sec}.")


def g_nonogram(r, df, c):
    while True:
        a, b = two_digits(r); rows = font_rows(a, b); d = {"rows": [T.runs(x) for x in rows], "cols": [T.runs([x[j] for x in rows]) for j in range(7)]}
        try: ans = T.solve({"type": "nonogram", "d": d})
        except AssertionError: continue
        break
    d["intro"] = "Shade squares to make a picture. The numbers by each row and column say how many shaded squares come together in a block, in order. The finished picture shows a two-digit code."
    return dict(type="nonogram", d=d, answer=ans, hints=["Start with rows or columns whose numbers fill most of the line, like a 5 in a column.", "Row 1 looks like this: " + rows[0].replace("1", "■").replace("0", "□")], how=f"The picture shows {ans}.")


def g_sudoku(r, df, c):
    base = ["1234", "3412", "2143", "4321"]; perm = dict(zip("1234", r.sample("1234", 4)))
    g = [[perm[ch] for ch in row] for row in base]
    for band in (0, 2):
        if r.random() < .5: g[band], g[band + 1] = g[band + 1], g[band]
    if r.random() < .5: g = g[2:] + g[:2]
    if r.random() < .5: g = [list(x) for x in zip(*g)]
    for stk in (0, 2):
        if r.random() < .5:
            for row in g: row[stk], row[stk + 1] = row[stk + 1], row[stk]
    sol = ["".join(x) for x in g]; puz = [list(x) for x in sol]; target = 8 if df < 4 else 7 if df < 7 else 6
    cells = [(i, j) for i in range(4) for j in range(4)]; r.shuffle(cells)
    for i, j in cells:
        if sum(ch != "." for row in puz for ch in row) <= target: break
        keep = puz[i][j]; puz[i][j] = "."
        if len(T.sudoku_solutions(["".join(x) for x in puz])) != 1: puz[i][j] = keep
    empt = [(i, j) for i in range(4) for j in range(4) if puz[i][j] == "."]; stars = sorted(r.sample(empt, 4))
    d = {"intro": "Fill the grid so every row, every column and every 2-by-2 box has the numbers 1, 2, 3 and 4. The code is the numbers in the ★ squares, reading left to right, top to bottom.", "grid": ["".join(x) for x in puz], "stars": [list(s) for s in stars]}
    i, j = stars[0]
    return dict(type="sudoku", d=d, answer="".join(sol[i][j] for i, j in stars), hints=["Look for a row, column or box that already has three numbers. The fourth is easy!", f"The first ★ square holds {sol[i][j]}."], how="Solved grid: " + " / ".join(sol) + ".")


def g_morse(r, df, c):
    w = pick(c, 3, 5 if df < 6 else 7)
    return dict(type="morse", d={"enc": " ".join(T.MORSE[ch] for ch in w)}, answer=w, hints=["Each group of dots and dashes is one letter. Find it in the key.", f"The first letter is {w[0]}."], how=f"Decoded: {w}.")


def g_pigpen(r, df, c):
    w = pick(c, 3, 5 if df < 6 else 6); syms = []
    for ch in w:
        k = ord(ch) - 65
        syms.append([0, k % 9, int(k >= 9)] if k < 18 else [1, (k - 18) % 4, int(k >= 22)])
    return dict(type="pigpen", d={"syms": syms}, answer=w, hints=["Match each symbol's shape to the key. Look carefully for a dot!", f"The first symbol is {w[0]}."], how=f"Decoded: {w}.")


def g_balance(r, df, c):
    shapes = ["tri", "sq", "cir"] + (["star"] if df >= 6 else [])
    while True:
        vals = dict(zip(shapes, r.sample(range(1, 10), len(shapes)))); eqs = [[[shapes[0], shapes[0]], 2 * vals[shapes[0]]]]
        pool = [[a, b] for a, b in itertools.combinations(shapes, 2)] + [[a, b, cc] for a, b, cc in itertools.combinations(shapes, 3)] + [[s, s, t] for s in shapes for t in shapes if s != t]
        r.shuffle(pool)
        for p in pool:
            if len(eqs) >= 6: break
            eqs.append([p, sum(vals[s] for s in p)])
            d = {"eqs": eqs, "ask": shapes}
            try: ans = T.solve({"type": "balance", "d": d}); break
            except AssertionError: pass
        else: continue
        if len(eqs) <= 5: break
    names = ", ".join(SHAPE_NAME[s] for s in shapes)
    d = {"intro": f"Each shape stands for a different number from 1 to 9. Use the sums to work out every shape. The code is the {names} numbers, in that order.", "eqs": eqs, "ask": shapes}
    return dict(type="balance", d=d, answer=ans, hints=["Start with the line that has two of the same shape.", f"Two {SHAPE_NAME[shapes[0]]}s make {eqs[0][1]}, so one {SHAPE_NAME[shapes[0]]} is {vals[shapes[0]]}."], how="Values: " + ", ".join(f"{SHAPE_NAME[s]} {vals[s]}" for s in shapes) + ".")


def g_pyramid(r, df, c):
    n = 4 if df < 5 else 5
    while True:
        bot = [r.randint(1, 9 if n == 4 else 6) for _ in range(n)]; full = [bot]
        while len(full[0]) > 1: full.insert(0, [full[0][i] + full[0][i + 1] for i in range(len(full[0]) - 1)])
        rows = [[None] * (i + 1) for i in range(n)]; rows[-1] = list(bot)
        if df >= 4:
            k = r.randrange(n - 1); rows[-1][k] = None; rows[-2][k] = full[-2][k]
        hidden = [(i, j) for i in range(1, n) for j in range(i + 1) if rows[i][j] is None]
        ask = [[0, 0], list(r.choice(hidden))]; d = {"rows": rows, "ask": ask}
        try: ans = T.solve({"type": "pyramid", "d": d})
        except AssertionError: continue
        break
    d = {"intro": "Each brick is the sum of the two bricks underneath it. Work out the missing bricks. The code is the numbers on the ★ bricks, top brick first.", "rows": rows, "ask": ask}
    return dict(type="pyramid", d=d, answer=ans, hints=["Work upwards: add each pair of neighbours in the bottom row.", f"The top brick is {full[0][0]}."], how=f"Top {full[0][0]}, other ★ brick {full[ask[1][0]][ask[1][1]]}.")


def collatz(n):
    k = 0
    while n != 1: n = n // 2 if n % 2 == 0 else 3 * n + 1; k += 1
    return k


def g_flowchart(r, df, c):
    if df < 5:
        while True:
            st, mul, add, lim = r.randint(2, 9), r.choice([2, 2, 3]), r.randint(0, 3), r.choice([50, 100])
            d = {"mode": "grow", "start": st, "mul": mul, "add": add, "limit": lim}; ans = T.solve({"type": "flowchart", "d": d}); laps = 0; n = st
            while n <= lim: n = n * mul + add; laps += 1
            if 3 <= laps <= 6: break
        d["intro"] = "Follow the flowchart from START. Go round the loop until the arrow lets you out. The code is the number at STOP."
        return dict(type="flowchart", d=d, answer=ans, hints=["Write n down each time it changes.", f"First time round: {st} × {mul}{f' + {add}' if add else ''} = {st * mul + add}."], how=f"n ends at {ans} after {laps} loops.")
    lo, hi = (5, 12) if df < 8 else (8, 18)
    st = r.choice([n for n in range(3, 40) if lo <= collatz(n) <= hi])
    d = {"mode": "collatz", "start": st, "intro": "Follow the flowchart from START, keeping track of n and steps. Go round until n reaches 1. The code is the number of steps."}
    nxt = st // 2 if st % 2 == 0 else st * 3 + 1
    return dict(type="flowchart", d=d, answer=str(collatz(st)), hints=["Keep a list: write each new n and add 1 to steps every time round.", f"{st} is {'even' if st % 2 == 0 else 'odd'}, so the first new n is {nxt}."], how=f"{collatz(st)} steps to reach 1.")


def g_parity(r, df, c):
    g = [[r.randint(0, 1) for _ in range(5)] for _ in range(5)]
    for row in g: row.append(sum(row) % 2)
    g.append([sum(g[i][j] for i in range(5)) % 2 for j in range(6)])
    i, j = r.randrange(6), r.randrange(6); g[i][j] ^= 1
    d = {"intro": "A magician laid out these cards so every row and every column had an even number of dark cards. Then one card was secretly flipped! Find it. The code is its row letter and column number, like B4.", "grid": ["".join(map(str, row)) for row in g]}
    return dict(type="parity", d=d, answer="ABCDEF"[i] + str(j + 1), hints=["Count the dark cards in each row. Which row has an odd number?", f"The odd row is row {'ABCDEF'[i]}. Now check the columns."], how=f"Row {'ABCDEF'[i]}, column {j + 1}.")


def g_checkdigit(r, df, c):
    codes = ["".join(str(r.randint(0, 9)) for _ in range(5)) + "?" for _ in range(3)]; d = {"codes": codes}
    ans = T.solve({"type": "checkdigit", "d": d}); ds = [int(x) for x in codes[0][:5]]; parts = [v * (1 if i % 2 == 0 else 2) for i, v in enumerate(ds)]
    d["intro"] = "Every parcel code ends with a check digit. Multiply the digits by 1, 2, 1, 2, 1 (starting from the left) and add up the answers. The check digit is the number you add to make the total a multiple of 10. The code is the three missing check digits."
    return dict(type="checkdigit", d=d, answer=ans, hints=["Do one parcel at a time. Write the five answers before adding them.", f"Parcel 1: {' + '.join(map(str, parts))} = {sum(parts)}, so its check digit is {ans[0]}."], how=f"Check digits: {', '.join(ans)}.")


def g_sortnet(r, df, c):
    n = 4 if df < 6 else 5
    while True:
        ins = r.sample(range(1, 10), n); comps = []
        for _ in range(r.randint(3, 4) if n == 4 else r.randint(4, 6)):
            a, b = sorted(r.sample(range(n), 2)); comps.append([a, b])
        d = {"inputs": ins, "comps": comps}; ans = T.solve({"type": "sortnet", "d": d})
        if ans != "".join(map(str, sorted(ins))) and ans != "".join(map(str, ins)): break
    d["intro"] = "Numbers travel along the wires from left to right. At each bridge the two numbers compare: the smaller one goes to the upper wire and the bigger one to the lower wire. The code is the numbers coming out on the right, top to bottom."
    a, b = comps[0]
    return dict(type="sortnet", d=d, answer=ans, hints=["Work through the bridges from left to right, one at a time, rewriting the column of numbers.", f"At the first bridge, {ins[a]} and {ins[b]} meet: {min(ins[a], ins[b])} goes up."], how=f"Outputs: {', '.join(ans)}.")


def g_rle(r, df, c):
    a, b = two_digits(r); rows = font_rows(a, b)
    enc = [" ".join(f"{len(m.group())}{'B' if m.group()[0] == '1' else 'W'}" for m in re.finditer(r"1+|0+", row)) for row in rows]
    d = {"intro": "To save space, BOLT stores each row of a picture as runs: 3B means 3 dark squares and 1W means 1 light square. Shade the grid row by row to reveal a two-digit number.", "rows": enc}
    return dict(type="rle", d=d, answer=a + b, hints=["Do one row at a time, left to right. The runs in each row add up to 7.", f"Row 1 is {enc[0]}: " + rows[0].replace("1", "■").replace("0", "□")], how=f"The picture shows {a}{b}.")


def g_stack(r, df, c):
    mode = r.choice(["stack", "queue"]); put, take = ("PUSH", "POP") if mode == "stack" else ("JOIN", "SERVE")
    while True:
        letters = r.sample([x for x in AB if x not in "AEIOU"], 6); ops = []; box = 0; out = 0; li = 0
        while li < len(letters) or (box and out < 5):
            if li < len(letters) and (box == 0 or r.random() < 0.55): ops.append(f"{put} {letters[li]}"); li += 1; box += 1
            elif box: ops.append(take); box -= 1; out += 1
            if out >= 5: break
        d = {"mode": mode, "ops": ops}; ans = T.solve({"type": "stack", "d": d})
        if 3 <= len(ans) <= 5: break
    intro = ("A stack is like a pile of crates: PUSH puts a crate on top and POP takes the top crate off. Write down the letter on every crate you POP, in order. That's the code." if mode == "stack"
             else "A queue is like a line at the tuck shop: JOIN adds someone to the back and SERVE takes the person at the front. Write down the letter of everyone served, in order. That's the code.")
    d["intro"] = intro
    return dict(type="stack", d=d, answer=ans, hints=["Draw the pile (or the line) and cross letters out as they leave.", f"The first letter to leave is {ans[0]}."], how=f"Letters taken: {', '.join(ans)}.", tkey=mode if mode == "queue" else "stack")


def g_wordsearch(r, df, c):
    dirs = ["R", "D"] if df < 5 else ["R", "D", "DR"] if df < 8 else ["R", "D", "DR", "L", "U"]
    code = pick(c, 4, 5)
    pool = [w for w in c["world"]["vocab"] + GENERIC if 3 <= len(w) <= 6 and w not in c["used"] and w not in FINALS and w != code]
    for _ in range(3000):
        n = 6; g = [[None] * n for _ in range(n)]; placed = []; cand = r.sample(pool, len(pool))
        for w in cand:
            empt = sum(x is None for row in g for x in row)
            if empt <= len(code): break
            spots = []
            for i in range(n):
                for j in range(n):
                    for dn in dirs:
                        a, b = T.WS_DIRS[dn]; cells = [(i + a * k, j + b * k) for k in range(len(w))]
                        if all(0 <= x < n and 0 <= y < n and g[x][y] in (None, w[k]) for k, (x, y) in enumerate(cells)):
                            new = sum(g[x][y] is None for x, y in cells)
                            if 0 < new <= empt - len(code): spots.append(cells)
            if not spots: continue
            cells = r.choice(spots)
            for k, (x, y) in enumerate(cells): g[x][y] = w[k]
            placed.append(w)
        if sum(x is None for row in g for x in row) != len(code) or not 4 <= len(placed) <= 8: continue
        it = iter(code); g = [[x if x is not None else next(it) for x in row] for row in g]
        d = {"grid": ["".join(row) for row in g], "words": sorted(placed), "dirs": dirs}
        try: ans = T.solve({"type": "wordsearch", "d": d})
        except AssertionError: continue
        if ans == code: break
    else: raise RuntimeError("word search failed")
    for w in placed: c["used"].add(w)
    dirtext = {2: "across and down", 3: "across, down and diagonally", 5: "across, down, diagonally, and even backwards or upwards"}[len(dirs)]
    d["intro"] = f"Find every word in the list. Words go {dirtext}. Tap letters to mark them. The letters left over, read from left to right and top to bottom, spell the code."
    return dict(type="wordsearch", d=d, answer=code, hints=["Cross off each word in the list as you find it.", f"The first leftover letter is {code[0]}."], how=f"Leftover letters: {code}.")


def g_clock(r, df, c):
    st = r.randint(1, 12); steps = [[r.choice("+-"), r.randint(2, 11)] for _ in range(3 if df < 6 else 4)]
    d = {"intro": f"BOLT's clock only goes from 1 to 12. Start at {st} o'clock and follow each move: + means hours later, − means hours earlier. Write the time after every move. The code is all the times, one after the other.", "start": st, "steps": steps}
    ans = T.solve({"type": "clock", "d": d}); first = (st + (steps[0][1] if steps[0][0] == "+" else -steps[0][1]) - 1) % 12 + 1
    return dict(type="clock", d=d, answer=ans, hints=["Count round the clock face. After 12 comes 1 again.", f"After the first move it is {first} o'clock."], how=f"Times: {ans}.")


def g_halving(r, df, c):
    hi = 15 if df < 4 else 31 if df < 7 else 63
    while True:
        t = r.randint(1, hi); d = {"lo": 1, "hi": hi, "target": t}; ans = T.solve({"type": "halving", "d": d}); k = 0; lo, h = 1, hi; gs = []
        while True:
            g = (lo + h) // 2; gs.append(g)
            if g == t: break
            lo, h = (g + 1, h) if t > g else (lo, g - 1)
        if len(gs) >= 3: break
    d["intro"] = f"BOLT's secret number is {t}, from 1 to {hi}. The smart way to find a secret number is to always guess the middle: add the lowest and highest numbers it could be, halve, and round down. Then BOLT says 'higher' or 'lower'. Which guesses would you make? The code is all the guesses, in order."
    return dict(type="halving", d=d, answer=ans, hints=["After each guess, the possible numbers shrink to one side.", f"The first guess is (1 + {hi}) ÷ 2 = {(1 + hi) // 2}."], how="Guesses: " + ", ".join(map(str, gs)) + ".")


GEN = {k[2:]: v for k, v in globals().items() if k.startswith("g_")}
assert set(GEN) == set(ALLT), set(ALLT) ^ set(GEN)


def leaks(level_vis, answers):
    up = level_vis.upper()
    return [a for a in answers if a.isalpha() and len(a) >= 4 and re.search(r"\b" + a + r"\b", up)]


def make_level(r, wi, li, W, prev_types, uses):
    word, name, story, clue = W["levels"][li]; df = 1 + wi * 0.95 + li * 0.1; n = len(word)
    for attempt in range(200):
        c = {"r": r, "world": W, "used": set()}
        weights = {t: ({"coords": 1.4, "rle": 1.8, "nonogram": 2.4, "pixels": 0.7}.get(t, 3 if t in NEW else 1.2)) / (1 + uses[t] * 0.6) for t in ALLT if t not in prev_types}
        types = []
        while len(types) < n:
            ks = [t for t in weights if t not in types]
            if len(types) and len({cat for cat, v in CATS.items() for t in types if t in v}) < len(types):
                pass
            t = r.choices(ks, [weights[k] for k in ks])[0]
            cat = next(k for k, v in CATS.items() if t in v)
            if sum(1 for x in types if x in CATS[cat]) >= 2: continue
            types.append(t)
        locks = []
        for t in types:
            lk = GEN[t](r, df, c)
            got = T.norm(T.solve({"type": lk["type"], "d": lk["d"]}))
            if lk["type"] == "cipher": assert T.norm(lk["answer"]) in T.solve({"type": "cipher", "d": lk["d"]}).split()
            else: assert got == T.norm(lk["answer"]), (t, got, lk["answer"])
            nouns = [x for x in W["nouns"] if word not in x.upper()]
            lk["t"] = r.choice(TITLES[lk.pop("tkey", t)]).replace("{N}", r.choice(nouns)); lk["s"] = SKILL[t]
            locks.append(lk)
        letters = list(word)
        while "".join(letters) == word: r.shuffle(letters)
        for lk, L in zip(locks, letters): lk["r"] = L
        fin_noun = r.choice([x for x in W["nouns"] if word not in x.upper()])
        final = {"answer": word, "title": f"The {fin_noun} Lock", "button": "Finish the world!" if li == 9 else r.choice(["Unlock", "Open it", "Power up", "Crack it"]),
                 "clue": clue, "hints": [f"Read the clue again and try different orders out loud. It has {n} letters.", f"It starts with {word[0]} and ends with {word[-1]}."],
                 "done": f"Lock open! {name} complete. BOLT's screen says {W['screen']}", "winTitle": r.choice(WIN_TITLES)}
        spec = {"key": f"x{wi * 10 + li}", "name": name, "tag": f"World {wi + 1} · Level {li + 1}", "world": W["name"], "story": story, "limit": n * (5 if wi < 5 else 6), "final": final,
                "locks": [{"t": lk["t"], "s": lk["s"], "type": lk["type"], "answer": lk["answer"], "r": lk["r"], "hints": lk["hints"], "how": lk["how"], "d": lk["d"]} for lk in locks]}
        answers = [T.norm(lk["answer"]) for lk in spec["locks"]] + [word]
        vis = json.dumps({"n": name, "s": story, "f": {k: v for k, v in final.items() if k != "answer"}, "l": [{k: v for k, v in lk.items() if k not in ("answer", "how")} for lk in spec["locks"]]})
        if leaks(vis, answers) or len(set(answers)) != len(answers): continue
        for t in types: uses[t] += 1
        return spec, types
    raise RuntimeError(f"could not build level {wi}-{li}")


def page_entry(spec):
    answers = [T.norm(lk["answer"]) for lk in spec["locks"]] + [spec["final"]["answer"]]
    return {"key": spec["key"], "name": spec["name"], "tag": spec["tag"], "story": spec["story"], "limit": spec["limit"],
            "locks": [{"t": lk["t"], "s": lk["s"], "type": lk["type"], "h": T.h(lk["answer"]), "r": lk["r"], "hints": lk["hints"], "max": len(T.norm(lk["answer"])), "d": lk["d"]} for lk in spec["locks"]],
            "final": {k: spec["final"][k] for k in ("title", "button", "clue", "hints", "done", "winTitle")} | {"h": T.h(spec["final"]["answer"])},
            "secret": base64.b64encode(json.dumps(answers)[::-1].encode()).decode()}


if __name__ == "__main__":
    r = random.Random(20261126); uses = {t: 0 for t in ALLT}; out = {"cats": CATS, "worlds": []}; os.makedirs("specs", exist_ok=True)
    for wi, W in enumerate(WORLDS):
        prev = []; specs = []; ents = []
        for li in range(10):
            spec, prev = make_level(r, wi, li, W, prev, uses); specs.append(spec); ents.append(page_entry(spec))
        json.dump(specs, open(f"specs/world-{wi + 1}.json", "w"), ensure_ascii=False, indent=1)
        for s in specs: s.update(colour=W["colour"], screen=W["screen"], blurb=W["blurb"])
        json.dump(specs, open(f"specs/world-{wi + 1}.json", "w"), ensure_ascii=False, indent=1)
        out["worlds"].append({k: W[k] for k in ("name", "icon", "colour", "blurb", "screen")} | {"levels": ents})
    json.dump(out, open("worlds.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print("type use:", sorted(uses.items(), key=lambda kv: -kv[1]))
    print("worlds.json bytes:", os.path.getsize("worlds.json"))
