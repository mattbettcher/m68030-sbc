from build_common import *

def bus_side(sh, part, pins, side, net_fmt, bus_x_off=12.7, wire_len=10.16):
    """connect a column of pins to a vertical bus via labels + bus entries. side 'L' or 'R'. returns (bus_x, ymin, ymax)"""
    ys = []
    for num_or_name, net in pins:
        x, y = part.pin(num_or_name)
        d = -1 if side == "L" else 1
        ex = x + d * wire_len
        sh.wire((x, y), (ex, y))
        sh.label(net, ex, y, 0 if side == "L" else 180)
        sh.bus_entry(ex, y, d * 2.54, -2.54)
        ys.append(y - 2.54)
        bx = ex + d * 2.54
    sh.bus((bx, min(ys)), (bx, max(ys)))
    return bx, min(ys), max(ys)

def build_cpu(P):
    sh = P.sub("cpu", "CPU: MC68030 PGA-128", 5)
    sh.comments = ['Pins verified vs MC68030UM sect. 14.2 (PGA) and Mackerel-68k symbol (128/128)', 'Pull-ups per spec 8.1; RESET_n/HALT_n 1k pull-ups are on the reset sheet', 'Decoupling per MC68030UM sect. 12 (10 uF + 0.1 uF + 330 pF)']
    fpC = "m68030-sbc:PGA128_13x13_MC68030"
    ds = "https://www.nxp.com/docs/en/reference-manual/MC68030UM.pdf"
    mpn = {"MPN": "MC68030RC33C", "Socket": "PGA-128 13x13 socket (XU1)"}
    # ---------------- unit A: buses
    ua = sh.sym("m68030-sbc:MC68030", "U1", "MC68030RC33C", 88.9, 121.92, unit=1, fp=fpC, ds=ds, fields=mpn,
                ref_at=(76.2, 78.74), val_at=(76.2, 167.64))
    bx, y1, y2 = bus_side(sh, ua, [("A%d" % i, "A%d" % i) for i in range(32)], "L", None)
    sh.bus((bx, y1), (bx, 71.12), (38.1, 71.12))
    sh.hlabel("A[0..31]", "output", 38.1, 71.12, 180)
    bx, y1, y2 = bus_side(sh, ua, [("D%d" % i, "D%d" % i) for i in range(32)], "R", None)
    sh.bus((bx, y1), (bx, 71.12), (137.16, 71.12))
    sh.hlabel("D[0..31]", "bidirectional", 137.16, 71.12, 0)
    sh.text("Address bus A0-A31 (outputs)", 30.48, 60.96, 1.5, bold=True)
    sh.text("Data bus D0-D31 (bidirectional)", 106.68, 60.96, 1.5, bold=True)
    # ---------------- unit B: control
    ub = sh.sym("m68030-sbc:MC68030", "U1", "MC68030RC33C", 213.36, 121.92, unit=2, fp=fpC, ds=ds, fields=mpn,
                ref_at=(200.66, 91.44), val_at=(200.66, 154.94))
    inputs = [("CLK", "CLK_CPU"), ("~{DSACK0}", "DSACK0_n"), ("~{DSACK1}", "DSACK1_n"), ("~{STERM}", "STERM_n"),
              ("~{AVEC}", "AVEC_n"), ("~{CIIN}", "CIIN_n"), ("~{CBACK}", "CBACK_n"), ("~{BERR}", "BERR_n"),
              ("~{HALT}", "HALT_n"), ("~{IPL0}", "IPL0_n"), ("~{IPL1}", "IPL1_n"), ("~{IPL2}", "IPL2_n"),
              ("~{BR}", "BR_n"), ("~{BGACK}", "BGACK_n")]
    for pn, net in inputs:
        ub.to_label(pn, net, length=22.86, hier="input")
    ub.to_label("~{RESET}", "RESET_n", length=22.86, hier="bidirectional")
    ub.to_label("~{CDIS}", "CDIS_n", length=7.62)
    ub.to_label("~{MMUDIS}", "MMUDIS_n", length=7.62)
    outs = [("FC0", "FC0"), ("FC1", "FC1"), ("FC2", "FC2"), ("SIZ0", "SIZ0"), ("SIZ1", "SIZ1"), ("R/~{W}", "R_W"),
            ("~{AS}", "AS_n"), ("~{DS}", "DS_n"), ("~{ECS}", "ECS_n"), ("~{OCS}", "OCS_n"), ("~{RMC}", "RMC_n"),
            ("~{CBREQ}", "CBREQ_n"), ("~{IPEND}", "IPEND_n"), ("~{STATUS}", "STATUS_n"), ("~{REFILL}", "REFILL_n"),
            ("~{BG}", "BG_n")]
    for pn, net in outs:
        ub.to_label(pn, net, length=22.86, hier="output")
    ub.to_label("~{DBEN}", "DBEN_n", length=7.62)
    ub.to_label("~{CIOUT}", "CIOUT_n", length=7.62)
    sh.text("Control / status", 198.12, 83.82, 1.5, bold=True)
    # ---------------- test points for CIOUT_n / DBEN_n / BG_n
    tpy = 172.72
    for i, (ref, net) in enumerate([("TP501", "CIOUT_n"), ("TP502", "DBEN_n"), ("TP503", "BG_n")]):
        x = 203.2 + i * 17.78
        tp = sh.sym("Connector:TestPoint", ref, net.replace("_n", "#"), x, tpy, 0, fp=TP, ref_at=(x + 2.54, tpy - 5.08), val_at=(x + 2.54, tpy - 2.54))
        px, py = tp.pin(1)
        sh.wire((px, py), (px, py + 5.08))
        sh.label(net, px, py + 5.08, 270)
    sh.text("Test points (spec 8.1: CIOUT_n and DBEN_n are test-point only)", 190.5, 160.02, 1.27)
    # ---------------- pull-up bank
    sh.text("Pull-ups (spec.md 8.1)", 289.56, 35.56, 1.5, bold=True)
    pu = [("R501", "1k", "DSACK0_n"), ("R502", "1k", "DSACK1_n"), ("R503", "1k", "STERM_n"), ("R504", "1k", "CBACK_n"),
          ("R505", "1k", "CIIN_n"), ("R506", "1k", "AVEC_n"), ("R507", "1k", "BERR_n"), ("R508", "1k", "BR_n"),
          ("R509", "1k", "BGACK_n"), ("R510", "10k", "IPL0_n"), ("R511", "10k", "IPL1_n"), ("R512", "10k", "IPL2_n"),
          ("R513", "10k", "CDIS_n"), ("R514", "10k", "MMUDIS_n")]
    pullup_bank(sh, pu, 304.8, 50.8)
    sh.text("1k: DSACKx (also the 68882 holding resistors), STERM, CBACK,\\nCIIN, AVEC, BERR, BR, BGACK.  10k: IPL2..0 (blank CPLD =\\nno interrupt), CDIS, MMUDIS.  RESET_n/HALT_n: reset sheet.", 289.56, 124.46, 1.27)
    # ---------------- jumpers
    for i, (ref, net, lbl) in enumerate([("JP1", "CDIS_n", "CDIS (cache disable)"), ("JP2", "MMUDIS_n", "MMUDIS (MMU disable)")]):
        y = 147.32 + i * 15.24
        j = sh.sym("Connector_Generic:Conn_01x02", ref, lbl, 320.04, y, 0, fp=HDR2, ref_at=(322.58, y - 1.27), val_at=(322.58, y + 3.81),
                   fields={"Note": "fit jumper = pull to GND"})
        p1 = j.pin(1); p2 = j.pin(2)
        sh.wire(p1, (p1[0] - 10.16, p1[1])); sh.label(net, p1[0] - 10.16, p1[1], 180)
        sh.wire(p2, (p2[0] - 5.08, p2[1])); sh.power("GND", p2[0] - 5.08, p2[1] + 0, 0) if False else None
        g = (p2[0] - 5.08, p2[1])
        sh.wire(g, (g[0], g[1] + 2.54)); sh.power("GND", g[0], g[1] + 2.54, 0)
    sh.text("JP1/JP2 open = normal operation (Linux needs the MMU)", 289.56, 175.26, 1.27)
    # ---------------- unit C: power + decoupling
    uc = sh.sym("m68030-sbc:MC68030", "U1", "MC68030RC33C", 76.2, 228.6, unit=3, fp=fpC, ds=ds, fields=mpn,
                ref_at=(104.14, 226.06), val_at=(104.14, 231.14))
    vcc = [n for n, p in uc.allpins() if p["name"] == "VCC"]
    gnd = [n for n, p in uc.allpins() if p["name"] == "GND"]
    ncs = [n for n, p in uc.allpins() if p["name"] == "NC"]
    pts = sorted(uc.pin(n) for n in vcc)
    ry = pts[0][1] - 2.54
    for p in pts: sh.wire(p, (p[0], ry))
    sh.wire((pts[0][0] - 5.08, ry), (pts[-1][0], ry))
    sh.power("+5V", pts[0][0] - 5.08, ry, 0)
    gp = sorted(uc.pin(n) for n in gnd)
    gy = gp[0][1] + 2.54
    for p in gp: sh.wire(p, (p[0], gy))
    sh.wire((gp[0][0], gy), (gp[-1][0], gy))
    sh.power("GND", gp[0][0], gy, 0)
    for n in ncs: uc.to_nc(n)
    sh.text("NC pins D5, E12, F4, F10, K5: do not connect (UM Fig. 14-1)", 76.2, 246.38, 1.27)
    specs = [("C%d" % (501 + i), "100n", C0805) for i in range(10)] + \
            [("C%d" % (511 + i), "330p", C0603, "C", {"fields": {"Dielectric": "C0G"}}) for i in range(4)] + \
            [("C515", "10u", C1206), ("C516", "10u", C1206), ("C517", "220u", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", "CP")]
    parts, ry2 = cap_row(sh, specs, 137.16, 228.6, 10.16)
    sh.text("CPU decoupling: 10x 100 nF (one per VCC pin, under the socket), 4x 330 pF C0G, 2x 10 uF X7R, 1x 220 uF low-ESR within 20 mm", 132.08, 213.36, 1.27)
    sh.text("HEATSINK: MC68030 dissipates up to 2.6 W (EC); theta-JA ~30 C/W (PGA, EC estimate) -> up to +78 C rise.\\nFit a stick-on PGA heatsink (HS1), mandatory for 33 MHz operation.", 132.08, 254.0, 1.5, bold=True)
    return sh
