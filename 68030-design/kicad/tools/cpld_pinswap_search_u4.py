# CPLD pin swap 2026-10-17 (see cpld/*/README.md 'Rev A.2 pin swap'). Work files went to /tmp/cpldwork/pins.
import os, sys, json, subprocess, re, os, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew, cpld_pinswap_opt as O
KD = '/workspace/68030-design/kicad'
b = pcbnew.LoadBoard(f'{KD}/m68030-sbc.kicad_pcb')
full = json.load(open('/tmp/cpldwork/pins/assign_full_c.json'))
start = json.load(open('/tmp/cpldwork/pins/assign_u4outlock_ABCHc.json'))
# apply U3 (same in both)
assert full['U3']['assign'] == start['U3']['assign']
def apply(ref, assign, orig):
    pads = {p.GetNumber(): p for p in b.FindFootprintByReference(ref).Pads()}
    netobj = {n: pads[p].GetNet() for n, p in orig.items()}
    for n, p in assign.items(): pads[p].SetNet(netobj[n])
apply('U3', start['U3']['assign'], start['U3']['orig'])
S = O.setup(b, 'U4', KD)   # U4 still original on board; S maps from board
orig4 = {n: p for n, p in zip(S['sigs'], S['pins'])}
def cost(a):
    d, x = O.evaluate(S, a); return d + 4 * x, d, x
W = '/tmp/cpldwork/srch'; os.makedirs(W, exist_ok=True)
shutil.copy('/tmp/cpldwork/base/dram/dram.edif', W); shutil.copytree('/tmp/cpldwork/base/dram/sim', W + '/sim', dirs_exist_ok=True)
V = open('/tmp/cpldwork/base/dram/dram.v').read()
def port(net): return net.split('/')[-1].replace('U4_', '')
cache = {}
def fit(a):
    key = tuple(sorted(a.items()))
    if key in cache: return cache[key]
    m = {port(n): int(p) for n, p in a.items()}
    v = re.sub(r'//PIN: ([A-Za-z0-9_]+)\s*: (\d+)', lambda g: f'//PIN: {g.group(1):<15s}: {m[g.group(1)]}' if g.group(1) in m else g.group(0), V)
    open(W + '/dram.v', 'w').write(v)
    env = dict(os.environ, WINEDEBUG='-all')
    subprocess.run(['/opt/atf15xx_yosys/run_fitter.sh', '-d', 'ATF1508AS', '-p', 'PLCC84', '-s', '7', 'dram', '-preassign', 'keep',
                    '-optimize', 'on', '-tdi_pullup', 'on', '-tms_pullup', 'on', '-pin_keep', 'on', '-verilog_sim', 'sdf'],
                   cwd=W, env=env, capture_output=True)
    f = open(W + '/dram.fit').read() if os.path.exists(W + '/dram.fit') else ''
    ok = 'Design FITS' in f
    t = subprocess.run(['python3', 'sim/sta_dram.py', 'dram.vo', 'dram.sdo'], cwd=W, capture_output=True, text=True).stdout if ok else ''
    mw = re.search(r'-> worst ([\d.]+) ns', t)
    ms = re.findall(r'^\s+(A0|A1|SIZ0|SIZ1|R_W)\s+([\d.]+)', t, re.M)
    worst = float(mw.group(1)) if mw else 99
    setup = max([float(x) for _, x in ms] or [99])
    r = (ok and worst <= 14.0 and setup <= 6.0, worst, setup); cache[key] = r; return r
cur = dict(start['U4']['assign'])
print('start', cost(cur), fit(cur)); assert fit(cur)[0]
target = full['U4']['assign']
for it in range(3):
    changed = False
    nets = sorted(cur, key=lambda n: n)
    for n in nets:
        if cur[n] == target[n]: continue
        tpin = target[n]; other = [k for k, p in cur.items() if p == tpin]
        cand = dict(cur)
        if other: cand[other[0]] = cur[n]
        cand[n] = tpin
        if cost(cand)[0] >= cost(cur)[0]: continue
        r = fit(cand)
        if r[0]:
            cur = cand; changed = True; print('accept', n, tpin, [round(v) for v in cost(cur)], flush=True)
    # also try pairwise swaps among all nets that lower cost
    for i, a in enumerate(nets):
        for bn in nets[i+1:]:
            cand = dict(cur); cand[a], cand[bn] = cur[bn], cur[a]
            if cost(cand)[0] < cost(cur)[0] - 5:
                r = fit(cand)
                if r[0]: cur = cand; changed = True; print('swap', a, bn, [round(v) for v in cost(cur)], flush=True)
    if not changed: break
print('final', cost(cur), fit(cur), 'fits run', len(cache))
start['U4']['assign'] = cur
json.dump(start, open('/tmp/cpldwork/pins/assign_search.json', 'w'), indent=1)
