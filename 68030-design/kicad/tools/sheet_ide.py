"""IDE / CF sheet. 40-pin header, 3x SN74ACT245N.
U11: DD7:0 <-> D31:24. U12: DD15:8 <-> D23:16. U13 one-way (DIR high, OE low):
DA2:0 (U3 pins 50-52), CS0, CS1, DIOR, DIOW, RESET.
ATA/ATAPI-6 §4.2.1 Table 5 terminations. Timing budget is in the sheet note and spec §3.2;
wait states are NOT changed here."""
from build_common import *
from sheet_cpu import bus_side

DIP20 = "Package_DIP:DIP-20_W7.62mm"
IDC40 = "Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical"
DS245 = "https://www.ti.com/lit/ds/symlink/sn74act245.pdf"
ACT = {"MPN": "SN74ACT245N", "Note": "TI SCAS452H, PDIP (N), active. Same 245 pinout; footprint stays DIP-20. Fig. 6-1 CL=50 pF only"}

# header pin -> (net or None, 'gnd'/'nc'/'sig'/'pu'/'pd')
# ATA-6 40-pin. Pin 20 is the key (no contact). Pin 32 was IOCS16, obsolete and left open.
# Pin 34 PDIAG:CBLID: ATA-6 note 7, a host without UDMA>2 shall not connect it.

def build_ide(P):
    sh = P.sub("ide", "IDE / CompactFlash: 40-pin header + 3x SN74ACT245N", 11, paper="A2")
    sh.comments = [
        "DA2:0 come from U3 pins 50-52 (glue Rev A.1), through U13. No address bus on this sheet",
        "IORDY 4.7k pull-up, DD7 10k pull-down: ATA/ATAPI-6 §4.2.1 Table 5",
        "13 wait states kept. SN74ACT245N meets t0/t1/t2/t4/t9; read t5 still misses (spec 3.2)",
    ]
    def act(ref, x, y):
        return sh.sym("74xx:74LS245", ref, "SN74ACT245N", x, y, fp=DIP20, ds=DS245, fields=dict(ACT),
                      ref_at=(x - 20.0, y - 22.0), val_at=(x - 20.0, y + 24.0))
    # ---- data transceivers. A side = IDE DD, B side = CPU D, DIR = R/W (high = A->B = read)
    pairs = [
        ("U11", 90.0, 95.0, [("A%d" % i, "DD%d" % i) for i in range(8)],
         [("B%d" % i, "D%d" % (24 + i)) for i in range(8)]),
        ("U12", 90.0, 185.0, [("A%d" % i, "DD%d" % (8 + i)) for i in range(8)],
         [("B%d" % i, "D%d" % (16 + i)) for i in range(8)]),
    ]
    buses = []
    for ref, x, y, a_pins, b_pins in pairs:
        u = act(ref, x, y)
        for pn, net in a_pins:
            u.to_label(pn, net, length=7.62)
        bx, y1, y2 = bus_side(sh, u, b_pins, "R", None, wire_len=7.62)
        buses.append((bx, min(y1, y2), max(y1, y2)))
        u.to_label("A->B", "R_W", length=10.16, hier="input")
        u.to_label("CE", "IDE_BUF_EN_n", length=12.7, hier="input")
        u.to_power("VCC", "+5V", length=5.08)
        u.to_power("GND", "GND", length=5.08)
    # both vertical member buses join one D[0..31]. D0-D15 are on the bus and unused here.
    top = 55.88
    for bx, y1, y2 in buses:
        sh.bus((bx, top), (bx, y2))
    sh.bus((buses[0][0], top), (buses[-1][0] + 20.32, top))
    sh.hlabel("D[0..31]", "bidirectional", buses[-1][0] + 20.32, top, 0)
    sh.text("D24-D31 (U11) and D16-D23 (U12) are members of D[0..31]. DIR = R/W high drives DD onto the CPU.", 145.0, 48.0, 1.0)
    # ---- U13 control, A -> B only
    u13 = act("U13", 90.0, 280.0)
    ctrl = [("A0", "IDE_DA0", "DA0"), ("A1", "IDE_DA1", "DA1"), ("A2", "IDE_DA2", "DA2"),
            ("A3", "IDE_CS0_n", "CS0_n"), ("A4", "IDE_CS1_n", "CS1_n"),
            ("A5", "IDE_DIOR_n", "DIOR_n"), ("A6", "IDE_DIOW_n", "DIOW_n"),
            ("A7", "PERIPH_RST_n", "RESET_n")]
    hier_in = {"IDE_DA0", "IDE_DA1", "IDE_DA2", "IDE_CS0_n", "IDE_CS1_n", "IDE_DIOR_n", "IDE_DIOW_n", "PERIPH_RST_n"}
    for i, (ap, src, dst) in enumerate(ctrl):
        u13.to_label(ap, src, length=12.7, hier="input")
        # 33 ohm series on the B output, then the IDE net
        bx, by = u13.pin("B%d" % i)
        r = R(sh, "R%d" % (911 + i), "33", bx + 12.7, by, 90,
              ref_at=(bx + 12.7, by - 2.2), val_at=(bx + 12.7, by + 2.2), just="center",
              fields={"Note": "source damping [EST]; not an ATA-6 PIO requirement"})
        a, b = sorted([r.pin(1), r.pin(2)])
        sh.wire((bx, by), a)
        sh.wire(b, (b[0] + 7.62, b[1]))
        sh.label(dst, b[0] + 7.62, b[1], 0)
    # DIR tied high (A->B), OE tied low (always driving the cable)
    u13.to_power("A->B", "+5V", length=7.62)
    u13.to_power("CE", "GND", length=7.62)
    u13.to_power("VCC", "+5V", length=5.08)
    u13.to_power("GND", "GND", length=5.08)
    sh.text("U13 is wired one way: DIR = +5V (A->B), OE = GND.\\nDA2:0 are U3 pins 50-52, registered (glue Rev A.1).", 20.0, 248.0, 1.0)
    # ---- 40-pin header
    j = sh.sym("Connector_Generic:Conn_02x20_Odd_Even", "J6", "IDE 40-pin", 430.0, 200.0, fp=IDC40,
               ds="https://www.te.com/",
               fields={"MPN": "Wurth 61204021621", "Note": "2x20 shrouded, 2.54 mm, DIN 41651. Remove pin 20 (key). CF adapter plugs in here."},
               ref_at=(445.0, 145.0), val_at=(445.0, 260.0))
    sig = {
        "1": "RESET_n", "3": "DD7", "5": "DD6", "7": "DD5", "9": "DD4", "11": "DD3", "13": "DD2", "15": "DD1", "17": "DD0",
        "21": "DMARQ", "23": "DIOW_n", "25": "DIOR_n", "27": "IDE_IORDY", "29": "DMACK_n", "31": "IDE_INTRQ",
        "33": "DA1", "35": "DA0", "37": "CS0_n", "39": "DASP_n",
        "4": "DD8", "6": "DD9", "8": "DD10", "10": "DD11", "12": "DD12", "14": "DD13", "16": "DD14", "18": "DD15",
        "36": "DA2", "38": "CS1_n",
    }
    gnd_pins = ["2", "19", "22", "24", "26", "30", "40"]
    for pn, net in sig.items():
        j.to_label(pn, net, length=10.16)
    for pn in gnd_pins:
        j.to_power(pn, "GND", length=5.08)
    j.to_power("28", "GND", length=7.62)   # CSEL grounded: the single device is master (ATA-6 Table 5 note 4)
    j.to_nc("20")   # key
    j.to_nc("32")   # IOCS16, not in ATA-6
    j.to_nc("34")   # PDIAG:CBLID, note 7: do not connect without UDMA > 2
    # terminations (ATA-6 §4.2.1 Table 5)
    pullup_bank(sh, [("R901", "4.7k", "IDE_IORDY")], 320.0, 40.0, hier="output")
    # DD7 pull-down
    r = R(sh, "R902", "10k", 330.0, 55.0, 90, ref_at=(329.0, 52.5), val_at=(331.3, 52.5), just="right")
    r.s["val_just"] = "left"
    a, b = sorted([r.pin(1), r.pin(2)])
    sh.wire(a, (a[0] - 5.08, a[1])); sh.label("DD7", a[0] - 5.08, a[1], 180)
    sh.wire(b, (b[0] + 2.54, b[1])); sh.power("GND", b[0] + 2.54, b[1] + 2.54 if False else b[1], 270)
    # INTRQ pull-down + hierarchical output
    r = R(sh, "R903", "10k", 360.0, 55.0, 90, ref_at=(359.0, 52.5), val_at=(361.3, 52.5), just="right")
    r.s["val_just"] = "left"
    a, b = sorted([r.pin(1), r.pin(2)])
    sh.wire(a, (a[0] - 8.0, a[1])); sh.hlabel("IDE_INTRQ", "output", a[0] - 8.0, a[1], 180)
    sh.wire(b, (b[0] + 2.54, b[1])); sh.power("GND", b[0] + 2.54, b[1], 270)
    # DMARQ 5.6k pull-down (Table 5 host column)
    r = R(sh, "R904", "5.6k", 300.0, 80.0, 90, ref_at=(299.0, 77.5), val_at=(301.3, 77.5), just="right")
    r.s["val_just"] = "left"
    a, b = sorted([r.pin(1), r.pin(2)])
    sh.wire(a, (a[0] - 5.08, a[1])); sh.label("DMARQ", a[0] - 5.08, a[1], 180)
    sh.wire(b, (b[0] + 2.54, b[1])); sh.power("GND", b[0] + 2.54, b[1], 270)
    # DMACK held negated (high): PIO only, not driven
    r = R(sh, "R905", "10k", 390.0, 80.0, 0, ref_at=(390.0, 76.5), val_at=(390.0, 83.5), just="center")
    p1, p2 = r.pin(1), r.pin(2)
    upper, lower = (p1, p2) if p1[1] < p2[1] else (p2, p1)
    sh.wire(upper, (upper[0], upper[1] - 3.0)); sh.power("+5V", upper[0], upper[1] - 3.0, 0)
    sh.wire(lower, (lower[0], lower[1] + 5.0)); sh.label("DMACK_n", lower[0], lower[1] + 5.0, 270)
    # activity LED on DASP (device open-collector, active low). Device provides the 10k pull-up (Table 5).
    # rot 0: cathode to the left, anode to the right. +5V -- 1k -- anode, cathode to DASP-.
    led = sh.sym("Device:LED", "D5", "IDE", 360.0, 100.0, 0, fp=LED0805,
                 ref_at=(360.0, 96.0), val_at=(360.0, 104.0))
    k, a_ = led.pin("K"), led.pin("A")
    rr = R(sh, "R906", "1k", a_[0] + 3.81, a_[1], 90,
           ref_at=(a_[0] + 3.81, a_[1] - 2.54), val_at=(a_[0] + 3.81, a_[1] + 2.54))
    sh.wire(a_, rr.pin(1))
    pwr = (rr.pin(2)[0] + 2.54, rr.pin(2)[1])
    sh.wire(rr.pin(2), pwr)
    sh.power("+5V", pwr[0], pwr[1], 270)
    sh.wire(k, (k[0] - 7.62, k[1]))
    sh.label("DASP_n", k[0] - 7.62, k[1], 180)
    cap_row(sh, [("C911", "100n", C0805), ("C912", "100n", C0805), ("C913", "100n", C0805)], 40.0, 360.0, 12.7)
    sh.text("U11 / U12 / U13 decoupling", 30.0, 345.0, 1.0)
    sh.text("IDE header (spec §1.2, §3.2). A CF-to-40-pin adapter uses this connector; no separate CF socket.", 250.0, 280.0, 1.27, bold=True)
    sh.text("Terminations, ATA/ATAPI-6 (T13/1410D) §4.2.1 Table 5, notes 3, 4, 5, 7, 10:\\n"
            "  R901 4.7k IORDY pull-up to +5V (table value; note 10 allows 1k, not used).\\n"
            "  R902 10k DD7 pull-down (note 3: host shall pull DD7 down, not up).\\n"
            "  R903 10k INTRQ pull-down (note 5; spec §3.5: active high).\\n"
            "  R904 5.6k DMARQ pull-down (table host column). DMA is not used.\\n"
            "  R905 10k holds DMACK- high (negated). PIO only; the host does not drive it [VERIFY on a real drive].\\n"
            "  Pin 28 CSEL grounded (note 4) so one device is the master. Pin 34 PDIAG not connected (note 7).\\n"
            "  DASP- lights D5 through R906 1k. The device has the 10k pull-up (table); the host must not drive DASP (note 9).\\n"
            "  R911-R918 33 ohm on U13 outputs are damping only [EST], not in the PIO table.",
            250.0, 290.0, 1.05)
    sh.text("PIO-0 vs SN74ACT245N (SCAS452H Fig. 6-1, CL = 50 pF only; no 150 pF number).\\n"
            "SN74, VCC 5 V +/- 0.5 V, over temperature: tPLH 1.5 to 8 ns, tPHL 1 to 9 ns. 13 WS unchanged.\\n"
            "At the drive: t0 631 ns (margin 31), t1 111.7 (42), t2 352.5 (62 vs 290), t4 50 (20), t9 36.6 (17).\\n"
            "Read t5 misses: DIOR tPLH and the data tpd both add, 10.5 - 8 - 9 = -6.5 ns at the latch\\n"
            "(EC #27 is 2 ns at 25 MHz, so 8.5 ns short). More wait states do not move that edge. spec 3.2.",
            250.0, 360.0, 1.05)
    return sh
