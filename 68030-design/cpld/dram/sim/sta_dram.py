#!/usr/bin/env python3
"""Static timing from the fit1508 SDF timing model (dram.vo + dram.sdo). All values are the fitter's single
(min=typ=max) SDF numbers for the ATF1508AS -7 model; board delays are NOT included."""
import re, sys, collections
vo = open(sys.argv[1]).read(); sdo = open(sys.argv[2]).read()
dl = collections.defaultdict(dict); chk = collections.defaultdict(dict)
for m in re.finditer(r'\(INSTANCE (\S+)\)(.*?)(?=\(CELL|\Z)', sdo, re.S):
    for p in re.finditer(r'\(IOPATH (\(posedge (\w+)\)|\w+) (\w+) \(\s*(\d+):', m.group(2)):
        src = p.group(2) or p.group(1); dl[m.group(1)][(src, p.group(3))] = int(p.group(4)) / 1000
    for p in re.finditer(r'\((SETUP|HOLD) (\w+) \(posedge CLK\) \((\d+):', m.group(2)):
        chk[m.group(1)][(p.group(1), p.group(2))] = int(p.group(3)) / 1000
cells = []; drv = {}
for m in re.finditer(r'^(\w+) (\w+) \((.*?)\);', vo, re.M):
    t, i, args = m.groups()
    if t == 'module': continue
    if '.' in args:
        d = dict(re.findall(r'\.(\w+)\((\w+)\)', args))
        if t == 'DFFEARS': c = (t, i, d['Q'], {k: d[k] for k in ('D', 'CLK', 'AR', 'AS', 'CE')})
        elif t == 'TRI': c = (t, i, d['Q'], {'A': d['A'], 'EN': d['EN']})
        elif t == 'BIBUF': c = (t, i, d['PAD'], {'A': d['A'], 'EN': d['EN']})
        else: continue
    else:
        a = [x.strip() for x in args.split(',')]
        c = (t, i, a[0], {('A' if t in ('INV', 'BUF') else f'A{k+1}'): n for k, n in enumerate(a[1:])})
    cells.append(c); drv[c[2]] = c
ports = re.search(r'module \w+\((.*?)\);', vo, re.S).group(1).replace('\n', '').split(',')
ports = [p.strip() for p in ports]
outs = [p for p in ports if p in drv]
ins = [p for p in ports if p not in drv]
regs = [c for c in cells if c[0] == 'DFFEARS']

def arrival(net, src, memo, through_async=True, stack=()):
    """max delay from port/net `src` to `net` (None if no path). Registers break paths except async AR/AS."""
    if net == src: return 0.0
    if net in memo: return memo[net]
    if net not in drv or net in ('gnd', 'vcc') or net in stack: return None
    t, i, o, pins = drv[net]
    best = None
    if t == 'DFFEARS':
        cands = []
        if src == '@CLK':   # clock-to-Q launch (arrival of the clock at CLK pin + CLK->Q)
            a = arrival(pins['CLK'], 'DRAM_CLK', {}, stack=stack + (net,))
            if a is not None: cands.append(a + dl[i].get(('CLK', 'Q'), 1.0))
        if through_async:
            for p in ('AR', 'AS'):
                a = arrival(pins[p], src, memo, through_async, stack + (net,))
                if a is not None: cands.append(a + dl[i].get((p, 'Q'), 2.0))
        best = max(cands) if cands else None
    else:
        for pin, n in pins.items():
            a = arrival(n, src, memo, through_async, stack + (net,))
            if a is None: continue
            op = 'QN' if t == 'INV' else ('PAD' if t == 'BIBUF' else 'Q')
            d = dl[i].get((pin, op), 0.0)
            if best is None or a + d > best: best = a + d
    memo[net] = best
    return best

def clk_at(reg): return arrival(reg[3]['CLK'], 'DRAM_CLK', {})

print(__doc__)
print("1. Clock-to-pad (DRAM_CLK pin -> output pad, via registers), ns")
m = {}
for o in sorted(outs):
    a = arrival(o, '@CLK', m, through_async=False)
    if a is not None: print(f"   {o:10s} {a:5.1f}")
print("2. Input pin -> output pad (combinational, and asynchronous preset/reset paths), ns")
for s in sorted(ins):
    mm = {}; res = []
    for o in sorted(outs):
        a = arrival(o, s, mm)
        if a is not None: res.append((a, o))
    if res and s != 'DRAM_CLK':
        res.sort(reverse=True)
        if s in ('AS_n', 'PWR_RST_n'):
            print(f"   {s:10s} (asynchronous preset/reset of the output registers, then to the pad):")
            for a, o in res: print(f"       -> {o:10s} {a:5.1f}")
            mc = {}; comb = [(arrival(o, s, mc, through_async=False), o) for o in sorted(outs)]
            comb = [(a, o) for a, o in comb if a is not None]
            if comb:
                print(f"     {s} combinational paths only (no register), e.g. DSACK driven high while the OE is still on:")
                for a, o in sorted(comb, reverse=True): print(f"       -> {o:10s} {a:5.1f}")
        else:
            print(f"   {s:10s} max {res[0][0]:5.1f} (to {', '.join(o for a, o in res)})")
print("3. Input setup to DRAM_CLK (pin -> register D arrival + tSU - clock arrival at the register), ns")
setups = {}
for s in sorted(ins):
    if s == 'DRAM_CLK': continue
    mm = {}; worst = None
    for r in regs:
        for pin in ('D', 'CE'):
            a = arrival(r[3][pin], s, mm, through_async=False)
            if a is None: continue
            su = chk[r[1]].get(('SETUP', pin), 3.0)
            v = a + su - clk_at(r)
            if worst is None or v > worst[0]: worst = (v, r[2])
    if worst: setups[s] = worst; print(f"   {s:10s} {worst[0]:5.1f}  (worst register {worst[1]})")
print("4. Register -> register (clock-to-Q + logic + tSU, relative to the clock at the capturing register), ns")
mm = {}; worst = []
for r in regs:
    for pin in ('D', 'CE'):
        a = arrival(r[3][pin], '@CLK', mm, through_async=False)
        if a is None: continue
        worst.append((a + chk[r[1]].get(('SETUP', pin), 3.0) - clk_at(r), r[2]))
worst.sort(reverse=True)
for v, n in worst[:5]: print(f"   {n:10s} {v:5.1f}")
fmax = 1000.0 / worst[0][0]
print(f"   -> worst {worst[0][0]:.1f} ns: fmax {fmax:.1f} MHz; 50 MHz (20 ns) {'MET' if worst[0][0] <= 20 else 'NOT MET'}, margin {20-worst[0][0]:.1f} ns")
