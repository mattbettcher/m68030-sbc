# m68030-sbc — KiCad project notes

Project: `m68030-sbc.kicad_pro` / `m68030-sbc.kicad_sch` (hierarchical, 13 pages). Design spec: `../spec.md`, BOM: `../bom.csv`.

- **KiCad version:** made with and checked in **KiCad 9.0.2** (Debian apt `kicad`, `kicad-cli 9.0.2`). Native schematic format is `version 20250114`, generator_version "9.0".
- **KiCad 10:** the project also opens in KiCad 10.0.6 (flatpak). Running ERC there gave the same findings, plus 3 `lib_symbol_mismatch` warnings on the solder-jumper symbols (the KiCad 10 stock library changed them; harmless). KiCad 10 also splits some `label_dangling` into a new `isolated_pin_label` category.
- **How the files were made:** the schematics are **generated** by `tools/build.py`, which uses the helper modules in `tools/` (`kgen.py`, `project.py`, `sheet_*.py`, `signals.py`, `mklib.py`). `tools/render.sh` regenerates the schematics, runs ERC and exports `out/`.
  - Once you start editing by hand in Eeschema, **stop regenerating**: `build.py` overwrites the `.kicad_sch` files.
  - `tools/mklib.py` builds `lib/m68030-sbc.kicad_sym`.
  - `tools/um_pga.py` is my independent transcription of the MC68030 PGA pinout.

## Sheets

| Page | Sheet | Status |
|---|---|---|
| 1 | root (`m68030-sbc.kicad_sch`, A2) | 12 sheet symbols with all inter-sheet pins, net labels, mounting holes H1–H4, attribution note |
| 2 | `power` | **Drawn.** J2 jack → F1 T5A → Q1 SUD50P04-08 reverse-polarity P-FET (R201, D3 12 V gate clamp) → VIN (D2 SMBJ28CA, TP201, C201–C204) → U8 LM2678S-5.0 (C205 CB, D1 B540C, L1 22 µH, C206–C208 3×100 µF tantalum, SJ201 ON/OFF disable) → JP202 → +5V (PWR_FLAG, TP202, D4/R202 LED, J3 bench input DNP) → U9 AMS1117-3.3 (C209/C210, TP203) → +3V3; TP204 GND |
| 3 | `clock` | **Drawn.** X1 25 MHz socketed DIP-14 can → U10 74ACT244 (all 8 inputs tied, 6 outputs used) → R301–R306 33 Ω series → CLK_CPU/GLUE/DRAMC/LA/EXP; R302 → JP3 FPU clock select (1-2 CPU, 2-3 X3); X3 + R308 + C304 DNP; X2 50 MHz → R307 → DRAM_CLK; Y1 3.6864 MHz + C307/C308 → DUART_X1/X2 (placed at U6) |
| 4 | `reset` | **Drawn.** U7 TPS3702CX50 (JP401 SET select) UV/OV open-drain wired-OR + R401 + SW3 → U27 TPS3808G50 MR; CT 100 k to VDD; RESET → PWR_RST_n (R403). SW1/SW2 → WARM_RST_BTN_n / NMI_BTN_n (R404/R405). R406/R407 1 k pull-ups on RESET_n / HALT_n |
| 5 | `cpu` | **Drawn.** U1 MC68030 in 3 units: A/D buses to A[0..31]/D[0..31]; control/status; power (10 VCC, 14 GND, 5 NC with no-connect flags). R501–R514 pull-ups, JP1 CDIS / JP2 MMUDIS headers, TP501–503 (CIOUT, DBEN, BG), C501–C517 decoupling, heatsink note |
| 6 | `fpu` | **Drawn** (as its own sheet). U2 MC68882 PLCC-68: A1–A4 from the bus; A0 and SIZE to VCC (32-bit port); SENSE to GND; pin 15 NC; CS/AS/DS/R_W/DSACK/CLK/RESET as hierarchical labels; C601–C609 |
| 7 | `glue_cpld` | **Drawn.** U3 ATF1508AS-7JX84 in a PLCC-84 THT socket, **FITTED pinout** from `../cpld/glue/pinout.csv` (read by `tools/sheet_glue.py`); every signal goes to a hierarchical label matching the root sheet; A[0..31] via bus entries. J4 10-pin JTAG (ATDH1150USB pinout) with R701/R702 4.7k TMS/TDI pull-ups and R703 4.7k TCK pull-down; C701–C708 100 nF (one per VCC pin) + C709 10 µF; D701 USER / D702 HALTED LEDs (R705/R706 1k, moved here from the debug sheet); R704 EXP_INT_n pull-up; JP701–JP703 open solder jumpers from the reserved SPI pins 46/48/49 to SPI_HW_SCK/MOSI/MISO; TP701–TP706 key strobes. Pins 50–52 = **IDE_DA0–2** outputs to the ide sheet (Rev A.1, 2026-09-27; TP707–TP709 on the former spares were removed) |
| 8 | `dram` (A2) | **Drawn** (`tools/sheet_dram.py`). U4 ATF1508AS-7JX84 in a PLCC-84 THT socket, **FITTED pinout** from `../cpld/dram/pinout.csv`. J5 10-pin JTAG (separate from J4, not chained) with R801/R802 4.7k TMS/TDI pull-ups and R803 4.7k TCK pull-down. C801–C808 100 nF + C809 10 µF. R804–R824 33 Ω series on U4_* → MA0–11, RAS0–3, CAS0–3, WE. J1 72-pin SIMM socket **TE 5822021-4**, new footprint `SIMM-72_TE-5822021-4` (see below); DQ1–32 → D0–D31 via bus entries (DQ1–8 → D0–7 … DQ25–32 → D24–31, Micron pinout); PD1–4 with R825–R828 10k pull-ups → SIMM_PD1–4. C810–C812 100 nF, C813–C815 10 µF, C816–C817 470 µF. JP801–JP804 open solder jumpers U4 pins 16/17/18/50 → STERM_n/CBREQ_n/CBACK_n/DS_n. TP801–TP809 (RAS0, RAS1, CAS0–3, WE, MUX_SEL, spare pin 81). Fallback (all DNP): U801–U803 74ACT257 (MC74ACT257DR2G, S = MUX_SEL, OE = GND, I0 = row A12–A21, I1 = column A2–A11) → R829–R838 33 Ω → MA2–MA11, C818–C820 |
| 9 | `rom` (A3) | **Drawn** (`tools/sheet_rom.py`). U5 SST39SF040-70-4C-NHE, PLCC-32 pinout DS20005022C Fig. 2 (symbol `SST39SF040-PLCC32`; the stock symbol is the DIP pinout and is not used). DQ0–DQ7 = D24–D31. A0–A18 on `A[0..31]`. CE# = ROM_CE_n, OE# = BUS_RD_n, WE# = BUS_WR_n. Socket footprint `PLCC-32_THT-Socket` (XU5). C551 100 nF, C552 10 µF |
| 10 | `duart_spi_rtc` (A3) | **Drawn** (`tools/sheet_duart.py`). U6 SC26C92A1A, symbol `m68030-sbc:SC26C92`, PLCC column of Fig. 1 (not DIP/PQFP). Pin 12 NC, no wire. D0–D7 = D24–D31. J7/J8 TTL-232 (pin 3 open). U22 SN74LVC125ADR on +3V3 shifts OP2–OP5; MISO is not shifted. U23 DS3234S# on +3V3, BT1 to VBAT with no diode, NC pins to GND, both SCLK pins tied. J9 pins 1–10 as in bom.csv. R1001 4.7k INTRN, R1004 10k NIC INT to +3V3, R1005/R1006 reset divider. Crystal stays on the clock sheet. 2 WS unchanged, glue not refit |
| 11 | `ide` (A2) | **Drawn** (`tools/sheet_ide.py`). U11/U12/U13 SN74ACT245N (DIP-20, SCAS452H; was HCT245). U11 DD0–7 ↔ D24–31, U12 DD8–15 ↔ D16–23, DIR = R/W, OE = IDE_BUF_EN_n. U13 is one-way (DIR = +5V, OE = GND): A0–A7 = IDE_DA0, IDE_DA1, IDE_DA2, IDE_CS0_n, IDE_CS1_n, IDE_DIOR_n, IDE_DIOW_n, PERIPH_RST_n, through R911–R918 33 Ω to the header. J6 40-pin. R901 4.7 k IORDY, R902 10 k DD7, R903 10 k INTRQ, R904 5.6 k DMARQ, R905 10 k DMACK, D5 + R906 1 k on DASP. C911–C913 100 nF. 13 wait states unchanged. ACT245 meets t0/t1/t2/t4/t5/t9 at 50 pF (spec §3.2; the t5 miss was a false 19.5 ns path) |
| 12 | `expansion` (A1) | **Drawn** (`tools/sheet_expansion.py`). U14–U17 SN74ACT244DW (OE to GND), U18–U21 SN74ACT245DW (OE = EXP_BUF_EN_n, DIR = R/W, card on A). J10 is `DIN41612-C96` (3 units) on `DIN41612_C_3x32_Female_Vertical_THT`, MPN HARTING 09032966821 [VERIFY]. Row a A0–A23 then SIZ/FC/R/W/AS/DS, row b D0–D31, row c the direct CPU/glue nets, GND, +5V, eight reserved. C1401–C1408 100 nF, C1409 10 µF. No CPLD pin moves |
| 13 | `debug` (A2) | **Drawn** (`tools/sheet_debug.py`). J11 LA1 A31→A0, J12 LA2 D31→D0, J13 LA3 the §8.4 list, each a 2×20 with GND on every 5th pin (Samtec TSW-120-07-G-D). TP1101 = LED_n, TP1102 = HALT_LED_n. D701/D702 are not repeated; SW1/SW2 stay on the reset sheet |

Buses cross the hierarchy as `A[0..31]` and `D[0..31]` (full width on every sheet). Local labels + bus entries break out the members.

## Attribution

`lib/m68030-sbc.pretty/PGA128_13x13_MC68030.kicad_mod` and `SIMM-72_Mackerel.kicad_mod` are copied (renamed) from **Mackerel-68k** by Colin Maykish (`SIMM-72_Mackerel` is kept for reference but no longer used; J1 uses the new TE footprint). The U4 logic `../cpld/dram/dram.v` is based on Mackerel-30's `dram_controller.v`. The MC68030 / MC68882 pin maps in `lib/m68030-sbc.kicad_sym` were cross-checked against Mackerel's symbols. Mackerel-68k is under the MIT License, © 2024 Colin Maykish; the full text is in `lib/LICENSE-mackerel-68k.txt`. The symbol graphics and pin grouping are my own (generated by `tools/mklib.py`).

## Pin and value verification (sources)

- **MC68030 PGA-128:** all 128 pins transcribed from the MC68030 User's Manual §14.2 pinout (PDF p. 575, checked against the page image) into `tools/um_pga.py`. Matches Mackerel's symbol 128/128. Pin types corrected where Mackerel was wrong: STATUS and REFILL are outputs, RESET is bidirectional open-drain. The PGA footprint (A1–N13, top view) matches the UM grid.
- **MC68882 PLCC-68:** checked against Freescale BR509 Rev. 3 p. 23 (page image); matches Mackerel 68/68. The FPU user's manual only has the PGA pinout. A web table (amiga-stuff) was found to be wrong and was not used.
- **LM2678S-5.0:** TI SNVS029L (Jun 2025) pin table, TO-263-7: 1 VSW, 2 VIN, 3 CB, 4 GND/tab, 5 NC, 6 FB, 7 ON/OFF. Components come from §7.2.1.2:
  - L = 22 µH (Fig. 7-3, region L41).
  - Output caps: 3× 100 µF/10 V tantalum (Table 7-5).
  - Catch diode: VR ≥ 1.3 × Vin (Table 7-4 class).
  - CB = 0.01 µF (step 7).
  - Input caps: Irms > Iload/2.
  - ON/OFF: must stay ≤ 6 V abs max and be left open if unused (§6.3.6).
- **TPS3702CX50:** TI SBVS251A, Table 10-2. SET high: UV 4.80 V, OV 5.20 V, ±0.9 %. Outputs are open-drain.
- **TPS3808G50:** TI SBVS050N. 4.65 V threshold; CT to VDD through 40–200 kΩ gives 300 ms typ (180–420 ms); open-drain RESET; MR has an internal pull-up.
- **AMS1117-3.3:** AMS datasheet "Stability" section: 22 µF solid tantalum on the output. The application circuit shows 10 µF on the input.
- **SUD50P04-08:** stock KiCad symbol/footprint (TO-252). Vgs ±20 V, so D3 clamps the gate at 12 V.
- **ATF1508AS PLCC-84** (Microchip doc0784 PLCC-84 pinout figure, cross-checked against the fitter's own PLCC84 pin diagram in `glue.fit`): VCCINT 3, 43; VCCIO 13, 26, 38, 53, 66, 78; GND 7, 19, 32, 42, 47, 59, 72, 82; JTAG TDI 14, TMS 23, TCK 62, TDO 71; dedicated inputs 83 (GCLK1), 84 (OE1), 1 (GCLR), 2 (OE2/GCLK2). With JTAG enabled there are 60 user I/O + 4 dedicated inputs.
- **JTAG header J4:** ATDH1150USB user guide (Atmel-8909A) Table 1, 10-pin: 1 TCK, 2 GND, 3 TDO, 4 VCCT (target VCC, the programmer senses it), 5 TMS, 6–8 NC, 9 TDI, 10 GND. Copy in `../datasheets/ATDH1150USB-UG.pdf`.
- **SC26C92 vs SC28L92** (spec §8.3): identical PLCC-44 pinout except pin 12 (SC28L92 I/M, SC26C92 NC). Pin 12 is left open on the DUART stub (Intel mode on an SC28L92).

## Unverified / estimated items ([VERIFY] / [EST])

1. PGA-128 footprint drill 0.762 mm (from Mackerel): check against the chosen PGA socket's datasheet.
2. SIMM-72 footprint: **fixed.** J1 is TE 5822021-4 with the new `SIMM-72_TE-5822021-4.kicad_mod` (`tools/mkfp_simm.py`, from the TE customer drawing `../datasheets/TE_5822021_CD.pdf`). Pads are Ø1.65 mm with a 1.02 mm drill; Mackerel had a 0.762 mm drill, which is the hole-size bug. Locating holes are NPTH 1.63 mm at the pin-1 end and centre (Mackerel: 2.45 mm) and 2.41 mm at the far end. Still [VERIFY]: whether TE's drawing/114-1061 wants the locating holes plated; print 1:1 against a real socket.
3. KEMET T495X107K010ATE100: the exact part number, ESR and stock for the Table 7-5 "C4" (100 µF/10 V) position are not verified.
4. C201–C203 (10 µF 50 V X7R 1210): check the ripple-current rating against the vendor curve. This is a deliberate deviation from Table 7-7.
5. C205: the SNVS029L pin table says 100 nF, while the design procedure and §7.1.6 say 0.01 µF. 10 nF is used (following the procedure); either value fits the 0603 pad.
6. D2 SMBJ28CA: the clamp voltage at rated Ipp (~45 V) is at the LM2678 45 V abs max [EST]. It covers short spikes only.
7. D3 MMSZ5242B: stock/availability not checked.
8. F1 fuse and holder: generic 5×20 T5A; exact part numbers not chosen. J2 barrel-jack footprint must match the purchased jack.
9. Oscillator pin 1 (EN vs NC on DIP-14 cans) is tied to +5V. This is harmless if NC; check against the purchased oscillators.
10. C307/C308 22 pF is an [EST]; size it to the crystal's CL.
11. 33 Ω series resistors (R301–R308) are an [EST]; tune on the scope.
12. SC26C92 availability: broker-only (DigiKey 0). The SC28L92 fits the same socket.
13. SC26C92 bus timing: tRWD margin is thin at 33 MHz (spec §3.2 adds an idle clock); tAH 25 ns is covered by the glue timing (spec §3.2).
14. TPS3702 window vs LM2678 tolerance: UV trips at 4.757–4.843 V against a regulator minimum of 4.85 V. This is tight; JP401 gives a ±9 % (UV 4.55 V) fallback (spec §10 risk 12).
15. MC68882 speed grade vs shared CPU clock: an FN25A/FN33A is required, or fit X3 + set JP3 to 2-3.
16. CPU heatsink: the thermal estimate is from the EC datasheet (up to 2.6 W).
17. U3 JTAG pull values (R701/R702 4.7k up, R703 4.7k TCK down) are [EST]. The fit enables the internal TDI/TMS pull-ups; the external parts are belt-and-braces. Programming through ATDH1150USB + ATMISP has **not** been tried.
18. U3 timing (Rev A.1, spec §3.2): chip selects 7.5–13 ns, IDE selects registered, clock-to-out 10–11 ns. DUART 2 WS, ROM 1 WS, and **IDE 13 WS** (640 ns cycle, meets ATA/ATAPI-6 t0). The FPU_CS_n glitch (risk 21) and pin keeper (risk 22) are resolved. Still [VERIFY]: 68882 #8B/#9 margins (spec risks 27/28; rechecked, cannot be closed on paper with an AS-qualified CS in the -7 ATF). IDE buffers are SN74ACT245N; read t5 meets EC #27 by 3.5 ns once the false 19.5 ns AS→DIOR arc is dropped (spec §3.2). There is still no 150 pF ACT delay. The U4 vs 68882 DSACK overlap (risk 23) is resolved by U4 Rev A.1 (see below).
19. U3 LED drive: D701/D702 are sunk by the CPLD (about 3 mA through 1k). This is within the ATF1508AS IOL, but check brightness on the real LEDs.

## Glue CPLD (U3) — fit result (Rev A.1, 2026-09-27)

- **Status: FITTED** (not provisional). The logic is `../cpld/glue/glue.v` (Verilog); build it with `../cpld/glue/build.sh`. Toolchain, quirks and verification are in `../cpld/glue/README.md`.
- **Flow:** Yosys 0.52 + hoglet67 `atf15xx_yosys` techmap scripts → EDIF → Microchip `fit1508.exe` (build 1918, 2007, from ProChip 5.0.1) under Wine 10.0. Options: `-d ATF1508AS -p PLCC84 -s 7 -preassign keep -optimize off -tdi_pullup on -tms_pullup on -pin_keep on`, JTAG ON, Pin-Keeper ON.
- **Utilization:** 121/128 macrocells, 62 flip-flops, 322 product terms, 13 cascades, 0 foldbacks; 57/60 user I/O + 4 JTAG + 4/4 dedicated inputs; no LAB above 100 %. That leaves 7 macrocells. (Rev A: 111 MC, 53 FF, 263 PT, 54/60 I/O.)
- **Pins:** locked with `//PIN:` comments; every Rev A pin kept its position. Pins 46/48/49 are reserved for the SPI master (behind JP701–703). Pins 50–52, spares in Rev A, are now IDE_DA0–2.
- **Rev A.1 changes** (from the open-items review; details in spec §3.2 and the README):
  - All per-cycle state is async-cleared by AS_n. This fixes a missed-AS-gap bug where state carried into the next cycle.
  - FPU_CS_n and EXP_SEL_n/EXP_BUF_EN_n are single product terms including AS_n, so there is no runt select.
  - DSACK/BERR/AVEC are released ≤ 20.5 ns after AS↑.
  - IDE_CS0/1_n, IDE_BUF_EN_n and the new IDE_DA0–2 are registered.
  - IDE is now 13 WS.
- **Verification:**
  - The functional testbench passes (0 errors) on the RTL and the zero-delay post-fit netlist.
  - A timed post-fit simulation (SDF back-annotated via `sim/sdf2v.py`, worst-case 68030 bus model) gives 0 errors, nominal and 50 % derated. The Rev A netlist under the same testbench gives 7453 errors.
  - Static timing is in `timing.txt` (`sim/sta_glue.py`): reg→reg 20.3 ns, fmax 49.3 MHz.
- **Fitter/flow quirks** (the fitter ones give `INTERNAL ERROR` or an EDIF error, not a helpful message):
  - A constant driving an output or OE fails.
  - One enable shared by several tri-state pins fails.
  - A port named `D`, or a cells.lib cell with a pin named `G`, breaks the EDIF.
  - The optimizer on never fitted.
  - Yosys `clean` deletes a register that feeds only a TRI enable (EN/ENA name mismatch); `build.sh` checks for this.

## ERC history — after the glue sheet

Result: **222 violations, all `label_dangling`** (error severity). Before the glue sheet was drawn there were 311 (310 `label_dangling` + 1 `pin_not_driven`). Drawing U3 resolved 89, including the U2 pin 29 FPU CS `pin_not_driven`, and added none.

KiCad 9 lists all of them under the root sheet. Each one is a label whose net has no second connection yet because its other end is on one of the 6 still-stubbed sheets (dram, rom, duart_spi_rtc, ide, expansion, debug). Examples: `CLK_DRAMC`, `DRAM_CLK`, `SIZ0/1`, `ECS_n`, the DRAM/ROM/DUART/IDE chip-select nets, and the stub-side hierarchical labels. There are no warnings, no power-pin, pin-conflict, off-grid, footprint-link or library-symbol findings, and no unconnected pins on the drawn sheets.

Checked with the netlist: every drawn-sheet pin lands on the intended net (clock tree, supervisor chain, buck, input protection, CPU/FPU power and pull-ups, and all 84 U3 pins against `pinout.csv`).
20. U4 series resistors R804–R824 (33 Ω) and the SIMM bulk capacitors (2× 470 µF) are [EST] starting values (spec §5.8); tune on the scope.
21. U4 JTAG pull values (R801–R803) as for U3 (item 17).

## DRAM CPLD (U4) — fit result

- **Status: FITTED.** Logic `../cpld/dram/dram.v`, built with `../cpld/dram/build.sh` (same flow as U3, but with `-optimize on -pin_keep on`, JTAG ON). Details, simulation and quirks are in `../cpld/dram/README.md`.
- **Utilization (Rev A.1, 2026-09-27):** 78/128 macrocells (Rev A 80), 50 flip-flops (52), 206 product terms (210), foldback 6 (7) / cascade 9; 55/60 user I/O + 4 JTAG; dedicated inputs 3/4 (pin 2 CLK_DRAMC is wired but unused). Pin-Keeper ON. All 58 locked pins kept; `pinout.csv` identical to Rev A, so the dram sheet did not change. **No fallback needed.**
- **Rev A.1 changes (spec risks 23 and 29):** DSACK1/0 are driven high by AS_n↑ directly (7.5 ns) and released to Z by an async clear from AS_n (17.5 ns; Rev A up to 57 ns, which overlapped a following 68882 cycle). The first AS synchroniser flop is async-set by AS_n, so a short AS-high gap (EC #15, 23 ns at 33 MHz) can no longer be missed (Rev A could stay in sAck and assert DSACK in a foreign cycle).
- **Fitted timing** (`../cpld/dram/timing.txt`): register → register 14.0 ns (50 MHz met, 6 ns margin); clock → RAS/CAS/WE 4.5 ns, → MA 10 ns, → DSACK 11 ns; AS_n↑ → RAS/CAS released 14 ns, → DSACK high 7.5 ns / Z 17.5 ns.
- **Simulation:** RTL and SDF-back-annotated post-fit netlist (25 and 33 MHz CPU, nominal and 50 % derated × 5 seeds) against a 60 ns EDO SIMM model: 0 errors, all byte lanes correct, refresh ≤ 15.2 µs per side, 2–3 WS at 25 MHz (max 8), 3–4 WS at 33 MHz (max 10). DSACK hand-over to a 68882-like agent ≥ 16.5 ns, 0 overlaps. Whole-system sim (`../cpld/sim_system/`, glue + U4 netlists + 68882 + expansion): 0 errors, 0 DSACK contention events in all 6 runs.

## ERC (kicad-cli 9.0.2, `erc-report.txt`) — after the dram sheet

Result: **147 violations, all `label_dangling`** (was 222 before the dram sheet was drawn; 311 before the glue sheet). All remaining ones are on the 5 stub sheets / root labels whose other end is not drawn yet. Netlist spot checks: A5 → U1/U4/U801; D0 → J1 pin 2; MA0 → J1 pin 12; DRAM_SEL_n U3 pin 55 → U4 pin 52; all 84 U4 pins and all 72 J1 pins connected.

## ERC — after the glue Rev A.1 update (2026-09-27)

Result: **159 violations, all `label_dangling`** (was 147). The +12 are the 4 labels on each of the 3 new nets `IDE_DA0`–`IDE_DA2`:
- the U3-side hierarchical label on the glue sheet;
- the root labels at the glue and ide sheet pins;
- the ide stub's hierarchical label.

These nets connect glue → ide correctly (netlist: `/IDE_DA0` → U3 pin 50, `/IDE_DA1` → 51, `/IDE_DA2` → 52). They count as dangling only because the ide sheet is still a stub with no component pin, the same class as the other 147, and they disappear when U13 is drawn. The ide stub no longer takes `A[0..31]`: DA2:0 come from U3. TP707–TP709 (on the former spare pins) were deleted, and `bom.csv` TP quantity went from 25 to 22.

## ERC — after the U4 Rev A.1 refit (2026-09-27)

Result: **159 violations, all `label_dangling`**, unchanged. U4 kept all its pins, so `tools/build.py` regenerated an identical `dram.kicad_sch` (and `glue_cpld.kicad_sch`). No parts changed; `bom.csv` unchanged.

## ERC — after rom, ide, expansion and debug (2026-10-03)

Before these four sheets: **159 violations, all `label_dangling`** (the glue Rev A.1 / U4 Rev A.1 result). `duart_spi_rtc` was still a stub, and so were rom, ide, expansion and debug.

After (`kicad-cli 9.0.2`, `tools/render.sh`): **34 violations, all `label_dangling`.** None are on rom, ide, expansion or debug. Every one is a duart net that still has no second pin:

- the duart stub's hierarchical labels (16; `A[0..31]` and `D[0..31]` are not in the count because those buses connect to real pins on other sheets);
- the matching glue-sheet hierarchical labels for `DUART_INT_n`, `NIC_INT_n`, `DUART_RST`, `SPI_HW_SCK`, `SPI_HW_MOSI`, `SPI_HW_MISO` (the SPI three go through the open solder jumpers);
- the root-sheet labels on those same nets.

Netlist checks: U5 PLCC pins match DS20005022C Fig. 2 (DQ0 = D24 … DQ7 = D31, CE = ROM_CE_n, OE = BUS_RD_n, WE = BUS_WR_n). `/IDE_DA0` is U3 pin 50 → U13 pin 2 → R911 → J6. `/D24` hits U1, U5, U11 and U21. J10 has all 96 pins (c25–c32 are the reserved no-connects). J11 is on A0 and A31; TP1101 is on LED_n with D701.

IDE buffers were swapped to SN74ACT245N on 2026-10-03 (same DIP-20 footprint). Wait states were **not** changed. SCAS452H Fig. 6-1 is CL = 50 pF only (tPLH 1.5–8, tPHL 1–9). t0/t1/t2/t4/t9 meet. Read t5 also meets (5.5 ns before the latch, 3.5 ns vs EC #27) because DIOR rises on the product term (tPD1 max 7.5 ns), not the 19.5 ns async-clear arc. No parts change. See spec §3.2 and risk 10.

## ERC — after the SN74ACT245N swap (2026-10-03)

Value and datasheet fields on U11–U13 only. No pins moved. ERC re-run with `kicad-cli` 9.0.2 on 2026-10-03 16:45 ET: **34 `label_dangling`**, all duart nets. Same as before the swap.

## ERC — after the duart sheet (2026-10-03)

Before: **34 violations, all `label_dangling`**, every one a duart net (the SN74ACT245N recheck the same day).

After (`kicad-cli` 9.0.2, `tools/render.sh`, 2026-10-03 17:25 ET): **0 violations.**

Chip stayed SC26C92A1A. XR68C681 is MaxLinear OBS (PDN 2024-01-23) and a Motorola-bus part, so it does not match `BUS_RD_n`/`BUS_WR_n`. TL16C552A is the orderable 5 V PLCC DUART; SLLS189D `td2`/`td4` ≥ 80 ns misses the 2-WS back-to-back gap (78.5 ns, spec §3.2), so wait states were not changed and the glue was not refit. `DUART_WS` is still 2, `DUART_DLY` still 0.

Netlist: U6 pin 28 = D24, pin 12 unconnected, pin 44 = +5V, pin 38 = DUART_RST. U23 pins 18 and 20 are both SPI_SCK, pin 4 = +3V3, pin 2 = GND, pin 19 = SPI_HW_MISO. U22 pins 14/7 = +3V3/GND.
