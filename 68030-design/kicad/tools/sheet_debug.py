"""Logic-analyzer headers per spec §8.4: J11 LA1 = A31-A0, J12 LA2 = D31-D0, J13 LA3 = the 32 control signals.
Each 2x20 header is 32 signals + 8 GND (pins 5,10,15,20,25,30,35,40).
USER/HALTED LEDs stay on the glue sheet (D701/D702). LED_n and HALT_LED_n come here as test points only,
because LA3 is already the 32 signals in §8.4. Reset/NMI buttons stay on the reset sheet."""
from build_common import *

HDR = "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical"
# signal pins of a 2x20, GND on 5,10,15,20,25,30,35,40
SIG_PINS = [n for n in range(1, 41) if n % 5 != 0]
GND_PINS = [5, 10, 15, 20, 25, 30, 35, 40]
LA3 = ["CLK_LA", "AS_n", "DS_n", "R_W", "SIZ1", "SIZ0", "FC2", "FC1", "FC0",
       "DSACK1_n", "DSACK0_n", "BERR_n", "HALT_n", "RESET_n", "STERM_n", "CIIN_n",
       "CBREQ_n", "CBACK_n", "AVEC_n", "IPL2_n", "IPL1_n", "IPL0_n", "IPEND_n",
       "STATUS_n", "REFILL_n", "ECS_n", "OCS_n", "RMC_n", "DRAM_SEL_n", "RAS0_n", "CAS3_n", "WE_n"]
assert len(LA3) == 32 and len(SIG_PINS) == 32

def build_debug(P):
    sh = P.sub("debug", "Logic analyzer headers LA1-LA3 (spec §8.4)", 13, paper="A2")
    sh.comments = [
        "J11-J13 may be left unpopulated after bring-up",
        "D701/D702 USER and HALTED LEDs are on the glue sheet; not repeated here",
        "SW1 warm reset and SW2 NMI are on the reset sheet",
    ]
    headers = [
        ("J11", "LA1 A31-A0", 80.0, ["A%d" % i for i in range(31, -1, -1)]),
        ("J12", "LA2 D31-D0", 250.0, ["D%d" % i for i in range(31, -1, -1)]),
        ("J13", "LA3 control", 430.0, LA3),
    ]
    for ref, val, x, nets in headers:
        j = sh.sym("Connector_Generic:Conn_02x20_Odd_Even", ref, val, x, 160.0, fp=HDR,
                   fields={"MPN": "Samtec TSW-120-07-G-D", "Note": "2x20 2.54 mm pin header. Unpopulated after bring-up is fine."},
                   ref_at=(x + 20.0, 100.0), val_at=(x + 20.0, 230.0))
        ends = []
        for pn, net in zip(SIG_PINS, nets):
            ex, ey = j.to_label(str(pn), net, length=7.62)
            if ref != "J13":
                px, py = j.pin(str(pn))
                dx = -1 if ex < px else 1
                sh.bus_entry(ex, ey, dx * 2.54, -2.54)
                ends.append((ex + dx * 2.54, ey - 2.54))
        for pn in GND_PINS:
            j.to_power(str(pn), "GND", length=5.08)
        if ref != "J13":
            busname = "A[0..31]" if ref == "J11" else "D[0..31]"
            xs = {}
            for bx, by in ends:
                xs.setdefault(bx, []).append(by)
            for bx, ys in xs.items():
                sh.bus((bx, min(ys)), (bx, max(ys)))
                sh.label(busname, bx, min(ys), 90)
    # one hierarchical label per net, along the top, wired to a local label of the same name
    # Address and data buses, then every scalar.
    sh.bus((25.4, 27.94), (40.64, 27.94))
    sh.hlabel("A[0..31]", "input", 25.4, 27.94, 180)
    sh.label("A[0..31]", 33.02, 27.94, 0)
    sh.bus((25.4, 40.64), (40.64, 40.64))
    sh.hlabel("D[0..31]", "input", 25.4, 40.64, 180)
    sh.label("D[0..31]", 33.02, 40.64, 0)
    scalars = ["CLK_LA", "AS_n", "DS_n", "R_W", "SIZ1", "SIZ0", "FC2", "FC1", "FC0",
               "DSACK1_n", "DSACK0_n", "BERR_n", "HALT_n", "RESET_n", "STERM_n", "CIIN_n",
               "CBREQ_n", "CBACK_n", "AVEC_n", "IPL2_n", "IPL1_n", "IPL0_n", "IPEND_n",
               "STATUS_n", "REFILL_n", "ECS_n", "OCS_n", "RMC_n", "DRAM_SEL_n", "RAS0_n",
               "CAS3_n", "WE_n"]
    for i, nm in enumerate(scalars):
        col, row = divmod(i, 16)
        x = 30.0 + col * 200.0
        y = 250.0 + row * 6.0
        sh.hlabel(nm, "input", x, y, 180)
        sh.label(nm, x + 15.0, y, 0)
        sh.wire((x, y), (x + 15.0, y))
    # LED nets: test points, not a second pair of LEDs
    for i, (ref, net) in enumerate((("TP1101", "LED_n"), ("TP1102", "HALT_LED_n"))):
        x = 460.0 + i * 20.0
        y = 280.0
        tp = sh.sym("Connector:TestPoint", ref, net, x, y, fp=TP, hide_val=True,
                    ref_at=(x + 2.0, y - 4.0))
        px, py = tp.pin(1)
        sh.wire((px, py), (px, py + 8.0))
        sh.hlabel(net, "input", px, py + 8.0, 270)
    sh.text("Logic analyzer (spec §8.4). Keep the headers within about 25 mm of the CPU [EST] so the stubs stay short.\\n"
            "Pin order on each header: signals on every pin that is not a multiple of 5; pins 5/10/15/20/25/30/35/40 are GND.\\n"
            "LA1 is A31 down to A0. LA2 is D31 down to D0. LA3 is the §8.4 list, in that order, starting at pin 1.\\n"
            "LED_n and HALT_LED_n are TP1101/TP1102 only. The LEDs themselves are D701/D702 on the glue sheet.",
            30.0, 360.0, 1.15)
    return sh
