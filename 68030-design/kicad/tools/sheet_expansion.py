"""Expansion sheet. J10 is a DIN 41612 type C 3x32 female (96 pins), the connector the
KiCad footprint Connector_DIN:DIN41612_C_3x32_Female_Vertical_THT is drawn for (HARTING).
Buffered A23:0, SIZ, FC, R/W, AS, DS (4x 74ACT244, OE grounded) and D31:0 (4x 74ACT245,
OE = EXP_BUF_EN_n). Response lines are direct, as in spec §1.2. The pin assignment is
new: spec risk 18 said it had not been written."""
from build_common import *
from sheet_cpu import bus_side

SO20 = "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm"
FP = "Connector_DIN:DIN41612_C_3x32_Female_Vertical_THT"
DS244 = "https://www.ti.com/lit/ds/symlink/sn74act244.pdf"
DS245 = "https://www.ti.com/lit/ds/symlink/sn74act245.pdf"

# 74LS244 channel order: (input pin, output pin)
CH244 = [("I0a", "O0a"), ("I1a", "O1a"), ("I2a", "O2a"), ("I3a", "O3a"),
         ("I0b", "O0b"), ("I1b", "O1b"), ("I2b", "O2b"), ("I3b", "O3b")]

def build_expansion(P):
    sh = P.sub("expansion", "Expansion J10: DIN 41612 type C 3x32, F800_0000", 12, paper="A1")
    sh.comments = [
        "Pinout defined on this sheet (spec risk 18 was 'not yet written')",
        "A24-A31 are not on the connector; EXP_SEL_n is the glue decode of F800_0000",
        "DSACK/BERR/HALT/BR/BGACK pull-ups are on the CPU sheet; EXP_INT pull-up is R704 on the glue sheet",
    ]
    # address / control buffers, always enabled.
    # A0-A23 join A[0..31] through bus entries at the 244 inputs. U17 is scalars, not bus members.
    groups = [
        ("U14", ["A%d" % i for i in range(8)]),
        ("U15", ["A%d" % i for i in range(8, 16)]),
        ("U16", ["A%d" % i for i in range(16, 24)]),
        ("U17", ["SIZ0", "SIZ1", "FC0", "FC1", "FC2", "R_W", "AS_n", "DS_n"]),
    ]
    abus = []
    for i, (ref, nets) in enumerate(groups):
        x, y = 70.0 + i * 95.0, 150.0
        u = sh.sym("74xx:74LS244", ref, "SN74ACT244DW", x, y, fp=SO20, ds=DS244,
                   fields={"MPN": "SN74ACT244DW"},
                   ref_at=(x - 18.0, y - 24.0), val_at=(x - 18.0, y + 26.0))
        if ref != "U17":
            bx, y1, y2 = bus_side(sh, u, [(ip, net) for (ip, op), net in zip(CH244, nets)], "L", None, wire_len=7.62)
            sh.label("A[0..31]", bx, min(y1, y2), 90)
            abus.append((bx, min(y1, y2)))
            for (ip, op), net in zip(CH244, nets):
                u.to_label(op, "J10_" + net, length=7.62)
        else:
            for (ip, op), net in zip(CH244, nets):
                u.to_label(ip, net, length=7.62)
                u.to_label(op, "J10_" + net, length=7.62)
        u.to_power("OEa", "GND", length=5.08)
        u.to_power("OEb", "GND", length=5.08)
        u.to_power("VCC", "+5V", length=4.0)
        u.to_power("GND", "GND", length=4.0)
    top = 40.64
    for bx, ytop in abus:
        sh.bus((bx, top), (bx, ytop))
    sh.bus((25.4, top), (abus[-1][0], top))
    sh.hlabel("A[0..31]", "input", 25.4, top, 180)
    sh.label("A[0..31]", 33.02, top, 0)
    hx = 40.64
    for nm in ("SIZ0", "SIZ1", "FC0", "FC1", "FC2", "R_W", "AS_n", "DS_n"):
        sh.hlabel(nm, "input", hx, 27.94, 180)
        sh.label(nm, hx + 12.7, 27.94, 0)
        sh.wire((hx, 27.94), (hx + 12.7, 27.94))
        hx += 25.4
    sh.text("A24-A31 are not buffered to J10. The card is selected by EXP_SEL_n (glue decode of F800_0000-FFFF_FFFF).", 250.0, 22.0, 1.0)
    # data transceivers. A = card, B = CPU, DIR = R/W so a read (R/W high) drives the card onto the CPU bus.
    dbus = []
    for i in range(4):
        x, y = 70.0 + i * 95.0, 280.0
        u = sh.sym("74xx:74LS245", "U%d" % (18 + i), "SN74ACT245DW", x, y, fp=SO20, ds=DS245,
                   fields={"MPN": "SN74ACT245DW"},
                   ref_at=(x - 18.0, y - 24.0), val_at=(x - 18.0, y + 26.0))
        pairs = []
        for b in range(8):
            bit = i * 8 + b
            u.to_label("A%d" % b, "J10_D%d" % bit, length=7.62)
            pairs.append(("B%d" % b, "D%d" % bit))
        bx, y1, y2 = bus_side(sh, u, pairs, "R", None, wire_len=7.62)
        sh.label("D[0..31]", bx, min(y1, y2), 90)
        dbus.append((bx, min(y1, y2)))
        u.to_label("A->B", "R_W", length=7.62)
        u.to_label("CE", "EXP_BUF_EN_n", length=10.16, hier="input")
        u.to_power("VCC", "+5V", length=5.08)
        u.to_power("GND", "GND", length=5.08)
    yb = 248.92
    for bx, ytop in dbus:
        sh.bus((bx, yb), (bx, ytop))
    sh.bus((dbus[0][0], yb), (dbus[-1][0] + 15.24, yb))
    sh.hlabel("D[0..31]", "bidirectional", dbus[-1][0] + 15.24, yb, 0)
    # connector, three units
    fields = {"MPN": "HARTING 09032966821",
              "Note": "DIN 41612 type C female, 96 pin, vertical. [VERIFY] the variant against the KiCad footprint (HARTING livebook, the footprint's source)"}
    units = []
    for ui, y in enumerate((80.0, 200.0, 340.0)):
        units.append(sh.sym("m68030-sbc:DIN41612-C96", "J10", "DIN41612-C-96", 620.0, y, unit=ui + 1, fp=FP,
                            ds="https://b2b.harting.com/files/livebooks/en/PRD0200000100063/downloads/livebook.pdf",
                            fields=fields, ref_at=(640.0, y - 45.0), val_at=(640.0, y + 48.0)))
    ja, jb, jc = units
    for i in range(24):
        ja.to_label("a%d" % (i + 1), "J10_A%d" % i, length=8.0)
    for i, net in enumerate(["SIZ0", "SIZ1", "FC0", "FC1", "FC2", "R_W", "AS_n", "DS_n"]):
        ja.to_label("a%d" % (25 + i), "J10_" + net, length=8.0)
    for i in range(32):
        jb.to_label("b%d" % (i + 1), "J10_D%d" % i, length=8.0)
    # row c: direct CPU/glue signals, then power
    direct = [
        ("c1", "CLK_EXP", "input"), ("c2", "EXP_SEL_n", "input"), ("c3", "PERIPH_RST_n", "input"),
        ("c4", "BG_n", "input"),
        ("c5", "BR_n", "output"), ("c6", "BGACK_n", "output"),
        ("c7", "DSACK0_n", "bidirectional"), ("c8", "DSACK1_n", "bidirectional"),
        ("c9", "BERR_n", "bidirectional"), ("c10", "HALT_n", "bidirectional"),
        ("c11", "EXP_INT_n", "output"),
    ]
    for pn, net, shape in direct:
        jc.to_label(pn, net, length=12.0, hier=shape)
    for i, pn in enumerate(["c%d" % n for n in range(12, 21)]):
        jc.to_power(pn, "GND", length=5.08)
    for pn in ["c%d" % n for n in range(21, 25)]:
        jc.to_power(pn, "+5V", length=5.08)
    for pn in ["c%d" % n for n in range(25, 33)]:
        jc.to_nc(pn)
    cap_row(sh, [("C%d" % (1401 + i), "100n", C0805) for i in range(8)] + [("C1409", "10u", C1206)],
            40.0, 400.0, 15.0)
    sh.text("Decoupling: 100 nF at each of U14-U21, plus 10 uF for the group", 30.0, 385.0, 1.0)
    sh.text("J10 pinout (this sheet is the definition; spec §10 risk 18 had none)", 560.0, 20.0, 1.5, bold=True)
    sh.text("Row a: a1-a24 = A0-A23, a25 SIZ0, a26 SIZ1, a27-a29 FC0-FC2, a30 R/W, a31 AS-, a32 DS-\\n"
            "  (all through U14-U17, 74ACT244, OE tied low so the card always sees the bus).\\n"
            "Row b: b1-b32 = D0-D31 through U18-U21, 74ACT245. OE = EXP_BUF_EN_n (glue, active low).\\n"
            "  DIR = R/W with the card on the A side, so a CPU read drives the card onto D.\\n"
            "Row c: c1 CLK_EXP, c2 EXP_SEL_n, c3 PERIPH_RST_n, c4 BG-, c5 BR-, c6 BGACK-,\\n"
            "  c7 DSACK0-, c8 DSACK1-, c9 BERR-, c10 HALT-, c11 EXP_INT- (open drain; pull-up is glue R704),\\n"
            "  c12-c20 GND, c21-c24 +5V (the 1 A expansion allowance, spec §6 [EST]), c25-c32 reserved.\\n"
            "A card that does not answer gets BERR from the glue timeout (spec §3.3). DSACK is the card's,\\n"
            "any width. No CPLD pin moves: EXP_SEL_n and EXP_BUF_EN_n stay on the fitted glue pins.",
            700.0, 30.0, 1.05)
    return sh
