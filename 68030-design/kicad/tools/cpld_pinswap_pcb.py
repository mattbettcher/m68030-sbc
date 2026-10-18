#!/usr/bin/env python3
"""Bring the PCB in line with the CPLD pin swap (2026-10-17).

1. U3/U4 pad nets are set from a kicad-cli netlist of the edited schematic (all other pads are checked
   and must already match, so the update cannot touch anything else).
2. The 21 U4 series terminations (R804-R824, 33R on MA/RAS/CAS/WE) are moved to B.Cu in the
   5.6 mm band between the SIMM pad rows and U4's top pad row, one under each net's SIMM pin, in SIMM
   order, so CPLD pin -> R -> SIMM pin is a few mm with no crossings. Their old F.Cu spots
   were chosen for the old pinout and are freed.
usage: cpld_pinswap_pcb.py <in.kicad_pcb> <netlist.net> <out.kicad_pcb>
"""
import re, sys, pcbnew
src, netf, out = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
mm, MM = pcbnew.ToMM, pcbnew.FromMM
# ---- 1. pad nets
s = open(netf).read(); want = {}
for blk in s.split('(net (code')[1:]:
    name = re.search(r'\(name "([^"]*)"\)', blk).group(1)
    for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', blk): want[(r, p)] = name
nets = {n: b.FindNet(n) for n in set(want.values())}
changed = 0
for f in b.GetFootprints():
    ref = f.GetReference()
    for p in f.Pads():
        k = (ref, p.GetNumber())
        if k not in want: continue
        if p.GetNetname() != want[k]:
            assert ref in ('U3', 'U4'), ('unexpected net change', k, p.GetNetname(), want[k])
            assert nets[want[k]] is not None, want[k]
            p.SetNet(nets[want[k]]); changed += 1
print('pad nets changed:', changed)
# ---- 2. series resistors
J1 = b.FindFootprintByReference('J1')
simm = {p.GetNetname(): p for p in J1.Pads()}
rows = []
for i in range(804, 825):
    f = b.FindFootprintByReference(f'R{i}')
    pads = {p.GetNumber(): p for p in f.Pads()}
    far = pads['2'].GetNetname(); assert far in simm, (f.GetReference(), far)
    rows.append((mm(simm[far].GetPosition().x), f))
rows.sort(key=lambda r: r[0])
Y = 13.92                     # band centre: SIMM row y 9.96 (pad edge 10.79) .. U4 row y 17.76 (edge 17.05)
PITCH, XMIN, XMAX = 1.6, 69.0, 129.0
obst = []                     # (x, y, r) round keep-outs on B.Cu
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        obst.append((mm(t.GetPosition().x), mm(t.GetPosition().y), mm(t.GetWidth(pcbnew.F_Cu)) / 2))
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD and f.GetReference() not in [r[1].GetReference() for r in rows]:
            obst.append((mm(p.GetPosition().x), mm(p.GetPosition().y), max(mm(p.GetSize().x), mm(p.GetSize().y)) / 2))
others_b = [f for f in b.GetFootprints() if f.GetLayer() == pcbnew.B_Cu]
def clear(x):
    # resistor pads: 0.8 x 0.95 at y = Y -/+ 0.82, vertical; keep 0.25 mm to obstacles
    for (ox, oy, r) in obst:
        for py in (Y - 0.82, Y + 0.82):
            dx = max(abs(ox - x) - 0.4, 0); dy = max(abs(oy - py) - 0.475, 0)
            if (dx * dx + dy * dy) ** 0.5 < r + 0.25: return False
    for f in others_b:
        bb = f.GetBoundingBox(False)
        if mm(bb.GetX()) - 0.8 < x < mm(bb.GetRight()) + 0.8 and mm(bb.GetY()) < Y + 1.5 and mm(bb.GetBottom()) > Y - 1.5: return False
    return True
last = XMIN - PITCH; placed = []
for tx, f in rows:
    x = max(tx, last + PITCH, XMIN)
    while not clear(x): x += 0.05
    assert x <= XMAX, (f.GetReference(), x)
    if f.GetLayer() != pcbnew.B_Cu: f.Flip(f.GetPosition(), False)
    f.SetPosition(pcbnew.VECTOR2I(MM(x), MM(Y)))
    for ang in (90, 270):
        f.SetOrientationDegrees(ang)
        p2 = [p for p in f.Pads() if p.GetNumber() == '2'][0]
        if mm(p2.GetPosition().y) < Y: break          # SIMM-side pad on top
    last = x; placed.append((f.GetReference(), round(x, 2), round(tx, 2)))
    for t in (f.Reference(),):
        t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(Y)))   # refdes on the part centre; nudge_refdes.py moves it
print('placed', placed)
pcbnew.SaveBoard(out, b)
# ---- 3. silkscreen: 1.6 mm pitch leaves no room for 21 refdes in the band. Hide them on silk (they stay on
#         B.Fab) and put one B.SilkS note inside the U4 socket outline.
b2 = pcbnew.LoadBoard(out)
for i in range(804, 825):
    b2.FindFootprintByReference(f'R{i}').Reference().SetVisible(False)
t = pcbnew.PCB_TEXT(b2)
t.SetText('R804-R824 (33R, U4 series)\nunder SIMM, SIMM pin order')
t.SetLayer(pcbnew.B_SilkS); t.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0))); t.SetTextThickness(MM(0.15))
t.SetPosition(pcbnew.VECTOR2I(MM(110.0), MM(33.0))); t.SetMirrored(True)
b2.Add(t)
pcbnew.SaveBoard(out, b2)
print('refdes hidden for R804-R824; B.SilkS note added')
