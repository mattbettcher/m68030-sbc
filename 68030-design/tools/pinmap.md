## glue: 57 of 60 I/O used, 3 spare; dedicated inputs 4/4
| Pin | Pin function | Side | Signal | Dir |
|---|---|---|---|---|
| 1 | INPUT/GCLR | top | PWR_RST_n (GCLR) | in |
| 2 | INPUT/OE2/GCLK2 | top | DS_n (OE2/GCLK2 used as input) | in |
| 83 | INPUT/GCLK1 | top | CPU_CLK (GCLK1) | in |
| 84 | INPUT/OE1 | top | AS_n (OE1 used as input) | in |
| 4 | I/O | top | FC2 | in |
| 5 | I/O | top | FC1 | in |
| 6 | I/O | top | FC0 | in |
| 8 | I/O | top | R_W | in |
| 9 | I/O | top | DSACK0_n | tri-state out |
| 10 | I/O | top | DSACK1_n | tri-state out |
| 11 | I/O | top | BERR_n | open-drain out |
| 12 | I/O/PD1 | left | A31 | in |
| 15 | I/O | left | A30 | in |
| 16 | I/O | left | A29 | in |
| 17 | I/O | left | A28 | in |
| 18 | I/O | left | A27 | in |
| 20 | I/O | left | A19 | in |
| 21 | I/O | left | A18 | in |
| 22 | I/O | left | A17 | in |
| 24 | I/O | left | A16 | in |
| 25 | I/O | left | A15 | in |
| 27 | I/O | left | A14 | in |
| 28 | I/O | left | A13 | in |
| 29 | I/O | left | A3 | in |
| 30 | I/O | left | A2 | in |
| 31 | I/O | left | A1 | in |
| 33 | I/O | bottom | DUART_INT_n | in |
| 34 | I/O | bottom | NIC_INT_n | in |
| 35 | I/O | bottom | EXP_INT_n | in |
| 36 | I/O | bottom | NMI_BTN_n | in |
| 37 | I/O | bottom | PERIPH_RST_n | out |
| 39 | I/O | bottom | DUART_RST | out |
| 40 | I/O | bottom | LED_n | out |
| 41 | I/O | bottom | WARM_RST_BTN_n | in |
| 44 | I/O | bottom | STATUS_n | in |
| 45 | I/O/PD2 | bottom | HALT_LED_n | out |
| 46 | I/O | bottom | SPI_HW_SCK | out (reserved) |
| 48 | I/O | bottom | SPI_HW_MOSI | out (reserved) |
| 49 | I/O | bottom | SPI_HW_MISO | in (reserved) |
| 54 | I/O | right | HALT_n | open-drain out |
| 55 | I/O | right | DRAM_SEL_n | out |
| 56 | I/O | right | FPU_CS_n | out |
| 57 | I/O | right | ROM_CE_n | out |
| 58 | I/O | right | BUS_RD_n | out |
| 60 | I/O | right | BUS_WR_n | out |
| 61 | I/O | right | DUART_CS_n | out |
| 63 | I/O | right | IDE_CS0_n | out |
| 64 | I/O | right | IDE_CS1_n | out |
| 65 | I/O | right | IDE_DIOR_n | out |
| 67 | I/O | right | IDE_DIOW_n | out |
| 68 | I/O | right | IDE_BUF_EN_n | out |
| 69 | I/O | right | EXP_SEL_n | out |
| 70 | I/O | right | EXP_BUF_EN_n | out |
| 73 | I/O | right | IDE_INTRQ | in |
| 74 | I/O | right | IDE_IORDY | in |
| 75 | I/O | top | AVEC_n | open-drain out |
| 76 | I/O | top | CIIN_n | open-drain out |
| 77 | I/O | top | IPL0_n | out |
| 79 | I/O | top | IPL1_n | out |
| 80 | I/O | top | IPL2_n | out |
| 81 | I/O/GCLK3 | top | RESET_n | bidir open-drain |
| 50 | I/O | bottom | spare (test point) | - |
| 51 | I/O | bottom | spare (test point) | - |
| 52 | I/O | bottom | spare (test point) | - |

## dram: 58 of 60 I/O used, 2 spare; dedicated inputs 4/4
| Pin | Pin function | Side | Signal | Dir |
|---|---|---|---|---|
| 1 | INPUT/GCLR | top | PWR_RST_n (GCLR) | in |
| 2 | INPUT/OE2/GCLK2 | top | CPU_CLK (GCLK2, for optional synchronous mode) | in |
| 83 | INPUT/GCLK1 | top | DRAM_CLK 50 MHz (GCLK1) | in |
| 84 | INPUT/OE1 | top | AS_n (OE1 used as input) | in |
| 4 | I/O | top | MA10 | out |
| 5 | I/O | top | MA11 | out |
| 6 | I/O | top | RAS0_n | out |
| 8 | I/O | top | RAS1_n | out |
| 9 | I/O | top | RAS2_n | out |
| 10 | I/O | top | RAS3_n | out |
| 11 | I/O | top | CAS0_n | out |
| 12 | I/O/PD1 | left | DSACK0_n | tri-state out |
| 15 | I/O | left | DSACK1_n | tri-state out |
| 16 | I/O | left | STERM_n | tri-state out (reserved, held off) |
| 17 | I/O | left | CBREQ_n | in (reserved) |
| 18 | I/O | left | CBACK_n | tri-state out (reserved, held off) |
| 20 | I/O | left | MA0 | out |
| 21 | I/O | left | MA1 | out |
| 22 | I/O | left | MA2 | out |
| 24 | I/O | left | MA3 | out |
| 25 | I/O | left | MA4 | out |
| 27 | I/O | left | MA5 | out |
| 28 | I/O | left | MA6 | out |
| 29 | I/O | left | MA7 | out |
| 30 | I/O | left | MA8 | out |
| 31 | I/O | left | MA9 | out |
| 33 | I/O | bottom | A10 | in |
| 34 | I/O | bottom | A9 | in |
| 35 | I/O | bottom | A8 | in |
| 36 | I/O | bottom | A7 | in |
| 37 | I/O | bottom | A6 | in |
| 39 | I/O | bottom | A5 | in |
| 40 | I/O | bottom | A4 | in |
| 41 | I/O | bottom | A3 | in |
| 44 | I/O | bottom | A2 | in |
| 45 | I/O/PD2 | bottom | A1 | in |
| 46 | I/O | bottom | A0 | in |
| 48 | I/O | bottom | SIZ1 | in |
| 49 | I/O | bottom | SIZ0 | in |
| 50 | I/O | bottom | DS_n | in |
| 51 | I/O | bottom | R_W | in |
| 52 | I/O | bottom | DRAM_SEL_n | in |
| 54 | I/O | right | A26 | in |
| 55 | I/O | right | A25 | in |
| 56 | I/O | right | A24 | in |
| 57 | I/O | right | A23 | in |
| 58 | I/O | right | A22 | in |
| 60 | I/O | right | A21 | in |
| 61 | I/O | right | A20 | in |
| 63 | I/O | right | A19 | in |
| 64 | I/O | right | A18 | in |
| 65 | I/O | right | A17 | in |
| 67 | I/O | right | A16 | in |
| 68 | I/O | right | A15 | in |
| 69 | I/O | right | A14 | in |
| 70 | I/O | right | A13 | in |
| 73 | I/O | right | A12 | in |
| 74 | I/O | right | A11 | in |
| 75 | I/O | top | CAS1_n | out |
| 76 | I/O | top | CAS2_n | out |
| 77 | I/O | top | CAS3_n | out |
| 79 | I/O | top | WE_n | out |
| 80 | I/O | top | spare (test point) | - |
| 81 | I/O | top | spare (test point) | - |

JTAG (both chips): {14: 'TDI', 23: 'TMS', 62: 'TCK', 71: 'TDO'}  VCCINT 3,43; VCCIO 13,26,38,53,66,78; GND [7, 19, 32, 42, 47, 59, 72, 82]
