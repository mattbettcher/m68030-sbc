"""Inter-sheet signal list (hierarchical labels / sheet pins), from spec.md §1.2 table, §4.2/§4.3 CPLD pin
tables, §7.2 reset and §8.4 LA list.  (name, shape) ; shapes: input, output, bidirectional, tri_state, passive.
Left column of each sheet symbol = inputs; right column = outputs / bidirectional."""
AB = ("A[0..31]", "input")
ABo = ("A[0..31]", "output")
DB = ("D[0..31]", "bidirectional")
I = lambda *n: [(x, "input") for x in n]
O = lambda *n: [(x, "output") for x in n]
B = lambda *n: [(x, "bidirectional") for x in n]
T = lambda *n: [(x, "tri_state") for x in n]
P = lambda *n: [(x, "passive") for x in n]
IPL = ["IPL0_n", "IPL1_n", "IPL2_n"]
FC = ["FC0", "FC1", "FC2"]
SIZ = ["SIZ0", "SIZ1"]

SHEETS = {
 "power": dict(L=[], R=[]),
 "clock": dict(L=[], R=O("CLK_CPU", "CLK_FPU", "CLK_GLUE", "CLK_DRAMC", "CLK_LA", "CLK_EXP", "DRAM_CLK") + P("DUART_X1", "DUART_X2")),
 "reset": dict(L=[], R=O("PWR_RST_n", "WARM_RST_BTN_n", "NMI_BTN_n") + B("RESET_n", "HALT_n")),
 "cpu": dict(
    L=I("CLK_CPU", "DSACK0_n", "DSACK1_n", "STERM_n", "CBACK_n", "CIIN_n", "AVEC_n", "BERR_n", "HALT_n") + I(*IPL) + I("BR_n", "BGACK_n"),
    R=[ABo, DB] + O(*FC) + O(*SIZ) + O("R_W", "AS_n", "DS_n", "RMC_n", "ECS_n", "OCS_n", "CBREQ_n", "IPEND_n", "STATUS_n", "REFILL_n", "BG_n") + B("RESET_n")),
 "fpu": dict(L=[AB] + I("AS_n", "DS_n", "R_W", "FPU_CS_n", "RESET_n", "CLK_FPU"), R=[DB] + T("DSACK0_n", "DSACK1_n")),
 "glue_cpld": dict(
    L=[AB] + I("CLK_GLUE", "PWR_RST_n", "AS_n", "DS_n", "R_W") + I(*FC) + I("STATUS_n", "WARM_RST_BTN_n", "NMI_BTN_n",
      "DUART_INT_n", "NIC_INT_n", "EXP_INT_n", "IDE_INTRQ", "IDE_IORDY", "SPI_HW_MISO"),
    R=T("DSACK0_n", "DSACK1_n") + O("BERR_n", "HALT_n", "AVEC_n", "CIIN_n") + O(*IPL) + B("RESET_n") +
      O("DRAM_SEL_n", "FPU_CS_n", "ROM_CE_n", "BUS_RD_n", "BUS_WR_n", "DUART_CS_n", "DUART_RST", "PERIPH_RST_n",
        "IDE_CS0_n", "IDE_CS1_n", "IDE_DA0", "IDE_DA1", "IDE_DA2", "IDE_DIOR_n", "IDE_DIOW_n", "IDE_BUF_EN_n",
        "EXP_SEL_n", "EXP_BUF_EN_n", "LED_n", "HALT_LED_n", "SPI_HW_SCK", "SPI_HW_MOSI")),
 "dram": dict(
    L=[AB] + I("CLK_DRAMC", "DRAM_CLK", "PWR_RST_n", "AS_n", "DS_n", "R_W") + I(*SIZ) + I("DRAM_SEL_n", "CBREQ_n"),
    R=[DB] + T("DSACK0_n", "DSACK1_n", "STERM_n", "CBACK_n") + O("SIMM_PD1", "SIMM_PD2", "SIMM_PD3", "SIMM_PD4", "RAS0_n", "CAS3_n", "WE_n")),
 "rom": dict(L=[AB] + I("ROM_CE_n", "BUS_RD_n", "BUS_WR_n"), R=[DB]),
 "duart_spi_rtc": dict(
    L=[AB] + I("DUART_CS_n", "BUS_RD_n", "BUS_WR_n", "DUART_RST", "PERIPH_RST_n", "SIMM_PD1", "SIMM_PD2", "SIMM_PD3", "SIMM_PD4",
      "SPI_HW_SCK", "SPI_HW_MOSI") + P("DUART_X1", "DUART_X2"),
    R=[DB] + O("DUART_INT_n", "NIC_INT_n", "SPI_HW_MISO")),
 "ide": dict(L=I("IDE_CS0_n", "IDE_CS1_n", "IDE_DA0", "IDE_DA1", "IDE_DA2", "IDE_DIOR_n", "IDE_DIOW_n", "IDE_BUF_EN_n",
               "R_W", "PERIPH_RST_n"),
             R=[DB] + O("IDE_INTRQ", "IDE_IORDY")),
 "expansion": dict(
    L=[AB] + I(*FC) + I(*SIZ) + I("R_W", "AS_n", "DS_n", "EXP_SEL_n", "EXP_BUF_EN_n", "CLK_EXP", "PERIPH_RST_n", "BG_n"),
    R=[DB] + O("EXP_INT_n", "BR_n", "BGACK_n") + B("DSACK0_n", "DSACK1_n", "BERR_n", "HALT_n")),
 "debug": dict(
    L=[AB, ("D[0..31]", "input")] + I("CLK_LA", "AS_n", "DS_n", "R_W", "SIZ1", "SIZ0", "FC2", "FC1", "FC0", "DSACK1_n", "DSACK0_n",
      "BERR_n", "HALT_n", "RESET_n", "STERM_n", "CIIN_n", "CBREQ_n", "CBACK_n", "AVEC_n", "IPL2_n", "IPL1_n", "IPL0_n",
      "IPEND_n", "STATUS_n", "REFILL_n", "ECS_n", "OCS_n", "RMC_n", "DRAM_SEL_n", "RAS0_n", "CAS3_n", "WE_n", "LED_n", "HALT_LED_n"),
    R=[]),
}
TITLES = {
 "power": "Power: 9-24 V input, LM2678-5.0 buck, AMS1117-3.3",
 "clock": "Clocks: CPU oscillator + 74ACT244 fan-out, DRAM 50 MHz, FPU option, DUART crystal",
 "reset": "Reset: TPS3702CX50 window + TPS3808G50 supervisor, buttons, RESET/HALT pull-ups",
 "cpu": "CPU: MC68030 PGA-128",
 "fpu": "FPU: MC68882 PLCC-68",
 "glue_cpld": "Glue/system CPLD U3 (ATF1508AS) — STUB",
 "dram": "DRAM controller CPLD U4 + 72-pin SIMM",
 "rom": "Boot flash SST39SF040",
 "duart_spi_rtc": "DUART SC26C92, bit-bang SPI, DS3234, NIC header",
 "ide": "IDE / CompactFlash",
 "expansion": "Expansion connector J10 (DIN41612)",
 "debug": "Logic-analyzer headers J11-J13",
}
SPECREF = {
 "glue_cpld": "spec.md §4.2 (U3 pin table), §2 decode, §3 bus cycles, §3.5 interrupts",
 "dram": "spec.md §4.3 (U4 pin table), §5 DRAM controller, §5.1 SIMM pinout",
 "rom": "spec.md §1.2 row 7, §2.2 boot overlay, §3.2 flash timing",
 "duart_spi_rtc": "spec.md §8.3 (SC26C92 PLCC-44 pins), §1.4/§1.5 SPI NIC + DS3234 RTC",
 "ide": "spec.md §1.2 row 9, §3.2 ATA PIO-0 timing (DA2:0 from U3 pins 50-52 since Rev A.1)",
 "expansion": "spec.md §1.2 row 10, §10 risk 18 (J10 pinout still to be written)",
 "debug": "spec.md §8.4 (LA1-LA3 signal list)",
}
ORDER = ["power", "clock", "reset", "cpu", "fpu", "glue_cpld", "dram", "rom", "duart_spi_rtc", "ide", "expansion", "debug"]
