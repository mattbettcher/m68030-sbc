#!/usr/bin/env python3
"""Option B condense: 275x215 -> 220x175 mm.

Starts from backup/m68030-sbc-pre-condense-20261017.kicad_pcb (copied to the
working board first), swaps the footprints that changed in the schematic,
re-applies every pad net from the schematic netlist, re-places the board,
and redoes the power vias, stitching and the In1 GND / In2 +5V (+3V3 island)
planes. Signals stay unrouted. Labels: run add_connector_labels.py after.

usage: condense_layout.py <board.kicad_pcb> <netlist.net>
"""
import math, os, shutil, sys, heapq
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from layout_pcb import (parse_netlist, Occupancy, bbox_of, orient, move_bbox, tidy_fields,
                        add_rect, add_text, frange, inject_stackup, lib_path)

ROOT = "/workspace/68030-design/kicad"
SRC = os.path.join(ROOT, "backup/m68030-sbc-pre-condense-20261017.kicad_pcb")
PCB = sys.argv[1] if len(sys.argv) > 1 else "/tmp/condense/m68030-sbc.kicad_pcb"
NETLIST = sys.argv[2] if len(sys.argv) > 2 else "/tmp/nl/m68030-sbc.net"
W, H = 220.0, 175.0
MARGIN, GAP = 0.8, 0.45
CLEARANCE = 0.15
PWR_VIA_DRILL, PWR_VIA_SIZE = 0.35, 0.75
POWER_NETS = {"GND", "+5V", "+3V3"}
HOLE = 4.5                       # M3 hole centre inset from each edge
ISL = (103.0, 136.0, 147.0, 174.4)  # +3V3 island on In2 (x0, y0, x1, y1)
ISL_OK_5V = {"U9", "J9", "R1002", "R1003", "C1002", "SW3"}  # +5V pads allowed inside the island (escaped)

mm = pcbnew.FromMM
tomm = pcbnew.ToMM

# courtyard-centre anchors: ref -> (cx, cy, rot, bottom)
ANCHORS = {
    "H1": (HOLE, HOLE, 0), "H2": (W - HOLE, HOLE, 0), "H3": (HOLE, H - HOLE, 0), "H4": (W - HOLE, H - HOLE, 0),
    # top edge
    "J1": (110, 8.45, 0), "J4": (30, 8.0, 90), "J5": (186, 8.0, 90),
    # left edge
    "J10": (8.0, 62, 0),
    # core column: SIMM -> DRAM CPLD -> CPU, glue left, FPU right
    "U4": (110, 33, 0), "U1": (110, 79, 0), "U3": (70, 78, 0), "U2": (149, 78, 0),
    "U801": (138, 22, 0), "U802": (147.5, 22, 0), "U803": (157, 22, 0),
    # LA block, three parallel 2x20 next to the FPU / CPU
    "J11": (188, 88, 0), "J12": (199, 88, 0), "J13": (210, 88, 0),
    # clocks
    "U10": (174.5, 70, 0), "X1": (174.5, 86, 0), "X3": (174.5, 95, 0), "X2": (139, 56, 0),
    # expansion buffers 2x4 beside the DIN
    "U14": (24, 24, 0), "U15": (40, 24, 0), "U16": (24, 42, 0), "U17": (40, 42, 0),
    "U18": (24, 60, 0), "U19": (40, 60, 0), "U20": (24, 78, 0), "U21": (40, 78, 0),
    # ROM / DUART / RTC row
    "U5": (60, 118, 0), "U6": (85, 120, 0), "Y1": (102, 120, 90),
    "U23": (114, 148, 0), "U22": (132, 146, 0), "U9": (140, 160, 0), "BT1": (88, 150, 0),
    # IDE
    "U11": (158, 140, 0), "U12": (173, 140, 0), "U13": (188, 140, 0),
    # power, bottom-left
    "L1": (13.5, 122, 0), "U8": (34, 136, 0), "Q1": (28, 150, 0),
    # bottom edge (same edge offsets as the 275x215 board)
    "J7": (47, 168, 90), "J8": (64, 168, 90), "SW1": (78, 168, 0), "SW2": (89, 168, 0), "SW3": (100, 168, 0),
    "J9": (124, 167.5, 90), "J6": (180, 164, 90), "TP203": (143, 171, 0),
}
SHEET_FALLBACK = {
    "/power/": (40, 155), "/clock/": (174, 105), "/reset/": (70, 150), "/cpu/": (110, 104),
    "/fpu/": (149, 100), "/glue_cpld/": (70, 100), "/dram/": (150, 40), "/rom/": (60, 135),
    "/duart_spi_rtc/": (125, 135), "/ide/": (175, 152), "/expansion/": (32, 95), "/debug/": (199, 120),
    "/": (110, 120),
}
# Jumpers that get a silkscreen function label: keep room around them.
LABEL_ROOM = {r: 2.4 for r in ("JP1", "JP2", "JP3", "JP202", "SJ201", "JP401", "JP701", "JP702", "JP703",
                               "JP801", "JP802", "JP803", "JP804")}
LABEL_ROOM["JP3"] = 3.2
BOTTOM_CAPS = {f"C{n}" for n in range(501, 511)}


def main():
    shutil.copyfile(SRC, PCB)
    board = pcbnew.LoadBoard(PCB)
    comps, nets, order = parse_netlist(NETLIST)
    by_ref = {c["ref"]: c for c in comps}

    # ---- strip routing, zones, drawings, label group ----
    for t in list(board.GetTracks()):
        board.RemoveNative(t)
    for z in [board.GetArea(i) for i in range(board.GetAreaCount())]:
        board.RemoveNative(z)
    for g in list(board.Groups()):
        for it in list(g.GetItems()):
            if it.GetClass() == "PCB_TEXT":
                board.RemoveNative(it)
        board.RemoveNative(g)
    for d in list(board.GetDrawings()):
        board.RemoveNative(d)

    # ---- nets: add any missing, then footprint swaps ----
    for name in order:
        if board.FindNet(name) is None:
            board.Add(pcbnew.NETINFO_ITEM(board, name))
    board.BuildListOfNets()
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    swapped = []
    for c in comps:
        old = fps.get(c["ref"])
        if old is None:
            raise SystemExit("footprint missing on board: " + c["ref"])
        cur = f"{old.GetFPID().GetLibNickname()}:{old.GetFPID().GetLibItemName()}"
        if cur == c["fp"]:
            old.SetValue(c["value"])
            continue
        nick, name = c["fp"].split(":", 1)
        new = pcbnew.FootprintLoad(lib_path(nick), name)
        if new is None:
            raise SystemExit("cannot load " + c["fp"])
        new.SetFPID(pcbnew.LIB_ID(nick, name))
        new.SetReference(c["ref"])
        new.SetValue(c["value"])
        new.SetPath(old.GetPath())
        new.SetSheetname(old.GetSheetname())
        new.SetSheetfile(old.GetSheetfile())
        new.SetDNP(old.IsDNP())
        new.SetExcludedFromBOM(old.IsExcludedFromBOM())
        new.SetExcludedFromPosFiles(old.IsExcludedFromPosFiles())
        for f in old.GetFields():
            n = f.GetName()
            if n in ("Reference", "Value", "Footprint"):
                continue
            nf = new.GetFieldByName(n)
            if nf is None:
                nf = pcbnew.PCB_FIELD(new, new.GetFieldCount(), n)
                new.Add(nf)
            nf.SetText(f.GetText())
            nf.SetVisible(False)
            nf.SetLayer(pcbnew.F_Fab)
        new.SetPosition(old.GetPosition())
        board.RemoveNative(old)
        board.Add(new)
        fps[c["ref"]] = new
        swapped.append((c["ref"], cur, c["fp"]))
        tidy_fields(new)
    print("swapped", swapped)

    # ---- pad nets from the netlist (parity) ----
    pinnet = {}
    for name, nodes in nets.items():
        for r, p in nodes:
            pinnet[(r, p)] = name
    miss = []
    for ref, fp in fps.items():
        for p in fp.Pads():
            num = p.GetNumber()
            if not num:
                p.SetNetCode(0)
                continue
            nn = pinnet.get((ref, num))
            if nn is None:
                miss.append((ref, num)); p.SetNetCode(0)
            else:
                p.SetNet(board.FindNet(nn))
    print("pads with no netlist node:", miss[:20], len(miss))

    # ---- placement ----
    occ = Occupancy()
    placed = set()
    hits = []
    for ref, (cx, cy, rot) in ANCHORS.items():
        fp = fps[ref]
        orient(fp, rot, False)
        box = move_bbox(fp, cx=cx, cy=cy)
        h = occ.hits(box[0] - GAP, box[1] - GAP, box[2] + GAP, box[3] + GAP, ignore=ref)
        if h or box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > H:
            hits.append((ref, h or "OFF", tuple(round(v, 1) for v in box)))
        occ.add(box, ref)
        placed.add(ref)
    # Barrel jack: opening is the footprint -X side, faces out the left edge.
    fp = fps["J2"]; orient(fp, 0, False)
    box = move_bbox(fp, left=1.0, cy=150)
    h = occ.hits(box[0] - GAP, box[1] - GAP, box[2] + GAP, box[3] + GAP, ignore="J2")
    if h: hits.append(("J2", h, box))
    occ.add(box, "J2"); placed.add("J2")
    print("anchor conflicts", len(hits))
    for x in hits: print("  ", x)
    if hits:
        pcbnew.SaveBoard(PCB, board); sys.exit(2)

    u1b = bbox_of(fps["U1"])
    hcx, hcy = (u1b[0] + u1b[2]) / 2, (u1b[1] + u1b[3]) / 2
    hs = (hcx - 20, hcy - 20, hcx + 20, hcy + 20)
    occ.add(hs, "HEATSINK")
    # +5V parts outside the allowed set keep out of the +3V3 island.
    five_v_refs = {r for r, _ in nets["+5V"]}
    three_v_refs = {r for r, _ in nets["+3V3"]}

    pad_pos = defaultdict(list); net_pads = defaultdict(list)
    def index_fp(ref):
        for p in fps[ref].Pads():
            x, y = tomm(p.GetPosition().x), tomm(p.GetPosition().y)
            pad_pos[ref].append((p.GetNumber(), x, y, p.GetNetname()))
            if p.GetNetname():
                net_pads[p.GetNetname()].append((ref, p.GetNumber(), x, y))
    for r in placed: index_fp(r)
    supply_use = defaultdict(int)

    def host_supply_pad(ref, supply, sheet):
        cands = []
        for href, pin, x, y in net_pads[supply]:
            if href == ref or href not in placed or href[0] not in "UJXQL":
                continue
            same = by_ref[href]["sheet"] == sheet
            cands.append((0 if same else 1, supply_use[(href, round(x, 2), round(y, 2))], href, x, y))
        if not cands: return None
        cands.sort(); _, _, href, x, y = cands[0]
        supply_use[(href, round(x, 2), round(y, 2))] += 1
        return href, x, y

    def try_spot(fp, cx, cy, rot, bottom, ref):
        orient(fp, rot, bottom)
        box = move_bbox(fp, cx=cx, cy=cy)
        if box[0] < MARGIN or box[1] < MARGIN or box[2] > W - MARGIN or box[3] > H - MARGIN:
            return None
        g = GAP + LABEL_ROOM.get(ref, 0.0)
        if occ.hits(box[0] - g, box[1] - g, box[2] + g, box[3] + g, ignore=ref, bottom=bottom):
            return None
        if ref in three_v_refs and not bottom:
            if not (box[0] > ISL[0] + 1.0 and box[2] < ISL[2] - 1.0 and box[1] > ISL[1] + 1.0 and box[3] < ISL[3] - 0.5):
                return None
        if ref in five_v_refs and ref not in ISL_OK_5V and not bottom:
            if box[0] < ISL[2] + 0.8 and box[2] > ISL[0] - 0.8 and box[1] < ISL[3] and box[3] > ISL[1] - 0.8:
                return None
        return box

    def spiral(fp, ref, ix, iy, rot, bottom):
        for rad in (0, 1.2, 2.0, 3.0, 4.5, 6.5, 9, 12, 16, 21, 28, 36, 46, 60):
            steps = 1 if rad == 0 else 24
            for k in range(steps):
                a = 2 * math.pi * k / steps
                for r in (rot, (rot + 90) % 360):
                    b = try_spot(fp, ix + rad * math.cos(a), iy + rad * math.sin(a), r, bottom, ref)
                    if b: return b
        return None

    def is_decap(ref):
        p = [n for n in POWER_NETS for r, _ in nets[n] if r == ref]
        return len(p) >= 2 and "GND" in p and any(x in ("+5V", "+3V3") for x in p)

    def signal_targets(ref):
        out, seen = [], set()
        for name, nodes in nets.items():
            if name in POWER_NETS or name.startswith("unconnected"): continue
            if not any(r == ref for r, _ in nodes): continue
            for r, pin, x, y in net_pads[name]:
                if r == ref or r not in placed or (r, pin) in seen: continue
                seen.add((r, pin)); out.append((r, x, y, name))
        return out

    rest = [c["ref"] for c in comps if c["ref"] not in placed]
    def area(ref):
        fp = fps[ref]; fp.SetPosition(pcbnew.VECTOR2I(0, 0)); b = bbox_of(fp)
        return -((b[2] - b[0]) * (b[3] - b[1]))
    rest.sort(key=area)
    failed = []
    for ref in rest:
        fp = fps[ref]; sheet = by_ref[ref]["sheet"]; bottom = ref in BOTTOM_CAPS
        tg = signal_targets(ref); rot = 0
        if is_decap(ref):
            sup = "+3V3" if any(r == ref for r, _ in nets["+3V3"]) else "+5V"
            host = host_supply_pad(ref, sup, sheet)
            if host:
                href, x, y = host; hb = bbox_of(fps[href])
                dx, dy = x - (hb[0] + hb[2]) / 2, y - (hb[1] + hb[3]) / 2
                n = math.hypot(dx, dy) or 1
                ix, iy = x + 3.0 * dx / n, y + 3.0 * dy / n
                rot = 90 if abs(dy) > abs(dx) else 0
            else:
                ix, iy = SHEET_FALLBACK.get(sheet, (W / 2, H / 2))
        elif tg:
            drv = [t for t in tg if t[0] in ("U10", "U4", "X1", "X2", "U13")]
            if len(tg) >= 2 and drv:
                d = drv[0]; o = next(t for t in tg if t[0] != d[0])
                ix, iy = d[1] + 0.28 * (o[1] - d[1]), d[2] + 0.28 * (o[2] - d[2])
                rot = 90 if abs(o[2] - d[2]) > abs(o[1] - d[1]) else 0
            elif len(tg) >= 2:
                ix, iy = (tg[0][1] + tg[1][1]) / 2, (tg[0][2] + tg[1][2]) / 2
                rot = 90 if abs(tg[0][2] - tg[1][2]) > abs(tg[0][1] - tg[1][1]) else 0
            else:
                r, x, y, _ = tg[0]; hb = bbox_of(fps[r])
                dx, dy = x - (hb[0] + hb[2]) / 2, y - (hb[1] + hb[3]) / 2
                n = math.hypot(dx, dy) or 1
                ix, iy = x + 2.6 * dx / n, y + 2.6 * dy / n
                rot = 90 if abs(dy) > abs(dx) else 0
        else:
            ix, iy = SHEET_FALLBACK.get(sheet, (W / 2, H / 2))
        b = spiral(fp, ref, ix, iy, rot, bottom)
        if not b:
            failed.append(ref); continue
        lr = LABEL_ROOM.get(ref, 0.0)
        occ.add((b[0] - lr, b[1] - lr, b[2] + lr, b[3] + lr) if lr else b, ref, bottom=bottom); placed.add(ref); index_fp(ref)
    print(f"placed {len(placed)}/{len(fps)} failed {failed}")
    if failed:
        pcbnew.SaveBoard(PCB, board); sys.exit(3)

    for ref, fp in fps.items():
        for it in (fp.Reference(), fp.Value()):
            x, y = tomm(it.GetPosition().x), tomm(it.GetPosition().y)
            if x < 1 or y < 1 or x > W - 1 or y > H - 1:
                b = bbox_of(fp); it.SetPosition(pcbnew.VECTOR2I_MM((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))

    # ---- outline + notes ----
    add_rect(board, pcbnew.Edge_Cuts, 0, 0, W, H, width=0.1)
    add_rect(board, pcbnew.F_Fab, *hs, width=0.2)
    add_rect(board, pcbnew.Cmts_User, *hs, width=0.15)
    add_text(board, "HEATSINK 40x40 mm on U1. Top-side keepout.", hcx, hs[1] - 1.2, pcbnew.F_Fab, size=0.7)
    add_text(board, "m68030-sbc Rev A  4-layer  220 x 175 mm", 150, 120, pcbnew.F_Fab, size=1.0)
    add_text(board, "SIMM locating holes UNVERIFIED (NPTH as drawn). J10 VERIFY vs HARTING 09032966821.", 110, 57, pcbnew.Cmts_User, size=0.7)
    add_text(board, "DNP: X3, U801-U803, J3. JP801-804 / JP701-703 open.", 110, 102, pcbnew.Cmts_User, size=0.7)

    # ---- power vias ----
    all_pads = []  # x, y, hx, hy, netname
    for ref, fp in fps.items():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            all_pads.append(((tomm(bb.GetLeft()) + tomm(bb.GetRight())) / 2, (tomm(bb.GetTop()) + tomm(bb.GetBottom())) / 2,
                             tomm(bb.GetWidth()) / 2, tomm(bb.GetHeight()) / 2, p.GetNetname(), p.GetLayerSet().Contains(pcbnew.F_Cu), p.GetLayerSet().Contains(pcbnew.B_Cu)))
    segs = []  # placed stubs: (x0,y0,x1,y1,net,layer)

    def in_isl(x, y, m=0.0):
        return ISL[0] - m <= x <= ISL[2] + m and ISL[1] - m <= y <= ISL[3] + m

    def via_ok(x, y, size, net):
        if x < 1.5 or y < 1.5 or x > W - 1.5 or y > H - 1.5: return False
        if net == "+3V3" and not in_isl(x, y, -1.2): return False
        if net == "+5V" and in_isl(x, y, 1.2): return False
        r = size / 2 + 0.2
        for px, py, hx, hy, *_ in all_pads:
            if abs(x - px) < hx + r and abs(y - py) < hy + r: return False
        for s in segs:
            if seg_dist(x, y, s) < r + 0.15: return False
        return True

    def seg_dist(x, y, s):
        x0, y0, x1, y1 = s[:4]; dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / L))
        return math.hypot(x - (x0 + t * dx), y - (y0 + t * dy))

    def stub_ok(x0, y0, x1, y1, net, layer_top, width=0.3):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.1))
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n; y = y0 + (y1 - y0) * i / n
            for px, py, hx, hy, pn, onF, onB in all_pads:
                if pn == net: continue
                if (layer_top and not onF) or ((not layer_top) and not onB): continue
                if abs(x - px) < hx + width / 2 + 0.2 and abs(y - py) < hy + width / 2 + 0.2: return False
        for s in segs:
            if s[4] == net or s[5] != layer_top: continue
            for i in range(n + 1):
                x = x0 + (x1 - x0) * i / n; y = y0 + (y1 - y0) * i / n
                if seg_dist(x, y, s) < width + 0.2: return False
        return True

    def add_via(x, y, net):
        v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        v.SetDrill(mm(PWR_VIA_DRILL)); v.SetWidth(pcbnew.F_Cu, mm(PWR_VIA_SIZE))
        v.SetNet(board.FindNet(net)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); board.Add(v)
        all_pads.append((x, y, PWR_VIA_SIZE / 2, PWR_VIA_SIZE / 2, net, True, True))

    def add_track(pts, net, top, width=0.3):
        for (a, b) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I_MM(*a)); t.SetEnd(pcbnew.VECTOR2I_MM(*b))
            t.SetWidth(mm(width)); t.SetLayer(pcbnew.F_Cu if top else pcbnew.B_Cu); t.SetNet(board.FindNet(net)); board.Add(t)
            segs.append((a[0], a[1], b[0], b[1], net, top))

    nvia, nfail, escapes = 0, [], []
    escape_jobs = []
    for ref, fp in sorted(fps.items()):
        for p in fp.Pads():
            net = p.GetNetname()
            if net not in POWER_NETS: continue
            x, y = tomm(p.GetPosition().x), tomm(p.GetPosition().y)
            pth = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            if net == "+5V" and in_isl(x, y, 0.6):
                escape_jobs.append((ref, p, x, y, pth)); continue
            if pth: continue
            top = not fp.IsFlipped()
            sz = p.GetSize(); sw, sh = tomm(sz.x), tomm(sz.y)
            if min(sw, sh) >= 3.0:
                k = 0
                for ox in (-0.25, 0.25) if max(sw, sh) < 6 else (-0.3, 0, 0.3):
                    for oy in (-0.25, 0.25) if max(sw, sh) < 6 else (-0.3, 0, 0.3):
                        vx, vy = x + ox * sw * 0.8, y + oy * sh * 0.8
                        if p.HitTest(pcbnew.VECTOR2I_MM(vx, vy)) and (net != "+3V3" or in_isl(vx, vy, -1.2)) and (net != "+5V" or not in_isl(vx, vy, 1.2)):
                            add_via(vx, vy, net); nvia += 1; k += 1
                if k: continue
            spot = None
            for dist in (1.0, 1.3, 1.7, 2.1, 2.6, 3.2):
                for k in range(16):
                    a = 2 * math.pi * k / 16
                    vx, vy = x + dist * math.cos(a), y + dist * math.sin(a)
                    if via_ok(vx, vy, PWR_VIA_SIZE, net) and stub_ok(x, y, vx, vy, net, top):
                        spot = (vx, vy); break
                if spot: break
            if not spot:
                nfail.append(f"{ref}.{p.GetNumber()}"); continue
            add_via(*spot, net); add_track([(x, y), spot], net, top); nvia += 1

    # +5V pads inside the +3V3 island: grid A* on F.Cu out of the island, then a via.
    G = 0.25
    gx0, gy0 = ISL[0] - 8, ISL[1] - 8
    GW, GH = int((ISL[2] - ISL[0] + 16) / G), int((min(H, ISL[3] + 8) - gy0) / G)
    def blocked_grid(net):
        bl = bytearray(GW * GH)
        ex = 0.15 + 0.2 + 0.05
        for px, py, hx, hy, pn, onF, onB in all_pads:
            if pn == net or not onF: continue
            for gy in range(max(0, int((py - hy - ex - gy0) / G)), min(GH, int((py + hy + ex - gy0) / G) + 1)):
                for gx in range(max(0, int((px - hx - ex - gx0) / G)), min(GW, int((px + hx + ex - gx0) / G) + 1)):
                    bl[gy * GW + gx] = 1
        for s in segs:
            if not s[5] or s[4] == net: continue
            n = max(2, int(math.hypot(s[2] - s[0], s[3] - s[1]) / 0.1))
            for i in range(n + 1):
                x = s[0] + (s[2] - s[0]) * i / n; y = s[1] + (s[3] - s[1]) * i / n
                for gy in range(max(0, int((y - 0.55 - gy0) / G)), min(GH, int((y + 0.55 - gy0) / G) + 1)):
                    for gx in range(max(0, int((x - 0.55 - gx0) / G)), min(GW, int((x + 0.55 - gx0) / G) + 1)):
                        bl[gy * GW + gx] = 1
        # board edge
        for gy in range(GH):
            for gx in range(GW):
                x, y = gx0 + gx * G, gy0 + gy * G
                if y > H - 0.8 or x < 0.8 or x > W - 0.8: bl[gy * GW + gx] = 1
        return bl
    for ref, p, x, y, pth in escape_jobs:
        bl = blocked_grid("+5V")
        sx, sy = int(round((x - gx0) / G)), int(round((y - gy0) / G))
        # free a small window on the own pad
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if 0 <= sx + dx < GW and 0 <= sy + dy < GH: bl[(sy + dy) * GW + sx + dx] = 0
        start = (sx, sy); came = {start: None}; g = {start: 0}; pq = [(0, start)]; goal = None
        while pq:
            _, cur = heapq.heappop(pq)
            cx, cy = gx0 + cur[0] * G, gy0 + cur[1] * G
            if not in_isl(cx, cy, 1.3) and via_ok(cx, cy, PWR_VIA_SIZE, "+5V"):
                goal = cur; break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cur[0] + dx, cur[1] + dy
                if not (0 <= nx < GW and 0 <= ny < GH) or bl[ny * GW + nx]: continue
                ng = g[cur] + 1
                if ng < g.get((nx, ny), 1 << 30):
                    g[(nx, ny)] = ng; came[(nx, ny)] = cur; heapq.heappush(pq, (ng, (nx, ny)))
        if not goal:
            nfail.append(f"{ref}.{p.GetNumber()} (island escape)"); continue
        path = []; c = goal
        while c: path.append((gx0 + c[0] * G, gy0 + c[1] * G)); c = came[c]
        path.reverse(); path[0] = (x, y)
        simp = [path[0]]
        for q in path[1:]:
            if len(simp) >= 2 and ((simp[-2][0] == simp[-1][0] == q[0]) or (simp[-2][1] == simp[-1][1] == q[1])):
                simp[-1] = q
            else:
                simp.append(q)
        add_track(simp, "+5V", True, width=0.3)
        add_via(*simp[-1], "+5V"); nvia += 1
        escapes.append((f"{ref}.{p.GetNumber()}", round(len(path) * G, 1)))
    print("power vias", nvia, "fail", nfail)
    print("island escapes", escapes)

    # Edge GND stitch: skipped. With GND only on In1 a stitch via has nothing to stitch to
    # (DRC flags it via_dangling). Add it back if outer-layer GND pours are added.
    st = 0
    if False:
     for (x, y) in ([(x, 1.8) for x in frange(10, W - 10, 10)] + [(x, H - 1.8) for x in frange(10, W - 10, 10)] +
                   [(1.8, y) for y in frange(10, H - 10, 10)] + [(W - 1.8, y) for y in frange(10, H - 10, 10)]):
        if via_ok(x, y, 0.8, "GND"):
            add_via(x, y, "GND"); st += 1
    print("edge stitch", st)

    # ---- zones ----
    def zone(net, layer, prio, outline, hole=None, name=None, spoke=0.4):
        z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(board.FindNet(net))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetThermalReliefGap(mm(0.25))
        z.SetThermalReliefSpokeWidth(mm(spoke)); z.SetMinThickness(mm(0.2)); z.SetLocalClearance(mm(0.2))
        z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        z.SetAssignedPriority(prio); z.SetZoneName(name or f"{net} {board.GetLayerName(layer)}")
        ol = z.Outline(); ol.NewOutline()
        for x, y in outline: ol.Append(mm(x), mm(y))
        if hole:
            ol.NewHole()
            x0, y0, x1, y1 = hole
            for x, y in ((x0, y0), (x0, y1), (x1, y1), (x1, y0)): ol.Append(mm(x), mm(y))
        board.Add(z); return z
    i = 0.6
    full = [(i, i), (W - i, i), (W - i, H - i), (i, H - i)]
    zone("GND", pcbnew.In1_Cu, 0, full)
    ix1, iy1 = min(ISL[2], W - 1.0), min(ISL[3], H - 1.0)
    # No hole cut: the priority-1 +3V3 island knocks +5V out (a hole here fractures the fill).
    zone("+5V", pcbnew.In2_Cu, 0, full)
    zone("+3V3", pcbnew.In2_Cu, 1, [(ISL[0], ISL[1]), (ix1, ISL[1]), (ix1, iy1), (ISL[0], iy1)], name="+3V3 island", spoke=0.35)
    # all +3V3 pads must be inside the island
    out3 = [(r, pin, round(x, 1), round(y, 1)) for r, pin, x, y in net_pads["+3V3"] if not in_isl(x, y, -0.8)]
    print("+3V3 pads outside island:", out3)

    tb = board.GetTitleBlock()
    tb.SetTitle("m68030-sbc Rev A - condensed 220x175"); tb.SetDate("2026-10-17")
    tb.SetComment(2, "Option B: 220x175 mm, SMD osc/IDE buffers/battery/fuse. Signals unrouted.")
    pcbnew.SaveBoard(PCB, board)
    inject_stackup(PCB)
    board = pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    inject_stackup(PCB)
    print("saved", PCB)


if __name__ == "__main__":
    main()
