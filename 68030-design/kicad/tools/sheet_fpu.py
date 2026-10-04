from build_common import *
from sheet_cpu import bus_side

def build_fpu(P):
    sh = P.sub("fpu", "FPU: MC68882 PLCC-68", 6)
    sh.comments = ['PLCC-68 pins verified vs BR509 Rev.3 p.23 and Mackerel-68k (68/68)', '32-bit port: A0 and SIZE tied to VCC (68881/2 UM / BR509)', 'FPU must be rated >= its clock (FN25A/FN33A), else use X3 + JP3']
    u = sh.sym("m68030-sbc:MC68882", "U2", "MC68882FN33A", 190.5, 132.08, fp="Package_LCC:PLCC-68_THT-Socket",
               ds="https://www.nxp.com/docs/en/data-sheet/BR509.pdf", fields={"MPN": "MC68882FN33A (or FN25A)", "Socket": "PLCC-68 THT socket (XU2)"},
               ref_at=(205.74, 83.82), val_at=(175.26, 187.96))
    # address A1..A4 via bus
    bx, y1, y2 = bus_side(sh, u, [("A%d" % i, "A%d" % i) for i in range(1, 5)], "L", None)
    sh.bus((bx, y1), (bx, 76.2), (139.7, 76.2))
    sh.hlabel("A[0..31]", "input", 139.7, 76.2, 180)
    # A0 and SIZE -> +5V
    x, y = u.pin("~{SIZE}")
    sh.wire((x, y), (x - 17.78, y))
    sh.power("+5V", x - 17.78, y, 90)
    # control
    for pn, net, shape in [("~{CS}", "FPU_CS_n", "input"), ("~{AS}", "AS_n", "input"), ("~{DS}", "DS_n", "input"),
                           ("R/~{W}", "R_W", "input"), ("~{DSACK0}", "DSACK0_n", "tri_state"), ("~{DSACK1}", "DSACK1_n", "tri_state"),
                           ("CLK", "CLK_FPU", "input"), ("~{RESET}", "RESET_n", "input")]:
        u.to_label(pn, net, length=25.4, hier=shape)
    x, y = u.pin("~{SENSE}")
    sh.wire((x, y), (x - 7.62, y)); sh.wire((x - 7.62, y), (x - 7.62, y + 2.54)); sh.power("GND", x - 7.62, y + 2.54, 0)
    u.to_nc("15")
    # data bus
    bx, y1, y2 = bus_side(sh, u, [("D%d" % i, "D%d" % i) for i in range(32)], "R", None)
    sh.bus((bx, y1), (bx, 76.2), (238.76, 76.2))
    sh.hlabel("D[0..31]", "bidirectional", 238.76, 76.2, 0)
    # power pins
    vcc = sorted(u.pin(n) for n, p in u.allpins() if p["name"] == "VCC")
    ry = vcc[0][1] - 2.54
    for p in vcc: sh.wire(p, (p[0], ry))
    sh.wire((vcc[0][0] - 5.08, ry), (vcc[-1][0], ry)); sh.power("+5V", vcc[0][0] - 5.08, ry, 0)
    ax, ay = u.pin("A0")          # A0 tied high for a 32-bit port: route up to the VCC rail
    sh.wire((ax, ay), (ax - 2.54, ay), (ax - 2.54, ry), (vcc[0][0] - 5.08, ry))
    gnd = sorted(u.pin(n) for n, p in u.allpins() if p["name"] == "GND")
    gy = gnd[0][1] + 2.54
    for p in gnd: sh.wire(p, (p[0], gy))
    sh.wire((gnd[0][0], gy), (gnd[-1][0], gy)); sh.power("GND", gnd[0][0], gy, 0)
    # decoupling: one 100n per VCC pin (8) + 10u
    specs = [("C%d" % (601 + i), "100n", C0805) for i in range(8)] + [("C609", "10u", C1206)]
    cap_row(sh, specs, 60.96, 228.6, 10.16)
    sh.text("FPU decoupling: 8x 100 nF (one per VCC pin: 10, 16, 17, 27, 43, 52, 53, 61) + 10 uF", 55.88, 213.36, 1.27)
    sh.text("Notes (spec.md 8.2):\\n- DSACK1_n/DSACK0_n connect directly to the CPU DSACK nets (three-state, actively\\n  negated then released; the 1k pull-ups on the CPU sheet are the holding resistors, UM 9.8).\\n- SENSE tied to GND (UM 9.11; the optional presence-detect circuit is not used).\\n- CLK_FPU comes from JP3 on the clock sheet (1-2 = CPU clock, 2-3 = optional X3).\\n- RESET shares the CPU RESET_n net.",
            55.88, 30.48, 1.27)
    return sh
