# Generates provisional ATF1508AS-7JX84 (PLCC-84) pin maps and checks the budget.
# Pin facts from Atmel/Microchip doc0784 (ATF1508AS datasheet) PLCC-84 pinout table.
DED = {1:"INPUT/GCLR", 2:"INPUT/OE2/GCLK2", 83:"INPUT/GCLK1", 84:"INPUT/OE1"}
VCC = [3,43,13,26,38,53,66,78]
GND = [7,19,32,42,47,59,72,82]
JTAG = {14:"TDI", 23:"TMS", 62:"TCK", 71:"TDO"}
IO = [p for p in range(1,85) if p not in DED and p not in VCC and p not in GND and p not in JTAG]
assert len(IO) == 60, len(IO)
# order I/O pins by package side (PLCC pin 1 at top-centre, counter-clockwise numbering)
def side(p):
    if p>=75 or p<=11: return "top"
    if p<=32: return "left"
    if p<=53: return "bottom"
    return "right"

glue_ded = {83:"CPU_CLK (GCLK1)", 84:"AS_n (OE1 used as input)", 2:"DS_n (OE2/GCLK2 used as input)", 1:"PWR_RST_n (GCLR)"}
glue = [
 # (signal, dir, group)
 ("A31","in","addr"),("A30","in","addr"),("A29","in","addr"),("A28","in","addr"),("A27","in","addr"),
 ("A19","in","addr"),("A18","in","addr"),("A17","in","addr"),("A16","in","addr"),
 ("A15","in","addr"),("A14","in","addr"),("A13","in","addr"),
 ("A3","in","addr"),("A2","in","addr"),("A1","in","addr"),
 ("FC2","in","cpu"),("FC1","in","cpu"),("FC0","in","cpu"),("R_W","in","cpu"),
 ("DSACK0_n","tri-state out","cpu"),("DSACK1_n","tri-state out","cpu"),
 ("BERR_n","open-drain out","cpu"),("AVEC_n","open-drain out","cpu"),("CIIN_n","open-drain out","cpu"),
 ("IPL0_n","out","cpu"),("IPL1_n","out","cpu"),("IPL2_n","out","cpu"),
 ("RESET_n","bidir open-drain","cpu"),("HALT_n","open-drain out","cpu"),
 ("DRAM_SEL_n","out","sel"),("FPU_CS_n","out","sel"),("ROM_CE_n","out","sel"),
 ("BUS_RD_n","out","sel"),("BUS_WR_n","out","sel"),("DUART_CS_n","out","sel"),
 ("IDE_CS0_n","out","sel"),("IDE_CS1_n","out","sel"),("IDE_DIOR_n","out","sel"),("IDE_DIOW_n","out","sel"),
 ("IDE_BUF_EN_n","out","sel"),("EXP_SEL_n","out","sel"),("EXP_BUF_EN_n","out","sel"),
 ("IDE_INTRQ","in","irq"),("IDE_IORDY","in","irq"),("DUART_INT_n","in","irq"),("NIC_INT_n","in","irq"),
 ("EXP_INT_n","in","irq"),("NMI_BTN_n","in","irq"),
 ("PERIPH_RST_n","out","misc"),("DUART_RST","out","misc"),("LED_n","out","misc"),
 ("WARM_RST_BTN_n","in","misc"),("STATUS_n","in","misc"),("HALT_LED_n","out","misc"),
 ("SPI_HW_SCK","out (reserved)","misc"),("SPI_HW_MOSI","out (reserved)","misc"),("SPI_HW_MISO","in (reserved)","misc"),
]
dram_ded = {83:"DRAM_CLK 50 MHz (GCLK1)", 2:"CPU_CLK (GCLK2, for optional synchronous mode)", 84:"AS_n (OE1 used as input)", 1:"PWR_RST_n (GCLR)"}
dram = [(f"A{i}","in","addr") for i in range(26,1,-1)] + [
 ("A1","in","addr"),("A0","in","addr"),("SIZ1","in","cpu"),("SIZ0","in","cpu"),
 ("DS_n","in","cpu"),("R_W","in","cpu"),("DRAM_SEL_n","in","cpu"),
 ("DSACK0_n","tri-state out","cpu"),("DSACK1_n","tri-state out","cpu"),
 ("STERM_n","tri-state out (reserved, held off)","cpu"),("CBREQ_n","in (reserved)","cpu"),("CBACK_n","tri-state out (reserved, held off)","cpu"),
] + [(f"MA{i}","out","simm") for i in range(12)] + [(f"RAS{i}_n","out","simm") for i in range(4)] + [(f"CAS{i}_n","out","simm") for i in range(4)] + [("WE_n","out","simm")]

def assign(sigs, pref):
    order = sorted(IO, key=lambda p: (["left","top","right","bottom"].index(side(p)) if pref=="glue" else ["right","bottom","left","top"].index(side(p)), p))
    out=[]
    for (s,d,g),p in zip(sigs, order):
        out.append((p,side(p),s,d,g))
    spare=[p for p in order[len(sigs):]]
    return out, spare

for name, ded, sigs in (("glue",glue_ded,glue),("dram",dram_ded,dram)):
    rows, spare = assign(sigs, name)
    print(f"## {name}: {len(sigs)} of 60 I/O used, {60-len(sigs)} spare; dedicated inputs 4/4")
    print("| Pin | Pin function | Side | Signal | Dir |")
    print("|---|---|---|---|---|")
    for p,f in sorted(ded.items()):
        print(f"| {p} | {DED[p]} | {side(p)} | {f} | in |")
    for p,sd,s,d,g in sorted(rows):
        fn = "I/O/GCLK3" if p==81 else ("I/O/PD1" if p==12 else ("I/O/PD2" if p==45 else "I/O"))
        print(f"| {p} | {fn} | {sd} | {s} | {d} |")
    for p in sorted(spare):
        print(f"| {p} | I/O | {side(p)} | spare (test point) | - |")
    print()
print("JTAG (both chips):", JTAG, " VCCINT 3,43; VCCIO 13,26,38,53,66,78; GND", GND)
