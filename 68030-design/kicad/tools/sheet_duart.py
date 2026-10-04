"""DUART / SPI / RTC sheet. SC26C92A1A PLCC-44 (Philips 2000-01 Fig. 1, PLCC column).
Crystal Y1 and C307/C308 stay on the clock sheet; this sheet only has DUART_X1/X2.
SPI is bit-banged on OP2-OP5. No SPI master in the glue (Rev A.1, 7 macrocells free).
DS3234 is powered from +3V3 so it shares a 3.3 V SPI bus with the NIC module.
"""
from build_common import *
from sheet_cpu import bus_side

PLCC = "Package_LCC:PLCC-44_THT-Socket"
SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
SOIC20 = "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm"
HDR6 = "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
HDR10 = "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical"
BATT = "Battery:BatteryHolder_Keystone_103_1x20mm"
DS_DUART = "${KIPRJMOD}/../datasheets/SC26C92.pdf"
DS_RTC = "https://www.analog.com/media/en/technical-documentation/data-sheets/DS3234.pdf"
DS_LVC = "https://www.ti.com/lit/gpn/sn74lvc125a"

def gnd_rail(sh, part, pins, length=5.08):
    pts = []
    for n in pins:
        x, y = part.pin(n)
        dx, dy = part.pdir(n)
        ex, ey = snap(x + dx * length), snap(y + dy * length)
        sh.wire((x, y), (ex, ey))
        pts.append((ex, ey))
    xs = pts[0][0]
    ys = [p[1] for p in pts]
    sh.wire((xs, min(ys)), (xs, max(ys)))
    sh.power("GND", xs, max(ys), 0)

def build_duart(P):
    sh = P.sub("duart_spi_rtc", "DUART SC26C92, bit-bang SPI, DS3234, NIC header", 10, paper="A3")
    sh.comments = [
        "U6 pinout: Philips SC26C92 datasheet (2000-01) Fig. 1 PLCC column, not DIP/PQFP",
        "Pin 12 is NC (SC28L92 I/M). Left open so an SC28L92 in the same socket is Intel mode",
        "2 wait states unchanged (DUART_WS=2, DUART_DLY=0). No glue refit",
        "DS3234 Maxim 19-5339: NC pins to GND, both SCLK pins tied, no diode in series with VBAT",
    ]
    u = sh.sym("m68030-sbc:SC26C92", "U6", "SC26C92A1A", 114.3, 119.38,
               fp=PLCC, ds=DS_DUART,
               fields={"MPN": "SC26C92A1A", "Socket": "PLCC-44 THT socket XU6 (same footprint)"},
               ref_at=(96.52, 70.0), val_at=(96.52, 175.26))
    bx, y1, y2 = bus_side(sh, u, [("A%d" % i, "A%d" % i) for i in range(4)], "L", None, wire_len=7.62)
    sh.bus((bx, y1), (bx, 33.02), (17.78, 33.02))
    sh.hlabel("A[0..31]", "input", 17.78, 33.02, 180)
    sh.text("A0-A3 only (reg_shift = 0)", 17.78, 27.94, 1.0)
    bx, y1, y2 = bus_side(sh, u, [("D%d" % i, "D%d" % (24 + i)) for i in range(8)], "R", None, wire_len=7.62)
    sh.bus((bx, y1), (bx, 33.02), (210.82, 33.02))
    sh.hlabel("D[0..31]", "bidirectional", 210.82, 33.02, 0)
    sh.text("D0-D7 = CPU D24-D31", 165.1, 27.94, 1.0)

    for num, net in (("10", "BUS_RD_n"), ("9", "BUS_WR_n"), ("39", "DUART_CS_n"), ("38", "DUART_RST")):
        u.to_label(num, net, length=17.78, hier="input")
    for num, net in (("3", "SIMM_PD1"), ("43", "SIMM_PD2"), ("42", "SIMM_PD3"), ("41", "SIMM_PD4")):
        u.to_label(num, net, length=17.78, hier="input")
    u.to_label("36", "DUART_X1", length=17.78, hier="passive")
    u.to_label("37", "DUART_X2", length=17.78, hier="passive")
    u.to_label("24", "DUART_INT_n", length=12.7, hier="output")
    u.to_power("44", "+5V", length=5.08)
    u.to_power("22", "GND", length=5.08)

    # serial + SPI names on the local side of the transceiver / shifter
    for num, net, ln in (
        ("33", "TXDA", 15.24), ("35", "RXDA", 15.24), ("13", "TXDB", 15.24), ("11", "RXDB", 15.24),
        ("32", "RTSA", 15.24), ("14", "RTSB", 15.24), ("8", "CTSA", 17.78), ("5", "CTSB", 17.78),
        ("30", "SPI_CS0_5", 20.32), ("16", "SPI_CS1_5", 20.32),
        ("29", "OP6", 15.24), ("17", "OP7", 15.24),
    ):
        u.to_label(num, net, length=ln)
    # 5 V side uses the hierarchical names. JP701-JP703 are open, so the CPLD pin is not on the net.
    u.to_label("31", "SPI_HW_SCK", length=22.86, hier="input")
    u.to_label("15", "SPI_HW_MOSI", length=22.86, hier="input")
    u.to_label("40", "SPI_HW_MISO", length=22.86, hier="output")

    # Drop INTRN / OP6 / OP7 below the symbol before placing parts, so they do not
    # cross the OP2-OP5 SPI stubs (a wire crossing is not a KiCad connection, but it reads as one).
    def drop(pin, net_x, y, name=None):
        x, py = u.pin(pin)
        sh.wire((x + net_x, py), (x + net_x, y))
        return x + net_x, y
    # INTRN label is 12.7 out. Pull-up hangs below it.
    ix, iy = drop("24", 12.7, 165.1)
    r = R(sh, "R1001", "4.7k", ix + 7.62, iy, 90,
          ref_at=(ix + 7.62, iy - 2.54), val_at=(ix + 7.62, iy + 2.54))
    sh.wire((ix, iy), r.pin(1))
    end = (r.pin(2)[0] + 2.54, r.pin(2)[1])
    sh.wire(r.pin(2), end)
    sh.power("+5V", end[0], end[1], 270)
    # OP6 LED, active low (reset leaves OP high, so the LED is off).
    # OP6 is above OP7; a straight drop would run through OP7's stub. Step right first.
    x6, y6 = u.pin("29")
    sh.wire((x6 + 15.24, y6), (x6 + 25.4, y6), (x6 + 25.4, 172.72))
    lx, ly = x6 + 25.4, 172.72
    led = sh.sym("Device:LED", "D6", "OP6", lx + 12.7, ly, 0, fp=LED0805,
                 ref_at=(lx + 12.7, ly - 3.81), val_at=(lx + 12.7, ly + 3.81))
    sh.wire((lx, ly), led.pin("K"))
    rr = R(sh, "R1007", "1k", led.pin("A")[0] + 5.08, ly, 90,
           ref_at=(led.pin("A")[0] + 5.08, ly - 2.54), val_at=(led.pin("A")[0] + 5.08, ly + 2.54))
    sh.wire(led.pin("A"), rr.pin(1))
    end = (rr.pin(2)[0] + 2.54, rr.pin(2)[1])
    sh.wire(rr.pin(2), end)
    sh.power("+5V", end[0], end[1], 270)
    # OP7 spare test point.
    tx, ty = drop("17", 15.24, 180.34)
    tp = sh.sym("Connector:TestPoint", "TP1001", "OP7", tx + 10.16, ty, 0, fp=TP,
                ref_at=(tx + 12.7, ty - 2.54), val_at=(tx + 12.7, ty))
    sh.wire((tx, ty), tp.pin(1))

    # CS idle-high pull-ups on the 5 V side (reset already drives OP high; these cover power-up).
    pullup_bank(sh, [("R1002", "10k", "SPI_CS0_5"), ("R1003", "10k", "SPI_CS1_5")], 248.92, 165.1)

    # ----- 74LVC125, +3V3, OE tied low (enabled). Four gates: SCK, MOSI, CS0, CS1.
    lvc_fp = {"MPN": "SN74LVC125ADR"}
    gates = [
        (1, "2", "1", "3", "SPI_HW_SCK", "SPI_SCK"),
        (2, "5", "4", "6", "SPI_HW_MOSI", "SPI_MOSI"),
        (3, "9", "10", "8", "SPI_CS0_5", "SPI_CS_NIC"),
        (4, "12", "13", "11", "SPI_CS1_5", "SPI_CS_RTC"),
    ]
    xg = 292.1
    for i, (unit, a_n, oe_n, y_n, anet, ynet) in enumerate(gates):
        y = 40.64 + i * 20.32
        g = sh.sym("74xx:74LVC125", "U22", "SN74LVC125ADR", xg, y, unit=unit, fp=SOIC14, ds=DS_LVC,
                   fields=lvc_fp, ref_at=(xg - 2.54, y - 5.08), val_at=(xg - 2.54, y + 5.08))
        g.to_label(a_n, anet, length=7.62)
        g.to_label(y_n, ynet, length=7.62)
        g.to_power(oe_n, "GND", length=2.54)
    # Power unit is below the gates. Gate 4's OE-to-GND stub sits just under that gate;
    # parking VCC/GND on the same x at the next grid up shorts pin 14 to that stub.
    pwr = sh.sym("74xx:74LVC125", "U22", "SN74LVC125ADR", xg, 152.4, unit=5, fp=SOIC14, ds=DS_LVC,
                 fields=lvc_fp, ref_at=(xg + 10.16, 139.7), val_at=(xg + 10.16, 165.1))
    pwr.to_power("14", "+3V3", length=3.81)
    pwr.to_power("7", "GND", length=3.81)
    cap_row(sh, [("C1003", "100n", C0603)], xg + 17.78, 152.4, 10.16, top="+3V3")

    # ----- DS3234, VCC = +3V3 (VIH = 0.7*VCC; a 5 V part would not see a valid high from the LVC125)
    rtc = sh.sym("m68030-sbc:DS3234", "U23", "DS3234S#", 355.6, 175.26, unit=1, fp=SOIC20, ds=DS_RTC,
                 fields={"MPN": "DS3234S#"}, ref_at=(340.36, 152.4), val_at=(340.36, 200.66))
    rtc.to_label("1", "SPI_CS_RTC", length=10.16)
    rtc.to_label("17", "SPI_MOSI", length=10.16)
    rtc.to_label("18", "SPI_SCK", length=10.16)
    rtc.to_label("20", "SPI_SCK", length=10.16)
    rtc.to_label("19", "SPI_HW_MISO", length=10.16)
    rtc.to_nc("3")   # 32 kHz push-pull; unused. Low if EN32kHz or BB32kHz is cleared.
    rtc.to_nc("6")   # open-drain RST, internal ~50k to VCC. No external pull-up (datasheet).
    rtc.to_power("4", "+3V3", length=5.08)
    rtc.to_power("15", "GND", length=5.08)
    # INT/SQW open-drain, defaults to interrupt with alarms off. Pull-up, not routed (no spare IRQ).
    ix, iy = rtc.pin("5")
    dx, dy = rtc.pdir("5")
    # straight left, clear of the CS/DIN stubs, then the pull-up sits above that run
    ex, ey = snap(ix + dx * 30.48), snap(iy + dy * 30.48)
    sh.wire((ix, iy), (ex, ey))
    sh.label("RTC_INT", ex, ey, 180)
    r = R(sh, "R1008", "10k", ex, ey - 10.16, 0,
          ref_at=(ex + 3.81, ey - 10.16), val_at=(ex + 3.81, ey - 7.62))
    top, bot = r.pin(1), r.pin(2)
    upper, lower = (top, bot) if top[1] < bot[1] else (bot, top)
    sh.wire(upper, (upper[0], upper[1] - 2.54))
    sh.power("+3V3", upper[0], upper[1] - 2.54, 0)
    sh.wire(lower, (ex, ey))
    tp = sh.sym("Connector:TestPoint", "TP1002", "RTC_INT", ex - 10.16, ey, 0, fp=TP,
                ref_at=(ex - 7.62, ey - 3.81), val_at=(ex - 7.62, ey - 1.27))
    sh.wire((ex, ey), tp.pin(1))
    # VBAT, no series diode (19-5339: a diode causes improper operation)
    bx_, by_ = rtc.pin("16")
    dx, dy = rtc.pdir("16")
    vx, vy = snap(bx_ + dx * 12.7), snap(by_ + dy * 12.7)
    sh.wire((bx_, by_), (vx, vy))
    sh.label("VBAT", vx, vy, 180 if dx < 0 else 0)
    bat = sh.sym("Device:Battery", "BT1", "CR2032", vx - 15.24, vy + 10.16, 0, fp=BATT,
                 fields={"MPN": "Keystone 103"}, ref_at=(vx - 20.32, vy + 5.08), val_at=(vx - 10.16, vy + 5.08))
    sh.wire(bat.pin(1), (bat.pin(1)[0], bat.pin(1)[1] - 5.08))
    sh.label("VBAT", bat.pin(1)[0], bat.pin(1)[1] - 5.08, 270)
    sh.wire(bat.pin(2), (bat.pin(2)[0], bat.pin(2)[1] + 2.54))
    sh.power("GND", bat.pin(2)[0], bat.pin(2)[1] + 2.54, 0)
    nc = sh.sym("m68030-sbc:DS3234", "U23", "DS3234S#", 355.6, 228.6, unit=2, fp=SOIC20, ds=DS_RTC,
                fields={"MPN": "DS3234S#"}, ref_at=(340.36, 210.82), val_at=(340.36, 248.92))
    gnd_rail(sh, nc, ["2", "7", "8", "9", "10", "11", "12", "13", "14"])
    cap_row(sh, [("C1004", "100n", C0603)], 393.7, 200.66, 10.16, top="+3V3")

    # ----- FTDI TTL-232 cable headers. Pin 3 (cable VCC) is not tied to the board.
    def ftdi(ref, y, tx, rx, rts, cts):
        j = sh.sym("Connector_Generic:Conn_01x06", ref, "TTL-232", 228.6, y, 0, fp=HDR6,
                   ref_at=(233.68, y - 7.62), val_at=(233.68, y + 10.16))
        j.to_power("1", "GND", length=5.08)
        j.to_label("2", rts, length=10.16)   # cable CTS input = our RTS
        j.to_nc("3")                          # cable VCC, do not back-feed
        j.to_label("4", rx, length=10.16)    # cable TXD = our RX
        j.to_label("5", tx, length=10.16)    # cable RXD = our TX
        j.to_label("6", cts, length=10.16)   # cable RTS = our CTS
    ftdi("J7", 78.74, "TXDA", "RXDA", "RTSA", "CTSA")
    ftdi("J8", 114.3, "TXDB", "RXDB", "RTSB", "CTSB")

    # ----- J9 2x5, pin order matches bom.csv: 3V3, 5V, GND, SCK, MOSI, MISO, CS, INT, RST, GND
    j9 = sh.sym("Connector_Generic:Conn_02x05_Odd_Even", "J9", "SPI NIC", 78.74, 210.82, 0, fp=HDR10,
                ref_at=(83.82, 198.12), val_at=(83.82, 226.06))
    j9.to_power("1", "+3V3", length=7.62)
    j9.to_power("2", "+5V", length=7.62)
    j9.to_power("3", "GND", length=7.62)
    j9.to_label("4", "SPI_SCK", length=10.16)
    j9.to_label("5", "SPI_MOSI", length=10.16)
    j9.to_label("6", "SPI_HW_MISO", length=10.16)
    j9.to_label("7", "SPI_CS_NIC", length=10.16)
    # INT is 3.3 V open-drain from the module. ATF1508 VIH min is 2.0 V, so no shifter.
    j9.to_label("8", "NIC_INT_n", length=12.7, hier="output")
    j9.to_label("9", "NIC_RST", length=10.16)
    j9.to_power("10", "GND", length=7.62)
    pullup_bank(sh, [("R1004", "10k", "NIC_INT_n")], 25.4, 200.66, rail="+3V3", hier="output")

    # PERIPH_RST_n is push-pull 5 V. Series 1.0k into 2.2k to GND -> 3.44 V at the module.
    # The pulldown is on the divided node, not on PERIPH_RST_n.
    rs = R(sh, "R1005", "1.0k", 152.4, 210.82, 0, ref_at=(156.0, 207.0), val_at=(156.0, 214.6))
    t, b = rs.pin(1), rs.pin(2)
    upper, lower = (t, b) if t[1] < b[1] else (b, t)
    sh.wire(upper, (upper[0], upper[1] - 5.08))
    sh.hlabel("PERIPH_RST_n", "input", upper[0], upper[1] - 5.08, 90)
    sh.wire(lower, (lower[0], lower[1] + 2.54))
    sh.label("NIC_RST", lower[0] + 5.08, lower[1] + 2.54, 0)
    sh.wire((lower[0], lower[1] + 2.54), (lower[0] + 5.08, lower[1] + 2.54))
    rd = R(sh, "R1006", "2.2k", lower[0], lower[1] + 10.16, 0,
           ref_at=(lower[0] + 4.0, lower[1] + 10.16), val_at=(lower[0] + 4.0, lower[1] + 12.7))
    t, b = rd.pin(1), rd.pin(2)
    up, lo = (t, b) if t[1] < b[1] else (b, t)
    sh.wire(up, (lower[0], lower[1] + 2.54))
    sh.power("GND", lo[0], lo[1], 0)

    cap_row(sh, [("C1001", "100n", C0805), ("C1002", "10u", C1206)], 40.64, 250.0, 12.7)
    sh.text("U6 decoupling (one VCC pin, PLCC pin 44)", 30.48, 232.0, 1.0)

    sh.text("SC26C92A1A  (spec §8.3). Kept. 2 wait states still hold; glue not refit.", 17.78, 12.7, 1.8, bold=True)
    sh.text("J7/J8 TTL-232: 1 GND, 2 CTS from our RTS, 3 cable VCC left open, 4 TXD to our RX, 5 RXD from our TX, 6 RTS to our CTS.",
            165.1, 236.22, 1.0)
    sh.text("J9 pins: 1 +3V3, 2 +5V, 3 GND, 4 SCK, 5 MOSI, 6 MISO, 7 CS, 8 INT, 9 RST, 10 GND. SPI is 3.3 V.",
            165.1, 240.0, 1.0)
    return sh
