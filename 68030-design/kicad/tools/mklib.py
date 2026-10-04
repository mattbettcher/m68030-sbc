"""Builds the project-local symbol library lib/m68030-sbc.kicad_sym.
MC68030 pin numbers: MC68030UM §14.2 (PGA, RC suffix) — transcribed in um_pga.py and cross-checked 128/128
against the Mackerel-68k (MIT) MC68030 symbol.  MC68882 PLCC-68: Freescale BR509 Rev.3 p.23 (FN suffix) —
cross-checked 68/68 against the Mackerel-68k MC68882 symbol.  LM2678 TO-263-7: TI SNVS029L Table 4-1."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sexp import dump, Sym
from um_pga import PGA

def ov(n):  # overbar name
    return "~{%s}" % n

def pin(num, name, typ, x, y, ang, length=2.54, hide=False):
    p = [Sym("pin"), Sym(typ), Sym("line"), [Sym("at"), x, y, ang], [Sym("length"), length]]
    if hide:
        p.append([Sym("hide"), Sym("yes")])
    p += [[Sym("name"), name, [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]],
          [Sym("number"), num, [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]]]
    return p

def prop(k, v, x=0, y=0, hide=False, just=None):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]
    if just: e.append([Sym("justify"), Sym(just)])
    if hide: e.append([Sym("hide"), Sym("yes")])
    return [Sym("property"), k, v, [Sym("at"), x, y, 0], e]

def rect(x1, y1, x2, y2):
    return [Sym("rectangle"), [Sym("start"), x1, y1], [Sym("end"), x2, y2],
            [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]], [Sym("fill"), [Sym("type"), Sym("background")]]]

def boxunit(name, unit, left, right, top=(), bottom=(), width=30.48, gap=0):
    """left/right: list of (num,name,type) or None (spacer). returns (sub-symbol, height)"""
    n = max(len(left), len(right))
    h = (n + 1) * 2.54
    h = max(h, 10.16)
    y0 = h / 2
    y0 = round(round(y0 / 2.54) * 2.54, 2)
    items = []
    w2 = width / 2
    for i, p in enumerate(left):
        if p: items.append(pin(p[0], p[1], p[2], -w2 - 2.54, y0 - 2.54 * (i + 1), 0, hide=p[3] if len(p) > 3 else False))
    for i, p in enumerate(right):
        if p: items.append(pin(p[0], p[1], p[2], w2 + 2.54, y0 - 2.54 * (i + 1), 180, hide=p[3] if len(p) > 3 else False))
    ybot = y0 - max(h, 2.54 * (n + 1))
    ybot = round(round(ybot / 2.54) * 2.54, 2)
    for i, p in enumerate(top):
        x = -2.54 * (len(top) - 1) / 2 + 2.54 * i
        x = round(round(x / 1.27) * 1.27, 2)
        items.append(pin(p[0], p[1], p[2], x, y0 + 2.54, 270, hide=p[3] if len(p) > 3 else False))
    for i, p in enumerate(bottom):
        x = -2.54 * (len(bottom) - 1) / 2 + 2.54 * i
        x = round(round(x / 1.27) * 1.27, 2)
        items.append(pin(p[0], p[1], p[2], x, ybot - 2.54, 90, hide=p[3] if len(p) > 3 else False))
    body = rect(-w2, y0, w2, ybot)
    return [Sym("symbol"), "%s_%d_1" % (name, unit), body] + items, (y0, ybot, w2)

def symbol(name, ref, value, fp, ds, desc, units, kw="", unit_names=None):
    s = [Sym("symbol"), name, [Sym("pin_names"), [Sym("offset"), 1.016]], [Sym("exclude_from_sim"), Sym("no")],
         [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")]]
    y0 = units[0][1][0]
    s += [prop("Reference", ref, -units[0][1][2], y0 + 1.27, just="left"), prop("Value", value, -units[0][1][2], units[0][1][1] - 1.27, just="left"),
          prop("Footprint", fp, 0, 0, True), prop("Datasheet", ds, 0, 0, True), prop("Description", desc, 0, 0, True),
          prop("ki_keywords", kw, 0, 0, True)]
    for u in units:
        s.append(u[0])
    return s

# ---------------------------------------------------------------- MC68030
def mc68030():
    inv = {}
    for k, v in PGA.items():
        inv.setdefault(v, []).append(k)
    one = lambda n: inv[n][0]
    A = [(one("A%d" % i), "A%d" % i, "output") for i in range(32)]
    D = [(one("D%d" % i), "D%d" % i, "bidirectional") for i in range(32)]
    u1, g1 = boxunit("MC68030", 1, A, D, width=25.4)
    L = [("E1", "CLK", "input"), None,
         ("F1", ov("DSACK0"), "input"), ("G2", ov("DSACK1"), "input"), ("G1", ov("STERM"), "input"),
         ("E2", ov("AVEC"), "input"), ("L1", ov("CIIN"), "input"), ("J1", ov("CBACK"), "input"),
         ("H1", ov("BERR"), "input"), ("H2", ov("HALT"), "input"), ("F12", ov("RESET"), "open_collector"), None,
         ("H13", ov("IPL0"), "input"), ("G13", ov("IPL1"), "input"), ("G12", ov("IPL2"), "input"), None,
         ("A1", ov("BR"), "input"), ("C3", ov("BGACK"), "input"), None,
         ("H12", ov("CDIS"), "input"), ("F13", ov("MMUDIS"), "input")]
    R = [("D2", "FC0", "output"), ("C1", "FC1", "output"), ("D1", "FC2", "output"), None,
         ("L2", "SIZ0", "output"), ("K3", "SIZ1", "output"), ("L3", "R/~{W}", "output"), None,
         ("J2", ov("AS"), "output"), ("K2", ov("DS"), "output"), ("M1", ov("DBEN"), "output"),
         ("M2", ov("ECS"), "output"), ("D3", ov("OCS"), "output"), ("B1", ov("RMC"), "output"), None,
         ("K1", ov("CBREQ"), "output"), ("C2", ov("CIOUT"), "output"), None,
         ("E13", ov("IPEND"), "output"), ("J12", ov("STATUS"), "output"), ("J13", ov("REFILL"), "output"), None,
         ("B2", ov("BG"), "output")]
    u2, g2 = boxunit("MC68030", 2, L, R, width=25.4)
    vcc = [(k, "VCC", "power_in") for k in ["C6", "D10", "L6", "K10", "K4", "D4", "H3", "F2", "F11", "H11"]]
    gnd = [(k, "GND", "power_in") for k in ["C5", "C7", "C9", "E11", "J11", "L9", "L7", "L5", "J3", "E3", "L8", "G3", "F3", "G11"]]
    nc = [(k, "NC", "no_connect") for k in ["D5", "E12", "F4", "F10", "K5"]]
    u3, g3 = boxunit("MC68030", 3, [], [], top=vcc, bottom=gnd + nc, width=50.8)
    # sanity: every PGA pin used exactly once
    used = []
    for u in (A, D, [p for p in L if p], [p for p in R if p], vcc, gnd, nc):
        used += [p[0] for p in u]
    assert sorted(used) == sorted(PGA), (len(used), set(PGA) - set(used))
    for u in (A, D, [p for p in L if p], [p for p in R if p]):
        for num, nm, _ in u:
            base = nm.replace("~{", "").replace("}", "").replace("R/W", "R/W")
            assert PGA[num].replace("/", "") == base.replace("/", ""), (num, nm, PGA[num])
    return symbol("MC68030", "U", "MC68030RC", "m68030-sbc:PGA128_13x13_MC68030",
                  "https://www.nxp.com/docs/en/reference-manual/MC68030UM.pdf",
                  "MC68030 32-bit CPU with PMMU, PGA-128 (RC suffix). Pinout per MC68030UM sect. 14.2", [(u1, g1), (u2, g2), (u3, g3)],
                  "68030 CPU MMU PGA")

# ---------------------------------------------------------------- MC68882 (PLCC-68, BR509 p.23)
PLCC68 = {1: "D2", 2: "D1", 3: "D0", 4: "SENSE", 5: "GND", 6: "GND", 7: "GND", 8: "GND", 9: "GND", 10: "VCC",
          11: "CLK", 12: "GND", 13: "RESET", 14: "GND", 15: "NC", 16: "VCC", 17: "VCC", 18: "SIZE", 19: "GND",
          20: "DS", 21: "AS", 22: "A4", 23: "A3", 24: "A2", 25: "A1", 26: "A0", 27: "VCC", 28: "R/W", 29: "CS",
          30: "GND", 31: "DSACK0", 32: "DSACK1", 41: "GND", 42: "D23", 43: "VCC", 51: "GND", 52: "VCC", 53: "VCC",
          61: "VCC", 62: "D8", 63: "GND"}
for i, n in enumerate(range(33, 41)): PLCC68[n] = "D%d" % (31 - i)
for i, n in enumerate(range(44, 51)): PLCC68[n] = "D%d" % (22 - i)
for i, n in enumerate(range(54, 61)): PLCC68[n] = "D%d" % (15 - i)
for i, n in enumerate(range(64, 69)): PLCC68[n] = "D%d" % (7 - i)
assert len(PLCC68) == 68

def mc68882():
    inv = {}
    for k, v in PLCC68.items(): inv.setdefault(v, []).append(str(k))
    one = lambda n: inv[n][0]
    L = [(one("A0"), "A0", "input"), (one("A1"), "A1", "input"), (one("A2"), "A2", "input"), (one("A3"), "A3", "input"),
         (one("A4"), "A4", "input"), None, (one("SIZE"), ov("SIZE"), "input"), (one("CS"), ov("CS"), "input"),
         (one("AS"), ov("AS"), "input"), (one("DS"), ov("DS"), "input"), (one("R/W"), "R/~{W}", "input"), None,
         (one("DSACK0"), ov("DSACK0"), "tri_state"), (one("DSACK1"), ov("DSACK1"), "tri_state"), None,
         (one("CLK"), "CLK", "input"), (one("RESET"), ov("RESET"), "input"), None,
         (one("SENSE"), ov("SENSE"), "passive"), None, None, None, None, None, None, None, None, None, None, None, None,
         ("15", "NC", "no_connect")]
    R = [(one("D%d" % i), "D%d" % i, "bidirectional") for i in range(32)]
    vcc = [(k, "VCC", "power_in") for k in inv["VCC"]]
    gnd = [(k, "GND", "power_in") for k in inv["GND"]]
    u1, g1 = boxunit("MC68882", 1, L, R, top=vcc, bottom=gnd, width=30.48)
    used = [p[0] for p in L if p] + [p[0] for p in R] + [p[0] for p in vcc] + [p[0] for p in gnd]
    assert sorted(used, key=int) == [str(i) for i in range(1, 69)], sorted(used, key=int)
    return symbol("MC68882", "U", "MC68882FN33A", "Package_LCC:PLCC-68_THT-Socket",
                  "https://www.nxp.com/docs/en/data-sheet/BR509.pdf",
                  "MC68882 floating-point coprocessor, PLCC-68 (FN suffix). Pinout per Freescale BR509 Rev.3 p.23", [(u1, g1)], "68882 FPU FPCP")

# ---------------------------------------------------------------- LM2678 TO-263-7
def lm2678():
    L = [("2", "VIN", "power_in"), None, ("7", "ON/~{OFF}", "input"), None]
    R = [("3", "CB", "passive"), ("1", "VSW", "power_out"), None, ("6", "FB", "input")]
    u1, g1 = boxunit("LM2678S-5.0", 1, L, R, bottom=[("4", "GND", "power_in")], width=15.24)
    u1.append(pin("5", "NC", "no_connect", 0, g1[0] + 2.54, 270, hide=True))
    return symbol("LM2678S-5.0", "U", "LM2678S-5.0", "Package_TO_SOT_SMD:TO-263-7_TabPin4",
                  "https://www.ti.com/lit/ds/symlink/lm2678.pdf",
                  "5 A SIMPLE SWITCHER step-down regulator, fixed 5.0 V, TO-263-7 (KTW). Pinout TI SNVS029L Table 4-1", [(u1, g1)], "buck regulator")

def tps3702():
    """Stock KiCad Power_Supervisor:TPS3702 with UV/OV pin type changed to open_collector
    (TI SBVS251A: UV and OV are open-drain, active-low outputs), renamed TPS3702CX50."""
    import copy
    from sexp import parse, find, findall
    e = parse(open("/usr/share/kicad/symbols/Power_Supervisor.kicad_sym").read())
    s = copy.deepcopy([x for x in e if isinstance(x, list) and x and x[0] == "symbol" and x[1] == "TPS3702"][0])
    s[1] = "TPS3702CX50"
    for sub in findall(s, "symbol"):
        sub[1] = sub[1].replace("TPS3702", "TPS3702CX50")
        for p in findall(sub, "pin"):
            if find(p, "name")[1] in ("UV", "OV"):
                p[1] = Sym("open_collector")
    for p in findall(s, "property"):
        if p[1] == "Value": p[2] = "TPS3702CX50"
        if p[1] == "Description": p[2] = "TPS3702 window supervisor, CX50 variant (UV 4.80 V / OV 5.20 V with SET high), open-drain UV/OV; derived from KiCad stock symbol"
    return s

# ---------------------------------------------------------------- ATF1508AS PLCC-84
# Pin functions per Atmel/Microchip ATF1508AS(L) datasheet doc0784 Rev. 0784P-7/05, "84-lead PLCC Top View"
# (re-checked 2026-09-26 against the rendered pinout figure), and identical to fit1508 v1918's PLCC84 pin
# diagram in cpld/glue/glue.fit. All other pins are I/O.
ATF_PLCC84_SPECIAL = {1: "INPUT/GCLR", 2: "INPUT/OE2/GCLK2", 83: "INPUT/GCLK1", 84: "INPUT/OE1",
    12: "I/O/PD1", 45: "I/O/PD2", 81: "I/O/GCLK3", 14: "I/O/TDI", 23: "I/O/TMS", 62: "I/O/TCK", 71: "I/O/TDO",
    3: "VCCINT", 43: "VCCINT", 13: "VCCIO", 26: "VCCIO", 38: "VCCIO", 53: "VCCIO", 66: "VCCIO", 78: "VCCIO",
    7: "GND", 19: "GND", 32: "GND", 42: "GND", 47: "GND", 59: "GND", 72: "GND", 82: "GND"}

def atf1508as_plcc84():
    """Pin order on the sides follows the U3 (glue) assignment so the sheet wires straight; pins are the device's."""
    def P(n):
        nm = ATF_PLCC84_SPECIAL.get(n, "I/O")
        if n in (1, 2, 83, 84): t = "input"
        elif n in (14, 23, 62): t = "input"
        elif n == 71: t = "tri_state"
        else: t = "bidirectional"
        return (str(n), nm, t)
    Lnums = [None, None, None, 83, 1, 84, 2, None, 4, 5, 6, 8, None, 12, 15, 16, 17, 18, 20, 21, 22, 24, 25, 27, 28, 29, 30, 31, None,
             44, 33, 34, 35, 73, 74, 36, 41, None, 49, None, 14, 23, 62, 71, None, None, None]
    Rnums = [None, None, None, 9, 10, 11, 75, 76, 54, 81, None, 77, 79, 80, None, 55, 56, 57, 58, 60, 61, None, 63, 64, 65, 67, 68, 69, 70,
             None, 37, 39, 40, 45, None, 46, 48, None, 50, 51, 52, None, None, None, None, None, None]
    L = [P(n) if n else None for n in Lnums]
    R = [P(n) if n else None for n in Rnums]
    vcc = [(str(n), ATF_PLCC84_SPECIAL[n], "power_in") for n in (3, 13, 26, 38, 43, 53, 66, 78)]
    gnd = [(str(n), "GND", "power_in") for n in (7, 19, 32, 42, 47, 59, 72, 82)]
    u1, g1 = boxunit("ATF1508AS-PLCC84", 1, L, R, top=vcc, bottom=gnd, width=33.02)
    used = [int(p[0]) for p in L + R + vcc + gnd if p]
    assert sorted(used) == list(range(1, 85)), sorted(set(range(1, 85)) - set(used))
    return symbol("ATF1508AS-PLCC84", "U", "ATF1508AS-7JX84", "Package_LCC:PLCC-84_THT-Socket",
                  "https://ww1.microchip.com/downloads/en/DeviceDoc/doc0784.pdf",
                  "ATF1508AS 128-macrocell 5 V CPLD, PLCC-84 (JX84). Pinout per doc0784 Rev. 0784P; JTAG ISP enabled (pins 14/23/62/71 reserved)",
                  [(u1, g1)], "CPLD ATF1508 PLD JTAG")

# ---------------------------------------------------------------- 72-pin SIMM socket (x32, no parity)
# Pinout: Micron MT8D432/MT16D832 (4/8 Meg x 32 EDO SIMM) datasheet, "PIN ASSIGNMENT (Front View)" table
# (datasheets/micron_simm.txt lines 245-263): 45 = RAS1#, 33 = RAS3# on 2-sided modules; 29 = A11 on larger
# modules; 35-38 are NC on x32 modules (parity on x36 modules). Cross-checked pin by pin against Mackerel-30's SIMM72 symbol.
SIMM72 = {1: "VSS", 39: "VSS", 72: "VSS", 10: "VDD", 30: "VDD", 59: "VDD",
          12: "A0", 13: "A1", 14: "A2", 15: "A3", 16: "A4", 17: "A5", 18: "A6", 28: "A7", 31: "A8", 32: "A9", 19: "A10", 29: "A11",
          44: "RAS0", 45: "RAS1", 34: "RAS2", 33: "RAS3", 40: "CAS0", 43: "CAS1", 41: "CAS2", 42: "CAS3", 47: "WE",
          67: "PRD1", 68: "PRD2", 69: "PRD3", 70: "PRD4"}
for i, n in enumerate([2, 4, 6, 8, 20, 22, 24, 26, 49, 51, 53, 55, 57, 61, 63, 65, 3, 5, 7, 9, 21, 23, 25, 27,
                       50, 52, 54, 56, 58, 60, 62, 64]):
    SIMM72[n] = "DQ%d" % (i + 1)
for n in (11, 35, 36, 37, 38, 46, 48, 66, 71):
    SIMM72[n] = "NC"
assert sorted(SIMM72) == list(range(1, 73))

def simm72():
    inv = {v: k for k, v in SIMM72.items() if v not in ("VSS", "VDD", "NC")}
    def P(nm, t, disp=None): return (str(inv[nm]), disp or nm, t)
    L = [P("A%d" % i, "input") for i in range(12)] + [None] + \
        [P("RAS%d" % i, "input", ov("RAS%d" % i)) for i in range(4)] + [P("CAS%d" % i, "input", ov("CAS%d" % i)) for i in range(4)] + \
        [P("WE", "input", ov("WE"))] + [None] + [P("PRD%d" % i, "passive") for i in range(1, 5)] + [None] + \
        [(str(n), "NC", "no_connect") for n in (11, 35, 36, 37, 38, 46, 48, 66, 71)]
    R = [P("DQ%d" % i, "bidirectional") for i in range(1, 33)]
    top = [(str(n), "VDD", "power_in") for n in (10, 30, 59)]
    bot = [(str(n), "VSS", "power_in") for n in (1, 39, 72)]
    u1, g1 = boxunit("SIMM72", 1, L, R, top=top, bottom=bot, width=25.4)
    used = sorted(int(p[0]) for p in L + R + top + bot if p)
    assert used == list(range(1, 73)), set(range(1, 73)) - set(used)
    return symbol("SIMM72", "J", "SIMM-72", "m68030-sbc:SIMM-72_TE-5822021-4",
                  "https://www.te.com/usa-en/product-5822021-4.html",
                  "72-pin SIMM socket, x32 (FPM/EDO, 5 V). Pinout per Micron MT8D432/MT16D832 datasheet; DQ1 = D0 on this board",
                  [(u1, g1)], "SIMM DRAM socket 72")

# SST39SF040 32-lead PLCC, DS20005022C Figure 2 (040 column). NOT the DIP numbering
# (the KiCad Memory_Flash:SST39SF040 symbol is the PDIP pinout, Figure 4).
SST_PLCC32 = {
 1:"A18", 2:"A16", 3:"A15", 4:"A12", 5:"A7", 6:"A6", 7:"A5", 8:"A4", 9:"A3", 10:"A2", 11:"A1", 12:"A0",
 13:"DQ0", 14:"DQ1", 15:"DQ2", 16:"VSS", 17:"DQ3", 18:"DQ4", 19:"DQ5", 20:"DQ6", 21:"DQ7",
 22:"CE", 23:"A10", 24:"OE", 25:"A11", 26:"A9", 27:"A8", 28:"A13", 29:"A14", 30:"A17", 31:"VDD", 32:"WE"}

def sst39sf040_plcc():
    inv = {v: k for k, v in SST_PLCC32.items()}
    def P(nm, t, disp=None):
        return (str(inv[nm]), disp or nm, t)
    L = [P("A%d" % i, "input") for i in range(19)] + [None,
         P("CE", "input", ov("CE")), P("OE", "input", ov("OE")), P("WE", "input", ov("WE"))]
    R = [P("DQ%d" % i, "bidirectional") for i in range(8)]
    u, g = boxunit("SST39SF040-PLCC32", 1, L, R, top=[P("VDD", "power_in")], bottom=[P("VSS", "power_in")], width=25.4)
    used = sorted(int(p[0]) for p in L + R + [P("VDD","power_in"), P("VSS","power_in")] if p)
    assert used == list(range(1, 33)), used
    return symbol("SST39SF040-PLCC32", "U", "SST39SF040-70-4C-NHE", "Package_LCC:PLCC-32_THT-Socket",
                  "https://ww1.microchip.com/downloads/en/DeviceDoc/20005022C.pdf",
                  "SST39SF040 512Kx8 5 V flash, 70 ns, PLCC-32 pinout per DS20005022C Fig. 2 (not the DIP pinout)",
                  [(u, g)], "flash NOR SST39 PLCC")

def din41612_c96():
    """Three units, pin numbers a1..c32 matching Connector_DIN:DIN41612_C_3x32_Female_Vertical_THT."""
    units = []
    for ui, row in enumerate("abc"):
        pins = [(f"{row}{i}", f"{row}{i}", "passive") for i in range(1, 33)]
        u, g = boxunit("DIN41612-C96", ui + 1, pins, [], width=20.32)
        units.append((u, g))
    return symbol("DIN41612-C96", "J", "DIN41612-C-96", "Connector_DIN:DIN41612_C_3x32_Female_Vertical_THT",
                  "https://b2b.harting.com/files/livebooks/en/PRD0200000100063/downloads/livebook.pdf",
                  "DIN 41612 / IEC 60603-2 type C, 3 rows x 32, female vertical. Pin numbers a1-a32, b1-b32, c1-c32",
                  units, "DIN41612 expansion")

def sc26c92():
    """PLCC-44 pin numbers from Philips SC26C92 datasheet (2000-01) Figure 1, PLCC column. Not the DIP or PQFP columns."""
    L = [("2", "A0", "input"), ("4", "A1", "input"), ("6", "A2", "input"), ("7", "A3", "input"),
         ("10", ov("RDN"), "input"), ("9", ov("WRN"), "input"), ("39", ov("CEN"), "input"), ("38", "RESET", "input"),
         ("8", "IP0", "input"), ("5", "IP1", "input"), ("40", "IP2", "input"), ("3", "IP3", "input"),
         ("43", "IP4", "input"), ("42", "IP5", "input"), ("41", "IP6", "input"),
         ("36", "X1", "passive"), ("37", "X2", "passive")]
    R = [("28", "D0", "bidirectional"), ("18", "D1", "bidirectional"), ("27", "D2", "bidirectional"), ("19", "D3", "bidirectional"),
         ("26", "D4", "bidirectional"), ("20", "D5", "bidirectional"), ("25", "D6", "bidirectional"), ("21", "D7", "bidirectional"),
         ("33", "TxDA", "output"), ("35", "RxDA", "input"), ("13", "TxDB", "output"), ("11", "RxDB", "input"),
         ("32", "OP0", "output"), ("14", "OP1", "output"), ("31", "OP2", "output"), ("15", "OP3", "output"),
         ("30", "OP4", "output"), ("16", "OP5", "output"), ("29", "OP6", "output"), ("17", "OP7", "output"),
         ("24", ov("INTRN"), "open_collector")]
    u, g = boxunit("SC26C92", 1, L, R, top=[("44", "VCC", "power_in")], bottom=[("22", "VSS", "power_in")], width=38.1)
    # pins 1, 12, 23, 34 are NC. Pin 12 is I/M on the SC28L92; leaving it open selects Intel mode on that part.
    # Spread the hidden NC pins so they are not stacked on each other (that reads as connected).
    for i, n in enumerate(("1", "12", "23", "34")):
        u.append(pin(n, "NC", "no_connect", -48.26, 40.64 - i * 5.08, 0, hide=True))
    nums = [p[0] for p in L + R] + ["44", "22", "1", "12", "23", "34"]
    assert sorted(int(n) for n in nums) == list(range(1, 45)), nums
    return symbol("SC26C92", "U", "SC26C92A1A", "Package_LCC:PLCC-44_THT-Socket",
                  "${KIPRJMOD}/../datasheets/SC26C92.pdf",
                  "SC26C92A1A dual UART, Intel bus, PLCC-44. Pinout: Philips SC26C92 datasheet (2000-01) Fig. 1 PLCC column",
                  [(u, g)], "DUART SC26C92")

def ds3234():
    """SOIC-20 pinout, Maxim DS3234 19-5339 Rev 4. NC pins 2 and 7-14 must be tied to GND. SCLK is pins 18 and 20."""
    L = [("1", ov("CS"), "input"), ("3", "32kHz", "output"), ("5", "INT/SQW", "open_collector"),
         ("6", ov("RST"), "bidirectional"), ("17", "DIN", "input"), ("18", "SCLK", "input"), ("16", "VBAT", "passive")]
    R = [("19", "DOUT", "tri_state"), ("20", "SCLK", "input")]
    u1, g1 = boxunit("DS3234", 1, L, R, top=[("4", "VCC", "power_in")], bottom=[("15", "GND", "power_in")], width=30.48)
    nc = [("2", "NC", "passive")] + [(str(n), "NC", "passive") for n in range(7, 15)]
    u2, g2 = boxunit("DS3234", 2, nc, [], width=20.32)
    nums = [p[0] for p in L + R + nc] + ["4", "15"]
    assert sorted(int(n) for n in nums) == list(range(1, 21)), sorted(nums)
    return symbol("DS3234", "U", "DS3234S#", "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
                  "https://www.analog.com/media/en/technical-documentation/data-sheets/DS3234.pdf",
                  "DS3234 SPI RTC, SOIC-20. Maxim 19-5339. NC pins must go to GND; SCLK pins 18 and 20 are shorted inside",
                  [(u1, g1), (u2, g2)], "RTC SPI DS3234")

def build(path):
    lib = [Sym("kicad_symbol_lib"), [Sym("version"), 20241209], [Sym("generator"), "m68030-sbc-mklib"],
           [Sym("generator_version"), "9.0"], mc68030(), mc68882(), lm2678(), tps3702(), atf1508as_plcc84(), simm72(),
           sst39sf040_plcc(), din41612_c96(), sc26c92(), ds3234()]
    with open(path, "w") as f:
        f.write(dump(lib) + "\n")

if __name__ == "__main__":
    build(sys.argv[1])
    print("wrote", sys.argv[1])

