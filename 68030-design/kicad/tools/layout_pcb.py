#!/usr/bin/env python3
"""First-pass PCB for m68030-sbc.

Builds the board from the KiCad sexpr netlist (schematic parity), places every
footprint, pours GND / +5V / +3V3, stitches SMD power pins, and routes the
clock and DRAM control nets that come out cleanly. Does not touch schematics.
"""
from __future__ import annotations

import math
import os
import re
import sys
import heapq
from collections import defaultdict

import pcbnew

ROOT = "/workspace/68030-design/kicad"
NETLIST = "/tmp/nl/m68030-sbc.net"
OUT = os.path.join(ROOT, "m68030-sbc.kicad_pcb")
FP_ROOT = "/usr/share/kicad/footprints"
PROJ_PRETTY = os.path.join(ROOT, "lib/m68030-sbc.pretty")

# Board outline. Spec is silent on exact size; this is sized to the parts
# with the connectors on the edges. Square corners (no radius).
W = 275.0
H = 215.0
MARGIN = 0.8
GAP = 0.45  # minimum gap between footprint bounding boxes (courtyards included)

POWER_NETS = {"GND", "+5V", "+3V3"}
# Critical nets routed on F.Cu (microstrip over the GND plane).
ROUTE_PREFIXES = (
    "/CLK_",
    "/DRAM_CLK",
    "/clock/CLKB_",
    "/clock/CLK_FPU",
    "/dram/U4_MA",
    "/dram/U4_RAS",
    "/dram/U4_CAS",
    "/dram/U4_WE",
    "/dram/MA",
    "/dram/RAS",
    "/dram/CAS",
    "/dram/WE",
    "/CAS3_n",
    "/RAS0_n",
    "/WE_n",
)

TRACK_W = 0.25  # mm, ~59 ohm microstrip, see LAYOUT.md
CLEARANCE = 0.15
VIA_DRILL = 0.30
VIA_SIZE = 0.60
PWR_VIA_DRILL = 0.40
PWR_VIA_SIZE = 0.80


def mm(v):
    return pcbnew.FromMM(v)


def tomm(v):
    return pcbnew.ToMM(v)


def lib_path(nick):
    if nick == "m68030-sbc":
        return PROJ_PRETTY
    return os.path.join(FP_ROOT, nick + ".pretty")


def parse_netlist(path):
    text = open(path, encoding="utf-8").read()
    # components
    body, _, nets_blob = text.partition("\n  (nets")
    comps = []
    for chunk in body.split("\n    (comp ")[1:]:
        ref = re.search(r'\(ref "([^"]+)"\)', chunk).group(1)
        val = re.search(r'\(value "([^"]*)"\)', chunk).group(1)
        fp = re.search(r'\(footprint "([^"]+)"\)', chunk).group(1)
        sheet = re.search(r'\(sheetpath \(names "([^"]*)"\)', chunk)
        sheet = sheet.group(1) if sheet else "/"
        comps.append({"ref": ref, "value": val, "fp": fp, "sheet": sheet})
    nets = {}  # name -> list[(ref, pin)]
    order = []
    for chunk in nets_blob.split("\n    (net ")[1:]:
        name = re.search(r'\(name "([^"]*)"\)', chunk).group(1)
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', chunk)
        nets[name] = nodes
        order.append(name)
    return comps, nets, order


class Occupancy:
    def __init__(self):
        self.boxes = []  # x0,y0,x1,y1,ref,bottom

    def hits(self, x0, y0, x1, y1, ignore=None, bottom=False):
        for a in self.boxes:
            if a[4] == ignore:
                continue
            # heatsink blocks top only
            if a[4] == "HEATSINK" and bottom:
                continue
            if x0 < a[2] and x1 > a[0] and y0 < a[3] and y1 > a[1]:
                return a[4]
        return None

    def add(self, box, ref, bottom=False):
        self.boxes.append((box[0], box[1], box[2], box[3], ref, bottom))


def bbox_of(fp):
    bb = fp.GetBoundingBox(False, False)
    return (tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom()))


def orient(fp, rot, bottom):
    # Flip first around the origin, then rotate. Calling twice is avoided.
    if bottom and not fp.IsFlipped():
        fp.Flip(pcbnew.VECTOR2I(0, 0), False)
    if (not bottom) and fp.IsFlipped():
        fp.Flip(pcbnew.VECTOR2I(0, 0), False)
    fp.SetOrientationDegrees(rot)


def move_bbox(fp, *, cx=None, cy=None, left=None, top=None):
    """Place so the courtyard bbox matches the requested center and/or edges."""
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    x0, y0, x1, y1 = bbox_of(fp)
    dx = dy = 0.0
    if cx is not None:
        dx = cx - (x0 + x1) / 2
    elif left is not None:
        dx = left - x0
    if cy is not None:
        dy = cy - (y0 + y1) / 2
    elif top is not None:
        dy = top - y0
    fp.SetPosition(pcbnew.VECTOR2I(mm(dx), mm(dy)))
    return bbox_of(fp)


def tidy_fields(fp):
    bb = fp.GetBoundingBox(False, False)
    ref = fp.Reference()
    ref.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
    ref.SetTextThickness(mm(0.12))
    val = fp.Value()
    val.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)))
    val.SetTextThickness(mm(0.1))
    # Keep the footprint's own silk reference; only pull text back on-board later.
    return bb


def add_line(board, layer, x0, y0, x1, y1, width=0.12):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(layer)
    s.SetStart(pcbnew.VECTOR2I_MM(x0, y0))
    s.SetEnd(pcbnew.VECTOR2I_MM(x1, y1))
    s.SetWidth(mm(width))
    board.Add(s)
    return s


def add_rect(board, layer, x0, y0, x1, y1, width=0.15):
    add_line(board, layer, x0, y0, x1, y0, width)
    add_line(board, layer, x1, y0, x1, y1, width)
    add_line(board, layer, x1, y1, x0, y1, width)
    add_line(board, layer, x0, y1, x0, y0, width)


def add_text(board, text, x, y, layer, size=1.0, rot=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    t.SetTextAngleDegrees(rot)
    board.Add(t)
    return t


def main():
    sys.stdout.reconfigure(line_buffering=True)
    comps, nets, net_order = parse_netlist(NETLIST)
    by_ref = {c["ref"]: c for c in comps}
    print(f"netlist {len(comps)} components, {len(nets)} nets")

    board = pcbnew.CreateEmptyBoard()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    ds.SetBoardThickness(mm(1.6))
    ds.m_HasStackup = True
    board.SetLayerName(pcbnew.In1_Cu, "GND")
    board.SetLayerName(pcbnew.In2_Cu, "+5V")
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)

    ds.m_MinClearance = mm(CLEARANCE)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.50)
    ds.m_ViasMinDrill = mm(0.30) if hasattr(ds, "m_ViasMinDrill") else ds.m_MinThroughDrill
    ds.m_MinThroughDrill = mm(0.30)
    ds.m_CopperEdgeClearance = mm(0.30)
    ds.m_HoleToHoleMin = mm(0.25)
    ds.m_HoleClearance = mm(0.20)
    ds.m_SilkClearance = mm(0.10)
    ds.m_MinSilkTextHeight = mm(0.6)
    ds.m_MinSilkTextThickness = mm(0.08)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(CLEARANCE))
    nc.SetTrackWidth(mm(0.20))
    nc.SetViaDiameter(mm(VIA_SIZE))
    nc.SetViaDrill(mm(VIA_DRILL))
    nc.SetDescription("Default 0.20 mm signal, 0.15 mm clearance")

    # Clock / DRAM netclass (wider, still within the SOIC escape).
    clk = pcbnew.NETCLASS("CLK_DRAM")
    clk.SetClearance(mm(CLEARANCE))
    clk.SetTrackWidth(mm(TRACK_W))
    clk.SetViaDiameter(mm(VIA_SIZE))
    clk.SetViaDrill(mm(VIA_DRILL))
    clk.SetPriority(1)
    ds.m_NetSettings.SetNetclass("CLK_DRAM", clk)
    for pat in ("/CLK_*", "/DRAM_CLK", "/clock/CLKB_*", "/clock/CLK_FPU*",
                "/dram/U4_*", "/dram/MA*", "/dram/RAS*", "/dram/CAS*", "/dram/WE*",
                "/CAS*", "/RAS*", "/WE_n"):
        ds.m_NetSettings.SetNetclassPatternAssignment(pat, "CLK_DRAM")
    ds.m_NetSettings.RecomputeEffectiveNetclasses()

    # Nets
    code = 1
    for name in net_order:
        ni = pcbnew.NETINFO_ITEM(board, name, code)
        board.Add(ni)
        code += 1
    board.BuildListOfNets()

    missing_fp = []
    fps = {}
    no_3d = []
    for c in comps:
        nick, name = c["fp"].split(":", 1)
        path = lib_path(nick)
        fp = pcbnew.FootprintLoad(path, name)
        if fp is None:
            missing_fp.append(c)
            continue
        fp.SetFPID(pcbnew.LIB_ID(nick, name))
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"])
        tidy_fields(fp)
        board.Add(fp)
        fps[c["ref"]] = fp
        models = list(fp.Models())
        if not models:
            no_3d.append((c["ref"], c["fp"], "no 3D model in footprint"))
        else:
            for m in models:
                fn = m.m_Filename or ""
                expanded = fn.replace("${KICAD9_3DMODEL_DIR}", "/usr/share/kicad/3dmodels")
                expanded = expanded.replace("${KICAD8_3DMODEL_DIR}", "/usr/share/kicad/3dmodels")
                if not os.path.isfile(expanded):
                    no_3d.append((c["ref"], c["fp"], fn))
                    break
    if missing_fp:
        print("MISSING FOOTPRINTS", missing_fp)
        sys.exit(1)
    print(f"loaded {len(fps)} footprints")

    # Assign pad nets from the netlist.
    pin_miss = []
    pad_index = {}
    for ref, fp in fps.items():
        pad_index[ref] = {}
        for p in fp.Pads():
            pad_index[ref].setdefault(p.GetNumber(), []).append(p)
    for name, nodes in nets.items():
        net = board.FindNet(name)
        if net is None:
            print("net missing", name)
            continue
        for ref, pin in nodes:
            pads = pad_index.get(ref, {}).get(pin)
            if not pads:
                pin_miss.append((ref, pin, name))
                continue
            for p in pads:
                p.SetNet(net)
    print(f"pad-net misses: {len(pin_miss)}")
    for row in pin_miss[:30]:
        print("  miss", row)

    # ----- placement -----
    occ = Occupancy()

    # (ref, cx, cy, rot, bottom) courtyard-center placement.
    # None means "special" (edge-aligned) handled below.
    anchors = {
        "H1": (8, 8, 0),
        "H2": (267, 8, 0),
        "H3": (8, 207, 0),
        "H4": (267, 207, 0),
        "J10": (12, 95, 0),          # left edge, DIN 41612
        "J1": (140, 8.2, 0),         # top edge, SIMM
        "J11": (268, 50, 0),       # right edge, LA1
        "J12": (268, 110, 0),
        "J13": (268, 170, 0),
        "J4": (50, 16, 90),          # top edge, left of SIMM, JTAG U3
        "J5": (222, 16, 90),         # top edge, right of SIMM, JTAG U4
        "J6": (185, 204, 90),        # bottom edge, IDE
        "J7": (36, 208, 90),         # bottom edge, TTL-232 A
        "J8": (60, 208, 90),
        "J9": (128, 206, 90),        # bottom edge, SPI / NIC, in the 3V3 cluster
        "J3": (78, 198, 0),
        "U1": (208, 102, 0),
        "U2": (150, 108, 0),
        "U4": (150, 52, 0),
        "U3": (100, 108, 0),
        "U5": (98, 150, 0),
        "U6": (132, 158, 0),
        "U10": (180, 142, 0),
        "X1": (158, 138, 0),
        "X2": (222, 140, 0),
        "X3": (236, 162, 0),         # DNP FPU oscillator
        "Y1": (112, 172, 90),
        "U14": (42, 50, 0),
        "U15": (64, 50, 0),
        "U16": (42, 68, 0),
        "U17": (64, 68, 0),
        "U18": (42, 86, 0),
        "U19": (64, 86, 0),
        "U20": (42, 104, 0),
        "U21": (64, 122, 0),
        "U11": (168, 176, 0),
        "U12": (190, 176, 0),
        "U13": (210, 176, 90),       # turned so the row fits above the IDE header
        "U801": (196, 44, 0),        # DNP fallback mux
        "U802": (214, 44, 0),
        "U803": (232, 44, 0),
        "U8": (52, 168, 0),
        "L1": (86, 170, 0),
        "Q1": (32, 152, 0),
        "F1": (52, 188, 0),
        "U9": (118, 190, 0),
        "U22": (140, 176, 0),
        "U23": (145, 193, 0),
        "BT1": (248, 188, 0),
        "U7": (56, 136, 0),
        "U27": (74, 136, 0),
        "SW1": (82, 208, 0),
        "SW2": (98, 208, 0),
        "SW3": (114, 208, 0),
        "JP3": (196, 158, 0),
    }

    placed = set()

    def commit(ref, fp, box, bottom=False):
        hit = occ.hits(box[0] - GAP, box[1] - GAP, box[2] + GAP, box[3] + GAP, ignore=ref, bottom=bottom)
        occ.add(box, ref, bottom=bottom)
        placed.add(ref)
        return hit

    anchor_hits = []
    for ref, (cx, cy, rot) in anchors.items():
        fp = fps[ref]
        orient(fp, rot, False)
        box = move_bbox(fp, cx=cx, cy=cy)
        hit = commit(ref, fp, box, False)
        if hit:
            anchor_hits.append((ref, hit, tuple(round(v, 1) for v in box)))
        if box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > H:
            anchor_hits.append((ref, "OFF_BOARD", tuple(round(v, 1) for v in box)))

    # Barrel jack: opening is the negative-X side of the footprint. Face it out the left edge.
    fp = fps["J2"]
    orient(fp, 0, False)
    box = move_bbox(fp, left=1.0, cy=164)
    hit = commit("J2", fp, box, False)
    if hit or box[0] < 0 or box[3] > H:
        anchor_hits.append(("J2", hit or "OFF_BOARD", tuple(round(v, 1) for v in box)))

    print(f"anchor conflicts: {len(anchor_hits)}")
    for row in anchor_hits:
        print("  ANCHOR", row)
    if anchor_hits:
        # Still save a preview so the geometry can be inspected, but stop before passives.
        pcbnew.SaveBoard(OUT, board)
        print("saved preview", OUT)
        sys.exit(2)

    # Heatsink keepout on the top side, 40 x 40 mm centered on the PGA.
    u1b = bbox_of(fps["U1"])
    hcx, hcy = (u1b[0] + u1b[2]) / 2, (u1b[1] + u1b[3]) / 2
    hs = (hcx - 20, hcy - 20, hcx + 20, hcy + 20)
    occ.add(hs, "HEATSINK", bottom=False)
    add_rect(board, pcbnew.F_Fab, *hs, width=0.2)
    add_rect(board, pcbnew.Cmts_User, *hs, width=0.15)
    add_text(
        board,
        "HEATSINK stick-on 40x40 mm centered on U1. Keep other top-side parts outside this outline. PGA thetaJA ~30 C/W, up to 2.6 W (spec 6.3).",
        hcx,
        hs[1] - 2.2,
        pcbnew.F_Fab,
        size=0.7,
    )

    # Pad lookup for placement targets.
    # ref -> list of (pin, x, y, netname, pad)
    pad_pos = defaultdict(list)
    net_pads = defaultdict(list)  # net -> list (ref, pin, x, y)

    def index_fp(ref):
        fp = fps[ref]
        for p in fp.Pads():
            pos = p.GetPosition()
            x, y = tomm(pos.x), tomm(pos.y)
            net = p.GetNetname()
            pad_pos[ref].append((p.GetNumber(), x, y, net, p))
            if net:
                net_pads[net].append((ref, p.GetNumber(), x, y))

    for ref in placed:
        index_fp(ref)

    supply_use = defaultdict(int)  # (host ref, px, py) -> count

    SHEET_FALLBACK = {
        "/power/": (60, 175),
        "/clock/": (180, 145),
        "/reset/": (70, 175),
        "/cpu/": (208, 130),
        "/fpu/": (150, 130),
        "/glue_cpld/": (100, 130),
        "/dram/": (170, 30),
        "/rom/": (98, 168),
        "/duart_spi_rtc/": (145, 185),
        "/ide/": (190, 190),
        "/expansion/": (52, 70),
        "/debug/": (230, 90),
        "/": (20, 20),
    }

    def host_supply_pad(ref, supply_net, sheet):
        cands = []
        for href, pin, x, y in net_pads[supply_net]:
            if href == ref or href not in placed:
                continue
            if href[0] not in ("U", "J", "X", "Q", "L"):
                continue
            same = by_ref[href]["sheet"] == sheet
            cands.append((0 if same else 1, supply_use[(href, round(x, 2), round(y, 2))], href, x, y))
        if not cands:
            return None
        cands.sort()
        _, _, href, x, y = cands[0]
        supply_use[(href, round(x, 2), round(y, 2))] += 1
        return href, x, y

    def try_spot(fp, cx, cy, rot, bottom, ref):
        orient(fp, rot, bottom)
        box = move_bbox(fp, cx=cx, cy=cy)
        if box[0] < MARGIN or box[1] < MARGIN or box[2] > W - MARGIN or box[3] > H - MARGIN:
            return None
        hit = occ.hits(box[0] - GAP, box[1] - GAP, box[2] + GAP, box[3] + GAP, ignore=ref, bottom=bottom)
        if hit:
            return None
        return box

    def spiral(fp, ref, ix, iy, rot, bottom):
        # Also try the opposite rotation if the preferred one is tight.
        rots = [rot, (rot + 90) % 360]
        for rad in (0, 1.6, 3.0, 4.5, 6.5, 9, 12, 16, 21, 28, 36, 46):
            steps = 1 if rad == 0 else 16
            for k in range(steps):
                ang = 2 * math.pi * k / steps
                x = ix + rad * math.cos(ang)
                y = iy + rad * math.sin(ang)
                for r in rots:
                    box = try_spot(fp, x, y, r, bottom, ref)
                    if box:
                        return box
        return None

    # CPU 100 nF (C501-C510) go on the bottom, just outside the PGA, per spec
    # "under the socket" as far as the 2.54 mm pin grid allows. 0805 does not
    # fit between the 1.42 mm PGA pads, and footprints must not stack, so they
    # sit in a ring outside U1 (and outside the 40 mm heatsink).
    bottom_caps = {f"C{n}" for n in range(501, 511)}

    def is_decap(ref):
        pins = []
        # nets from netlist, footprint not placed yet
        for name, nodes in ((n, nets[n]) for n in POWER_NETS):
            for r, pin in nodes:
                if r == ref:
                    pins.append(name)
        return len(pins) >= 2 and "GND" in pins and any(p in ("+5V", "+3V3") for p in pins)

    def signal_targets(ref):
        """Placed pads on this part's non-power nets."""
        targets = []
        seen = set()
        for name, nodes in nets.items():
            if name in POWER_NETS or name.startswith("unconnected"):
                continue
            mine = [pin for r, pin in nodes if r == ref]
            if not mine:
                continue
            for r, pin, x, y in net_pads[name]:
                if r == ref or r not in placed:
                    continue
                key = (r, pin)
                if key in seen:
                    continue
                seen.add(key)
                targets.append((r, x, y, name))
        return targets

    passives = [c["ref"] for c in comps if c["ref"] not in placed]
    # Larger first.
    def area_key(ref):
        fp = fps[ref]
        fp.SetPosition(pcbnew.VECTOR2I(0, 0))
        b = bbox_of(fp)
        return -((b[2] - b[0]) * (b[3] - b[1]))

    passives.sort(key=area_key)
    failed = []
    for ref in passives:
        fp = fps[ref]
        sheet = by_ref[ref]["sheet"]
        bottom = ref in bottom_caps
        targets = signal_targets(ref)
        rot = 0
        if is_decap(ref):
            supply = "+3V3" if any(
                r == ref for r, _ in nets.get("+3V3", [])
            ) else "+5V"
            host = host_supply_pad(ref, supply, sheet)
            if host:
                href, x, y = host
                hb = bbox_of(fps[href])
                cxh, cyh = (hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2
                dx, dy = x - cxh, y - cyh
                norm = math.hypot(dx, dy) or 1
                # Sit just outside the host, on the pad's side.
                ix = x + 3.2 * dx / norm
                iy = y + 3.2 * dy / norm
                rot = 90 if abs(dy) > abs(dx) else 0
            else:
                ix, iy = SHEET_FALLBACK.get(sheet, (W / 2, H / 2))
        elif targets:
            # Source termination: keep series resistors next to the driver.
            drivers = [t for t in targets if t[0] in ("U10", "U4", "X1", "X2", "U13")]
            if len(targets) >= 2 and drivers:
                d = drivers[0]
                other = next(t for t in targets if t[0] != d[0])
                ix = d[1] + 0.28 * (other[1] - d[1])
                iy = d[2] + 0.28 * (other[2] - d[2])
                rot = 90 if abs(other[2] - d[2]) > abs(other[1] - d[1]) else 0
            elif len(targets) >= 2:
                ix = sum(t[1] for t in targets[:2]) / 2
                iy = sum(t[2] for t in targets[:2]) / 2
                rot = 90 if abs(targets[0][2] - targets[1][2]) > abs(targets[0][1] - targets[1][1]) else 0
            else:
                r, x, y, _ = targets[0]
                hb = bbox_of(fps[r])
                cxh, cyh = (hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2
                dx, dy = x - cxh, y - cyh
                norm = math.hypot(dx, dy) or 1
                ix = x + 2.6 * dx / norm
                iy = y + 2.6 * dy / norm
                rot = 90 if abs(dy) > abs(dx) else 0
        else:
            ix, iy = SHEET_FALLBACK.get(sheet, (40, 40))
        box = spiral(fp, ref, ix, iy, rot, bottom)
        if not box:
            failed.append(ref)
            continue
        occ.add(box, ref, bottom=bottom)
        placed.add(ref)
        index_fp(ref)

    print(f"placed {len(placed)}/{len(fps)} failed {len(failed)} {failed}")

    # Pull reference/value text back inside the outline if a footprint default hangs off.
    for ref, fp in fps.items():
        for item in (fp.Reference(), fp.Value()):
            pos = item.GetPosition()
            x, y = tomm(pos.x), tomm(pos.y)
            if x < 1 or y < 1 or x > W - 1 or y > H - 1:
                b = bbox_of(fp)
                item.SetPosition(pcbnew.VECTOR2I_MM((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))

    # Outline, square corners.
    add_rect(board, pcbnew.Edge_Cuts, 0, 0, W, H, width=0.1)

    add_text(board, "m68030-sbc  Rev A   4-layer   275 x 215 mm", 70, 28, pcbnew.F_SilkS, size=1.2)
    add_text(
        board,
        "SIMM locating holes UNVERIFIED: NPTH as drawn (1.63 / 2.41 mm). Do not treat as plated. Print 1:1 vs TE 5822021 / 114-1061.",
        140,
        20,
        pcbnew.F_Fab,
        size=0.7,
    )
    add_text(
        board,
        "J10 footprint is KiCad DIN41612_C_3x32_Female_Vertical_THT. VERIFY against HARTING 09032966821 before ordering.",
        28,
        30,
        pcbnew.F_Fab,
        size=0.6,
    )
    add_text(
        board,
        "DNP: X3, U801 U802 U803 (74ACT257 mux fallback). JP801-804 and JP701-703 open.",
        40,
        36,
        pcbnew.F_Fab,
        size=0.7,
    )

    # ----- power vias on SMD pads -----
    # Spatial pads for via clearance.
    all_pads = []
    for ref, fp in fps.items():
        for p in fp.Pads():
            pos = p.GetPosition()
            sz = p.GetSize()
            all_pads.append((tomm(pos.x), tomm(pos.y), tomm(sz.x) / 2, tomm(sz.y) / 2, p.GetNumber(), ref, p.GetAttribute()))

    def via_ok(x, y, drill, size):
        if x < 1.2 or y < 1.2 or x > W - 1.2 or y > H - 1.2:
            return False
        r = size / 2 + CLEARANCE
        for px, py, hx, hy, *_ in all_pads:
            if abs(x - px) < hx + r and abs(y - py) < hy + r:
                return False
        return True

    n_vias = 0
    for ref, fp in fps.items():
        for p in fp.Pads():
            netname = p.GetNetname()
            if netname not in POWER_NETS:
                continue
            attr = p.GetAttribute()
            # THT pads already pierce the planes.
            if attr == pcbnew.PAD_ATTRIB_PTH:
                continue
            pos = p.GetPosition()
            x, y = tomm(pos.x), tomm(pos.y)
            drill = PWR_VIA_DRILL
            size = PWR_VIA_SIZE
            spot = None
            for dist in (1.05, 1.35, 1.7, 2.1, 2.6):
                for k in range(16):
                    ang = 2 * math.pi * k / 16
                    vx, vy = x + dist * math.cos(ang), y + dist * math.sin(ang)
                    if via_ok(vx, vy, drill, size):
                        spot = (vx, vy)
                        break
                if spot:
                    break
            if not spot:
                continue
            net = p.GetNet()
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I_MM(*spot))
            via.SetDrill(mm(drill))
            via.SetWidth(pcbnew.F_Cu, mm(size))
            via.SetNet(net)
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            board.Add(via)
            layer = pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu
            tr = pcbnew.PCB_TRACK(board)
            tr.SetStart(pcbnew.VECTOR2I_MM(x, y))
            tr.SetEnd(pcbnew.VECTOR2I_MM(*spot))
            tr.SetWidth(mm(0.30 if netname != "GND" else 0.30))
            tr.SetLayer(layer)
            tr.SetNet(net)
            board.Add(tr)
            # Remember the via as a pad so later vias clear it.
            all_pads.append((spot[0], spot[1], size / 2, size / 2, "via", ref, 0))
            n_vias += 1
    print(f"power vias {n_vias}")

    # Edge GND stitch, skipping anything too close to a pad.
    stitch = 0
    for i, (x, y) in enumerate(
        [(x, 2.0) for x in frange(8, W - 8, 12)]
        + [(x, H - 2.0) for x in frange(8, W - 8, 12)]
        + [(2.0, y) for y in frange(8, H - 8, 12)]
        + [(W - 2.0, y) for y in frange(8, H - 8, 12)]
    ):
        if via_ok(x, y, 0.4, 0.8):
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            via.SetDrill(mm(0.40))
            via.SetWidth(pcbnew.F_Cu, mm(0.80))
            via.SetNet(board.FindNet("GND"))
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            board.Add(via)
            all_pads.append((x, y, 0.4, 0.4, "st", "H", 0))
            stitch += 1
    print(f"edge stitch vias {stitch}")

    # Zones. +3V3 island is the bbox of every +3V3 pad, expanded, cut out of +5V.
    xs, ys = [], []
    for ref, pin, x, y in net_pads["+3V3"]:
        xs.append(x)
        ys.append(y)
    if xs:
        ix0, iy0, ix1, iy1 = min(xs) - 3.5, min(ys) - 3.5, max(xs) + 3.5, max(ys) + 3.5
        # Keep the island and the +5V hole strictly inside the zone outline (inset 0.6).
        ix0 = max(ix0, 2.0)
        iy0 = max(iy0, 2.0)
        ix1 = min(ix1, W - 2.0)
        iy1 = min(iy1, H - 2.0)
    else:
        ix0 = iy0 = ix1 = iy1 = 0

    def make_zone(name, layer, priority, hole=None):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(board.FindNet(name))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(0.25))
        z.SetThermalReliefSpokeWidth(mm(0.40))
        z.SetMinThickness(mm(0.20))
        z.SetLocalClearance(mm(0.20))
        z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        z.SetAssignedPriority(priority)
        z.SetZoneName(name + " " + board.GetLayerName(layer))
        ol = z.Outline()
        ol.NewOutline()
        inset = 0.6
        for x, y in ((inset, inset), (W - inset, inset), (W - inset, H - inset), (inset, H - inset)):
            ol.Append(mm(x), mm(y))
        if hole:
            ol.NewHole()
            x0, y0, x1, y1 = hole
            # Hole wound opposite the outline (outline is CW in +Y-down? KiCad wants the hole
            # opposite the outline. Outline above is clockwise in screen coords (Y down) which
            # is the usual KiCad positive orientation. Hole goes the other way.
            for x, y in ((x0, y0), (x0, y1), (x1, y1), (x1, y0)):
                ol.Append(mm(x), mm(y))
        board.Add(z)
        return z

    gnd_z = make_zone("GND", pcbnew.In1_Cu, 0)
    p5_hole = (ix0 - 0.6, iy0 - 0.6, ix1 + 0.6, iy1 + 0.6) if xs else None
    p5_z = make_zone("+5V", pcbnew.In2_Cu, 0, hole=p5_hole)
    p3_z = None
    if xs:
        p3_z = pcbnew.ZONE(board)
        p3_z.SetLayer(pcbnew.In2_Cu)
        p3_z.SetNet(board.FindNet("+3V3"))
        p3_z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        p3_z.SetThermalReliefGap(mm(0.25))
        p3_z.SetThermalReliefSpokeWidth(mm(0.35))
        p3_z.SetMinThickness(mm(0.20))
        p3_z.SetLocalClearance(mm(0.20))
        p3_z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
        p3_z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        p3_z.SetAssignedPriority(1)
        p3_z.SetZoneName("+3V3 island")
        ol = p3_z.Outline()
        ol.NewOutline()
        for x, y in ((ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)):
            ol.Append(mm(x), mm(y))
        board.Add(p3_z)
    print(f"+3V3 island {ix0:.1f},{iy0:.1f} .. {ix1:.1f},{iy1:.1f}")

    # ----- route critical nets on F.Cu -----
    routed_nets = []
    skipped_nets = []
    route_names = []
    for name in net_order:
        if name in POWER_NETS or name.startswith("unconnected"):
            continue
        if any(name.startswith(p) or name == p.rstrip("*") for p in ROUTE_PREFIXES) or any(
            name.startswith(p) for p in ROUTE_PREFIXES
        ):
            # filter more carefully
            ok = False
            for p in ROUTE_PREFIXES:
                if p.endswith("_") or p.endswith("*"):
                    if name.startswith(p.rstrip("*")):
                        ok = True
                elif name == p or name.startswith(p):
                    ok = True
            if ok:
                route_names.append(name)
    # de-dup while preserving order
    seen = set()
    route_names = [n for n in route_names if not (n in seen or seen.add(n))]
    print(f"route candidates {len(route_names)}")

    # Raster of foreign pads for a 0.25 mm track.
    GRID = 0.40
    GW = int(W / GRID) + 2
    GH = int(H / GRID) + 2
    blocked = bytearray(GW * GH)
    expand = CLEARANCE + TRACK_W / 2

    def cell(x, y):
        gx = int(round(x / GRID))
        gy = int(round(y / GRID))
        if gx < 0 or gy < 0 or gx >= GW or gy >= GH:
            return None
        return gy * GW + gx

    for ref, fp in fps.items():
        for p in fp.Pads():
            pos = p.GetPosition()
            sz = p.GetSize()
            x, y = tomm(pos.x), tomm(pos.y)
            hx = tomm(sz.x) / 2 + expand
            hy = tomm(sz.y) / 2 + expand
            # rotation of the pad
            ang = p.GetOrientation().AsDegrees()
            # For non-orthogonal pads, use the larger half as a circle.
            if abs(ang) % 90 > 1:
                r = max(hx, hy)
                hx = hy = r
            x0 = int((x - hx) / GRID)
            x1 = int((x + hx) / GRID)
            y0 = int((y - hy) / GRID)
            y1 = int((y + hy) / GRID)
            for gy in range(max(0, y0), min(GH, y1 + 1)):
                row = gy * GW
                for gx in range(max(0, x0), min(GW, x1 + 1)):
                    blocked[row + gx] = 1

    def nearest_free(x, y):
        c = cell(x, y)
        if c is not None and not blocked[c]:
            gx = int(round(x / GRID))
            gy = int(round(y / GRID))
            return gx, gy
        for rad in range(1, 12):
            for dx in range(-rad, rad + 1):
                for dy in (-rad, rad):
                    gx = int(round(x / GRID)) + dx
                    gy = int(round(y / GRID)) + dy
                    if 0 <= gx < GW and 0 <= gy < GH and not blocked[gy * GW + gx]:
                        return gx, gy
            for dy in range(-rad + 1, rad):
                for dx in (-rad, rad):
                    gx = int(round(x / GRID)) + dx
                    gy = int(round(y / GRID)) + dy
                    if 0 <= gx < GW and 0 <= gy < GH and not blocked[gy * GW + gx]:
                        return gx, gy
        return None

    def escape_point(ref, x, y):
        b = bbox_of(fps[ref])
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        dx, dy = x - cx, y - cy
        # Push outward past the pad. Distance from pad to footprint center,
        # then a bit more so we clear the pin ring.
        norm = math.hypot(dx, dy) or 1.0
        # How far is the pad from the bbox edge along this ray?
        ux, uy = dx / norm, dy / norm
        ex, ey = x + ux * 2.2, y + uy * 2.2
        return ex, ey

    def astar(a, b):
        if a == b:
            return [a]
        start, goal = a, b
        opens = [(0, start)]
        came = {start: None}
        gscore = {start: 0}
        while opens:
            _, cur = heapq.heappop(opens)
            if cur == goal:
                path = []
                while cur is not None:
                    path.append(cur)
                    cur = came[cur]
                path.reverse()
                return path
            cx, cy = cur
            base = gscore[cur]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if nx < 1 or ny < 1 or nx >= GW - 1 or ny >= GH - 1:
                    continue
                if blocked[ny * GW + nx] and (nx, ny) != goal:
                    continue
                ng = base + 1
                key = (nx, ny)
                if ng < gscore.get(key, 1 << 30):
                    gscore[key] = ng
                    came[key] = cur
                    h = abs(nx - goal[0]) + abs(ny - goal[1])
                    heapq.heappush(opens, (ng + h, key))
        return None

    def emit_path(points, net, layer=pcbnew.F_Cu):
        # points are (x_mm, y_mm). Merge colinear.
        if len(points) < 2:
            return
        simp = [points[0]]
        for p in points[1:]:
            if len(simp) >= 2:
                ax, ay = simp[-2]
                bx, by = simp[-1]
                cx, cy = p
                if (ax == bx == cx) or (ay == by == cy):
                    simp[-1] = p
                    continue
            if p != simp[-1]:
                simp.append(p)
        for a, b in zip(simp, simp[1:]):
            if a == b:
                continue
            tr = pcbnew.PCB_TRACK(board)
            tr.SetStart(pcbnew.VECTOR2I_MM(*a))
            tr.SetEnd(pcbnew.VECTOR2I_MM(*b))
            tr.SetWidth(mm(TRACK_W))
            tr.SetLayer(layer)
            tr.SetNet(net)
            board.Add(tr)

    def mark_path(cells):
        # Keep later nets off this track, expanded by one cell.
        for gx, gy in cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    x, y = gx + dx, gy + dy
                    if 0 <= x < GW and 0 <= y < GH:
                        blocked[y * GW + x] = 1

    for name in route_names:
        nodes = [(r, pin) for r, pin in nets[name] if r in fps]
        # Unique pad centers.
        pts = []
        for r, pin in nodes:
            pads = pad_index[r].get(pin, [])
            if not pads:
                continue
            pos = pads[0].GetPosition()
            pts.append((r, tomm(pos.x), tomm(pos.y)))
        if len(pts) < 2:
            skipped_nets.append((name, "pins"))
            continue
        # Route as a chain of escapes, longest-star from the first driver-ish pin.
        net = board.FindNet(name)
        ok_all = True
        # Unblock this net's own pads so the escape can leave the pad center.
        own_cells = []
        for r, x, y in pts:
            for p in pad_index[r].get(next(pin for rr, pin in nodes if rr == r), []):
                pass
            c = cell(x, y)
            # clear a small window around own pad center
            gx = int(round(x / GRID))
            gy = int(round(y / GRID))
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    xx, yy = gx + dx, gy + dy
                    if 0 <= xx < GW and 0 <= yy < GH:
                        own_cells.append((yy * GW + xx, blocked[yy * GW + xx]))
                        blocked[yy * GW + xx] = 0
        chain = []
        # Order: driver first if present.
        pts_sorted = sorted(pts, key=lambda t: (0 if t[0] in ("U10", "U4", "X1", "X2", "U3") else 1, t[0]))
        escapes = []
        for r, x, y in pts_sorted:
            ex, ey = escape_point(r, x, y)
            escapes.append((r, x, y, ex, ey))
        # Draw pad -> escape directly (own pad is same net) and A* between escapes.
        drawn = []
        for i in range(len(escapes) - 1):
            r1, x1, y1, e1x, e1y = escapes[i]
            r2, x2, y2, e2x, e2y = escapes[i + 1]
            a = nearest_free(e1x, e1y)
            b = nearest_free(e2x, e2y)
            if not a or not b:
                ok_all = False
                break
            path = astar(a, b)
            if not path:
                ok_all = False
                break
            # Reject a route that wandered more than 2.2x the manhattan span or +80 mm.
            man = (abs(e1x - e2x) + abs(e1y - e2y))
            length = (len(path) - 1) * GRID
            if length > max(man * 2.4, man + 70):
                ok_all = False
                break
            cells = path
            mm_pts = [(x1, y1), (a[0] * GRID, a[1] * GRID)]
            mm_pts += [(gx * GRID, gy * GRID) for gx, gy in path]
            mm_pts += [(x2, y2)]
            drawn.append((mm_pts, cells, length))
        # restore own-pad windows before marking the track (track marker will re-block)
        for idx, old in own_cells:
            blocked[idx] = old
        if not ok_all or not drawn:
            if len(escapes) >= 2:
                r1, x1, y1, e1x, e1y = escapes[0]
                r2, x2, y2, e2x, e2y = escapes[-1]
                man = abs(x1 - x2) + abs(y1 - y2)
                if man <= 14 and len(escapes) == 2:
                    # Direct orthogonal stub. Used for series resistors sitting on the pin.
                    emit_path([(x1, y1), (x2, y1), (x2, y2)], net)
                    routed_nets.append((name, round(man, 1), 2))
                    continue
            skipped_nets.append((name, "no-path"))
            continue
        total = 0
        for mm_pts, cells, length in drawn:
            emit_path(mm_pts, net)
            mark_path(cells)
            total += length
        routed_nets.append((name, round(total, 1), len(pts)))

    print(f"routed {len(routed_nets)} skipped {len(skipped_nets)}")
    for name, length, n in routed_nets:
        if "CLK" in name or name == "/DRAM_CLK":
            print(f"  {name:24} {length:7.1f} mm  pins {n}")
    print("skipped sample", skipped_nets[:25], "count", len(skipped_nets))

    # Fill zones last so tracks are already there (zones avoid tracks via clearance).
    # Save before fill so a filler crash cannot throw away the placement.
    pcbnew.SaveBoard(OUT, board)
    inject_stackup(OUT)
    print("saved pre-fill", OUT)
    print("filling zones...")
    try:
        filler = pcbnew.ZONE_FILLER(board)
        ok = filler.Fill(board.Zones())
        print("fill ret", ok, "filled", gnd_z.IsFilled(), p5_z.IsFilled(), None if p3_z is None else p3_z.IsFilled())
    except Exception as e:
        print("FILL EXC", type(e), e)

    tb = board.GetTitleBlock()
    tb.SetTitle("m68030-sbc Rev A — first layout")
    tb.SetRevision("A")
    tb.SetDate("2026-10-03")
    tb.SetComment(0, "4-layer: F.Cu sig / In1 GND / In2 +5V (+3V3 island) / B.Cu sig")
    tb.SetComment(1, "1 oz, FR-4, 1.6 mm. Clocks+DRAM 0.25 mm ~59 ohm over 0.20 mm prepreg.")
    tb.SetComment(2, "Generated from schematic netlist. Not a finished route.")

    pcbnew.SaveBoard(OUT, board)
    inject_stackup(OUT)
    print("saved", OUT)

    # Summary for the report
    open("/tmp/nl/layout_summary.txt", "w").write(
        "\n".join(
            [
                f"board {W} x {H}",
                f"placed {len(placed)} failed {failed}",
                f"pin_miss {len(pin_miss)}",
                f"power_vias {n_vias} stitch {stitch}",
                f"routed {len(routed_nets)} skipped {len(skipped_nets)}",
                f"3v3 {ix0:.2f} {iy0:.2f} {ix1:.2f} {iy1:.2f}",
                f"heatsink {hs[0]:.2f} {hs[1]:.2f} {hs[2]:.2f} {hs[3]:.2f}",
                "ROUTED",
                *[f"{n}\t{L}\t{pins}" for n, L, pins in routed_nets],
                "SKIP",
                *[f"{n}\t{why}" for n, why in skipped_nets],
                "PINMISS",
                *[f"{a}\t{b}\t{c}" for a, b, c in pin_miss],
                "NO3D_UNIQUE",
            ]
        )
    )
    # unique missing 3d footprints
    uniq = []
    seenf = set()
    for ref, fpname, why in no_3d:
        if fpname in seenf:
            continue
        seenf.add(fpname)
        uniq.append(f"{fpname}\t{why}")
    open("/tmp/nl/missing_3d.txt", "w").write("\n".join(uniq))
    print("unique footprints missing 3d", len(uniq))


def frange(a, b, step):
    x = a
    while x <= b + 1e-6:
        yield x
        x += step


def inject_stackup(path):
    """KiCad 9 python bindings do not round-trip BOARD_STACKUP. Insert it."""
    text = open(path, encoding="utf-8").read()
    if "(stackup" in text:
        return
    stack = """\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "White"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
\t\t\t(layer "In1.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 2" (type "core") (thickness 1.06) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
\t\t\t(layer "In2.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 3" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
"""
    text = text.replace("\t(setup\n", "\t(setup\n" + stack, 1)
    open(path, "w", encoding="utf-8").write(text)


if __name__ == "__main__":
    main()
