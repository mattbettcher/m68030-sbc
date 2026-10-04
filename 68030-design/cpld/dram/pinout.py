#!/usr/bin/env python3
"""Extract the full 84-pin table from fit1508's dram.fit pin diagram -> pinout.csv / pinout.md"""
import re
L=open('dram.fit').read().split('\n')
top=[i for i,l in enumerate(L) if re.match(r'\s+\|\s+11 10\s+9',l)][0]
pins={}
def vert(rows_idx, numline):
    cols=[(m.start(),int(m.group())) for m in re.finditer(r'\d+',L[numline])]
    for c,n in cols:
        s=''.join((L[r][c+len(str(n))-1] if len(L[r])>c+len(str(n))-1 else ' ') for r in rows_idx)
        pins[n]=s.strip().replace(' ','')
# top labels are the lines above the '+---' line (bottom-aligned, read downward)
plus_top=top-1; k=plus_top-1; rows=[]
while L[k].strip(): rows.insert(0,k); k-=1
vert(rows, top)
bot=[i for i,l in enumerate(L) if re.match(r'\s+\|\s+33 34 35',l)][0]
k=bot+2; rows=[]
while k<len(L) and L[k].strip(): rows.append(k); k+=1
vert(rows, bot)
for l in L[top+1:bot]:
    m=re.match(r'\s*(\S*)\|\s*(\d+)\s.*?\s(\d+)\s*\|(\S*)',l)
    if m: pins[int(m.group(2))]=m.group(1); pins[int(m.group(3))]=m.group(4)
assert len(pins)==84, len(pins)
role={1:'GCLR (dedicated input)',2:'OE2/GCLK2 (dedicated input)',83:'GCLK1 (dedicated input)',84:'OE1 (dedicated input)'}
res={16:'reserved STERM_n (solder jumper JP801 open)',17:'reserved CBREQ_n (solder jumper JP802 open)',
     18:'reserved CBACK_n (solder jumper JP803 open)',50:'reserved DS_n (solder jumper JP804 open)',
     81:'spare I/O/GCLK3 (test point TP809)',2:'CLK_DRAMC on GCLK2 (for a future CPU-clock-synchronous FSM; unused in Rev A logic)'}
tt=open('dram.tt3').read()
with open('pinout.csv','w') as f:
    f.write('pin,fitter_name,function\n')
    for n in range(1,85):
        nm=pins[n]; fn=role.get(n,'')
        if not nm: fn=res.get(n,'unused I/O')
        f.write(f'{n},{nm},{fn}\n')
print(open('pinout.csv').read())

# ---- markdown table (also pasted into spec.md 4.2)
import re as _re
v = open('dram.v').read()
dirs = {}
for kind, names in _re.findall(r'^\s*(input|output|inout)\s+([A-Za-z0-9_, ]+?)\s*,?\s*(?://.*)?$', v, _re.M):
    for n in names.split(','):
        n = n.strip()
        if n: dirs[n] = kind
DESC = {"DSACK0_n": "out, 3-state (driven only while terminating)", "DSACK1_n": "out, 3-state (driven only while terminating)"}
NET = {"RAS0_n": "RAS0_n (via 33R)", "RAS1_n": "RAS1_n (via 33R)", "RAS2_n": "RAS2_n (via 33R)", "RAS3_n": "RAS3_n (via 33R)",
       "CAS0_n": "CAS0_n (via 33R)", "CAS1_n": "CAS1_n (via 33R)", "CAS2_n": "CAS2_n (via 33R)", "CAS3_n": "CAS3_n (via 33R)",
       "WE_n": "WE_n (via 33R)", **{f"MA{i}": f"MA{i} (via 33R)" for i in range(12)}}
lines = ["| Pin | Pin function (doc0784) | Signal (net) | Dir |", "|---|---|---|---|"]
import csv as _csv
fn = {}
for r in _csv.DictReader(open('pinout.csv')):
    p = int(r['pin']); nm = r['fitter_name']
    func = r['function']
    if nm in ('VCC', 'GND', 'TDI', 'TMS', 'TCK', 'TDO'):
        continue
    if not nm:
        pf = "OE2/GCLK2 (dedicated input)" if p == 2 else ("I/O/GCLK3" if p == 81 else "I/O")
        lines.append("| %d | %s | %s | - |" % (p, pf, func)); continue
    d = DESC.get(nm, {"input": "in", "output": "out", "inout": "bidir"}.get(dirs.get(nm, ''), '?'))
    pf = {1: "GCLR (dedicated input)", 2: "OE2/GCLK2 (dedicated input)", 83: "GCLK1 (dedicated input)", 84: "OE1 (dedicated input)"}.get(p) or \
         ("I/O/PD1" if p == 12 else "I/O/PD2" if p == 45 else "I/O/GCLK3" if p == 81 else "I/O")
    lines.append("| %d | %s | %s | %s |" % (p, pf, NET.get(nm, nm), d))
open('pinout.md', 'w').write("# U4 DRAM controller CPLD pinout (fit1508 v1918 result, extracted from dram.fit)\n\n"
    "Power: VCCINT 3, 43; VCCIO 13, 26, 38, 53, 66, 78 (all +5V). GND 7, 19, 32, 42, 47, 59, 72, 82.\n"
    "JTAG (enabled): TDI 14, TMS 23, TCK 62, TDO 71.\n\n" + "\n".join(lines) + "\n")
