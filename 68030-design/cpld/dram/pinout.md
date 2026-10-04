# U4 DRAM controller CPLD pinout (fit1508 v1918 result, extracted from dram.fit)

Power: VCCINT 3, 43; VCCIO 13, 26, 38, 53, 66, 78 (all +5V). GND 7, 19, 32, 42, 47, 59, 72, 82.
JTAG (enabled): TDI 14, TMS 23, TCK 62, TDO 71.

| Pin | Pin function (doc0784) | Signal (net) | Dir |
|---|---|---|---|
| 1 | GCLR (dedicated input) | PWR_RST_n | in |
| 2 | OE2/GCLK2 (dedicated input) | CLK_DRAMC on GCLK2 (for a future CPU-clock-synchronous FSM; unused in Rev A logic) | - |
| 4 | I/O | MA10 (via 33R) | out |
| 5 | I/O | MA11 (via 33R) | out |
| 6 | I/O | RAS0_n (via 33R) | out |
| 8 | I/O | RAS1_n (via 33R) | out |
| 9 | I/O | RAS2_n (via 33R) | out |
| 10 | I/O | RAS3_n (via 33R) | out |
| 11 | I/O | CAS0_n (via 33R) | out |
| 12 | I/O/PD1 | DSACK0_n | out, 3-state (driven only while terminating) |
| 15 | I/O | DSACK1_n | out, 3-state (driven only while terminating) |
| 16 | I/O | reserved STERM_n (solder jumper JP801 open) | - |
| 17 | I/O | reserved CBREQ_n (solder jumper JP802 open) | - |
| 18 | I/O | reserved CBACK_n (solder jumper JP803 open) | - |
| 20 | I/O | MA0 (via 33R) | out |
| 21 | I/O | MA1 (via 33R) | out |
| 22 | I/O | MA2 (via 33R) | out |
| 24 | I/O | MA3 (via 33R) | out |
| 25 | I/O | MA4 (via 33R) | out |
| 27 | I/O | MA5 (via 33R) | out |
| 28 | I/O | MA6 (via 33R) | out |
| 29 | I/O | MA7 (via 33R) | out |
| 30 | I/O | MA8 (via 33R) | out |
| 31 | I/O | MA9 (via 33R) | out |
| 33 | I/O | A10 | in |
| 34 | I/O | A9 | in |
| 35 | I/O | A8 | in |
| 36 | I/O | A7 | in |
| 37 | I/O | A6 | in |
| 39 | I/O | A5 | in |
| 40 | I/O | A4 | in |
| 41 | I/O | A3 | in |
| 44 | I/O | A2 | in |
| 45 | I/O/PD2 | A1 | in |
| 46 | I/O | A0 | in |
| 48 | I/O | SIZ1 | in |
| 49 | I/O | SIZ0 | in |
| 50 | I/O | reserved DS_n (solder jumper JP804 open) | - |
| 51 | I/O | R_W | in |
| 52 | I/O | DRAM_SEL_n | in |
| 54 | I/O | A26 | in |
| 55 | I/O | A25 | in |
| 56 | I/O | A24 | in |
| 57 | I/O | A23 | in |
| 58 | I/O | A22 | in |
| 60 | I/O | A21 | in |
| 61 | I/O | A20 | in |
| 63 | I/O | A19 | in |
| 64 | I/O | A18 | in |
| 65 | I/O | A17 | in |
| 67 | I/O | A16 | in |
| 68 | I/O | A15 | in |
| 69 | I/O | A14 | in |
| 70 | I/O | A13 | in |
| 73 | I/O | A12 | in |
| 74 | I/O | A11 | in |
| 75 | I/O | CAS1_n (via 33R) | out |
| 76 | I/O | CAS2_n (via 33R) | out |
| 77 | I/O | CAS3_n (via 33R) | out |
| 79 | I/O | WE_n (via 33R) | out |
| 80 | I/O | MUX_SEL | out |
| 81 | I/O/GCLK3 | spare I/O/GCLK3 (test point TP809) | - |
| 83 | GCLK1 (dedicated input) | DRAM_CLK | in |
| 84 | OE1 (dedicated input) | AS_n | in |
