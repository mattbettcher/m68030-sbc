from build_common import *

def osc(sh, ref, val, x, y, fp=OSC14, dnp=False, mpn=None, en_to_vcc=True):
    o = sh.sym("Oscillator:CXO_DIP14", ref, val, x, y, fp=fp, dnp=dnp, fields={"MPN": mpn} if mpn else None,
               ref_at=(x + 5.08, y - 6.35), val_at=(x + 5.08, y + 6.35))
    o.to_power("14", "+5V")
    o.to_power("7", "GND")
    if en_to_vcc:
        ex, ey = o.pin("1")
        sh.wire((ex, ey), (ex - 5.08, ey))
        sh.power("+5V", ex - 5.08, ey, 90)
    return o

def series_row(sh, ref, x, y, src_label, dst, hier=True, val="33R"):
    r = R(sh, ref, val, x, y, 90)
    a, b = r.pin(1), r.pin(2)
    sh.wire(a, (a[0] - 7.62, a[1])); sh.label(src_label, a[0] - 7.62, a[1], 180)
    sh.wire(b, (b[0] + 10.16, b[1]))
    if hier:
        sh.hlabel(dst, "output", b[0] + 10.16, b[1], 0)
    else:
        sh.label(dst, b[0] + 10.16, b[1], 0)
    return r

def build_clock(P):
    sh = P.sub("clock", "Clocks", 3)
    sh.comments = ['spec 7.1: socketed X1 (25 -> 33.333 MHz), 74ACT244 fan-out, 33R series [EST]', '68030 needs a stable, continuous clock before VCC is valid (UM 7.8)', 'Place Y1 next to U6 pins 36/37 (DUART sheet)']
    # ---------------- CPU oscillator + fan-out
    sh.text("CPU clock: X1 (socketed DIP-14 full-can) -> U10 74ACT244, one 33R series resistor per load", 30.48, 50.8, 1.5, bold=True)
    x1 = osc(sh, "X1", "25.000MHz", 68.58, 76.2, mpn="25.000 MHz 5 V CMOS full-can oscillator (socketed)")
    u10 = sh.sym("74xx:74HC244", "U10", "74ACT244", 111.76, 88.9, fp="Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
                 ds="https://www.ti.com/lit/ds/symlink/sn74act244.pdf", fields={"MPN": "SN74ACT244DWR"},
                 ref_at=(114.3, 66.04), val_at=(114.3, 111.76))
    u10.to_power("20", "+5V"); u10.to_power("10", "GND")
    ins = ["2", "4", "6", "8", "17", "15", "13", "11"]
    pts = sorted([u10.pin(n) for n in ins], key=lambda p: p[1])
    tie_x = pts[0][0] - 5.08
    for p in pts:
        sh.wire(p, (tie_x, p[1]))
    sh.wire((tie_x, pts[0][1]), (tie_x, pts[-1][1]))
    o = x1.pin("8")
    sh.wire(o, (tie_x, o[1]))
    sh.label("OSC_CPU", o[0] + 2.54, o[1], 0)
    for n in ("1", "19"):
        p = u10.pin(n); sh.wire(p, (p[0] - 2.54, p[1]))
    p1, p2 = u10.pin("1"), u10.pin("19")
    sh.wire((p1[0] - 2.54, p1[1]), (p2[0] - 2.54, p2[1] + 2.54))
    sh.power("GND", p2[0] - 2.54, p2[1] + 2.54, 0)
    outs = [("18", "CLKB_CPU"), ("16", "CLKB_FPU"), ("14", "CLKB_GLUE"), ("12", "CLKB_DRAMC"), ("3", "CLKB_LA"), ("5", "CLKB_EXP")]
    for n, net in outs:
        u10.to_label(n, net, length=5.08)
    for n in ("7", "9"):
        u10.to_nc(n)
    sh.text("2Y2, 2Y3: spare outputs", 127.0, 99.06, 1.0)
    cap_row(sh, [("C301", "100n", C0603), ("C302", "10u", C1206)], 45.72, 104.14, 10.16)
    sh.text("X1 decoupling", 40.64, 114.3, 1.0)
    cap_row(sh, [("C303", "100n", C0603)], 134.62, 119.38, 7.62)
    sh.text("U10 decoupling", 129.54, 129.54, 1.0)
    # ---------------- series resistors
    sh.text("Series termination at the source (one load per output)", 162.56, 50.8, 1.5, bold=True)
    rows = [("R301", "CLKB_CPU", "CLK_CPU", True), ("R302", "CLKB_FPU", "CLK_FPU_CPU", False), ("R303", "CLKB_GLUE", "CLK_GLUE", True),
            ("R304", "CLKB_DRAMC", "CLK_DRAMC", True), ("R305", "CLKB_LA", "CLK_LA", True), ("R306", "CLKB_EXP", "CLK_EXP", True)]
    for i, (ref, a, b, h) in enumerate(rows):
        series_row(sh, ref, 182.88, 63.5 + i * 7.62, a, b, h)
    sh.text("CLK_CPU -> U1 CLK (E1); CLK_GLUE -> U3 pin 83 (GCLK1);\\nCLK_DRAMC -> U4 pin 2 (GCLK2); CLK_LA -> LA3; CLK_EXP -> J10", 162.56, 111.76, 1.27)
    # ---------------- FPU clock select
    sh.text("FPU clock select (spec 7.1): JP3 1-2 = CPU clock (default), 2-3 = X3", 251.46, 50.8, 1.5, bold=True)
    jp3 = sh.sym("Connector_Generic:Conn_01x03", "JP3", "FPU_CLK_SEL", 294.64, 76.2, fp=HDR3, ref_at=(297.18, 73.66), val_at=(297.18, 81.28),
                 fields={"Note": "jumper 1-2 fitted by default"})
    a, b, c = jp3.pin(1), jp3.pin(2), jp3.pin(3)
    sh.wire(a, (a[0] - 12.7, a[1])); sh.label("CLK_FPU_CPU", a[0] - 12.7, a[1], 180)
    sh.wire(b, (b[0] - 5.08, b[1])); sh.wire((b[0] - 5.08, b[1]), (b[0] - 5.08, b[1] - 10.16))
    sh.wire((b[0] - 5.08, b[1] - 10.16), (b[0] + 10.16, b[1] - 10.16))
    sh.hlabel("CLK_FPU", "output", b[0] + 10.16, b[1] - 10.16, 0)
    sh.wire(c, (c[0] - 12.7, c[1])); sh.label("CLKB_X3", c[0] - 12.7, c[1], 180)
    x3 = osc(sh, "X3", "FPU osc (DNP)", 264.16, 101.6, dnp=True, mpn="optional 5 V CMOS oscillator for a slower 68882")
    r308 = R(sh, "R308", "33R", 284.48, 101.6, 90, dnp=True)
    sh.wire(x3.pin("8"), r308.pin(1))
    b8 = r308.pin(2); sh.wire(b8, (b8[0] + 5.08, b8[1])); sh.label("CLKB_X3", b8[0] + 5.08, b8[1], 0)
    cap_row(sh, [("C304", "100n", C0603, "C", {"dnp": True})], 294.64, 119.38, 7.62)
    sh.text("X3/R308/C304 DNP unless a slower 68882 (FN16/FN20) is used", 251.46, 124.46, 1.0)
    # ---------------- DRAM clock
    sh.text("DRAM controller clock: X2 50 MHz, single load (U4 GCLK1, pin 83)", 30.48, 142.24, 1.5, bold=True)
    x2 = osc(sh, "X2", "50.000MHz", 68.58, 165.1, mpn="50.000 MHz 5 V CMOS oscillator")
    r307 = R(sh, "R307", "33R", 91.44, 165.1, 90)
    sh.wire(x2.pin("8"), r307.pin(1))
    b7 = r307.pin(2); sh.wire(b7, (b7[0] + 10.16, b7[1])); sh.hlabel("DRAM_CLK", "output", b7[0] + 10.16, b7[1], 0)
    cap_row(sh, [("C305", "100n", C0603), ("C306", "10u", C1206)], 45.72, 190.5, 10.16)
    sh.text("X2 decoupling", 40.64, 200.66, 1.0)
    # ---------------- DUART crystal
    sh.text("DUART baud clock: Y1 3.6864 MHz on U6 X1/CLK (36) and X2 (37)", 162.56, 142.24, 1.5, bold=True)
    y1 = sh.sym("Device:Crystal", "Y1", "3.6864MHz", 198.12, 162.56, 0, fp="Crystal:Crystal_HC49-4H_Vertical",
                fields={"MPN": "3.6864 MHz HC-49 (CL per chosen part)"}, ref_at=(198.12, 154.94), val_at=(198.12, 157.48), just="center")
    a, b = y1.pin(1), y1.pin(2)
    sh.wire(a, (a[0] - 17.78, a[1])); sh.hlabel("DUART_X1", "passive", a[0] - 17.78, a[1], 180)
    sh.wire(b, (b[0] + 17.78, b[1])); sh.hlabel("DUART_X2", "passive", b[0] + 17.78, b[1], 0)
    for ref, px in (("C307", a[0] - 7.62), ("C308", b[0] + 5.08)):
        c = C(sh, ref, "22p C0G", px, a[1] + 6.35, 0)
        sh.wire(c.pin(1), (px, a[1]))
        g = c.pin(2); sh.power("GND", g[0], g[1], 0)
    sh.text("C307/C308: 22 pF [EST] - size to the crystal's CL (spec 7.1).", 162.56, 180.34, 1.0)
    sh.text("Oscillator pin 1 (EN/NC on DIP-14 full cans) is tied to +5V: harmless if NC, enables the output if E/D.\\nVerify against the purchased oscillator's datasheet [VERIFY].",
            30.48, 213.36, 1.27)
    return sh
