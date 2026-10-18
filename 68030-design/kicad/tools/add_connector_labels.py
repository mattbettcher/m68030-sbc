#!/usr/bin/env python3
"""Add F.SilkS function labels next to every connector / jumper on the
m68030-sbc board. Board-level texts, collected in group "connector_labels".
Re-runnable: removes the previous group first. Does not touch schematics.

Each label is placed by a search: candidate positions around the anchor
(connector bbox or a single pad) are tried in preference order, and the first
one whose text box stays clear of pads, vias, holes, other courtyards, all
existing F.SilkS items, the board edge and labels already placed wins.
"""
import os
import sys
import pcbnew

# 220x175 board (2026-10-17 condense): SRC is the unlabeled output of
# tools/condense_layout.py. The 275x215 pre-label board is
# backup/m68030-sbc-prelabels-20261017.kicad_pcb. Override with env vars.
PCB = os.environ.get("LABEL_PCB", "/workspace/68030-design/kicad/m68030-sbc.kicad_pcb")
SRC = os.environ.get("LABEL_SRC", "/workspace/68030-design/kicad/backup/m68030-sbc-220x175-prelabels-20261017.kicad_pcb")
GROUP = "connector_labels"
H = 1.0      # text height/width mm
T = 0.15     # stroke mm
MM = 1e6

def mm(v): return int(round(v * MM))

# (key, text, anchor, sides, angle)
#   anchor: "J7" (whole footprint) or "J7.4" (one pad)
#   sides: preference list of "above"/"below"/"left"/"right"
#   angle: 0 or 90
LABELS = [
 # --- function labels -------------------------------------------------
 ("J1",   "SIMM 72 DRAM",        "J1",  ["below", "above"], 0),
 ("J2",   "PWR IN 9-24V DC",     "J2",  ["above", "below"], 0),
 ("J3",   "5V BENCH IN",         "J3",  ["left", "right", "above"], 0),
 ("J4",   "JTAG GLUE U3",        "J4",  ["below", "above", "right"], 0),
 ("J5",   "JTAG DRAM U4",        "J5",  ["below", "above", "left"], 0),
 ("J6",   "IDE 40-PIN",          "J6",  ["above", "right", "left"], 0),
 ("J7",   "SERIAL A TTL",        "J7",  ["above"], 0),
 ("J8",   "SERIAL B TTL",        "J8",  ["above"], 0),
 ("J9",   "SPI NIC",             "J9",  ["right", "left", "above"], 0),
 ("J10",  "EXPANSION DIN-41612", "J10", ["right", "left"], 90),
 ("J11",  "LA1 A31-A0",          "J11", ["left"], 90),
 ("J12",  "LA2 D31-D0",          "J12", ["left"], 90),
 ("J13",  "LA3 CTRL",            "J13", ["left"], 90),
 ("JP1",  "CDIS",                "JP1", ["right", "left", "below"], 0),
 ("JP2",  "MMUDIS",              "JP2", ["above", "right", "left"], 0),
 ("JP3",  "FPU CLK",             "JP3", ["above", "right", "left"], 0),
 ("JP202","BUCK ISO|ISO",            "JP202", ["above", "below", "right", "left"], 0),
 ("SJ201","BUCK OFF",            "SJ201", ["below", "above", "left", "right"], 0),
 ("JP401","RST SET",             "JP401", ["above", "below", "left", "right"], 0),
 ("JP701","SCK",                 "JP701", ["right", "left", "above", "below"], 0),
 ("JP702","MOSI",                "JP702", ["above", "below", "left", "right"], 0),
 ("JP703","MISO",                "JP703", ["right", "left", "above", "below"], 0),
 ("JP801","STERM",               "JP801", ["left", "above", "right", "below"], 0),
 # fallback legend for the crowded U4 reserve jumpers (used only if needed)
 ("JP802","CBREQ",               "JP802", ["right", "above", "below", "left"], 0),
 ("JP801L","JP801 STERM\nJP802 CBREQ", "JP802", ["right", "below", "above", "left"], 0),
 ("JP803","CBACK",               "JP803", ["left", "below", "right", "above"], 0),
 ("JP804","DS",                  "JP804", ["right", "left", "above", "below"], 0),
 # --- pin names -------------------------------------------------------
 ("J7.1", "GND", "J7.1", ["below"], 90), ("J7.2", "RTS", "J7.2", ["below"], 90),
 ("J7.3", "NC",  "J7.3", ["below"], 90), ("J7.4", "RXD", "J7.4", ["below"], 90),
 ("J7.5", "TXD", "J7.5", ["below"], 90), ("J7.6", "CTS", "J7.6", ["below"], 90),
 ("J8.1", "GND", "J8.1", ["below"], 90), ("J8.2", "RTS", "J8.2", ["below"], 90),
 ("J8.3", "NC",  "J8.3", ["below"], 90), ("J8.4", "RXD", "J8.4", ["below"], 90),
 ("J8.5", "TXD", "J8.5", ["below"], 90), ("J8.6", "CTS", "J8.6", ["below"], 90),
 ("J3.1", "+5V", "J3.1", ["right"], 0),  ("J3.2", "GND", "J3.2", ["right"], 0),
 ("J9.1", "3V3", "J9.1", ["below"], 90), ("J9.3", "GND", "J9.3", ["below"], 90),
 ("J9.5", "MOSI","J9.5", ["below"], 90), ("J9.7", "CS",  "J9.7", ["below"], 90),
 ("J9.9", "RST", "J9.9", ["below"], 90),
 ("J9.2", "5V",  "J9.2", ["above"], 90), ("J9.4", "SCK", "J9.4", ["above"], 90),
 ("J9.6", "MISO","J9.6", ["above"], 90), ("J9.8", "INT", "J9.8", ["above"], 90),
 ("J9.10","GND", "J9.10",["above"], 90),
 ("JP3.1","CPU", "JP3.1", ["right", "left", "above", "below"], 0),
 ("JP3.3","X3",  "JP3.3", ["right", "left", "above", "below"], 0),
 ("J2.1", "+", "J2.1", ["above", "below", "right"], 0),
]

LOOSE = {"JP202", "JP802", "JP804", "J9.1", "JP3", "SJ201", "JP401", "JP803", "JP3.1", "JP3.3"}
# 220x175: jumpers sit in denser passive fields, so their labels may sit further out.
MAXGAP = {"JP801L": 9.0, "JP802L": 9.0, "JP3": 4.0, "JP202": 4.0, "SJ201": 4.0, "JP401": 4.0,
          "JP803": 4.0, "JP804": 4.0, "JP3.1": 4.0, "JP3.3": 4.0}  # may touch the 0.25 mm courtyard margin of passives
PAD_CLR = 0.30   # silk to pad / hole / via
SILK_CLR = 0.20  # silk to silk
CRT_CLR = 0.05   # text box to foreign courtyard
EDGE_CLR = 0.5

def box(l, t, r, b_): return (l, t, r, b_)
def inflate(bb, d): return (bb[0]-d, bb[1]-d, bb[2]+d, bb[3]+d)
def hit(a, c): return not (a[2] <= c[0] or c[2] <= a[0] or a[3] <= c[1] or c[3] <= a[1])
def bb2(b): return (b.GetLeft()/MM, b.GetTop()/MM, b.GetRight()/MM, b.GetBottom()/MM)

def main(dry=False):
    # Always start from the pre-label backup so re-runs are idempotent.
    # Copy it into place first: LoadBoard() takes design rules / netclasses
    # from the .kicad_pro next to the board, and Save() writes them back.
    import shutil
    if not dry:
        shutil.copyfile(SRC, PCB)
        board = pcbnew.LoadBoard(PCB)
    else:
        board = pcbnew.LoadBoard(SRC)  # read-only preview; never saved

    eb = [bb2(d.GetBoundingBox()) for d in board.GetDrawings()
          if d.GetLayer() == pcbnew.Edge_Cuts]
    edge = (min(x[0] for x in eb), min(x[1] for x in eb),
            max(x[2] for x in eb), max(x[3] for x in eb))
    inner = (edge[0]+EDGE_CLR, edge[1]+EDGE_CLR, edge[2]-EDGE_CLR, edge[3]-EDGE_CLR)

    pads, silk, crt = [], [], {}
    fsilk = board.GetLayerID("F.SilkS")
    for f in board.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            pads.append(inflate(bb2(p.GetBoundingBox()), PAD_CLR))
        if f.GetLayer() == pcbnew.F_Cu:
            cb = [bb2(g.GetBoundingBox()) for g in f.GraphicalItems()
                  if g.GetLayer() == pcbnew.F_CrtYd]
            if cb:
                crt[ref] = (min(x[0] for x in cb), min(x[1] for x in cb),
                            max(x[2] for x in cb), max(x[3] for x in cb))
            else:
                crt[ref] = bb2(f.GetBoundingBox(False, False))
        for g in list(f.GraphicalItems()) + [f.Reference(), f.Value()]:
            if g.GetLayer() == fsilk and g.IsVisible() if hasattr(g, "IsVisible") else g.GetLayer() == fsilk:
                silk.append(inflate(bb2(g.GetBoundingBox()), SILK_CLR))
    for d in board.GetDrawings():
        if d.GetLayer() == fsilk:
            silk.append(inflate(bb2(d.GetBoundingBox()), SILK_CLR))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            pads.append(inflate(bb2(t.GetBoundingBox()), PAD_CLR))

    placed, report, missing = [], [], []
    missing_keys = set()
    grp = pcbnew.PCB_GROUP(board)
    grp.SetName(GROUP)
    board.Add(grp)

    def try_place(key, text, tw, ref, abox, near_pin, sides, ang, maxgap):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetLayer(fsilk)
        t.SetTextSize(pcbnew.VECTOR2I(mm(tw), mm(H)))
        t.SetTextThickness(mm(T))
        t.SetTextAngleDegrees(ang)
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetPosition(pcbnew.VECTOR2I(0, 0))
        tb = bb2(t.GetBoundingBox())
        w, h = tb[2]-tb[0], tb[3]-tb[1]
        cx0, cy0 = (abox[0]+abox[2])/2, (abox[1]+abox[3])/2
        best = None
        gaps = [g for g in (0.25 + 0.2*i for i in range(30)) if g <= maxgap]
        for si, side in enumerate(sides):
            horiz = side in ("above", "below")
            span = (abox[2]-abox[0]) if horiz else (abox[3]-abox[1])
            if near_pin: span = 0.5
            if key.endswith("L"): span = 16.0
            offs = [0.0]
            k = 0.25
            while k <= span/2 + 1e-6:
                offs += [k, -k]; k += 0.25
            for gap in gaps:
                for o in offs:
                    score = gap + 2.0*si + 0.15*abs(o)
                    if best and score >= best[3]: continue
                    if side == "above":  c = (cx0+o, abox[1]-gap-h/2)
                    elif side == "below": c = (cx0+o, abox[3]+gap+h/2)
                    elif side == "left":  c = (abox[0]-gap-w/2, cy0+o)
                    else:                 c = (abox[2]+gap+w/2, cy0+o)
                    r = (c[0]-w/2, c[1]-h/2, c[0]+w/2, c[1]+h/2)
                    if r[0] < inner[0] or r[1] < inner[1] or r[2] > inner[2] or r[3] > inner[3]:
                        continue
                    if any(hit(r, p) for p in pads): continue
                    if any(hit(r, s) for s in silk): continue
                    if any(hit(r, inflate(p, SILK_CLR)) for p in placed): continue
                    shrink = 0.25 if key in LOOSE else 0.0
                    bad = False
                    for cref, cb in crt.items():
                        if cref == ref and near_pin:
                            continue  # pin names may sit inside own courtyard
                        if hit(r, inflate(cb, CRT_CLR - shrink)):
                            bad = True; break
                    if bad: continue
                    best = (c, side, gap, score)
        if not best:
            return None
        t.SetPosition(pcbnew.VECTOR2I(mm(best[0][0]), mm(best[0][1])))
        return t, best

    for key, text_alts, anchor, sides, ang in LABELS:
        if "." in anchor:
            ref, padn = anchor.split(".", 1)
            fp = board.FindFootprintByReference(ref)
            pad = [p for p in fp.Pads() if p.GetNumber() == padn][0]
            abox = bb2(pad.GetBoundingBox())
            near_pin = True
        else:
            ref = anchor
            fp = board.FindFootprintByReference(ref)
            abox = crt.get(ref) or bb2(fp.GetBoundingBox(False, False))
            near_pin = False
        if key.endswith("L") and not ({"JP801", "JP802"} & missing_keys):
            continue  # legend only when the direct label did not fit
        small = ref.startswith(("JP", "SJ")) and not near_pin
        maxgap = 1.6 if small else (3.0 if not near_pin else 4.0)
        maxgap = MAXGAP.get(key, maxgap)
        res = None
        for text in text_alts.split("|"):
            for tw in ((H,) if key not in LOOSE else (H, 0.85)):
                res = try_place(key, text, tw, ref, abox, near_pin, sides, ang, maxgap)
                if res: break
            if res: break
        if not res:
            missing.append((key, text_alts)); missing_keys.add(key); continue
        t, best = res
        board.Add(t); grp.AddItem(t)
        placed.append(bb2(t.GetBoundingBox()))
        report.append((key, text, best[1], round(best[0][0], 2), round(best[0][1], 2), ang, tw))

    for r in report: print("PLACED", *r)
    legend = {"JP801", "JP802"} if any(k == "JP801L" for k, *_ in report) else set()
    for m in missing:
        if m[0] not in legend: print("MISSING", *m)
    for k in sorted(legend): print("LEGEND-ONLY", k)
    if not dry:
        board.Save(PCB)
    return report, missing

if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
