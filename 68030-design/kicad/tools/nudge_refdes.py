#!/usr/bin/env python3
"""Move footprint reference texts that sit on another footprint's silk/body or on
pads to a clear spot around their own footprint. Silk only; no copper change.
usage: nudge_refdes.py <board.kicad_pcb>"""
import sys
import pcbnew
MM = 1e6
def bb2(b): return (b.GetLeft()/MM, b.GetTop()/MM, b.GetRight()/MM, b.GetBottom()/MM)
def infl(b, d): return (b[0]-d, b[1]-d, b[2]+d, b[3]+d)
def hit(a, c): return not (a[2] <= c[0] or c[2] <= a[0] or a[3] <= c[1] or c[3] <= a[1])

path = sys.argv[1]
board = pcbnew.LoadBoard(path)
eb = [bb2(d.GetBoundingBox()) for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
edge = (min(x[0] for x in eb)+0.5, min(x[1] for x in eb)+0.5, max(x[2] for x in eb)-0.5, max(x[3] for x in eb)-0.5)
fsilk = pcbnew.F_SilkS
body, pads, silkseg, refs = {}, [], [], {}
for f in board.GetFootprints():
    r = f.GetReference()
    body[r] = bb2(f.GetBoundingBox(False, False))
    for p in f.Pads():
        pads.append((r, infl(bb2(p.GetBoundingBox()), 0.15)))
    for g in f.GraphicalItems():
        if g.GetLayer() == fsilk:
            silkseg.append((r, infl(bb2(g.GetBoundingBox()), 0.1)))
    t = f.Reference()
    if t.IsVisible() and t.GetLayer() == fsilk:
        refs[r] = t
def clear(r, box):
    if box[0] < edge[0] or box[1] < edge[1] or box[2] > edge[2] or box[3] > edge[3]: return False
    for o, b in pads:
        if hit(box, b): return False
    for o, b in silkseg:
        if o != r and hit(box, b): return False
    for o, b in body.items():
        if o != r and hit(box, infl(b, -0.2)): return False
    for o, t in refs.items():
        if o != r and hit(box, infl(bb2(t.GetBoundingBox()), 0.1)): return False
    return True
moved, stuck = 0, []
for r, t in refs.items():
    cur = bb2(t.GetBoundingBox())
    if clear(r, cur): continue
    fb = body[r]; ok = False
    pos0, ang0 = t.GetPosition(), t.GetTextAngleDegrees()
    for ang in (t.GetTextAngleDegrees(), (t.GetTextAngleDegrees() + 90) % 180):
        t.SetTextAngleDegrees(ang)
        tb = bb2(t.GetBoundingBox()); w, h = tb[2]-tb[0], tb[3]-tb[1]
        cx0, cy0 = (fb[0]+fb[2])/2, (fb[1]+fb[3])/2
        cands = []
        for gap in (0.2, 0.5, 0.9, 1.4, 2.0):
            for o in (0, -1, 1, -2, 2, -3, 3):
                cands += [(cx0+o, fb[1]-gap-h/2), (cx0+o, fb[3]+gap+h/2), (fb[0]-gap-w/2, cy0+o), (fb[2]+gap+w/2, cy0+o)]
        for cx, cy in cands:
            t.SetPosition(pcbnew.VECTOR2I(int(cx*MM), int(cy*MM)))
            if clear(r, bb2(t.GetBoundingBox())):
                ok = True; break
        if ok: break
    if ok: moved += 1
    else:
        stuck.append(r)
        t.SetTextAngleDegrees(ang0); t.SetPosition(pos0)
print("moved", moved, "left as is", len(stuck), stuck[:40])
board.Save(path)
