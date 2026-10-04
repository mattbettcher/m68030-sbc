"""Glue/system CPLD sheet (U3 ATF1508AS-7JX84). The pin assignment is read from the fitter output
../../cpld/glue/pinout.csv (fit1508 v1918, extracted from glue.fit by cpld/glue/pinout.py)."""
import csv
from build_common import *
from sheet_cpu import bus_side

HERE = os.path.dirname(os.path.abspath(__file__))
PINOUT = os.path.normpath(os.path.join(HERE, "..", "..", "cpld", "glue", "pinout.csv"))
PLCC = "Package_LCC:PLCC-84_THT-Socket"
IDC10 = "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical"
SJ2 = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"

# fitter port name -> (schematic net, hierarchical-label shape or None for local label)
NETMAP = {"CLK": ("CLK_GLUE", "input")}
SHAPE = {}
for n in ("PWR_RST_n", "AS_n", "DS_n", "R_W", "FC0", "FC1", "FC2", "STATUS_n", "WARM_RST_BTN_n", "NMI_BTN_n",
          "DUART_INT_n", "NIC_INT_n", "EXP_INT_n", "IDE_INTRQ", "IDE_IORDY"):
    SHAPE[n] = "input"
for n in ("DSACK0_n", "DSACK1_n"):
    SHAPE[n] = "tri_state"
SHAPE["RESET_n"] = "bidirectional"
for n in ("BERR_n", "HALT_n", "AVEC_n", "CIIN_n", "IPL0_n", "IPL1_n", "IPL2_n", "DRAM_SEL_n", "FPU_CS_n", "ROM_CE_n",
          "BUS_RD_n", "BUS_WR_n", "DUART_CS_n", "DUART_RST", "PERIPH_RST_n", "IDE_CS0_n", "IDE_CS1_n", "IDE_DIOR_n",
          "IDE_DIOW_n", "IDE_BUF_EN_n", "EXP_SEL_n", "EXP_BUF_EN_n", "LED_n", "HALT_LED_n",
          "IDE_DA0", "IDE_DA1", "IDE_DA2"):
    SHAPE[n] = "output"
ADDR = ["A31", "A30", "A29", "A28", "A27", "A19", "A18", "A17", "A16", "A15", "A14", "A13", "A3", "A2", "A1"]
SPI = {46: ("SPI_HW_SCK", "output", "JP701"), 48: ("SPI_HW_MOSI", "output", "JP702"), 49: ("SPI_HW_MISO", "input", "JP703")}
JTAG = {14: "JTAG_TDI", 23: "JTAG_TMS", 62: "JTAG_TCK", 71: "JTAG_TDO"}

def load_pinout():
    rows = list(csv.DictReader(open(PINOUT)))
    return {int(r["pin"]): r["fitter_name"] for r in rows}

def build_glue(P):
    pins = load_pinout()
    sh = P.sub("glue_cpld", "Glue/system CPLD U3: ATF1508AS-7JX84 (PLCC-84)", 7)
    sh.comments = ["FITTED pinout: fit1508 v1918, cpld/glue/pinout.csv (Rev A.1: 121/128 MC)",
                   "PLCC-84 pins vs doc0784 Rev.0784P; J4 per ATDH1150USB UG",
                   "Logic: cpld/glue/glue.v; build: cpld/glue/build.sh"]
    ux, uy = 185.42, 139.7
    u = sh.sym("m68030-sbc:ATF1508AS-PLCC84", "U3", "ATF1508AS-7JX84", ux, uy, fp=PLCC,
               ds="https://ww1.microchip.com/downloads/en/DeviceDoc/doc0784.pdf",
               fields={"MPN": "ATF1508AS-7JX84", "Socket": "PLCC-84 THT socket (XU3)", "Firmware": "cpld/glue/glue.jed"},
               ref_at=(ux + 19.05, uy - 60.96), val_at=(ux + 19.05, uy + 60.96))
    # sanity: the symbol and the fitter agree on every power/JTAG/dedicated pin
    for n, nm in pins.items():
        pinname = [p["name"] for num, p in u.allpins() if num == str(n)][0]
        if nm in ("VCC",): assert pinname.startswith("VCC"), (n, pinname)
        elif nm in ("GND", "TDI", "TMS", "TCK", "TDO"): assert nm in pinname, (n, nm, pinname)
    byname = {nm: n for n, nm in pins.items() if nm}
    # ---------------- address bus (left)
    bx, y1, y2 = bus_side(sh, u, [(str(byname[a]), a) for a in ADDR], "L", None)
    sh.bus((bx, y1), (bx - 20.32, y1))
    sh.hlabel("A[0..31]", "input", bx - 20.32, y1, 180)
    # ---------------- other CPLD signals -> hierarchical labels
    for n, nm in sorted(pins.items()):
        if not nm or nm in ("VCC", "GND") or nm in ADDR or n in JTAG:
            continue
        net, shape = NETMAP.get(nm, (nm, SHAPE.get(nm)))
        assert shape, (n, nm)
        u.to_label(str(n), net, length=35.56, hier=shape)
    # ---------------- JTAG pins -> local labels
    for n, net in JTAG.items():
        u.to_label(str(n), net, length=10.16)
    # ---------------- reserved SPI master pins via open solder jumpers
    for n, (net, shape, ref) in SPI.items():
        x, y = u.pin(str(n))
        d = 1 if x > ux else -1
        jx = x + d * (12.7 if n != 48 else 22.86)
        ry = y + 2.54 if n == 48 else y - 2.54
        jp = sh.sym("Jumper:SolderJumper_2_Open", ref, "open", jx, y, 0, fp=SJ2, hide_val=True,
                    ref_at=(jx, ry), val_at=(jx, y + 2.54), just="center", fields={"Note": "leave open until the CPLD SPI master exists"})
        near, far = (jp.pin("1"), jp.pin("2")) if d < 0 else (jp.pin("1"), jp.pin("2"))
        a, b = (jp.pin("2"), jp.pin("1")) if d < 0 else (jp.pin("1"), jp.pin("2"))
        sh.wire((x, y), a)
        end = (x + d * 35.56, y)
        sh.wire(b, end)
        sh.hlabel(net, shape, end[0], end[1], 0 if d > 0 else 180)
    ny = u.pin("52")[1] + 3.81
    sh.text("Pins 50-52: IDE_DA0-2, registered IDE address (Rev A.1, was spare/TP707-709) -> ide sheet (U13).\\n"
            "Pins 46/48/49: reserved CPLD SPI master (spec 1.4), behind open solder jumpers.", ux + 21.59, ny, 1.0)
    # ---------------- power pins
    vcc = sorted(u.pin(n) for n, p in u.allpins() if p["name"].startswith("VCC"))
    ry = vcc[0][1] - 2.54
    for p in vcc: sh.wire(p, (p[0], ry))
    sh.wire((vcc[0][0] - 5.08, ry), (vcc[-1][0], ry)); sh.power("+5V", vcc[0][0] - 5.08, ry, 0)
    gnd = sorted(u.pin(n) for n, p in u.allpins() if p["name"] == "GND")
    gy = gnd[0][1] + 2.54
    for p in gnd: sh.wire(p, (p[0], gy))
    sh.wire((gnd[0][0], gy), (gnd[-1][0], gy)); sh.power("GND", gnd[0][0], gy, 0)
    # ---------------- decoupling
    specs = [("C%d" % (701 + i), "100n", C0805) for i in range(8)] + [("C709", "10u", C1206)]
    cap_row(sh, specs, 116.84, 254.0, 10.16)
    sh.text("U3 decoupling: 8x 100 nF, one at each VCC pin (VCCINT 3, 43; VCCIO 13, 26, 38, 53, 66, 78), + 10 uF bulk", 111.76, 238.76, 1.27)
    # ---------------- JTAG header J4
    jx0, jy0 = 50.8, 223.52
    j4 = sh.sym("Connector_Generic:Conn_02x05_Odd_Even", "J4", "JTAG (ATDH1150USB)", jx0, jy0, 0, fp=IDC10,
                ref_at=(jx0 + 1.27, jy0 - 8.89), val_at=(jx0 + 1.27, jy0 + 10.16), just="center",
                fields={"Note": "Microchip ATDH1150USB 10-pin JTAG-A: 1 TCK 2 GND 3 TDO 4 VCCT 5 TMS 6-8 NC 9 TDI 10 GND"})
    for pn, net in (("1", "JTAG_TCK"), ("3", "JTAG_TDO"), ("5", "JTAG_TMS"), ("9", "JTAG_TDI")):
        j4.to_label(pn, net, length=12.7)
    j4.to_nc("7"); j4.to_nc("6"); j4.to_nc("8")
    p4 = j4.pin("4"); sh.wire(p4, (p4[0] + 5.08, p4[1])); sh.power("+5V", p4[0] + 5.08, p4[1], 270)
    p2 = j4.pin("2"); p10 = j4.pin("10")
    gx = p2[0] + 10.16
    sh.wire(p2, (gx, p2[1])); sh.wire(p10, (gx, p10[1])); sh.wire((gx, p2[1]), (gx, p10[1] + 2.54)); sh.power("GND", gx, p10[1] + 2.54, 0)
    pullup_bank(sh, [("R701", "4.7k", "JTAG_TMS"), ("R702", "4.7k", "JTAG_TDI")], 40.64, 182.88)
    r = R(sh, "R703", "4.7k", 76.2, 190.5, 90, ref_at=(75.565, 188.595), val_at=(76.835, 188.595), just="right")
    r.s["val_just"] = "left"
    a, b = sorted([r.pin(1), r.pin(2)])
    sh.wire(a, (a[0] - 5.08, a[1])); sh.label("JTAG_TCK", a[0] - 5.08, a[1], 180)
    sh.wire(b, (b[0] + 2.54, b[1])); sh.wire((b[0] + 2.54, b[1]), (b[0] + 2.54, b[1] + 2.54)); sh.power("GND", b[0] + 2.54, b[1] + 2.54, 0)
    sh.text("JTAG J4 (U3). Pinout: Microchip ATDH1150USB user guide (Atmel-8909A) Table 1 / Fig. 4.\\n"
            "VCCT = +5V (the ATF1508AS VCCIO). TMS/TDI also have the device's internal pull-up option\\n"
            "enabled in the fit (-tdi_pullup/-tms_pullup on); R701/R702 4.7k pull-ups and R703 4.7k TCK\\n"
            "pull-down keep the TAP idle with no cable / blank part [EST values].", 22.86, 160.02, 1.0)
    sh.text("JTAG ISP header", 22.86, 154.94, 1.5, bold=True)
    # ---------------- LEDs (active-low CPLD outputs)
    sh.text("Status LEDs (U3 sinks; ~3 mA)", 294.64, 193.04, 1.5, bold=True)
    for i, (rref, dref, net, val) in enumerate([("R705", "D701", "LED_n", "USER"), ("R706", "D702", "HALT_LED_n", "HALTED")]):
        y = 203.2 + i * 10.16
        x0 = 297.18
        sh.power("+5V", x0, y, 90)
        rr = R(sh, rref, "1k", x0 + 6.35, y, 90)
        sh.wire((x0, y), sorted([rr.pin(1), rr.pin(2)])[0])
        d = sh.sym("Device:LED", dref, val, x0 + 19.05, y, 180, fp=LED0805)
        sh.wire(sorted([rr.pin(1), rr.pin(2)])[1], d.pin("A"))
        k = d.pin("K")
        sh.wire(k, (k[0] + 10.16, k[1])); sh.label(net, k[0] + 10.16, k[1], 0)
    # ---------------- EXP_INT_n pull-up (spec 3.5: open-drain from the expansion card, 4.7k)
    sh.text("Interrupt input pull-up (spec 3.5)", 294.64, 226.06, 1.5, bold=True)
    pullup_bank(sh, [("R704", "4.7k", "EXP_INT_n")], 309.88, 238.76)
    # ---------------- test points on key strobes
    sh.text("Test points (key strobes)", 294.64, 147.32, 1.5, bold=True)
    for i, (ref, net) in enumerate([("TP701", "BUS_RD_n"), ("TP702", "BUS_WR_n"), ("TP703", "ROM_CE_n"),
                                    ("TP704", "DUART_CS_n"), ("TP705", "IDE_DIOR_n"), ("TP706", "IDE_DIOW_n")]):
        x = 299.72 + i * 10.16
        y = 160.02
        tp = sh.sym("Connector:TestPoint", ref, net.replace("_n", "#").replace("U3_SPARE", "U3-"), x, y, 0, fp=TP, hide_val=True, ref_at=(x + 1.27, y - 5.08), val_at=(x + 1.27, y - 2.54), just="left")
        px, py = tp.pin(1)
        sh.wire((px, py), (px, py + 7.62))
        sh.label(net, px, py + 7.62, 270)
    # ---------------- notes
    sh.text("U3 glue / system controller (spec 2, 3, 4.2, 7.2)", 22.86, 30.48, 2.0, bold=True)
    sh.text("FITTED PINOUT: Yosys 0.52 + hoglet67/atf15xx_yosys -> Microchip fit1508.exe v1918 (Wine 10),\\n"
            "ATF1508AS PLCC84 -7, JTAG ON, pins locked (-preassign keep), -pin_keep on, -optimize off.\\n"
            "Rev A.1 (2026-09-27): 121/128 macrocells, 62 flip-flops, 322 product terms; 57/60 user I/O + 4 JTAG + 4/4 dedicated inputs.\\n"
            "Sources, reports, JEDEC: cpld/glue/ (glue.v, glue.fit, glue.jed, pinout.csv).\\n"
            "No series resistors on U3 outputs (spec calls for none; add after scope checks if needed).\\n"
            "Open-drain nets (RESET_n, HALT_n) are emulated with OE; DSACKx/AVEC/BERR are driven low, driven high\\n"
            "when AS_n rises and released <= 20.5 ns later (async clear; pull-ups on CPU sheet).\\n"
            "FPU_CS_n / EXP_SEL_n / EXP_BUF_EN_n: one product term incl. AS_n (no stale-decode runt, spec 3.2).",
            22.86, 38.1, 1.0)
    return sh
