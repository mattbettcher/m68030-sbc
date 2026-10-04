# U3 glue CPLD pinout (fit1508 v1918 result, extracted from glue.fit)

Power: VCCINT 3, 43; VCCIO 13, 26, 38, 53, 66, 78 (all +5V). GND 7, 19, 32, 42, 47, 59, 72, 82.
JTAG (enabled): TDI 14, TMS 23, TCK 62, TDO 71.

| Pin | Pin function (doc0784) | Signal (net) | Dir |
|---|---|---|---|
| 1 | GCLR (dedicated input) | PWR_RST_n | in |
| 2 | OE2/GCLK2 (dedicated input) | DS_n | in |
| 4 | I/O | FC2 | in |
| 5 | I/O | FC1 | in |
| 6 | I/O | FC0 | in |
| 8 | I/O | R_W | in |
| 9 | I/O | DSACK0_n | out, 3-state (driven only while terminating) |
| 10 | I/O | DSACK1_n | out, 3-state |
| 11 | I/O | BERR_n | out, 3-state |
| 12 | I/O/PD1 | A31 | in |
| 15 | I/O | A30 | in |
| 16 | I/O | A29 | in |
| 17 | I/O | A28 | in |
| 18 | I/O | A27 | in |
| 20 | I/O | A19 | in |
| 21 | I/O | A18 | in |
| 22 | I/O | A17 | in |
| 24 | I/O | A16 | in |
| 25 | I/O | A15 | in |
| 27 | I/O | A14 | in |
| 28 | I/O | A13 | in |
| 29 | I/O | A3 | in |
| 30 | I/O | A2 | in |
| 31 | I/O | A1 | in |
| 33 | I/O | DUART_INT_n | in |
| 34 | I/O | NIC_INT_n | in |
| 35 | I/O | EXP_INT_n | in |
| 36 | I/O | NMI_BTN_n | in |
| 37 | I/O | PERIPH_RST_n | out |
| 39 | I/O | DUART_RST | out |
| 40 | I/O | LED_n | out |
| 41 | I/O | WARM_RST_BTN_n | in |
| 44 | I/O | STATUS_n | in |
| 45 | I/O/PD2 | HALT_LED_n | out |
| 46 | I/O | reserved SPI_HW_SCK (jumper | - |
| 48 | I/O | reserved SPI_HW_MOSI (jumper | - |
| 49 | I/O | reserved SPI_HW_MISO (jumper | - |
| 50 | I/O | IDE_DA0 | out |
| 51 | I/O | IDE_DA1 | out |
| 52 | I/O | IDE_DA2 | out |
| 54 | I/O | HALT_n | out, open-drain emulated (OE) |
| 55 | I/O | DRAM_SEL_n | out |
| 56 | I/O | FPU_CS_n | out |
| 57 | I/O | ROM_CE_n | out |
| 58 | I/O | BUS_RD_n | out |
| 60 | I/O | BUS_WR_n | out |
| 61 | I/O | DUART_CS_n | out |
| 63 | I/O | IDE_CS0_n | out |
| 64 | I/O | IDE_CS1_n | out |
| 65 | I/O | IDE_DIOR_n | out |
| 67 | I/O | IDE_DIOW_n | out |
| 68 | I/O | IDE_BUF_EN_n | out |
| 69 | I/O | EXP_SEL_n | out |
| 70 | I/O | EXP_BUF_EN_n | out |
| 73 | I/O | IDE_INTRQ | in |
| 74 | I/O | IDE_IORDY | in |
| 75 | I/O | AVEC_n | out, 3-state |
| 76 | I/O | CIIN_n | out, push-pull |
| 77 | I/O | IPL0_n | out |
| 79 | I/O | IPL1_n | out |
| 80 | I/O | IPL2_n | out |
| 81 | I/O/GCLK3 | RESET_n | bidir, open-drain emulated (OE) + read back |
| 83 | GCLK1 (dedicated input) | CLK_GLUE | in |
| 84 | OE1 (dedicated input) | AS_n | in |
