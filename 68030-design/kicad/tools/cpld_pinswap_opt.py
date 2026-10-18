# CPLD pin swap 2026-10-17 (see cpld/*/README.md 'Rev A.2 pin swap'). Work files went to /tmp/cpldwork/pins.
"""Pin-assignment optimiser for U3/U4 on the current 220x175 placement.
cost(pin, net) = distance from the CPLD pad to the net's nearest other pad (series resistors on U4 nets are
looked through to the far side, i.e. the SIMM pad), plus a crossing penalty refined by pairwise swaps."""
import os, sys, json, math, itertools, collections, random
import pcbnew, numpy as np
from scipy.optimize import linear_sum_assignment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import cpld_pinswap_schpins as schpins
LAB = {}
for i, grp in enumerate([(4,5,6,8,9,10,11,12),(14,15,16,17,18,20,21,22),(23,24,25,27,28,29,30,31),(33,34,35,36,37,39,40,41),
                         (44,45,46,48,49,50,51,52),(54,55,56,57,58,60,61,62),(63,64,65,67,68,69,70,71),(73,74,75,76,77,79,80,81)]):
    for p in grp: LAB[p] = 'ABCDEFGH'[i]
FIXED = {1, 2, 83, 84, 14, 23, 62, 71}
CFG = {'U3': dict(sheet='glue_cpld.kicad_sch', reserved={46, 48, 49}),
       'U4': dict(sheet='dram.kicad_sch', reserved={16, 17, 18, 50, 81, 2})}
def mm(v): return pcbnew.ToMM(v)
def seg_cross(a, b, c, d):
    def o(p, q, r): return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])
    return (o(a,b,c)*o(a,b,d) < 0) and (o(c,d,a)*o(c,d,b) < 0)
def setup(board, ref, kdir, series_through=True, rot=0):
    cfg = CFG[ref]
    sch = schpins.load(f'{kdir}/{cfg["sheet"]}', ref)
    fp = board.FindFootprintByReference(ref)
    padpos = {p.GetNumber(): (mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in fp.Pads()}
    if rot:
        bb = fp.GetBoundingBox(False); cx, cy = mm(bb.GetCenter().x), mm(bb.GetCenter().y)
        th = math.radians(rot)
        padpos = {k: (cx + (x-cx)*math.cos(th) + (y-cy)*math.sin(th), cy - (x-cx)*math.sin(th) + (y-cy)*math.cos(th)) for k, (x, y) in padpos.items()}
    nets = collections.defaultdict(list)
    for p in board.GetPads(): nets[p.GetNetname()].append(p)
    pads_by_num = {p.GetNumber(): p for p in fp.Pads()}
    pins, sigs, targets, seriesR = [], [], {}, {}
    for n, v in sch.items():
        n_i = int(n)
        if n_i in FIXED or n_i in cfg['reserved'] or not v['labels']: continue
        if n_i not in LAB: continue
        net = pads_by_num[n].GetNetname()
        pins.append(n); sigs.append(net)
        tg = []
        for q in nets[net]:
            f = q.GetParentFootprint()
            if f.GetReference() == ref: continue
            if series_through and f.GetReference().startswith('R') and len(f.Pads()) == 2 and net.startswith('/dram/U4_'):
                other = [x for x in f.Pads() if x.GetNumber() != q.GetNumber()][0]
                seriesR[net] = f.GetReference()
                for z in nets[other.GetNetname()]:
                    if z.GetParentFootprint().GetReference() not in (f.GetReference(),) and not z.GetParentFootprint().IsDNP():
                        tg.append((mm(z.GetPosition().x), mm(z.GetPosition().y), z.GetParentFootprint().GetReference()))
            else:
                if f.IsDNP(): continue
                tg.append((mm(q.GetPosition().x), mm(q.GetPosition().y), f.GetReference()))
        targets[net] = tg
    return dict(pins=pins, sigs=sigs, padpos=padpos, targets=targets, seriesR=seriesR, sch=sch)
def nearest(pt, tg):
    return min(tg, key=lambda t: math.hypot(t[0]-pt[0], t[1]-pt[1]))
def evaluate(S, assign):  # assign: net -> pin
    tot = 0; segs = []
    for net, pin in assign.items():
        p = S['padpos'][pin]; t = nearest(p, S['targets'][net])
        tot += math.hypot(t[0]-p[0], t[1]-p[1]); segs.append((p, (t[0], t[1])))
    cr = sum(1 for a, b in itertools.combinations(segs, 2) if seg_cross(a[0], a[1], b[0], b[1]))
    return tot, cr
def optimise(S, wcross=4.0, seed=1, lab_lock=False, fixed=()):
    pins, sigs = S['pins'], S['sigs']
    C = np.zeros((len(sigs), len(pins)))
    for i, net in enumerate(sigs):
        for j, pin in enumerate(pins):
            p = S['padpos'][pin]; t = nearest(p, S['targets'][net])
            C[i, j] = math.hypot(t[0]-p[0], t[1]-p[1])
            if net in fixed and pin != S['orig'][net]: C[i, j] += 1e6
            if (lab_lock is True or (lab_lock and net in lab_lock)) and LAB[int(pin)] != LAB[int(S['cur'][net])]: C[i, j] += 1e6
    r, c = linear_sum_assignment(C)
    assign = {sigs[i]: pins[j] for i, j in zip(r, c)}
    def score(a):
        d, x = evaluate(S, a); return d + wcross*x
    best = score(assign); rnd = random.Random(seed); nets = list(assign)
    improved = True
    while improved:
        improved = False
        for a, b in itertools.combinations(nets, 2):
            if lab_lock is True and LAB[int(assign[a])] != LAB[int(assign[b])]: continue
            if lab_lock and lab_lock is not True and (a in lab_lock or b in lab_lock) and LAB[int(assign[a])] != LAB[int(assign[b])]: continue
            if a in fixed or b in fixed: continue
            assign[a], assign[b] = assign[b], assign[a]
            s = score(assign)
            if s < best - 1e-6: best = s; improved = True
            else: assign[a], assign[b] = assign[b], assign[a]
    return assign
