#!/usr/bin/env python3
"""Static timing of the fitted glue CPLD from the fit1508 SDF timing model (glue.vo + glue.sdo).
All values are the fitter's single (min=typ=max) SDF numbers for the ATF1508AS-7 model; board/PCB
delays are NOT included. The ATF1508AS datasheet gives no minimum delays, so "min" paths below are
the same single SDF numbers and are NOT guaranteed minima [VERIFY]."""
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
ports = [p.strip() for p in re.search(r'module \w+\((.*?)\);', vo, re.S).group(1).replace('\n', '').split(',')]
outs = [p for p in ports if p in drv]
ins = [p for p in ports if p not in drv]
regs = [c for c in cells if c[0] == 'DFFEARS']

def arrival(net, src, memo, through_async=True, stack=(), agg=max):
    """max (or min) delay from port `src` (or '@CLK' = clock launch) to `net`; None if no path."""
    if net == src: return 0.0
    if net in memo: return memo[net]
    if net not in drv or net in ('gnd', 'vcc') or net in stack: return None
    t, i, o, pins = drv[net]
    cands = []
    if t == 'DFFEARS':
        if src == '@CLK':
            a = arrival(pins['CLK'], 'CLK', {}, stack=stack + (net,))
            if a is not None: cands.append(a + dl[i].get(('CLK', 'Q'), 1.0))
        if through_async:
            for p in ('AR', 'AS'):
                a = arrival(pins[p], src, memo, through_async, stack + (net,), agg)
                if a is not None: cands.append(a + dl[i].get((p, 'Q'), 2.0))
    else:
        op = 'QN' if t == 'INV' else ('PAD' if t == 'BIBUF' else 'Q')
        for pin, n in pins.items():
            a = arrival(n, src, memo, through_async, stack + (net,), agg)
            if a is not None: cands.append(a + dl[i].get((pin, op), 0.0))
    best = agg(cands) if cands else None
    memo[net] = best
    return best

def clk_at(reg): return arrival(reg[3]['CLK'], 'CLK', {})

print(__doc__)
print("1. Clock-to-pad (CLK pin -> output pad via registers), ns")
m = {}
for o in sorted(outs):
    a = arrival(o, '@CLK', m, through_async=False)
    if a is not None: print(f"   {o:14s} {a:5.1f}")
print("2. Input pin -> output pad (combinational; for AS_n/PWR_RST_n including async clear/preset paths), ns")
for s in sorted(ins):
    if s == 'CLK': continue
    res = []
    for o in sorted(outs):
        a = arrival(o, s, {})
        if a is not None: res.append((a, o))
    if not res: continue
    res.sort(reverse=True)
    if s in ('AS_n', 'PWR_RST_n'):
        print(f"   {s:10s} (max = slowest path incl. async clear -> register -> pad; min = fastest path):")
        for a, o in res: print(f"       -> {o:14s} max {a:5.1f}  min {arrival(o, s, {}, agg=min):5.1f}")
    else:
        print(f"   {s:10s} max {res[0][0]:5.1f} (to {', '.join(o for a, o in res)})")
print("3. Combinational chip selects: address/FC decode vs AS_n (runt-select check).")
print("   An address/FC input changes >= 7 ns before AS_n falls (MC68030 EC #11, 25 MHz). A stale select")
print("   (previous cycle's decode) can appear when AS_n asserts if  max(addr path) - 7 > min(AS_n path).")
sel = [o for o in ('FPU_CS_n', 'EXP_SEL_n', 'EXP_BUF_EN_n', 'DRAM_SEL_n', 'ROM_CE_n', 'DUART_CS_n', 'CIIN_n',
                   'IDE_CS0_n', 'IDE_CS1_n', 'IDE_BUF_EN_n') if o in outs]
for o in sel:
    amax = []; asmin = arrival(o, 'AS_n', {}, through_async=False, agg=min)
    for s in ins:
        if s in ('CLK', 'AS_n'): continue
        a = arrival(o, s, {}, through_async=False)
        if a is not None: amax.append((a, s))
    if asmin is None or not amax:
        print(f"   {o:14s} registered decode (no combinational address/FC path): glitch-free by construction"); continue
    amax.sort(reverse=True)
    lo = min(a for a, s in amax)
    runt = amax[0][0] - 7.0 - asmin
    tag = "single pass" if abs(amax[0][0] - lo) < 0.05 and abs(amax[0][0] - asmin) < 0.05 else "multi-level"
    print(f"   {o:14s} addr/FC max {amax[0][0]:5.1f} (via {amax[0][1]}), AS_n min {asmin:5.1f}, {tag}: "
          + (f"stale window up to {runt:4.1f} ns" if runt > 0 else f"no stale window (margin {-runt:4.1f} ns)"))
print("4. Input setup to CLK (pin -> register D/CE arrival + tSU - clock arrival at the register), ns")
for s in sorted(ins):
    if s == 'CLK': continue
    mm = {}; worst = None
    for r in regs:
        for pin in ('D', 'CE'):
            a = arrival(r[3][pin], s, mm, through_async=False)
            if a is None: continue
            v = a + chk[r[1]].get(('SETUP', pin), 3.0) - clk_at(r)
            if worst is None or v > worst[0]: worst = (v, r[2])
    if worst: print(f"   {s:10s} {worst[0]:5.1f}  (worst register {worst[1]})")
print("5. Register -> register (clock-to-Q + logic + tSU - clock arrival at the capturing register), ns")
mm = {}; worst = []
for r in regs:
    for pin in ('D', 'CE'):
        a = arrival(r[3][pin], '@CLK', mm, through_async=False)
        if a is None: continue
        worst.append((a + chk[r[1]].get(('SETUP', pin), 3.0) - clk_at(r), r[2]))
worst.sort(reverse=True)
for v, n in worst[:5]: print(f"   {n:10s} {v:5.1f}")
print(f"   -> worst {worst[0][0]:.1f} ns: fmax {1000/worst[0][0]:.1f} MHz; 25 MHz (40 ns) "
      f"{'MET' if worst[0][0] <= 40 else 'NOT MET'}, 33.33 MHz (30 ns) {'MET' if worst[0][0] <= 30 else 'NOT MET'}")
