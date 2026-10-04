# U3 glue / system CPLD (ATF1508AS-7JX84)

Verilog source, fitter results and programming file for U3 on the `glue_cpld` KiCad sheet.
Spec: `../../spec.md` §2 (memory map), §2.4 (registers), §3 (bus cycles), §3.5–3.6 (interrupts, timer), §4.2 (pins), §7.2 (reset).

| File | What |
|---|---|
| `glue.v` | The logic (module `glue`). `//PIN:` comments lock the pinout. `CPU_CLK_HZ` (default 25 MHz) selects the wait states and the timer divider. |
| `build.sh` | Yosys → EDIF → fit1508 (with checks: fit, Pin-Keeper ON, no TRI enable removed), then `timing.txt` and the three simulations. |
| `glue.fit` | Fitter report: utilization, pin diagram, equations. |
| `glue.jed` | JEDEC programming file (program with ATMISP + ATDH1150USB on J4). |
| `glue.pin` / `glue.io` / `glue.tt3` / `glue.vo` / `glue.sdo` | Fitter pin file, I/O report, fitted equations, gate-level Verilog timing model, SDF. |
| `pinout.csv`, `pinout.md` | All 84 pins, extracted from the `glue.fit` pin diagram by `pinout.py`. **The KiCad sheet reads `pinout.csv`.** |
| `timing.txt` | Static timing from the fitter's SDF model (`sim/sta_glue.py`): clock-to-pad, pin-to-pad incl. async-clear paths, chip-select stale-decode check, input setup, reg→reg / fmax. |
| `sim/` | `tb_glue.v` functional testbench (RTL with `cells_rtl.v`; `-DPOSTFIT` on the fitted `glue.vo` with `prims.v`, zero delay). Timed post-fit: `sdf2v.py` back-annotates `glue.vo` with `glue.sdo` → `glue_timed.v`; `prims_timed.v` (transport delays, `+derate`/`+dmin`/`+seed=`, DFF setup/hold/recovery checks); `tb_timed.v` (worst-case 68030 bus model, U4/68882/expansion agents, monitors for wrong-cycle selects, false terminations, DSACK contention, 68882 #8/#8B/#9, IDE t0/t1/t2/t4/t9). Logs `sim_*.log`; `sim_timed_revA*.log` = the Rev A netlist under the same timed testbench. |
| `yosys.log`, `fit_run.log` | Tool logs from the last run. |

## Result — Rev A.1 (2026-09-27, fit1508 v1918)

`$Device PLCC84 fits; JTAG ON; Secure OFF`, **`Pin-Keeper = ON`**. Pins are locked (`-preassign keep`); every Rev A pin kept its
position. The only pinout change: pins 50/51/52 (Rev A spares, TP707–709) are now the new outputs **IDE_DA0/1/2**.

| Resource | Rev A (2026-09-26) | **Rev A.1** |
|---|---|---|
| Macrocells | 111 / 128 | **121 / 128 (94 %)** |
| Flip-flops | 53 | **62** |
| Product terms | 263 | **322** (of 640) |
| I/O (fitter count incl. 4 JTAG) | 58 / 64 | **61 / 64** (57/60 user I/O; free: 46/48/49 SPI reserve behind JP701–703) |
| Dedicated inputs | 4 / 4 | 4 / 4 |
| Foldback / cascade | 0 / 13 | 0 / 13 |
| Per-LAB | all ≤ 100 % | all ≤ 100 % |

Options: `-d ATF1508AS -p PLCC84 -s 7 -preassign keep -optimize off -tdi_pullup on -tms_pullup on -pin_keep on -verilog_sim sdf`.
(A refit of the unchanged Rev A source with `-pin_keep on` gave identical pins and timing; the JED differed in one fuse.)

Timing from the SDF model (`timing.txt`; ATF1508AS-7 model, no board delay; the datasheet gives no minimum delays, so min paths are [VERIFY]):

| Path | Rev A | **Rev A.1** |
|---|---|---|
| FPU_CS_n from address/FC | 18.5 (via A16), 4.0 ns stale-decode window | **7.5**, one product term incl. AS_n, no window (7 ns margin) |
| EXP_SEL_n / EXP_BUF_EN_n | 18.5 | **7.5**, single PT |
| ROM_CE_n / DUART_CS_n / DRAM_SEL_n / CIIN_n | 18.5 via FC, 4 ns stale window | **13.0**, AS_n path 7.5 → no stale window (1.5 ns margin) |
| IDE_CS0/1_n, IDE_BUF_EN_n | 18.5 / 26 (BUF_EN 11.5 ns stale window) | **registered** (clock-to-pad 10.0) |
| IDE_DA0-2 | (A1–A3 direct) | registered, clock-to-pad **4.5** |
| DSACKx/AVEC/BERR clock-to-pad | 11.0 | 11.0 |
| AS_n↑ → DSACKx/AVEC/BERR driven high / released | ≤ 1 clock | **7.5 / ≤ 20.5** |
| BUS_RD_n / BUS_WR_n clock-to-pad | 10.0 | 10.0 |
| Worst reg → reg | 19.5 | **20.3** (fmax 49.3 MHz; 25 MHz and 33.33 MHz met) |
| Worst input setup | 33.5 | **22.5** (FC → a flag register that is only sampled from R2 on; `act` AS_n setup 6.0) |

- **`-optimize off` is required.** With the optimizer on, every attempt ended in "Grouping fail" / "Placement fail".
- `-xor_synthesis on` is not used. Its per-LAB table shows a LAB at "17/16 (106 %)", which looks like the TDO macrocell's buried node being counted twice. The final fit has no LAB above 100 %.
- **Headroom is 7 macrocells.** The optional CPLD SPI master (§1.4, est. 15–20 MC) does **not** fit in U3 as synthesized. Separate OE registers for the termination pins were tried and cost 130/128 MC.

## Toolchain (Linux, reproducible)

1. `apt install yosys wine wine32:i386 innoextract iverilog`. Used here: Yosys 0.52, Wine 10.0, Icarus 12.0.
2. `git clone https://github.com/hoglet67/atf15xx_yosys /opt/atf15xx_yosys`
3. Get fit1508 from Microchip ProChip 5.0.1, `http://ww1.microchip.com/downloads/en/DeviceDoc/ProChip5.0.1.zip`. It is an Inno Setup installer; you don't need to run it:
   `innoextract -I app/Prochip/pldfit setup.exe`. Then copy `fit1508.exe`, `aprim.lib` and `atmel.std` into `/opt/atf15xx_yosys/vendor/`. The SHA1s match the atf15xx_yosys README.
4. `./build.sh`. Set `ATF15XX_YOSYS` if the checkout is elsewhere.

### fit1508 quirks found (v1918, 3-21-07)

These all show up as a bare `INTERNAL ERROR - Please contact your Hot-Line`:
- A constant (GND/VCC net) feeding an output or OE, e.g. `assign X = 1'b0;` or `assign RESET_n = en ? 1'b0 : 1'bz;`.
  - Fix: remove the constant outputs (the SPI pins are not ports), and write open-drain emulation as `en ? ~en : 1'bz`.
- One enable net shared by several three-state pins.
  - Fix: give each pin its own enable (DSACK0/1, AVEC and BERR are each enabled by their own flag).
- EDIF "number of connectors" error when a cells.lib cell has a pin named `G` (the 7+-input AND/OR cells). Build wide ANDs from AND6/AND5/AND2 instead.
- Separately, a design port named `D` collided with a primitive pin name and gave an EDIF "number of connectors" error. Avoid single-letter port names (A, B, D, Q, …).

### Yosys-flow trap (atf15xx_yosys)

`cells.lib` names the TRI enable pin `EN` but `run_yosys.sh` maps `ENA`. A register that feeds **only** a TRI enable therefore looks unused and `clean` deletes it; the first Rev A.1 fit came out with `DSACK0_n.OE = 0`. The termination pins now use `x_n = x_q ? ~(x_q & as) : 1'bz` (the register also feeds the data path), and `build.sh` fails if any of DSACK0/1/AVEC/BERR has `OE = 0` in `glue.fit`.

## Verification done (Rev A.1)

| Run | Result |
|---|---|
| `sim_rtl.log`: `tb_glue.v` on the RTL | 26 checks, **0 errors** |
| `sim_postfit.log`: same tests on the fitted `glue.vo`, zero delay | **0 errors**. Includes a "missed AS gap" test. IDE clock-quantised: t0 720, t1 120, t2 360, t9 57, t4 70 ns |
| `sim_timed.log`: timed post-fit (SDF), 4398 cycles, 50 % of them at the 68030 EC extremes | **0 errors**, 0 wrong-cycle runts. 68882: #8 0 violations, #8B min 19.57 ns, #9 min 7.50 ns. Glue releases terminations ≤ 20.5 ns after AS↑. IDE: t0 640, t1 120, t2 360, t4 57, t9 45.5 ns |
| `sim_timed_derate.log` (`+derate +seed=22`; also seeds 11/33/44/55 run by hand) | **0 errors**. #8B ≥ 20.1, #9 ≥ 5.1, t0 ≥ 639, t9 ≥ 43.6 ns |
| `sim_timed_revA.log` / `_derate`: Rev A netlist under the same timed testbench | **7453 / 6997 errors**, including 3008 false early terminations from carried-over cycle state, 626 stray DIOR, 556 stray BUS_RD, and 10 FPU_CS runts giving 7 false 68882 STARTs |

- **U4 vs 68882 DSACK contention (spec risk 23): resolved by U4 Rev A.1.** `tb_timed.v` still uses a behavioural model of the *Rev A* U4 (DSACK driven high until 57 ns after AS↑), so the contention events it reports (~50 of ≤ 17.9 ns, ≤ 21.5 ns derated; none involve the glue) describe Rev A and are kept as the reference. U4 Rev A.1 releases DSACK 17.5 ns after AS↑; the whole-system sim with both real netlists (`../sim_system/`, 6 runs) shows 0 contention events and 0 errors.
- The DFF setup/recovery/hold hits in the timed logs are on the registers that capture the asynchronous AS_n/IORDY and on the async-clear release (`cyc_clr`) near a clock edge. The registers whose clear releases near an edge either have D = 0 (`cnt`, flags) or are `act`, where a late capture just delays the cycle by one clock. The testbench monitors show no functional effect.
- The SDF numbers are the fitter's model, not guaranteed silicon minima [VERIFY]. #9 (AS↑ → CS negated ≥ 5 ns) relies on the 7.5 ns AS→FPU_CS path, which is a model number, not a guaranteed minimum.

## Design notes / deviations from the spec found while writing the logic

1. **CIIN_n is push-pull**, not open-drain. The glue is its only driver; the 1k pull-up on the CPU sheet is harmless.
2. **DSACKx/AVEC/BERR** are driven high directly by AS_n↑ (7.5 ns) and released by the async clear (≤ 20.5 ns after AS↑).
3. The SPI master is **not implemented**. Pins 46/48/49 are reserved behind open solder jumpers JP701–703.
   - Unused pins are shown as "NC = must be unconnected" in the fit report, so the jumpers must stay open while the pins are unused.
4. The warm-reset stretch reuses timer bits `div[9:0]`: RESET_n is held while the (debounced) button is down, then for 1024–2047 more clocks. The RESET instruction is only observed (PERIPH_RST_n = RESET_n, DUART_RST = its inverse); it does not re-arm the overlay.
5. BUS_WR_n is gated with DS_n, so write data is valid. BUS_RD_n is registered and gated with AS_n. `rd_q`/`wr_q` are qualified with `act`, so the strobes start at R2 at the earliest.
6. **IDE (Rev A.1):** IDE_CS0/1_n and IDE_DA0-2 are registered. They load once per cycle at R2 and clear one clock after AS_n is seen high, so they are stable across DIOR/DIOW (t1, t9). DIOR ends at AS_n↑; DIOW ends at the DSACK1 edge (t4). `IDE_SETUP` = 4, `IDE_PULSE` = 9, so **W = 13** at 25 MHz; with `FAST` (33 MHz) the values are 5/13, W = 18. Back-to-back DIOR-to-DIOR = (W + 3)·T = 640 ns at 25 MHz and 630 ns at 33 MHz, against ATA/ATAPI-6 Table 67 t0 ≥ 600 ns.
7. **All per-cycle registers are async-cleared by `cyc_clr = AS_n | ~PWR_RST_n`** (Rev A.1 fix). Rev A cleared them only when AS_n was *sampled* high. With AS↑ at F+18 (EC #12) and the next AS↓ 30 ns later (#15), the one clock edge in the gap can miss it, and DSACK/BUS_RD/DIOR state then carries into the next cycle. A late AS_n capture only adds one clock.
8. **FPU_CS_n** is one product term including AS_n (FC=7, A19–16 = 0010, A15–13 = 001). EXP_SEL_n/EXP_BUF_EN_n are three PTs, each including AS_n. They are built from `(* keep *)` cells.lib instances so ABC cannot share or split the decode. This removes the runt/stale-select window (MC68881UM §10.2 Fig. 10-5).
9. HALTED LED: STATUS_n low for 7 or more consecutive clocks (the UM says more than 3 means halted).
