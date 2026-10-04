#!/usr/bin/env python3
"""Back-annotate the fit1508 Verilog timing model: copy glue.vo and give every primitive instance its SDF
delays as parameters (iverilog 12 rejects the fitter's SDF 1.0 file, so $sdf_annotate is not used).
Models are in prims_timed.v (transport delays). Adapted from cpld/dram/sim/sdf2v.py.
Usage: sdf2v.py glue.vo glue.sdo > glue_timed.v"""
import re, sys
vo, sdo = open(sys.argv[1]).read(), open(sys.argv[2]).read()
par = {}
for m in re.finditer(r'\(CELLTYPE "(\w+)"\)\s*\(INSTANCE (\S+)\)(.*?)(?=\(CELL\b|\Z)', sdo, re.S):
    t, inst, body = m.groups()
    io = {(a or b): int(v) / 1000 for a, b, v in
          [(x[1], x[0], x[2]) for x in re.findall(r'\(IOPATH (\w+|\(posedge (\w+)\)) \w+ \((\d+):', body)]}
    io = {k.replace('(posedge ', '').rstrip(')'): v for k, v in io.items()}
    ck = {f'{k}_{p}': int(v) / 1000 for k, p, v in re.findall(r'\((SETUP|HOLD) (\w+) \(posedge CLK\) \((\d+):', body)}
    if t == 'DFFEARS':
        par[inst] = f".TCQ({io.get('CLK', 0)}), .TAR({io.get('AR', 0)}), .TAS({io.get('AS', 0)}), " \
                    f".TSU({ck.get('SETUP_D', 0)}), .THD({ck.get('HOLD_D', 0)})"
    elif t in ('TRI', 'BIBUF'):
        par[inst] = f".TA({io.get('A', 0)}), .TEN({io.get('EN', 0)})"
    else:
        par[inst] = f".TP({max(io.values()) if io else 0})"
# clock tree: every combinational instance between the CLK port and a DFFEARS CLK pin gets ND=1 (no derating)
drv = {}
for m in re.finditer(r'^(\w+) (\w+) \((.*?)\);', vo, re.M):
    t, i, a = m.groups()
    if t == 'module' or '.' in a: continue
    nets = [x.strip() for x in a.split(',')]
    drv[nets[0]] = (i, nets[1:])
clk_insts, todo = set(), re.findall(r'\.CLK\((\w+)\)', vo)
while todo:
    n_ = todo.pop()
    if n_ in drv and drv[n_][0] not in clk_insts:
        clk_insts.add(drv[n_][0]); todo += drv[n_][1]
for i in clk_insts:
    if i in par: par[i] += ", .ND(1)"
n = 0
def sub(m):
    global n
    t, inst = m.group(1), m.group(2)
    if inst in par: n += 1; return f"{t} #({par[inst]}) {inst} ("
    return m.group(0)
out = re.sub(r'^(\w+) (\w+) \(', sub, vo, flags=re.M)
sys.stdout.write(out)
sys.stderr.write(f"sdf2v: annotated {n} of {len(par)} SDF instances ({len(clk_insts)} clock-tree instances not derated)\n")
