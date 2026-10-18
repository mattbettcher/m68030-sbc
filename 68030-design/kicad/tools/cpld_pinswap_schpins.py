# CPLD pin swap 2026-10-17 (see cpld/*/README.md 'Rev A.2 pin swap'). Work files went to /tmp/cpldwork/pins.
"""Map CPLD symbol pins to the label chains attached to them in a sheet."""
import os, sys, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse
def r(v): return round(float(v), 2)
def load(path, ref):
    t = parse(open(path).read())
    libs = [e for e in t if isinstance(e, list) and e and e[0] == 'lib_symbols'][0]
    pins = {}
    def walk(e):
        if isinstance(e, list):
            if e and e[0] == 'pin':
                at = [x for x in e if isinstance(x, list) and x[0] == 'at'][0]
                num = [x for x in e if isinstance(x, list) and x[0] == 'number'][0][1]
                pins[num] = (float(at[1]), float(at[2]))
            for x in e: walk(x)
    sym = [e for e in libs[1:] if e[1] == 'm68030-sbc:ATF1508AS-PLCC84'][0]
    walk(sym)
    inst = None; others = []
    for e in t:
        if isinstance(e, list) and e and e[0] == 'symbol':
            props = {x[1]: x[2] for x in e if isinstance(x, list) and x[0] == 'property'}
            if props.get('Reference') == ref: inst = e
    at = [x for x in inst if isinstance(x, list) and x[0] == 'at'][0]
    mir = [x for x in inst if isinstance(x, list) and x[0] == 'mirror']
    X, Y, rot = float(at[1]), float(at[2]), int(float(at[3]))
    assert rot == 0 and not mir, (rot, mir)
    ends = {n: (r(X + x), r(Y - y)) for n, (x, y) in pins.items()}
    wires = []; labels = collections.defaultdict(list); ncs = set(); junc = set()
    for e in t:
        if not (isinstance(e, list) and e): continue
        if e[0] == 'wire':
            pts = [x for x in e if isinstance(x, list) and x[0] == 'pts'][0]
            a, b = [(r(p[1]), r(p[2])) for p in pts[1:3]]
            wires.append((a, b))
        elif e[0] in ('label', 'global_label', 'hierarchical_label'):
            a = [x for x in e if isinstance(x, list) and x[0] == 'at'][0]
            labels[(r(a[1]), r(a[2]))].append((e[0], e[1]))
        elif e[0] == 'no_connect':
            a = [x for x in e if isinstance(x, list) and x[0] == 'at'][0]; ncs.add((r(a[1]), r(a[2])))
    adj = collections.defaultdict(set)
    for a, b in wires: adj[a].add(b); adj[b].add(a)
    endset = {v: k for k, v in ends.items()}
    res = {}
    for n, p in ends.items():
        seen = {p}; st = [p]
        while st:
            q = st.pop()
            for w in adj[q]:
                if w not in seen: seen.add(w); st.append(w)
        labs = [(pt, l) for pt in seen for l in labels.get(pt, [])]
        otherpins = [endset[pt] for pt in seen if pt in endset and pt != p]
        res[n] = dict(end=p, labels=labs, nwires=len(seen) - 1, nc=p in ncs, otherpins=otherpins)
    return res
if __name__ == '__main__':
    res = load(sys.argv[1], sys.argv[2])
    for n in sorted(res, key=int):
        v = res[n]; print(n, v['labels'], 'wirepts', v['nwires'], 'NC' if v['nc'] else '', v['otherpins'])
