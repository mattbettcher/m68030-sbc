"""Boot flash sheet. SST39SF040-70-4C-NHE, PLCC-32 pinout DS20005022C Figure 2.
8-bit on CPU D31-D24 (flash DQ0 = D24). CE# = ROM_CE_n, OE# = BUS_RD_n,
WE# = BUS_WR_n (glue asserts BUS_WR_n only when FLASH_WE = 1, spec §2.4)."""
from build_common import *
from sheet_cpu import bus_side

PLCC_SOCK = "Package_LCC:PLCC-32_THT-Socket"
DS = "https://ww1.microchip.com/downloads/en/DeviceDoc/20005022C.pdf"

def build_rom(P):
    sh = P.sub("rom", "Boot flash: SST39SF040-70 (PLCC-32) at E000_0000", 9, paper="A3")
    sh.comments = [
        "PLCC pinout: Microchip DS20005022C Fig. 2 (SST39SF040 column), not the PDIP pinout",
        "70 ns grade: Table 11 TCE/TAA 70 ns, TOE 35 ns. 1 WS at 25 MHz still holds (spec §3.2)",
        "WE# is BUS_WR_n, which the glue drives only while the FLASH_WE register is set",
    ]
    u = sh.sym("m68030-sbc:SST39SF040-PLCC32", "U5", "SST39SF040-70-4C-NHE", 168.0, 130.0,
               fp=PLCC_SOCK, ds=DS,
               fields={"MPN": "SST39SF040-70-4C-NHE", "Socket": "PLCC-32 THT socket XU5 (same footprint)"},
               ref_at=(150.0, 70.0), val_at=(150.0, 195.0))
    bx, y1, y2 = bus_side(sh, u, [("A%d" % i, "A%d" % i) for i in range(19)], "L", None, wire_len=7.62)
    sh.bus((bx, y1), (bx, 40.64), (25.4, 40.64))
    sh.hlabel("A[0..31]", "input", 25.4, 40.64, 180)
    sh.text("A0-A18 (A19-A31 are on the bus but not used by the 512 KB part; the glue alias is in the decode)", 25.4, 33.0, 1.0)
    bx, y1, y2 = bus_side(sh, u, [("DQ%d" % i, "D%d" % (24 + i)) for i in range(8)], "R", None, wire_len=7.62)
    sh.bus((bx, y1), (bx, 40.64), (300.0, 40.64))
    sh.hlabel("D[0..31]", "bidirectional", 300.0, 40.64, 0)
    sh.text("DQ0-DQ7 = CPU D24-D31 (8-bit port, DSACK0 only)", 250.0, 33.0, 1.0)
    u.to_label("~{CE}", "ROM_CE_n", length=12.7, hier="input")
    u.to_label("~{OE}", "BUS_RD_n", length=12.7, hier="input")
    u.to_label("~{WE}", "BUS_WR_n", length=12.7, hier="input")
    u.to_power("VDD", "+5V", length=5.08)
    u.to_power("VSS", "GND", length=5.08)
    cap_row(sh, [("C551", "100n", C0805), ("C552", "10u", C1206)], 250.0, 250.0, 12.7)
    sh.text("Decoupling at the socket: 100 nF + 10 uF on the one VDD pin (PLCC pin 31)", 240.0, 230.0, 1.0)
    sh.text("SST39SF040 boot ROM (spec §2.2, §3.2, §8)", 20.0, 15.0, 2.0, bold=True)
    sh.text("Orderable part SST39SF040-70-4C-NHE (PLCC-32, 70 ns, commercial). The -70-4C-PHE is the DIP-32\\n"
            "option and is NOT this pinout. Socket footprint is the PLCC-32 THT socket (BOM XU5); the chip sits in it.\\n"
            "Read timing, 25 MHz, 1 wait state, no buffer on this bus (DS20005022C Table 11, 70 ns column):\\n"
            "  TCE = TAA = 70 ns, TOE = 35 ns. CE at the pin <= 26.5 ns (spec §3.2) so data <= 96.5 ns,\\n"
            "  needed by 118 ns: 21.5 ns margin. OE path: BUS_RD at 70 ns + TOE 35 + 1 ns board = 106 ns,\\n"
            "  margin 12 ns. TRC min 70 ns; a 1-WS cycle is far longer. 33 MHz still needs ROM_WS = 2 (spec §3.2).\\n"
            "In-system program/erase: WE# is BUS_WR_n. The glue drives it only when FLASH_WE = 1 (spec §2.4).\\n"
            "Byte program completes internally within 20 us (datasheet Byte-Program section); the CPU polls DQ7/DQ6.",
            20.0, 210.0, 1.15)
    return sh
