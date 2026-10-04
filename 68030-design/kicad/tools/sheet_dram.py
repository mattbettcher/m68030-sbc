"""DRAM controller + SIMM sheet (U4 ATF1508AS-7JX84 + J1 72-pin SIMM socket). The U4 pin assignment is read from
the fitter output ../../cpld/dram/pinout.csv (fit1508 v1918, extracted from dram.fit by cpld/dram/pinout.py).
SIMM pinout: Micron MT8D432/MT16D832 datasheet (symbol m68030-sbc:SIMM72, see mklib.py). Spec: spec.md 4.3, 5."""
import csv
from build_common import *
from sheet_cpu import bus_side

HERE = os.path.dirname(os.path.abspath(__file__))
PINOUT = os.path.normpath(os.path.join(HERE, "..", "..", "cpld", "dram", "pinout.csv"))
PLCC = "Package_LCC:PLCC-84_THT-Socket"
IDC10 = "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical"
SJ2 = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
SO16 = "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
CP10 = "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"
SIMMFP = "m68030-sbc:SIMM-72_TE-5822021-4"

HIER_IN = {"DRAM_CLK", "PWR_RST_n", "AS_n", "R_W", "SIZ0", "SIZ1", "DRAM_SEL_n"}
HIER_TRI = {"DSACK0_n", "DSACK1_n"}
STROBES = ["MA%d" % i for i in range(12)] + ["RAS0_n", "RAS1_n", "RAS2_n", "RAS3_n", "CAS0_n", "CAS1_n", "CAS2_n", "CAS3_n", "WE_n"]
# reserved pins behind open solder jumpers: pin -> (net, hier shape, ref)
JUMPERED = {16: ("STERM_n", "tri_state", "JP801"), 17: ("CBREQ_n", "input", "JP802"), 18: ("CBACK_n", "tri_state", "JP803"),
            50: ("DS_n", "input", "JP804")}
JTAG = {14: "U4_TDI", 23: "U4_TMS", 62: "U4_TCK", 71: "U4_TDO"}
# 74ACT257 fallback: MA2..MA11 = (row bit on I0, column bit on I1) per spec 5.2 (S = MUX_SEL: low = row, high = column)
MUXMAP = [("MA%d" % (i + 2), "A%d" % (i + 14), "A%d" % (i + 4)) for i in range(8)] + [("MA10", "A22", "A23"), ("MA11", "A24", "A25")]

def load_pinout():
    return {int(r["pin"]): r["fitter_name"] for r in csv.DictReader(open(PINOUT))}

def build_dram(P):
    pins = load_pinout()
    sh = P.sub("dram", "DRAM controller CPLD U4 (ATF1508AS-7JX84) + 72-pin SIMM J1", 8, paper="A2")
    sh.comments = ["FITTED pinout: fit1508 v1918, cpld/dram/pinout.csv (80/128 MC, 50 MHz met)",
                   "SIMM pinout: Micron MT8D432/MT16D832; socket TE 5822021-4 (hole pattern ENG_CD_5822021_B1)",
                   "Logic: cpld/dram/dram.v (after Mackerel-30 dram_controller.v); build: cpld/dram/build.sh"]
    # ================================================================ U4
    ux, uy = 177.8, 203.2
    u = sh.sym("m68030-sbc:ATF1508AS-PLCC84", "U4", "ATF1508AS-7JX84", ux, uy, fp=PLCC,
               ds="https://ww1.microchip.com/downloads/en/DeviceDoc/doc0784.pdf",
               fields={"MPN": "ATF1508AS-7JX84", "Socket": "PLCC-84 THT socket (XU4)", "Firmware": "cpld/dram/dram.jed"},
               ref_at=(ux + 19.05, uy - 60.96), val_at=(ux + 19.05, uy + 60.96))
    for n, nm in pins.items():
        pinname = [p["name"] for num, p in u.allpins() if num == str(n)][0]
        if nm == "VCC": assert pinname.startswith("VCC"), (n, pinname)
        elif nm in ("GND", "TDI", "TMS", "TCK", "TDO"): assert nm in pinname, (n, nm, pinname)
    for n, nm in sorted(pins.items()):
        if nm in ("VCC", "GND") or n in JTAG or n in JUMPERED:
            continue
        if n == 2:
            u.to_label("2", "CLK_DRAMC", length=25.4, hier="input"); continue
        if n == 81:
            u.to_label("81", "U4_SPARE81", length=10.16); continue
        assert nm, (n, "unexpected unused pin")
        if nm in HIER_IN: u.to_label(str(n), nm, length=25.4, hier="input")
        elif nm in HIER_TRI: u.to_label(str(n), nm, length=25.4, hier="tri_state")
        elif nm in STROBES: u.to_label(str(n), "U4_" + nm, length=10.16)
        elif nm == "MUX_SEL": u.to_label(str(n), "MUX_SEL", length=10.16)
        elif nm.startswith("A") and nm[1:].isdigit(): u.to_label(str(n), nm, length=7.62)
        else: raise AssertionError((n, nm))
    for n, net in JTAG.items():
        u.to_label(str(n), net, length=10.16)
    # reserved pins through open solder jumpers
    for n, (net, shape, ref) in JUMPERED.items():
        x, y = u.pin(str(n))
        d = 1 if x > ux else -1
        off = {16: 7.62, 17: 17.78, 18: 27.94}.get(n, 12.7)       # stagger the adjacent pins' jumpers
        jx = x + d * off
        jp = sh.sym("Jumper:SolderJumper_2_Open", ref, "open", jx, y, 0, fp=SJ2, hide_val=True,
                    ref_at=(jx, y - 2.54), val_at=(jx, y + 2.54), just="center",
                    fields={"Note": "leave open in Rev A (pin unused by dram.v; fitter: NC pins unconnected)"})
        a, b = (jp.pin("2"), jp.pin("1")) if d < 0 else (jp.pin("1"), jp.pin("2"))
        sh.wire((x, y), a)
        end = (x + d * (38.1 if n in (16, 17, 18) else 25.4), y)
        sh.wire(b, end)
        sh.hlabel(net, shape, end[0], end[1], 0 if d > 0 else 180)
    # address bus: A-labels on U4 pins are members of the A[0..31] bus
    sh.bus((111.76, 132.08), (127.0, 132.08))
    sh.hlabel("A[0..31]", "input", 111.76, 132.08, 180)
    sh.label("A[0..31]", 116.84, 132.08, 0)
    sh.text("U4 address inputs A0-A26 are labelled A<n> (members of bus A[0..31])", 106.68, 127.0, 1.0)
    # power pins
    vcc = sorted(u.pin(n) for n, p in u.allpins() if p["name"].startswith("VCC"))
    ry = vcc[0][1] - 2.54
    for p in vcc: sh.wire(p, (p[0], ry))
    sh.wire((vcc[0][0] - 5.08, ry), (vcc[-1][0], ry)); sh.power("+5V", vcc[0][0] - 5.08, ry, 0)
    gnd = sorted(u.pin(n) for n, p in u.allpins() if p["name"] == "GND")
    gy = gnd[0][1] + 2.54
    for p in gnd: sh.wire(p, (p[0], gy))
    sh.wire((gnd[0][0], gy), (gnd[-1][0], gy)); sh.power("GND", gnd[0][0], gy, 0)
    # U4 decoupling
    cap_row(sh, [("C%d" % (801 + i), "100n", C0805) for i in range(8)] + [("C809", "10u", C1206)], 142.24, 287.02, 10.16)
    sh.text("U4 decoupling: 8x 100 nF, one at each VCC pin (VCCINT 3, 43; VCCIO 13, 26, 38, 53, 66, 78), + 10 uF bulk", 137.16, 274.32, 1.27)
    # ================================================================ series resistors (at U4)
    sx, sy = 271.78, 137.16
    sh.text("Series terminations at U4 (spec 5.8)", 256.54, 124.46, 1.5, bold=True)
    sh.text("33R, placed next to U4 (source termination)", 256.54, 129.54, 1.0)
    for i, nm in enumerate(STROBES):
        y = sy + i * 5.08
        r = R(sh, "R%d" % (804 + i), "33", sx, y, 90, ref_at=(sx, y - 1.905), val_at=(sx, y + 1.905), just="center")
        a, b = sorted([r.pin(1), r.pin(2)])
        sh.wire(a, (a[0] - 5.08, a[1])); sh.label("U4_" + nm, a[0] - 5.08, a[1], 180)
        sh.wire(b, (b[0] + 5.08, b[1])); sh.label(nm, b[0] + 5.08, b[1], 0)
    sh.text("R806-R815 (MA2-MA11): remove if the\\n74ACT257 fallback (U801-U803) is fitted", 256.54, sy + len(STROBES) * 5.08 + 1.27, 1.0)
    # ================================================================ SIMM socket J1
    jx, jy = 419.1, 198.12
    j1 = sh.sym("m68030-sbc:SIMM72", "J1", "SIMM-72 socket", jx, jy, fp=SIMMFP,
                ds="https://www.te.com/usa-en/product-5822021-4.html",
                fields={"MPN": "TE 5822021-4", "Note": "72-pos vertical SIMM socket, metal latches; 5 V FPM/EDO x32 module, 60 ns"},
                ref_at=(jx + 13.97, jy - 53.34), val_at=(jx + 13.97, jy + 54.61))
    for i in range(12):
        j1.to_label("A%d" % i, "MA%d" % i, length=10.16)
    for s, pn in (("RAS", "~{RAS%d}"), ("CAS", "~{CAS%d}")):
        for i in range(4):
            j1.to_label(pn % i, "%s%d_n" % (s, i), length=10.16)
    j1.to_label("~{WE}", "WE_n", length=10.16)
    for i in range(1, 5):
        j1.to_label("PRD%d" % i, "SIMM_PD%d" % i, length=10.16)
    for n in (11, 35, 36, 37, 38, 46, 48, 66, 71):
        j1.to_nc(str(n))
    bx, y1, y2 = bus_side(sh, j1, [("DQ%d" % (i + 1), "D%d" % i) for i in range(32)], "R", None)
    sh.bus((bx, y1), (bx, 139.7), (452.12, 139.7))
    sh.hlabel("D[0..31]", "bidirectional", 452.12, 139.7, 0)
    sh.text("DQ1-DQ8 = D0-D7 (CAS0), DQ9-16 = D8-15 (CAS1),\\nDQ17-24 = D16-23 (CAS2), DQ25-32 = D24-31 (CAS3)", 440.69, 256.54, 1.0)
    # SIMM power
    vd = sorted(j1.pin(n) for n in ("10", "30", "59"))
    ry = vd[0][1] - 2.54
    for p in vd: sh.wire(p, (p[0], ry))
    sh.wire((vd[0][0] - 5.08, ry), (vd[-1][0], ry)); sh.power("+5V", vd[0][0] - 5.08, ry, 0)
    vs = sorted(j1.pin(n) for n in ("1", "39", "72"))
    gy = vs[0][1] + 2.54
    for p in vs: sh.wire(p, (p[0], gy))
    sh.wire((vs[0][0], gy), (vs[-1][0], gy)); sh.power("GND", vs[0][0], gy, 0)
    # presence-detect pull-ups -> DUART inputs (hierarchical outputs)
    sh.text("SIMM presence detect (spec 5.1): 10k pull-ups;\\nmodule ties PRDn to VSS or leaves it open.\\nRead on DUART IP3-IP6 (advisory; firmware sizes by probing)", 355.6, 261.62, 1.0)
    pullup_bank(sh, [("R%d" % (825 + i), "10k", "SIMM_PD%d" % (i + 1)) for i in range(4)], 368.3, 281.94, hier="output")
    # SIMM decoupling + bulk
    specs = [("C810", "100n", C0805), ("C811", "100n", C0805), ("C812", "100n", C0805),
             ("C813", "10u", C1206), ("C814", "10u", C1206), ("C815", "10u", C1206),
             ("C816", "470u", CP10, "CP", {"fields": {"Note": "low-ESR electrolytic, >= 10 V, at socket end (pin 1)"}}),
             ("C817", "470u", CP10, "CP", {"fields": {"Note": "low-ESR electrolytic, >= 10 V, at socket end (pin 72)"}})]
    cap_row(sh, specs, 406.4, 299.72, 10.16)
    sh.text("SIMM decoupling (spec 6.3): 100 nF + 10 uF at each VDD pin (10, 30, 59), 2x 470 uF low-ESR at the socket ends\\n"
            "for the CBR refresh current spikes (all 16/32 DRAMs refresh at once)", 401.32, 284.48, 1.0)
    # ================================================================ test points
    sh.text("Test points (SIMM side of the series resistors)", 256.54, 256.54, 1.5, bold=True)
    tps = [("TP801", "RAS0_n", "output"), ("TP802", "RAS1_n", None), ("TP803", "CAS0_n", None), ("TP804", "CAS1_n", None),
           ("TP805", "CAS2_n", None), ("TP806", "CAS3_n", "output"), ("TP807", "WE_n", "output"), ("TP808", "MUX_SEL", None),
           ("TP809", "U4_SPARE81", None)]
    for i, (ref, net, hier) in enumerate(tps):
        x = 261.62 + i * 10.16
        y = 266.7
        tp = sh.sym("Connector:TestPoint", ref, net.replace("_n", "#").replace("U4_SPARE", "U4-"), x, y, 0, fp=TP, hide_val=True,
                    ref_at=(x + 1.27, y - 5.08), val_at=(x + 1.27, y - 2.54), just="left")
        px, py = tp.pin(1)
        sh.wire((px, py), (px, py + 7.62))
        if hier: sh.hlabel(net, hier, px, py + 7.62, 270)
        else: sh.label(net, px, py + 7.62, 270)
    # ================================================================ JTAG J5
    jx0, jy0 = 50.8, 223.52
    j5 = sh.sym("Connector_Generic:Conn_02x05_Odd_Even", "J5", "JTAG U4 (ATDH1150USB)", jx0, jy0, 0, fp=IDC10,
                ref_at=(jx0 + 1.27, jy0 - 8.89), val_at=(jx0 + 1.27, jy0 + 10.16), just="center",
                fields={"Note": "Microchip ATDH1150USB 10-pin JTAG-A: 1 TCK 2 GND 3 TDO 4 VCCT 5 TMS 6-8 NC 9 TDI 10 GND"})
    for pn, net in (("1", "U4_TCK"), ("3", "U4_TDO"), ("5", "U4_TMS"), ("9", "U4_TDI")):
        j5.to_label(pn, net, length=12.7)
    j5.to_nc("7"); j5.to_nc("6"); j5.to_nc("8")
    p4 = j5.pin("4"); sh.wire(p4, (p4[0] + 5.08, p4[1])); sh.power("+5V", p4[0] + 5.08, p4[1], 270)
    p2 = j5.pin("2"); p10 = j5.pin("10")
    gx = p2[0] + 10.16
    sh.wire(p2, (gx, p2[1])); sh.wire(p10, (gx, p10[1])); sh.wire((gx, p2[1]), (gx, p10[1] + 2.54)); sh.power("GND", gx, p10[1] + 2.54, 0)
    pullup_bank(sh, [("R801", "4.7k", "U4_TMS"), ("R802", "4.7k", "U4_TDI")], 40.64, 182.88)
    r = R(sh, "R803", "4.7k", 76.2, 190.5, 90, ref_at=(75.565, 188.595), val_at=(76.835, 188.595), just="right")
    r.s["val_just"] = "left"
    a, b = sorted([r.pin(1), r.pin(2)])
    sh.wire(a, (a[0] - 5.08, a[1])); sh.label("U4_TCK", a[0] - 5.08, a[1], 180)
    sh.wire(b, (b[0] + 2.54, b[1])); sh.wire((b[0] + 2.54, b[1]), (b[0] + 2.54, b[1] + 2.54)); sh.power("GND", b[0] + 2.54, b[1] + 2.54, 0)
    sh.text("JTAG ISP header", 22.86, 154.94, 1.5, bold=True)
    sh.text("J5: separate header for U4 (same pinout as J4 on the glue sheet; ATDH1150USB UG Table 1).\\n"
            "Not chained with U3: the ATDH1150USB/ATMISP support multi-device chains, but a separate\\n"
            "header lets each CPLD be programmed/recovered alone and a blank or damaged part cannot\\n"
            "break the other's chain. R801/R802 4.7k pull-ups, R803 4.7k TCK pull-down [EST values].", 22.86, 160.02, 1.0)
    # ================================================================ 74ACT257 fallback (DNP)
    sh.text("Fallback: external row/column address muxes (DNP)", 284.48, 22.86, 1.5, bold=True)
    sh.text("Not needed: U4 fits with the MA mux inside (80/128 MC, 50 MHz met). To use: fit U801-U803 + C818-C820 and\\n"
            "R829-R838, remove R806-R815 (U4 MA2-MA11 path), and rebuild dram.v with MA2-MA11 unused. S = MUX_SEL\\n"
            "(U4 pin 80; low = row on I0, high = column on I1). 74ACT257 tpd <= 10.5 ns (onsemi MC74ACT257), vs 7.5-10 ns in U4.",
            284.48, 27.94, 1.0)
    chans = [("2", "3", "4"), ("5", "6", "7"), ("14", "13", "12"), ("11", "10", "9")]
    rnum = 829
    for k in range(3):
        mx, my = 317.5 + k * 76.2, 71.12
        m = sh.sym("74xx:74LS257", "U%d" % (801 + k), "74ACT257", mx, my, fp=SO16, dnp=True,
                   ds="https://www.onsemi.com/pdf/datasheet/mc74ac257-d.pdf", fields={"MPN": "MC74ACT257DR2G"},
                   ref_at=(mx + 2.54, my - 26.67), val_at=(mx + 2.54, my + 29.21))
        m.to_label("S", "MUX_SEL", length=7.62)
        m.to_power("OE", "GND", length=5.08)
        m.to_power("VCC", "+5V", length=2.54)
        m.to_power("GND", "GND", length=2.54)
        for c in range(4):
            idx = k * 4 + c
            i0, i1, z = chans[c]
            if idx < len(MUXMAP):
                ma, row, col = MUXMAP[idx]
                m.to_label(i0, row, length=7.62)
                m.to_label(i1, col, length=7.62)
                zx, zy = m.pin(z)
                rr = R(sh, "R%d" % rnum, "33", zx + 10.16, zy, 90, dnp=True, ref_at=(zx + 10.16, zy - 1.905), val_at=(zx + 10.16, zy + 1.905), just="center")
                rnum += 1
                a, b = sorted([rr.pin(1), rr.pin(2)])
                sh.wire((zx, zy), a)
                sh.wire(b, (b[0] + 5.08, b[1])); sh.label(ma, b[0] + 5.08, b[1], 0)
            else:
                m.to_power(i0, "GND", length=5.08)
                m.to_power(i1, "GND", length=5.08)
                m.to_nc(z)
    cap_row(sh, [("C%d" % (818 + i), "100n", C0805, "C", {"dnp": True}) for i in range(3)], 533.4, 78.74, 10.16)
    sh.text("U801-U803 decoupling (DNP)", 528.32, 63.5, 1.0)
    # ================================================================ notes
    sh.text("U4 DRAM controller + 72-pin SIMM (spec 3.2, 4.3, 5)", 22.86, 30.48, 2.0, bold=True)
    sh.text("FITTED PINOUT: Yosys + hoglet67/atf15xx_yosys -> Microchip fit1508.exe v1918 (Wine), ATF1508AS PLCC84 -7, JTAG ON,\\n"
            "pins locked (-preassign keep), -optimize on, -pin_keep on. Result: 80/128 macrocells, 52 flip-flops, 210 product terms;\\n"
            "55/60 user I/O + 4 JTAG + 3/4 dedicated inputs. Worst register-to-register 14.0 ns (50 MHz = 20 ns met).\\n"
            "Sources, reports, JEDEC, testbench: cpld/dram/ (dram.v, dram.fit, dram.jed, timing.txt, sim/).\\n"
            "Logic after Mackerel-30 dram_controller.v (C. Maykish, MIT): 50 MHz FSM, 2-flop AS synchroniser, CBR refresh\\n"
            "every 7.5 us alternating sides, 100 us + 16 CBR power-up, CAS lanes from SIZ1/SIZ0/A1/A0, DSACK1+0 (32-bit port).\\n"
            "Pins 16/17/18/50 (STERM_n/CBREQ_n/CBACK_n/DS_n) are unused in Rev A: reached only through open solder jumpers.\\n"
            "Pin 2 (GCLK2) carries CLK_DRAMC for a future CPU-synchronous (burst) FSM; pin 81 spare -> TP809.",
            22.86, 38.1, 1.0)
    sh.text("Series resistors: 33R source termination on MA/RAS/CAS/WE. Trace Z0 ~50-60R minus the CPLD output impedance\\n"
            "(~15-25R) [EST]; SIMM input loads (Micron): MA 48/95 pF, WE 64/127 pF, RAS 32 pF, CAS 16/32 pF (1/2-sided) ->\\n"
            "33R x 100 pF ~ 3.3 ns edge slowing, inside the DRAM timing margins (tRAH/tASC/tCAH >= 14 ns post-fit).",
            22.86, 76.2, 1.0)
    return sh
