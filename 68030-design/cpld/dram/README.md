# U4 DRAM controller CPLD (ATF1508AS-7JX84): one 72-pin 5 V EDO/FPM SIMM

This folder holds the Verilog source, fitter results, programming file and verification for U4 on the `dram` KiCad sheet.
Spec references: `../../spec.md` §5 (DRAM controller), §3.2 (timing and wait states), §4.3 (pins).

The logic is **based on Mackerel-30's `pld/mackerel-30/dram_controller/dram_controller.v`** (Colin Maykish, MIT licence, https://github.com/crmaykish/mackerel-68k). It reuses the same ideas:
- a 50 MHz controller clock that runs asynchronously to the CPU;
- a 2-flop AS synchroniser;
- CBR refresh;
- A26 as the SIMM side select;
- the SIZ1/SIZ0/A1/A0 → CAS byte-lane table (Mackerel lines 89–122, after MC68030 UM Table 7-4).

Differences from Mackerel are listed in the `dram.v` header and in spec §5.7.

| File | What |
|---|---|
| `dram.v` | The logic (module `dram`). `//PIN:` comments lock the pinout to spec §4.3. |
| `build.sh` | Runs Yosys (atf15xx_yosys scripts) → EDIF → fit1508 under Wine. Then produces `timing.txt` and `pinout.*`, back-annotates the netlist, and runs the RTL and post-fit simulations. |
| `dram.fit`, `dram.jed` | Fitter report and JEDEC file. Program the JEDEC with ATMISP + ATDH1150USB on **J5**. |
| `dram.pin` / `.io` / `.tt3` / `.vo` / `.sdo` | Fitter pin file, I/O report, equations, gate-level timing model, SDF. |
| `pinout.csv`, `pinout.md` | All 84 pins, extracted from `dram.fit` by `pinout.py`. **The KiCad sheet reads `pinout.csv`.** |
| `timing.txt` | Static timing from the fitter SDF, produced by `sim/sta_dram.py`: clock-to-pad, pin-to-pad incl. AS_n asynchronous release, input setup, register→register. |
| `sim/tb_dram.v` | Testbench containing an MC68030 asynchronous-bus model (25 MHz, or 33.33 MHz with `+cpu33`, EC timing ranges for each; half of the cycles use the worst-case AS-high gap: AS↑ at #12 max, next AS↓ exactly #15 later), a glue-decode model with fitted delays (it reproduces the decode glitch), a foreign 8-bit device, a 68882-like agent that answers FC=7 cycles with DSACK at AS + 7.5 + 0..25 ns (UM §12.6 #19 has no minimum), and the monitors (DSACK hand-over gap/overlap, U4 drive still on at the next AS↓, EC #28/#31, SIMM data contention). |
| `sim/simm_edo.v` | Behavioural 60 ns EDO SIMM (Micron MT8D432/MT16D832-6 X timing table) with timing and protocol checks. |
| `sim/sdf2v.py`, `sim/prims_timed.v` | Back-annotation of `dram.vo` with the SDF delays (iverilog 12 rejects the fitter's SDF, so `$sdf_annotate` is not used). Same files as `../glue/sim/`: transport delays, `+derate` (each path delay scaled by a random 0.5–1.0 factor, `+seed=`; the clock tree is not derated), setup/hold/recovery checks; on a violation the flop picks old/new at random. |
| `sim/sta_dram.py` | Static timing from the SDF → `timing.txt` (now also lists the combinational AS_n → DSACK path). |
| `sim/sim_rtl.log`, `sim_rtl_33.log`, `sim_postfit.log`, `sim_postfit_33.log`, `sim_postfit_derate.log`, `sim_postfit_33_derate.log` | Logs from the last run (derated logs: seeds 11/22/33/44/55). |
| `../sim_system/` | Whole-system timed sim: glue U3 + U4 netlists (both SDF-annotated) + SIMM + MC68882 + expansion-card models (`run.sh`, `tb_system.v`, `sim_system*.log`). |

## Fit result (Rev A.1, 2026-09-27, fit1508 v1918, `-preassign keep -optimize on -pin_keep on`, JTAG on)

`$Device PLCC84 fits; JTAG ON; Secure OFF`, `Pin-Keeper = ON`. All 58 locked pins were placed as assigned; `pinout.csv` is identical to Rev A, so the dram sheet is unchanged.

| Resource | Rev A | **Rev A.1** |
|---|---|---|
| Macrocells | 80 / 128 | **78 / 128 (60 %)** |
| Flip-flops | 52 | **50** |
| Product terms | 210 | **206** |
| I/O | 55 of 60 user I/O + 4 JTAG ("59/64") | same |
| Dedicated inputs | 3/4 (pin 2 GCLK2 wired to CLK_DRAMC, unused) | same |
| Foldback / cascade | 7 / 9 | 6 / 9 |
| Worst register → register | 14.0 ns | **14.0 ns** (fmax 71.4 MHz; 50 MHz met, 6.0 ns margin) |

**No fallback was needed.** There are no external 74ACT257 muxes (their footprints stay DNP) and no TQFP-100 part. Presence detect is off the CPLD by design; it goes to the DUART inputs.

## Fitted timing (`timing.txt`, fitter SDF, -7 speed grade, board delay not included)

| Path | ns |
|---|---|
| **Register → register (worst)** | **14.0 → 50 MHz (20 ns) met, 6.0 ns margin (fmax ≈ 71 MHz)** |
| DRAM_CLK → RAS/CAS/WE/MUX_SEL pads (registered in the pin macrocell) | 4.5 |
| DRAM_CLK → MA pads (buried column flop + mux) | 10.0 |
| DRAM_CLK → DSACK pads (ack register + AND with AS + 3-state) | 11.0 |
| A[25:2] → MA (row/column mux) | 7.5 |
| AS_n↑ → RAS/CAS released (async preset) | 14.0 |
| AS_n↑ → WE/MUX_SEL | 11.0 |
| AS_n↑ → DSACK driven high (combinational, one array pass) | **7.5** (Rev A: 16.5) |
| AS_n↑ → DSACK released to Z (async clear of the ack register → OE) | **17.5** (Rev A: ≤ 57, second DRAM_CLK edge) |
| AS_n↑ → MA back to row | 16.5 |
| Input setup: A0/A1/SIZ/R_W, and AS_n into the synchroniser | 6.0 |
| Input setup: DRAM_SEL_n and A26 → RAS registers (two array passes: the fitter keeps the shared start term as a node) | 11.5 |

**DRAM_SEL_n margin.** DRAM_SEL_n is sampled only at the clock where the synchronised AS edge is first seen. With AS_n at the U4 pin at time a, that clock is at a + 46 ns or later, less a metastability allowance. The glue decode settles by max(14, a + 8.5) ns, 1 ns board included (glue `timing.txt`). So the required 11.5 ns setup leaves **≥ 23 ns of margin**.

## Cycle (50 MHz ticks, from the start edge e0)

| Tick | Events |
|---|---|
| e0 | RAS asserted (side from A26), row address on MA |
| e0+20 | Column select: MA switches 10 ns later. WE is asserted here for writes (early write) |
| e0+40 | CAS asserted (reads: all four; writes: the lane table) and DSACK1/0 asserted (32-bit port) |
| AS_n↑ | Everything is released asynchronously: RAS/CAS 14 ns, WE/MUX_SEL 11 ns, DSACK driven high at 7.5 ns and released to Z at 17.5 ns (both straight from AS_n, no clock involved) |
| as3 high (2 clocks after as1 is async-set) | FSM sAck → sI; a new cycle needs a new synchronised AS falling edge |

**Refresh (R0–R8).** CAS is asserted at R1 and RAS at R2. Both go high at R6, giving tRAS = 80 ns, tCSR = 20 ns and tCHR = 80 ns. Precharge then runs to at least 60 ns. Refresh runs every 375 clocks (7.5 µs), alternating sides, so each side is refreshed every 15 µs (limit 15.6 µs = 32 ms / 2048).

**Power-up.** 14 ticks (105 µs), then 16 CBR cycles, then `ready`. Accesses before `ready` get no DSACK and time out via the glue's BERR timer.

## Simulation results (`build.sh`, Rev A.1, 2026-09-27): all runs 0 errors

Each tb_dram run covers ~810 bus cycles: ~650 DRAM, ~150 foreign ROM/IO/FPU-space (FC=7 cycles are answered by the 68882-like agent), 1 early access that must time out; all 16 SIZ/A1/A0 combinations as raw writes with read-back; 1/2/4-byte operands at every offset (misaligned longwords split by dynamic bus sizing); 500 random mixed operations; a 20 µs idle period. Derated = 50 % random derate, 5 seeds (min/max over seeds).

| Check (limit, Micron EDO -6; EC 25/33 MHz) | RTL 25 | Post-fit 25 | Post-fit 25 derated | Post-fit 33 | Post-fit 33 derated |
|---|---|---|---|---|---|
| tRAS ≥ 60 | 80.1 | 80.1 | 80.1 | 80.1 | 80.1 |
| tRP ≥ 40 | 60.1 | 60.1 | 60.1 | 60.1 | 60.1 |
| tRCD ≥ 14 | 40.0 | 40.0 | 39.1 | 40.0 | 39.1 |
| tRAH ≥ 10 | 22.0 | 25.5 | 22.4 | 25.5 | 22.4 |
| tASC ≥ 0 | 18.0 | 14.5 | 14.3 | 14.5 | 14.3 |
| tCAS ≥ 10 / tCP ≥ 10 | 54.2 / 100.1 | 62.9 / 100.1 | 57.7 / 99.1 | 54.0 / 100.1 | 47.2 / 99.1 |
| tCSR ≥ 5 / tCHR ≥ 10 (CBR) | 20.0 / 80.1 | 20.0 / 80.1 | 19.5 / 79.7 | 20.0 / 80.1 | 19.5 / 79.7 |
| tWCS ≥ 0 / tWCH ≥ 10 | 20.0 / 54.2 | 20.0 / 59.9 | 19.0 / 56.1 | 20.0 / 51.7 | 19.0 / 44.9 |
| SIMM timing errors | 0 | 0 | 0 | 0 | 0 |
| Refresh gap per side ≤ 15 625 | 15 175 | 15 195 | 15 195 | 15 115 | 15 175 |
| EC #31 DSACK → data (≤ 28 / ≤ 20), min margin | 4.8 | 11.3 | 9.3 | **3.3** | **1.3** |
| EC #28 AS↑ → DSACK negated (≤ 40 / ≤ 30) | 10.0 | **7.5** | ≤ 8.6 | 7.5 | ≤ 8.6 |
| AS↑ → DSACK released (Z) | 27.3 | **17.5** | ≤ 15.9 | 17.5 | ≤ 15.9 |
| DSACK hand-over gap (U4 Z → next driver on) / overlaps | 31.4 / 0 | **34.3 / 0** | ≥ 24.7 / 0 | **16.5 / 0** | ≥ 16.8 / 0 |
| U4 DSACK still driven when the next AS falls | 0 | 0 | 0 | 0 | 0 |
| SIMM data release → next driver on | 17.9 | 14.9 | ≥ 14.7 | **5.3** | ≥ 6.5 |
| Wait states (count) | 2: 589, 3: 57, 6+: 16, max 7 | 2: 488, 3: 154, 4–5: 3, 6+: 18, max 8 | max 8 | 3: 559, 4: 72, 6+: 19, max 10 | max 10 |

RTL uses an assumed +10/+12 ns output model (CAS 12 ns vs 4.5 ns fitted); its EC #31 figure at 33 MHz (−3.2 ns) is therefore informational only, the fitted netlist has +3.3 ns.

**Rev A vs Rev A.1 under the same testbench** (Rev A netlist re-simulated, logs not kept in the tree):

| | Rev A post-fit 25 | Rev A post-fit 33 | Rev A.1 post-fit 25 | Rev A.1 post-fit 33 |
|---|---|---|---|---|
| AS↑ → DSACK released (Z) | 57.0 | 57.0 | 17.5 | 17.5 |
| DSACK overlaps with the 68882-like agent | 2 (X on the bus) | 7 | **0** | **0** |
| U4 still driving DSACK when the next AS fell | 175×, up to 27.0 ns | 427×, up to 33.8 ns | **0** | **0** |
| Hand-over gap min | 4.4 (overlap) | 3.8 (overlap) | 34.3 | 16.5 |
| tRP / tCP min | 60.1 / 95.9 | 56.7 / 93.9 | 60.1 / 100.1 | 60.1 / 100.1 |
| Errors | 4 | 14 | 0 | 0 |

**Whole-system sim** (`../sim_system/`, glue Rev A.1 + U4 Rev A.1 netlists, 4000 random cycles, nominal + 50 % derate × 5 seeds): 0 errors in all 6 runs; DSACK contention events 0; U4 DSACK driven high ≤ 7.5 / released ≤ 17.5 ns after AS↑ (derated ≤ 13.9); hand-over gap from U4 to the next DSACK/BERR/AVEC driver ≥ 21.0 ns (derated ≥ 21.5); U4 DSACK0/1 skew ≤ 0.9 ns (EC #31A ≤ 7); 0 SIMM timing errors; reference-checked DRAM data 0 mismatches; refresh gap ≤ 15 235 ns. The Rev A U4 netlist in the same bench: 7–22 contention events per run (longest 5.9 ns nominal, 15.3 ns derated), U4 released up to 53.7 ns after AS↑, and in every derated run 33–39 false U4 DSACK assertions in non-DRAM cycles (the missed-AS-gap bug below).

**Post-fit timing-check hits.** Setup/recovery hits occur only on the AS_n synchroniser (asynchronous input) and at the release of the AS-driven preset/clear registers (their D equals the preset value there, so the outcome is the same either way). None occur on any register that samples DRAM_SEL_n, A26, SIZ, A1/A0 or R_W.

**Power-up artefact.** The netlist starts with every register at 0, as an ATF15xx does after power-up, so the active-low strobes are low for about 7 ns until the AS_n preset acts. The testbench holds the SIMM inputs high for the first 50 ns.

## Quirks and findings
- **Stale-AS race (found in the Rev A post-fit sim, fixed; still in place).** A level test of the synchronised AS could start a DRAM cycle on the *previous* cycle's AS for up to 40 ns after a short AS-high gap. The RAS registers then missed DRAM_SEL_n (2 array passes) while the 1-pass state flop did not, so CAS was asserted without RAS. The fix: start only on the synchronised AS falling edge (`as_new`), and latch a request (`dreq`) if refresh is busy.
- **Pin registers hold the active-low pin values.** This lets the fitter place RAS/CAS/WE in their pin macrocells: 4.5 ns clock-to-pad and asynchronous PRESET from AS_n. `(* keep *)` stops Yosys merging RAS0/RAS2 and RAS1/RAS3.
- **The optimizer is on here** (it was off for the glue, where it failed). With it off, the worst register path was 21 ns (3 array passes), which does not meet 50 MHz.
- **DSACK outputs (Rev A.1, spec risk 23).** `DSACKx_n = kx ? ~(kx & AS) : Z`. kx is set with CAS (11 ns clock-to-pad) and asynchronously cleared by `AS_n | ~PWR_RST_n`. AS_n↑ drives the pin high in one array pass (7.5 ns) and the clear turns the OE off 17.5 ns after AS_n↑. Two registers, one per pin, because fit1508 fails on a shared enable. Rev A kept the enables on until the second DRAM_CLK edge after AS↑ (≤ 57 ns), which overlapped a following MC68882 cycle (DSACK may come at START + 0, UM §12.6 #19 has no minimum).
  - Paper worst case to the 68882: next AS↓ ≥ AS↑ + #15 (30 ns at 25 MHz, 23 ns at 33 MHz), glue FPU_CS_n ≥ 7.5 ns later (SDF; the ATF minimum is not specified **[VERIFY]**), 68882 DSACK ≥ 0 after that. Gap = 30 + 7.5 − 17.5 = **20.0 ns** (25 MHz), 23 + 7.5 − 17.5 = **13.0 ns** (33 MHz); with a zero CS delay 12.5 / 5.5 ns. Board delay is not included.
- **Missed-AS-gap bug (found and fixed in Rev A.1).** Rev A sampled AS_n directly into as1 (6 ns setup, 20 ns clock). The capture window in the shortest AS-high gap (EC #15: 30 ns at 25 MHz, 23 ns at 33 MHz) is gap − 6 ns − hold: at 25 MHz only ~4 ns more than one clock period, at 33 MHz shorter than a period, so the gap can be missed. The FSM then stays in sAck with the DSACK enables on and asserts DSACK (low) in the next, foreign cycle; a latched `dreq` can also carry over. Seen in the Rev A whole-system derated sim (33–39 false DSACK assertions per 4400 cycles at 25 MHz). Fix: as1 is asynchronously set by AS_n high and held until as2 has seen it (`as1 <= as1 & ~as2`), and the FSM ends a cycle on as3, so any AS-high gap is seen; DSACK is cleared by AS_n itself.
- **Unused pins.** `-pin_keep on` is used. Pins 16/17/18/50 (STERM_n/CBREQ_n/CBACK_n/DS_n) reach U4 only through open solder jumpers. Pin 81 is a spare with a test point.
