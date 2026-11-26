#!/usr/bin/env python3
"""Curiosity Cove Code-Break: daily challenge builder and checker.

Usage:  python3 daily_tool.py spec.json daily.json
  spec.json  = one new challenge WITH plain answers (format below)
  daily.json = the current list of published challenges (created if missing)
The tool solves every lock from its own data, refuses anything wrong or
ambiguous, hashes the answers, and writes the updated daily.json (newest 14 kept).

Spec format:
{"date":"YYYY-MM-DD","name":"...","story":"...","limit":20,
 "final":{"answer":"WORD","title":"The ... Lock","button":"Verb","clue":"...","hints":["...","..."],"done":"...","winTitle":"..."},
 "locks":[{"t":"Title","s":"Skill","type":"<type>","answer":"...","r":"L","hints":["...","..."],"d":{...}}]}

Types and their "d" data (all auto-checked):
 binary   {"rows":["0101",...]}                      answer = each row's value (0-9) joined
 binary5  {"intro":..,"rows":["10011",...]}          answer = letters (A=1..Z=26)
 grid     {"grid":5x5 letters with one "*" start,"program":[["right",2],...]}  answer = letter at each stop
 spiral   {"intro":..,"grid":5x5 with "*" start facing UP,"program":["Forward 1","Turn right",...]}  answer = letter after each Forward
 cipher   {"enc":"...","shift":n}  (kid shifts BACK n)  answer = any word(s) of the decoded text, as given
 caesar5  {"intro":..,"enc":"...","shift":n}          answer = decoded text
 atbash   {"intro":..,"enc":"..."}                    answer = decoded text
 a1z26    {"intro":..,"nums":[..]}                    answer = letters
 binadd   {"intro":..,"a":"0101","b":"0011"}          answer = sum in binary, same width as a
 bubble   {"intro":..,"list":[..]}                    answer = number of swaps
 sequence {"intro":..,"seq":[..]}  (constant 1st or 2nd differences)  answer = next two terms joined
 gates    {"intro":..,"inputs":{"A":1,..},"gates":["Light 1 = A AND B","Light 2 = NOT C","Light 3 = A OR B",...]}  answer = outputs joined
 loops    {"program_lines":[pseudo-code with flash RED/BLUE/GREEN/YELLOW]}  answer = counts RED,BLUE,GREEN,YELLOW joined
 sorter   {"intro":..,"items":[..],"code":[pseudo-code with 'drop it in bin A/B/C']}  answer = counts A,B,C joined
 variables{"intro":..,"code":[pseudo-code ending with SHOW x]}   answer = shown value
 score    {"intro":..,"code":[pseudo-code with FOR each number in [..] ... SHOW score]}  answer = shown value
 graph    {"intro":..,"nodes":{"Name":[x0-3,y0-2],..},"edges":[["A","B",w],..]}  start = first node, goal = last node; answer = shortest distance (must be unique)
 pixels   {"pixel_rows":[5 strings of 7 bits]}  answer = 2 digits drawn in the 3x5 font below with a blank middle column
New kinds (each needs an "intro" unless marked [fixed text]):
 maze      {"w":5-7,"h":5-7,"cells":[h strings of w hex digits; open sides 1=N 2=E 4=S 8=W],"start":[r,c],"goal":[r,c],"letters":[[r,c,"L"],..]}
           must be a perfect maze (one route); answer = letters on the route, in order
 mastermind{"len":3|4,"digits":6,"guesses":[["123",black,white],..]}  no repeated digits; answer = the only code that fits
 nonogram  {"rows":[[runs],.. 5 rows],"cols":[[runs],.. 7 cols]}  unique picture of 2 digits in the 3x5 font; answer = the digits
 sudoku    {"grid":4 strings of 4 chars, "." = empty,"stars":[[r,c],..]}  unique 4x4 (2x2 boxes); answer = star cells in order
 morse     {"enc":".- -... / ..."} [fixed text]  answer = decoded letters
 pigpen    {"syms":[[g,i,dot],..]} g=0: # grid cell i 0-8 (A-I, dot J-R); g=1: X cell i 0-3 top,right,bottom,left (S-V, dot W-Z)  [fixed text]
 balance   {"eqs":[[["tri","tri"],10],..],"ask":["tri","sq","cir"]} shapes tri/sq/cir/star, different whole numbers 1-9, unique; answer = ask values
 pyramid   {"rows":[[top],..,[bottom]] with null blanks,"ask":[[r,i],..]} each brick = sum of the two below; unique; answer = ask values
 flowchart {"mode":"collatz","start":n} answer = steps to reach 1 | {"mode":"grow","start":n,"mul":2,"add":0,"limit":100} answer = n when it first passes limit
 parity    {"grid":6 strings of 6 bits, exactly one bit flipped from even rows and columns} answer = row letter A-F + column 1-6
 checkdigit{"codes":["48273?",..]} weights 1,2,1,2.. from the left; check digit makes the total a multiple of 10; answer = check digits
 sortnet   {"inputs":[..],"comps":[[0,1],..]} smaller number goes to the upper wire; answer = outputs top to bottom
 rle       {"rows":["3B 1W 3B",..]} 5 rows of 7 squares, B dark W light; picture = 2 digits in the 3x5 font
 stack     {"mode":"stack","ops":["PUSH R","POP",..]} | {"mode":"queue","ops":["JOIN R","SERVE",..]} answer = letters taken, in order
 wordsearch{"grid":[rows],"words":[..],"dirs":["R","D",..]} each word exactly once; answer = leftover letters in reading order
 clock     {"start":1-12,"steps":[["+",7],["-",3],..]} 12-hour clock; answer = time after each move, joined
 halving   {"lo":1,"hi":31,"target":n} always guess (lo+hi)//2; answer = all guesses joined
 coords    {"cols":7,"points":[[x,y],..]} x 1-7 across, y 1-5 up; picture = 2 digits in the 3x5 font
 lineup    {"robots":[4-5 names with different first letters],"clues":[..]} clue forms: "X is first in line." "X is last in line." "X is in space 2."
           "X is not first." "X is not last." "X is not in space 2." "X stands directly to the right of Y." "X stands somewhere to the left of Y."
           "X and Y stand next to each other." "X and Y do not stand next to each other."  unique; answer = first letters in order
Pseudo-code: 4-space indents; REPEAT n TIMES: / FOR each number in [..]: / IF number is even: / IF number is odd: /
 IF number > n: (also <, >=, <=, ==) / ELSE IF ...: / ELSE: / x = expression / flash COLOUR / drop it in bin X / SHOW x
"""
import json, re, sys, base64, heapq, itertools

FONT = {"0": ["111","101","101","101","111"], "1": ["010","110","010","010","111"], "2": ["111","001","111","100","111"],
        "3": ["111","001","111","001","111"], "4": ["101","101","111","001","001"], "5": ["111","100","111","001","111"],
        "6": ["111","100","111","101","111"], "7": ["111","001","010","010","010"], "8": ["111","101","111","101","111"],
        "9": ["111","101","111","001","111"]}
DIRS = {"right": (0, 1), "left": (0, -1), "up": (-1, 0), "down": (1, 0)}
ALLOWED = set(["binary","binary5","grid","spiral","cipher","caesar5","atbash","a1z26","binadd","bubble","sequence","gates","loops","sorter","variables","score","graph","pixels",
               "maze","mastermind","nonogram","sudoku","morse","pigpen","balance","pyramid","flowchart","parity","checkdigit","sortnet","rle","stack","wordsearch","clock","halving","coords","lineup"])


def h(s):
    s = re.sub(r"[^A-Z0-9]", "", s.upper()); x = 2166136261
    for ch in s:
        x ^= ord(ch); x = (x * 16777619) & 0xFFFFFFFF
    return format(x, "x")


def norm(s): return re.sub(r"[^A-Z0-9]", "", str(s).upper())
def unshift(t, n): return "".join(chr((ord(c) - 65 - n) % 26 + 65) if c.isalpha() else c for c in t.upper())
def atb(t): return "".join(chr(155 - ord(c)) if c.isalpha() else c for c in t.upper())


def run_pseudo(lines):
    py, ind = ["flashes=[];bins=[];out=[]"], []
    for raw in lines:
        if not raw.strip(): continue
        depth = (len(raw) - len(raw.lstrip(" "))) // 4; s = raw.strip(); pad = "    " * depth
        def cond(c):
            c = c.strip()
            m = re.fullmatch(r"(\w+) is even", c)
            if m: return f"{m.group(1)} % 2 == 0"
            m = re.fullmatch(r"(\w+) is odd", c)
            if m: return f"{m.group(1)} % 2 == 1"
            m = re.fullmatch(r"(\w+) (>|<|>=|<=|==|!=) (-?\d+)", c)
            if m: return f"{m.group(1)} {m.group(2)} {m.group(3)}"
            raise ValueError("unsupported condition: " + c)
        if m := re.fullmatch(r"REPEAT (\d+) TIMES:", s): py.append(f"{pad}for _ in range({m.group(1)}):")
        elif m := re.fullmatch(r"FOR each (\w+) in (\[[-\d,\s]*\]):", s): py.append(f"{pad}for {m.group(1)} in {m.group(2)}:")
        elif m := re.fullmatch(r"FOR each (\w+):", s): py.append(f"{pad}for {m.group(1)} in ITEMS:")
        elif m := re.fullmatch(r"ELSE IF (.+):", s): py.append(f"{pad}elif {cond(m.group(1))}:")
        elif m := re.fullmatch(r"IF (.+):", s): py.append(f"{pad}if {cond(m.group(1))}:")
        elif s == "ELSE:": py.append(f"{pad}else:")
        elif m := re.fullmatch(r"flash (RED|BLUE|GREEN|YELLOW)", s): py.append(f"{pad}flashes.append('{m.group(1)}')")
        elif m := re.fullmatch(r"drop it in bin ([ABC])", s): py.append(f"{pad}bins.append('{m.group(1)}')")
        elif m := re.fullmatch(r"SHOW (\w+)", s): py.append(f"{pad}out.append({m.group(1)})")
        elif m := re.fullmatch(r"(\w+) = ([\w\s+\-*]+)", s): py.append(f"{pad}{m.group(1)} = {m.group(2)}")
        else: raise ValueError("unsupported line: " + s)
    return py


def exec_pseudo(lines, items=None):
    env = {"ITEMS": items or []}; exec("\n".join(run_pseudo(lines)), {"__builtins__": {"range": range}}, env); return env


def solve(lk):
    t, d = lk["type"], lk["d"]
    if t == "binary":
        vals = [int(r, 2) for r in d["rows"]]; assert all(len(r) == 4 for r in d["rows"]) and all(v <= 9 for v in vals), "binary rows must be 4 bits worth 0-9"
        return "".join(map(str, vals))
    if t == "binary5":
        assert all(len(r) == 5 and 1 <= int(r, 2) <= 26 for r in d["rows"]); return "".join(chr(64 + int(r, 2)) for r in d["rows"])
    if t in ("grid", "spiral"):
        g = d["grid"]; assert len(g) == 5 and all(len(r) == 5 for r in g); starts = [(i, j) for i in range(5) for j in range(5) if g[i][j] == "*"]; assert len(starts) == 1
        r, c = starts[0]; out = ""
        if t == "grid":
            for dr, n in d["program"]:
                a, b = DIRS[dr]; r += a * n; c += b * n; assert 0 <= r < 5 and 0 <= c < 5, "path leaves grid"; out += g[r][c]
        else:
            a, b = -1, 0
            for step in d["program"]:
                if step == "Turn right": a, b = b, -a
                elif step == "Turn left": a, b = -b, a
                else:
                    n = int(re.fullmatch(r"Forward (\d)", step).group(1)); r += a * n; c += b * n; assert 0 <= r < 5 and 0 <= c < 5, "path leaves grid"; out += g[r][c]
        assert "*" not in out; return out
    if t == "cipher": return unshift(d["enc"], d["shift"])
    if t == "caesar5": return unshift(d["enc"], d["shift"])
    if t == "atbash": return atb(d["enc"])
    if t == "a1z26": assert all(1 <= n <= 26 for n in d["nums"]); return "".join(chr(64 + n) for n in d["nums"])
    if t == "binadd":
        w = len(d["a"]); s = int(d["a"], 2) + int(d["b"], 2); assert s < 2 ** w, "sum overflows width"; return format(s, f"0{w}b")
    if t == "bubble":
        a = list(d["list"]); sw = 0
        for i in range(len(a)):
            for j in range(len(a) - 1 - i):
                if a[j] > a[j + 1]: a[j], a[j + 1] = a[j + 1], a[j]; sw += 1
        return str(sw)
    if t == "sequence":
        s = d["seq"]; d1 = [b - a for a, b in zip(s, s[1:])]
        if len(set(d1)) == 1: n1 = s[-1] + d1[0]; n2 = n1 + d1[0]
        else:
            d2 = [b - a for a, b in zip(d1, d1[1:])]; assert len(set(d2)) == 1, "sequence needs constant 1st or 2nd differences"
            g1 = d1[-1] + d2[0]; n1 = s[-1] + g1; n2 = n1 + g1 + d2[0]
        return f"{n1}{n2}"
    if t == "gates":
        I = d["inputs"]; out = ""
        for gl in d["gates"]:
            e = gl.split("=", 1)[1].strip()
            if m := re.fullmatch(r"NOT (\w)", e): v = 1 - I[m.group(1)]
            elif m := re.fullmatch(r"(\w) (AND|OR|XOR) (\w)", e):
                x, y = I[m.group(1)], I[m.group(3)]; v = {"AND": x & y, "OR": x | y, "XOR": x ^ y}[m.group(2)]
            else: raise ValueError("unsupported gate: " + gl)
            out += str(v)
        return out
    if t == "loops":
        f = exec_pseudo(d["program_lines"])["flashes"]; return "".join(str(f.count(c)) for c in ("RED", "BLUE", "GREEN", "YELLOW"))
    if t == "sorter":
        b = exec_pseudo(d["code"], d["items"])["bins"]; assert len(b) == len(d["items"]); return "".join(str(b.count(x)) for x in "ABC")
    if t in ("variables", "score"):
        o = exec_pseudo(d["code"])["out"]; assert len(o) == 1, "exactly one SHOW"; return str(o[0])
    if t == "graph":
        names = list(d["nodes"]); start, goal = names[0], names[-1]; adj = {}
        for a, b, w in d["edges"]: adj.setdefault(a, []).append((b, w)); adj.setdefault(b, []).append((a, w))
        tots = []
        def dfs(u, seen, tot):
            if u == goal: tots.append(tot); return
            for v, w in adj.get(u, []):
                if v not in seen: dfs(v, seen | {v}, tot + w)
        dfs(start, {start}, 0); best = min(tots); assert tots.count(best) == 1, "shortest route is not unique"; return str(best)
    if t == "pixels":
        rows = d["pixel_rows"]; assert len(rows) == 5 and all(len(r) == 7 for r in rows)
        for a, b in itertools.product("0123456789", repeat=2):
            if all(FONT[a][i] + "0" + FONT[b][i] == rows[i] for i in range(5)): return a + b
        raise ValueError("pixels do not draw two digits in the standard font")
    return solve_more(t, d)


MORSE = {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
         "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--.."}
AB = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
WS_DIRS = {"R": (0, 1), "L": (0, -1), "D": (1, 0), "U": (-1, 0), "DR": (1, 1), "UL": (-1, -1), "DL": (1, -1), "UR": (-1, 1)}


def runs(line):
    r = [len(x) for x in "".join(line).split("0") if x]; return r or [0]


def font_pair(rows):
    for a, b in itertools.product("0123456789", repeat=2):
        if all(FONT[a][i] + "0" + FONT[b][i] == rows[i] for i in range(5)): return a + b
    raise ValueError("picture does not show two digits in the standard 3x5 font")


def pig_letter(g, i, dot):
    if g == 0: assert 0 <= i <= 8; return AB[i + (9 if dot else 0)]
    assert 0 <= i <= 3; return AB[18 + i + (4 if dot else 0)]


def sudoku_solutions(g, n=4, limit=2):
    g = [list(r) for r in g]; out = []
    def ok(r, c, v):
        if v in g[r] or v in (g[i][c] for i in range(n)): return False
        br, bc = r // 2 * 2, c // 2 * 2
        return all(g[i][j] != v for i in range(br, br + 2) for j in range(bc, bc + 2))
    def bt():
        if len(out) >= limit: return
        for r in range(n):
            for c in range(n):
                if g[r][c] == ".":
                    for v in "1234":
                        if ok(r, c, v): g[r][c] = v; bt(); g[r][c] = "."
                    return
        out.append(["".join(r) for r in g])
    bt(); return out


def lineup_check(names, clues):
    pos_of = lambda p, nm: p.index(nm) + 1
    def holds(p, c):
        c = c.rstrip(".")
        if m := re.fullmatch(r"(\w+) is first in line", c): return pos_of(p, m[1]) == 1
        if m := re.fullmatch(r"(\w+) is last in line", c): return pos_of(p, m[1]) == len(p)
        if m := re.fullmatch(r"(\w+) is in space (\d)", c): return pos_of(p, m[1]) == int(m[2])
        if m := re.fullmatch(r"(\w+) is not first", c): return pos_of(p, m[1]) != 1
        if m := re.fullmatch(r"(\w+) is not last", c): return pos_of(p, m[1]) != len(p)
        if m := re.fullmatch(r"(\w+) is not in space (\d)", c): return pos_of(p, m[1]) != int(m[2])
        if m := re.fullmatch(r"(\w+) stands directly to the right of (\w+)", c): return pos_of(p, m[1]) == pos_of(p, m[2]) + 1
        if m := re.fullmatch(r"(\w+) stands somewhere to the left of (\w+)", c): return pos_of(p, m[1]) < pos_of(p, m[2])
        if m := re.fullmatch(r"(\w+) and (\w+) stand next to each other", c): return abs(pos_of(p, m[1]) - pos_of(p, m[2])) == 1
        if m := re.fullmatch(r"(\w+) and (\w+) do not stand next to each other", c): return abs(pos_of(p, m[1]) - pos_of(p, m[2])) != 1
        raise ValueError("unsupported line-up clue: " + c)
    return [p for p in itertools.permutations(names) if all(holds(p, c) for c in clues)]


def solve_more(t, d):
    if t == "maze":
        w, hh = d["w"], d["h"]; cells = d["cells"]; op = lambda r, c: int(cells[r][c], 16); edges = 0
        assert len(cells) == hh and all(len(r) == w for r in cells)
        for r in range(hh):
            for c in range(w):
                v = op(r, c)
                if v & 2: assert c + 1 < w and op(r, c + 1) & 8, "maze walls disagree"; edges += 1
                if v & 4: assert r + 1 < hh and op(r + 1, c) & 1, "maze walls disagree"; edges += 1
                if v & 1: assert r > 0 and op(r - 1, c) & 4, "maze walls disagree"
                if v & 8: assert c > 0 and op(r, c - 1) & 2, "maze walls disagree"
        start, goal = tuple(d["start"]), tuple(d["goal"]); par = {start: None}; q = [start]
        for r, c in q:
            v = op(r, c)
            for bit, (a, b) in ((1, (-1, 0)), (2, (0, 1)), (4, (1, 0)), (8, (0, -1))):
                if v & bit and (r + a, c + b) not in par: par[(r + a, c + b)] = (r, c); q.append((r + a, c + b))
        assert len(par) == w * hh and edges == w * hh - 1, "maze must have exactly one route between any two squares"
        path, p = [], goal
        while p: path.append(p); p = par[p]
        path.reverse(); L = {(r, c): x for r, c, x in d["letters"]}
        return "".join(L[p] for p in path if p in L)
    if t == "mastermind":
        n = d["len"]; digs = "123456789"[: d["digits"]]
        def fb(code, g): b = sum(x == y for x, y in zip(code, g)); return b, len(set(code) & set(g)) - b
        c = ["".join(p) for p in itertools.permutations(digs, n) if all(fb("".join(p), g) == (b, wt) for g, b, wt in d["guesses"])]
        assert len(c) == 1, f"code cracker has {len(c)} possible codes, needs exactly 1"; return c[0]
    if t == "nonogram":
        W = len(d["cols"]); pats = [["".join(p) for p in itertools.product("01", repeat=W) if runs(p) == list(rc)] for rc in d["rows"]]; sols = []
        for combo in itertools.product(*pats):
            if all(runs([row[j] for row in combo]) == list(d["cols"][j]) for j in range(W)):
                sols.append(combo)
                if len(sols) > 1: break
        assert len(sols) == 1, "nonogram must have exactly one solution"; return font_pair(list(sols[0]))
    if t == "sudoku":
        s = sudoku_solutions(d["grid"]); assert len(s) == 1, "mini sudoku must have exactly one solution"
        for r, c in d["stars"]: assert d["grid"][r][c] == ".", "star squares must be empty"
        return "".join(s[0][r][c] for r, c in d["stars"])
    if t == "morse":
        inv = {v: k for k, v in MORSE.items()}; return "".join(inv[x] for x in d["enc"].replace("/", " ").split())
    if t == "pigpen": return "".join(pig_letter(*x) for x in d["syms"])
    if t == "balance":
        shapes = sorted({s for eq, _ in d["eqs"] for s in eq} | set(d["ask"])); sols = []
        for vals in itertools.permutations(range(1, 10), len(shapes)):
            m = dict(zip(shapes, vals))
            if all(sum(m[s] for s in eq) == tot for eq, tot in d["eqs"]): sols.append(m)
        assert len(sols) == 1, f"shape sums have {len(sols)} solutions, need exactly 1"; return "".join(str(sols[0][s]) for s in d["ask"])
    if t == "pyramid":
        rows = d["rows"]; n = len(rows); bot = rows[-1]; unk = [i for i, v in enumerate(bot) if v is None]; sols = []
        assert all(len(rows[i]) == i + 1 for i in range(n))
        for vals in itertools.product(range(0, 41), repeat=len(unk)):
            b = list(bot)
            for i, v in zip(unk, vals): b[i] = v
            full = [b]
            while len(full[0]) > 1: full.insert(0, [full[0][i] + full[0][i + 1] for i in range(len(full[0]) - 1)])
            if all(rows[r][i] is None or rows[r][i] == full[r][i] for r in range(n) for i in range(r + 1)): sols.append(full)
        assert len(sols) == 1, "pyramid must have exactly one solution"; return "".join(str(sols[0][r][i]) for r, i in d["ask"])
    if t == "flowchart":
        n = d["start"]; k = 0
        if d["mode"] == "collatz":
            while n != 1: n = n // 2 if n % 2 == 0 else 3 * n + 1; k += 1; assert k < 40
            return str(k)
        while n <= d["limit"]: n = n * d["mul"] + d["add"]; k += 1; assert k < 30
        return str(n)
    if t == "parity":
        g = d["grid"]; assert len(g) == 6 and all(len(r) == 6 for r in g)
        rs = [i for i in range(6) if g[i].count("1") % 2]; cs = [j for j in range(6) if [g[i][j] for i in range(6)].count("1") % 2]
        assert len(rs) == 1 and len(cs) == 1, "exactly one card must be flipped"; return "ABCDEF"[rs[0]] + str(cs[0] + 1)
    if t == "checkdigit":
        out = ""
        for code in d["codes"]:
            ds = [int(x) for x in code.rstrip("?")]; tot = sum(v * (1 if i % 2 == 0 else 2) for i, v in enumerate(ds)); out += str((10 - tot % 10) % 10)
        return out
    if t == "sortnet":
        v = list(d["inputs"])
        for a, b in d["comps"]:
            a, b = min(a, b), max(a, b)
            if v[a] > v[b]: v[a], v[b] = v[b], v[a]
        return "".join(map(str, v))
    if t == "rle":
        rows = []
        for r in d["rows"]:
            s = "".join(("1" if col == "B" else "0") * int(num) for num, col in re.findall(r"(\d+)([BW])", r)); assert len(s) == 7, "each row must decode to 7 squares"; rows.append(s)
        return font_pair(rows)
    if t == "stack":
        box, out = [], ""
        for o in d["ops"]:
            if o.startswith(("PUSH ", "JOIN ")): box.append(o.split()[1])
            else: assert box, "nothing to take"; out += box.pop() if d["mode"] == "stack" else box.pop(0)
        return out
    if t == "wordsearch":
        g = d["grid"]; R, C = len(g), len(g[0]); used = set()
        for word in d["words"]:
            found = []
            for r in range(R):
                for c in range(C):
                    for dn in d["dirs"]:
                        a, b = WS_DIRS[dn]; cells = [(r + a * i, c + b * i) for i in range(len(word))]
                        if all(0 <= x < R and 0 <= y < C and g[x][y] == word[i] for i, (x, y) in enumerate(cells)): found.append(cells)
            assert len(found) == 1, f"{word} appears {len(found)} times in the word search"; used |= set(found[0])
        return "".join(g[r][c] for r in range(R) for c in range(C) if (r, c) not in used)
    if t == "clock":
        hr = d["start"]; out = ""
        for op, n in d["steps"]: hr = (hr + (n if op == "+" else -n) - 1) % 12 + 1; out += str(hr)
        return out
    if t == "halving":
        lo, hi, out = d["lo"], d["hi"], []
        while True:
            g = (lo + hi) // 2; out.append(str(g))
            if g == d["target"]: return "".join(out)
            lo, hi = (g + 1, hi) if d["target"] > g else (lo, g - 1)
            assert len(out) < 10
    if t == "coords":
        cols = d.get("cols", 5); rows = [["0"] * cols for _ in range(5)]
        for x, y in d["points"]: rows[5 - y][x - 1] = "1"
        return font_pair(["".join(r) for r in rows])
    if t == "lineup":
        sols = lineup_check(d["robots"], d["clues"]); assert len(sols) == 1, f"line-up has {len(sols)} answers, needs exactly 1"
        return "".join(nm[0] for nm in sols[0])
    raise ValueError("unsupported type " + t)


def build(spec):
    errs = []
    for k in ("date", "name", "story", "limit", "final", "locks"):
        if k not in spec: errs.append("missing " + k)
    if errs: raise SystemExit("; ".join(errs))
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", spec["date"]), "date must be YYYY-MM-DD"
    locks = spec["locks"]; assert 4 <= len(locks) <= 6, "use 4 to 6 locks"
    fin = spec["final"]; FA = norm(fin["answer"])
    for lk in locks:
        assert lk["type"] in ALLOWED, f"type {lk['type']} is not allowed in daily challenges"
        assert len(lk["hints"]) == 2, "each lock needs exactly 2 hints"
        assert len(lk["r"]) == 1 and lk["r"].isalpha(), "reward must be one letter"
        got = norm(solve(lk))
        if lk["type"] == "cipher":
            assert norm(lk["answer"]) in [norm(w) for w in solve(lk).split()] or norm(lk["answer"]) == got, f"{lk['t']}: answer is not in the decoded text '{solve(lk)}'"
        else:
            assert got == norm(lk["answer"]), f"{lk['t']}: solver got {got} but answer says {norm(lk['answer'])}"
    letters = "".join(lk["r"].upper() for lk in locks)
    assert sorted(letters) == sorted(FA), f"reward letters {letters} don't unscramble to {FA}"
    assert letters != FA, "reward letters must be scrambled, not already in order"
    assert len(fin["hints"]) == 2
    answers = [norm(lk["answer"]) for lk in locks] + [FA]
    visible = json.dumps({k: spec[k] for k in ("name", "story")} | {"final": {k: v for k, v in fin.items() if k != "answer"}} |
                         {"locks": [{k: v for k, v in lk.items() if k not in ("answer",)} for lk in locks]}).upper()
    for a in answers:
        if a.isalpha() and len(a) >= 4 and re.search(r"\b" + a + r"\b", visible):
            raise SystemExit(f"answer {a} is given away in the visible text")
    entry = {"date": spec["date"], "name": spec["name"], "tag": "Daily challenge", "story": spec["story"], "limit": int(spec["limit"]),
             "locks": [{"t": lk["t"], "s": lk["s"], "type": lk["type"], "h": h(lk["answer"]), "r": lk["r"].upper(), "hints": lk["hints"], "max": len(norm(lk["answer"])), "d": lk["d"]} for lk in locks],
             "final": {k: fin[k] for k in ("title", "button", "clue", "hints", "done", "winTitle")} | {"h": h(FA)},
             "secret": base64.b64encode(json.dumps(answers)[::-1].encode()).decode()}
    return entry


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]
    entry = build(spec)
    try: cur = json.load(open(out))
    except FileNotFoundError: cur = []
    cur = [e for e in cur if e.get("date") != entry["date"]] + [entry]
    cur = sorted(cur, key=lambda e: e["date"], reverse=True)[:14]
    json.dump(cur, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"OK: {entry['date']} '{entry['name']}' with {len(entry['locks'])} locks. daily.json now holds {len(cur)} challenges.")
