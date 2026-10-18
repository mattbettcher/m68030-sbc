# m68030-sbc layout: 220 x 175 mm (Option B condense, 2026-10-17)

KiCad 9.0.2. Board file stays `(version 20241229)`, `generator_version "9.0"`.
Not committed. Schematics were not regenerated (`tools/build.py` not run).

The 275 x 215 mm board and everything it was built from are in `backup/`:
`m68030-sbc-pre-condense-20261017.kicad_pcb` / `.kicad_pro`, and the
schematic sheets, `bom.csv` and the old `LAYOUT.md` in `backup/pre-condense-20261017/`.

## How this board is built (re-runnable)

1. `tools/condense_swaps.py` - edits only the Footprint / Value / MPN (and the
   existing IDE Note) fields of X1-X3, U11-U13, BT1, F1 in the .kicad_sch files.
   Fields that did not exist are not added.
2. `kicad-cli sch export netlist --format kicadsexpr -o /tmp/nl/m68030-sbc.net m68030-sbc.kicad_sch`
3. `tools/condense_layout.py <board> <netlist>` - starts from the pre-condense
   backup, swaps the changed footprints (keeps symbol path / DNP / fields),
   re-applies every pad net from the netlist, places the board, adds the power
   vias / +3V3-island escapes and the planes, fills zones.
4. `tools/nudge_refdes.py <board>` - moves reference texts off other parts' silk/pads.
5. Copy that board to `backup/m68030-sbc-220x175-prelabels-20261017.kicad_pcb`,
   then `tools/add_connector_labels.py` (default SRC is that file; `LABEL_SRC` /
   `LABEL_PCB` env vars override).

Steps 3-5 were run in a scratch copy (`/tmp/condense`) and the result copied in.
`m68030-sbc.kicad_pro` is byte-identical to the GitHub copy (md5 e1e1168f...),
so the netclasses and design rules are untouched.

## Board

- Outline 220 x 175 mm, square corners, Edge.Cuts 0.1 mm. Origin top-left, +Y down.
  Area 385 cm2 (was 591 cm2, -35%).
- Mounting: H1-H4 M3 (`MountingHole_3.2mm_M3_Pad`, GND) at (4.5, 4.5), (215.5, 4.5),
  (4.5, 170.5), (215.5, 170.5).
- Front courtyard utilization 44% (was 31%). Unrouted signal wiring estimate
  (Manhattan MST of all non-power nets) 42.2 m (was 50.7 m).

## Part swaps (schematic fields only, nets unchanged)

| Ref | Was | Now | Footprint |
|---|---|---|---|
| X1 | 25 MHz 5 V DIP-14 can | ECS-3951M-250-BN-TR (5 V HCMOS, 7x5) | `m68030-sbc:Oscillator_SMD_ECS-3951M_7.0x5.0mm_DIP14PinMap` |
| X2 | 50 MHz 5 V DIP-14 | ECS-3951M-500-BN-TR | same |
| X3 (DNP) | DIP-14 | ECS-3951M-200-BN-TR, 20 MHz [VERIFY freq] | same |
| U11-U13 | SN74ACT245N DIP-20 | SN74ACT245DW | `Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm` |
| BT1 | Keystone 103 | Keystone 3034 SMD CR2032 retainer | `Battery:BatteryHolder_Keystone_3034_1x20mm` |
| F1 | T5A 5x20 + Schurter holder | Littelfuse 0454005.MR (NANO2 Slo-Blo 5 A, 125 V) | `Fuse:Fuse_Littelfuse-NANO2-451_453` |

Oscillator pin handling: the symbol is still `Oscillator:CXO_DIP14` (pins 1 EN,
7 GND, 8 OUT, 14 VCC). The project footprint uses the 7x5 4-pad land pattern
(Abracon ASV geometry, 1.8 x 2.0 mm pads on 5.08 x 4.0 mm) with pad numbers
1/7/8/14 on the ECS pads 1 (tri-state) / 2 (GND) / 3 (OUT) / 4 (VDD). Pin 1 is
tied to +5V, which the ECS datasheet treats as enabled (open or >= 2.2 V = run).
[VERIFY land pattern vs ECS "Suggested Land Pattern" figure.]
Battery: footprint pad 1 = the two outer + tabs, pad 2 = the centre - pad,
matching `Device:Battery` pin 1 (+) / pin 2 (-).
Fuse: the KiCad 451/453 land pattern (1.96 x 3.15 mm pads, 2.95 mm gap)
matches the 452/454 datasheet's recommended pad layout.

## Stackup (spec was silent on weight and dielectric)

| Layer | Name | Copper / dielectric | Role |
|---|---|---|---|
| F.Cu | F.Cu | 1 oz / 0.035 mm | signal |
| dielectric 1 | prepreg FR-4 | 0.20 mm, Er 4.3, loss 0.02 | |
| In1.Cu | GND | 1 oz / 0.035 mm | solid ground, not split |
| dielectric 2 | core FR-4 | 1.06 mm, Er 4.3, loss 0.02 | |
| In2.Cu | +5V | 1 oz / 0.035 mm | +5V plane, priority 0 |
| dielectric 3 | prepreg FR-4 | 0.20 mm, Er 4.3, loss 0.02 | |
| B.Cu | B.Cu | 1 oz / 0.035 mm | signal (CPU 100 nF caps only, this pass) |

Finished thickness 1.6 mm. Mask ~0.01 mm green. Copper finish recorded as ENIG.
1 oz is enough for the ~3.9 A design total on a plane.

In2 also has the +3V3 island (see Power below).

Impedance (not a controlled-impedance order): a 0.25 mm F.Cu trace over the
0.20 mm prepreg to the GND plane is about 59 ohm (IPC-2141 style, Er 4.3).
Bottom traces would reference +5V, so clocks and DRAM were intended to stay on
top. They are not routed yet. Default netclass: 0.20 mm trace, 0.15 mm
clearance, via 0.60/0.30. The power stitches used here are 0.30 mm traces and
0.75/0.35 vias.

## Placement (220 x 175)

Courtyard-centre anchors in `tools/condense_layout.py` (`ANCHORS`); passives are
placed next to the pins they serve, decaps on their host's supply pin.

- Top edge: J1 SIMM centred at x 110 (51.6-168.4), J4 JTAG U3 (30, 8), J5 JTAG U4 (186, 8).
- Left edge: J10 DIN 41612 (8, 62), y 14-110. J2 barrel jack, opening out the left edge, y 150.
- Core column under the SIMM centre: U4 DRAM CPLD (110, 33) between the SIMM and
  the CPU; U1 PGA (110, 79) with the 40 x 40 heatsink keepout (90-130, 59-99).
  U3 glue CPLD left (70, 78), U2 FPU right (149, 78).
  Centre-to-centre: CPU-SIMM 71 mm (was 162), CPU-U4 46 (was 108), CPU-DIN 119 (was 203).
- DRAM: U801-U803 (DNP mux) at y 22 right of U4, series R / caps around U4, X2 (139, 56)
  between U4 and the FPU.
- Clocks: U10 (174.5, 70), X1 (174.5, 86), X3 DNP (174.5, 95), JP3 nearby, between the FPU and the LA block.
- LA headers J11/J12/J13: parallel block at x 188 / 199 / 210, y 62-114, 11 mm pitch,
  beside the FPU and CPU instead of along the edge.
- Expansion buffers U14-U21: 2 x 4 SOIC-20W block beside the DIN, x 18-46, y 17-85, decaps in the gaps.
- ROM U5 (60, 118), DUART U6 (85, 120), Y1 beside U6, BT1 (88, 150).
- +3V3 cluster: U23 RTC (114, 148), U22 (132, 146), U9 3V3 reg (140, 160), J9 SPI (124, 168), TP203.
- IDE: U11-U13 SOIC-20W at y 140 (x 158/173/188), J6 IDE (180, 164) on the bottom edge.
- Power bottom-left: L1 (13.5, 122), U8 (34, 136), Q1, F1, C204 and the tantalums next to J2.
- Bottom edge: J7 / J8 TTL serial, SW1-SW3, J9, J6 at the same edge offsets as before.
- C501-C510 (CPU 100 nF) on B.Cu in a ring just outside the PGA pins, as before.

## Power

- In1 GND: one solid zone, board inset 0.6 mm. In2 +5V: one zone, no hole.
  In2 +3V3 island, priority 1, x 103-147, y 136-174.4 mm; it knocks +5V out.
- Every SMD power pad has a 0.30 mm stub to a 0.75/0.35 via (333 vias). Pads >= 3 mm
  (BT1 centre, U8 tab) get vias in the pad. No signal tracks.
- +3V3 vias are kept inside the island, +5V vias outside it. The +5V pads inside the
  island are escaped on F.Cu to vias outside: U9.3, J9.2, C1002.1, R1002.1, R1003.1.
  (Signals were routed afterwards, see "Scripted full route".)
- No edge GND stitch vias: with GND only on In1 they have nothing to stitch to
  (DRC flags them as dangling). Add them back if F/B GND pours are added.

## DRC (kicad-cli, schematic parity on)

Routed board (2026-10-18): 0 errors, 0 parity issues, **0 unconnected**, 5 warnings
(3 silk_overlap, 2 silk_over_copper, reference texts that could not be moved; same as before routing).
ERC 0 / 0.

## Silkscreen connector labels

`tools/add_connector_labels.py` (group `connector_labels`), re-run on the new
placement. All function labels and pin names placed; JP801/JP802 use the
two-line legend. The jumpers that carry labels get 2.4 mm (JP3 3.2 mm) of
room in `condense_layout.py` (`LABEL_ROOM`).

## Routing

**Fully routed on 4 layers (2026-10-18), all 499 connections, by a scripted grid router** — see
"Scripted full route" below. The autoroute tests further down are the earlier scratch experiments.

### Scripted full route (4L, 2026-10-18)

Signals only on F.Cu and B.Cu; In1 GND and In2 +5V (+3V3 island) stay solid planes. Backup of the
unrouted board, project and sheets: `backup/pre-route-20261017/` (progress log `PROGRESS.md` there).
Tools: `tools/route/` (re-runnable; work dir was /tmp/route).

- Router: own grid router, not FreeRouting. Grid 2.54/6 = 0.4233 mm aligned to the U1 PGA pins,
  so a 1.27 / 2.54 mm pin field has a track lane exactly in the middle of every pin gap.
  Orthogonal 0.20 mm tracks (0.25 mm for the CLK_DRAM class, `.kicad_pro` unchanged), 0.6/0.3 vias.
  Obstacles come from the real pad/track/via polygons with 0.16 mm (0.15 rule + margin) clearance,
  0.2 mm hole clearance, 0.25 mm hole-to-hole and 0.3 mm edge clearance.
  A* in C (`astar.c`) with bend and via costs. PathFinder negotiated congestion (`router.py`, `run.py`)
  across all 346 nets until no grid cell is shared. `writer.py` writes the tracks/vias **locked**.
- Order (as requested):
  1. The 53 two-pin clock and DRAM nets were routed first, alone, and then frozen as hard obstacles:
     clocks and series terminations, U4 → R804-R824, R → SIMM. Clocks cost 2× on B.Cu, so they
     stay on F.Cu over In1 GND.
  2. Then the multi-pin DRAM nets (RAS/CAS/WE with their LA/TP branches), the CPU nets, the
     FPU/glue/ROM/DUART/LA buses and the rest, in that priority, negotiated together.
- PGA escape: 4 layers have no inner signal layer, so "channel vias" can't help inside the PGA field.
  Each 2.54 mm gap carries 1 track per layer (F and B). The router ran the escape together with the
  other nets in the new CPLD bus order instead of a separate fanout pass. All 120 U1 signal pins escaped.
- Placement nudges: 55 ICs/connectors/jumpers (U*, J*, JP*, X*, SW*, Y1; not U1) were moved by
  ≤ 0.212 mm so their pins sit on the grid. Their power stubs moved with them.
  Without this, the staggered SIMM rows had no lane between pads, and MA1/3/5/10 took 40-55 mm detours.
- DNP fallback removed: U801-U803 and R829-R838, all `dnp yes` in `dram.kicad_sch`, now
  `(on_board no)` there. Their 13 power stubs and vias went with them. R825-R828 are fitted pull-ups and
  were kept. C818-C820 (DNP decaps) were kept.
- Result: 100 % routed. 2453 signal vias, 56.1 m of signal track (F 27.3 m, B 28.8 m), all locked.
  In1 GND fills 33,400 mm² in one piece (87 % of the board after via antipads), In2 +5V 31,600 mm².
- Clocks (length / vias; % on F.Cu):

  | Net | Length / vias | On F.Cu |
  |---|---|---|
  | CLK_CPU | 75 mm / 2 | 87 % |
  | CLK_GLUE | 109 / 0 | 100 % |
  | CLK_FPU | 26 / 0 | 100 % |
  | CLK_DRAMC | 38 / 0 | 100 % |
  | DRAM_CLK | 37 / 0 | 100 % |
  | CLK_LA | 28 / 0 | 100 % |
  | CLK_EXP | 147 / 2 | 98 % |
  | CLK_FPU_CPU | 52 / 2 | 96 % |
  | CLKB_* (driver to series R) | 15-98 / 0-2 | — |

- DRAM:
  - U4 → series R (U4_MA*): 3-38 mm, 0-1 via.
  - R → SIMM (MA0-11): 3-9 mm.
  - RAS2/3 3-6 mm, RAS1 40 mm, CAS0 24, CAS2 40, CAS1 84 mm.
  - RAS0_n 325 mm / 17 vias, CAS3_n 232 / 7 and WE_n 224 / 5. These include their branches to TP80x and LA J13.
- Risky areas:
  - The long SIMM-side RAS0/CAS3/WE nets: the LA/TP branch is an unterminated stub.
  - CLK_EXP (147 mm to the DIN) and CLK_GLUE (109 mm) are long because of the oscillator/buffer
    placement (U10 at the right-hand side).
  - Series Rs sit at the SIMM, up to 38 mm from U4 (source termination is less effective at that distance).
  - Orthogonal-only routing with many vias (≈ 2450). Rows of antipads perforate In1/In2 under the
    buses, but both planes stay in one piece.
  - Not yet checked: crosstalk on long parallel bus runs. Hand clean-up (45° corners, via
    reduction) is cosmetic and was not done.

### Autoroute test (scratch only, 2026-10-17)

FreeRouting 2.5.0 on OpenJDK 25 (`/opt/freerouting`), DSN exported with pcbnew
`ExportSpecctraDSN` from a scratch copy, fanout + 2 routing passes, optimizer off,
29 min wall time. Session imported into `/tmp/autoroute/m68030-sbc-autorouted.kicad_pcb`
only; the main board has no signal tracks. Image: `renders/m68030-sbc-220x175-autoroute-4L.png`.

- Fanout: 410 of 805 SMD pins escaped (51%).
- FreeRouting: 489 of 850 items still unrouted after pass 2 (586 after pass 1).
  A parallel 25-pass run gave the same 489 after its second pass (14 min per pass)
  and was stopped.
- KiCad DRC on the imported board: 362 of 499 connections still open, so 27%
  completed. About 335 new vias, 16.1 m of track (power stubs included).
  0 shorts or clearance errors; 6 track_width errors and 71 dangling fanout vias,
  all from the router.
- Open ends by part: U1 PGA 155, U2 FPU 77, U3 and U4 55 each, LA J11-J13 78,
  J1 SIMM 36, J10 DIN 29. The PGA escape and the 32-bit buses fanning out to the
  CPLDs, FPU and LA block are where it fails.
- Verdict: with only F.Cu and B.Cu for signals, 4 layers will not route at
  220 x 175 by autorouter, and a hand route would be very hard. Go to 6 layers
  (e.g. F sig / GND / sig / sig / +5V(+3V3) / B sig), or route the PGA
  escape and buses by hand. Re-run the same test on a 6-layer scratch copy before
  committing to that.

### CPLD pin swap, Rev A.2 (2026-10-17)

U3 (glue) and U4 (DRAM) user pins were re-assigned to match the bus order at the CPU, FPU,
SIMM, LA headers and DIN in this placement (the owner allowed moving the locked pins).
Details and the old-to-new pin tables are in `cpld/glue/README.md` and `cpld/dram/README.md`.

- Method (`tools/cpld_pinswap_opt.py`, `_assign.py`, `_search_u4.py`): cost = straight
  distance from each CPLD pad to the nearest other pad of the net. Hungarian assignment,
  then pairwise swaps with a 4 mm penalty per crossing. Dedicated pins, JTAG, power, the
  jumpered pins and TP pins stay fixed. Rotating either CPLD gained <= 1.5 %, so neither was rotated.
- Result: U3 57 pins moved, 2784 -> 2369 mm, 254 -> 0 crossings. U4 54 pins moved,
  1598 -> 1296 mm, 372 -> 8 crossings. The U4 optimum with no limits was 1191 mm / 0, but
  fit1508 then lost all 9 cascades (19.5 ns instead of 14.0 ns), so a search with the fitter
  in the loop kept the timing.
- Fits: glue 121/128 MC, 20.3 ns. DRAM 78/128 MC, 14.0 ns. Both are the same as Rev A.1.
  All CPLD and system sims: 0 errors, 0 DSACK contention.
- Schematic: the label edits were made in place (`tools/cpld_pinswap_sch.py`, not build.py).
  On the glue sheet the short bus stubs at U3 were replaced by plain labels. ERC 0 / 0.
- PCB (`tools/cpld_pinswap_pcb.py`): 111 U3/U4 pad nets updated from the netlist.
  R804-R824 (33R U4 series resistors) moved to B.Cu in one row at y 13.9 under the SIMM
  pins, in SIMM pin order. Their refdes are hidden; a B.SilkS note marks the row.
  DRC is unchanged: 0 errors, parity 0, 499 unconnected, 5 silk warnings.
- Backup of everything before the swap: `backup/pre-pinswap-20261017/`.

### Autoroute re-test after the pin swap (scratch only)

Same flow and caps as before: FreeRouting 2.5.0, optimizer off, fanout + 2 passes (4L) /
+ 1 pass (6L, F/In1 sig, In2 GND, In3 +5V/+3V3, In4/B sig), run in parallel, about 29 min.
Scratch boards are in `/tmp/autoroute_ps/{4L,6L}`. Images:
`renders/m68030-sbc-220x175-pinswap-autoroute-4L.png` and `-6L.png`.
Open-end counts use the same method as the earlier runs (pads still on the KiCad ratsnest).

| | 4L before | 4L after | 6L before | 6L after |
|---|---|---|---|---|
| Fanout escaped | 410/805 | 445/805 | 669/805 | 670/805 |
| Open connections (of 499) | 362 | 337 | 373 | 350 |
| Completion | 27 % | 32.5 % | 25 % | 29.9 % |
| U1 CPU | 138 | 89 | 135 | 115 |
| U2 FPU | 55 | 44 | 44 | 50 |
| U3 glue | 46 | 30 | 36 | 30 |
| U4 DRAM | 44 | 18 | 47 | 14 |
| J1 SIMM | 34 | 21 | 45 | 44 |
| J10 DIN | 29 | 29 | 26 | 26 |
| J11/J12/J13 LA | 26/31/21 | 28/21/23 | 30/28/20 | 27/30/26 |

After the swap: 4L has 305 signal vias and 15.4 m of signal track; 6L has 420 vias and 13.4 m.
Both still have router artefacts: 11 track_width errors each, and 78 (4L) / 127 (6L) dangling fanout vias.

- The swap roughly halved the open ends at U4 and cut U3 by about a third. U1 also dropped
  a lot on 4L, because fewer CPLD nets compete for its escape. Completion went up about
  5 points on both stackups. The board is still far from routed: about 2/3 open.
- The CPU PGA escape is still the main blocker (U1 89 / 115 open ends), then the FPU and LA headers.
  A hand fanout would need, for the 13x13 PGA-128 on a 2.54 mm grid: a dogbone or via-in-channel
  plan, with one 0.2 mm track between pins on each signal layer (0.6/0.3 vias fit in the
  pin channels). Escape the outer two rings on F/B. Escape the inner rings on In1/In4 (6L)
  through vias placed in the channel diagonals. Fix the bus order of D0-31 / A0-31 at the PGA
  edge to match the new CPLD/FPU/LA order. The C501-C510 B.Cu decaps limit the B.Cu channels.
  Then re-run the autoroute with the fanout locked. Not done.
- The DNP fallback parts (U801-U803, R825-R838) still add routing load. Removing them
  is a candidate cleanup.

### SI fix: DRAM resistors, strobe stubs, clocks (2026-10-18)

Backup of the pre-fix board and sheets: `kicad/backup/pre-sifix-20261018/` (pcb sha1 07fb0239…). All signal tracks were stripped, parts moved, and the board re-routed with the scripted router (`kicad/tools/route/sifix/`). Result: 100% routed, DRC 0 errors, 0 unconnected, parity 0, ERC 0/0, `.kicad_pro` unchanged. 53.84 m signal track, 2365 vias (was 56.12 m / 2453).

- **DRAM 33R (R804–R824):** all on B.Cu right next to U4. Pad-to-U4-pin distance is now 1.6–6.9 mm (was 2.9–27.2 mm).
- **RAS0_n / CAS3_n / WE_n:** J13 (LA3) pins 37/38/39 are now no-connect in `debug.kicad_sch`. J13 is ~190 mm from the SIMM, so a daisy chain was not an option. TP801/TP806/TP807 moved next to the SIMM-side resistors at y 14.4. Totals: RAS0_n 27.5 mm/1 via (TP inline), CAS3_n 17.8 mm/0 (TP stub 13.5 mm), WE_n 17.4 mm/1 (TP stub 9.7 mm). Was 325/17, 232/7, 224/5.
- **Clock block moved** to the left of U4, above U3: U10 (62.2, 38.2), X1 (61.3, 49.3), R301–R306 at 3.3 mm from the U10 pins, plus C301/C302/C305/C306. R307 moved to the X2 output and R308 to the X3 output. C304 moved too.
- **U10 output swap** (`clock.kicad_sch` labels only; all inputs are still OSC_CPU): pin 18 = CLKB_DRAMC, pin 14 = CLKB_CPU, pin 12 = CLKB_GLUE. Pins 16 (FPU), 3 (LA) and 5 (EXP) are unchanged.
- Clocks route mostly or entirely on F.Cu over In1 GND (B.Cu was cost-weighted 4× for clocks). CLK_CPU 57/0, CLK_GLUE 22/0, CLK_EXP 56/0, CLK_DRAMC 62/0, CLK_FPU_CPU 70/0, DRAM_CLK 59/0, CLK_LA 202/2, CLKB_X3 80/0 (mm/vias).
- The JP801/JP802 legend was rotated 90° and placed between the jumpers at (78, 40).
- **Note:** `build.py` / `sheet_debug.py` / `sheet_clock.py` do not contain these schematic edits. Re-running them would undo the J13 NC and the U10 swap.

### 45° chamfer pass (2026-10-18)

Backup of the board before this pass: `backup/pre-45deg-20261018/` (pcb sha1 2221a671…).
Tool: `tools/route/chamfer45/` (`chamfer.py` → `write45.py` → `fill.py`; `angles.py` counts the bends).
Placement, vias and layers are unchanged. Only signal tracks on F.Cu/B.Cu were edited; the power stubs were left as they were.

- Method:
  - At each 90° corner, cut both legs by the same amount c and join the cut points with a 45° segment.
  - c is the largest value that fits the clearance check. The first try is the full length available. That is half a leg when the leg's other end is also a corner, otherwise the whole leg (stopping at T-junctions, vias and same-net pads). Then it falls back through 3.0 … 0.1 mm.
  - Each try is checked at 0.16 mm against other-net tracks, pads, vias and footprint copper. Holes are checked at 0.21 mm and the board edge at 0.31 mm.
  - It never makes an acute angle. It repeats until nothing changes, then merges collinear runs (6099 merges). Single-grid jogs and staircases became one diagonal.
- Result:
  - 14,403 chamfers. Sizes: 7477 at 0.21 mm (half-grid jog), 3174 at 0.22–0.42, 2380 at 0.43–1.0, 978 at 1–2 and 257 over 2 mm (up to 8.9).
  - 90° bends went from 14,456 to 43:
    - 14 sit on a via centre.
    - 25 are inside the copper of a same-net pad.
    - 4 had no room: DUART_X2 at (101.5, 118.4) on B.Cu, and J10_D3/D6/D12 at the J10 edge pins (x 7.55).
  - Signal track 53.84 → 49.87 m (−7.4 %). Vias 2365, unchanged. No net got longer.
- SI nets (mm, before → after; vias unchanged):

  | Net | Before | After |
  |---|---|---|
  | CLK_CPU | 57.2 | 54.3 |
  | CLK_GLUE | 21.6 | 21.1 |
  | CLK_EXP | 56.3 | 53.9 |
  | CLK_DRAMC | 61.8 | 59.4 |
  | CLK_LA | 201.9 | 195.6 |
  | CLK_FPU_CPU | 70.3 | 67.8 |
  | CLK_FPU | 25.8 | 24.0 |
  | DRAM_CLK | 59.3 | 57.7 |
  | CLKB_X3 | 80.4 | 79.1 |
  | OSC_CPU | 36.8 | 34.2 |
  | RAS0_n | 27.5 | 24.5 |
  | CAS3_n | 17.8 | 16.5 |
  | WE_n | 17.4 | 16.6 |

- DRC 0 errors, 0 unconnected, parity 0; 4 silk warnings (same as before). ERC 0/0. `.kicad_pro` unchanged.
- Renders: `renders/m68030-sbc-45deg-{top,bottom,zoom}.png`. The zoom covers x 70–118, y 40–76 mm (U3 right edge, U1 top-left, U4 bottom).

### De-hitch / pull-tight pass (2026-10-18)

Backup of the 45° board: `backup/pre-dehitch-20261018/` (sha1 aae84342…). Tool: `tools/route/dehitch/`.
Placement, vias and layers are unchanged; only signal tracks on F.Cu/B.Cu were edited.

Method: each track path between fixed points (pads, vias, T-junctions; tracks split there first) is rebuilt in three steps:

1. **Pull-tight.** A DP over the path's vertices finds the fewest octilinear segments, using straight or straight+45° links. Every bend must be ≤ 45°. A track end that sits alone in a pad may slide inside the pad.
   - The first passes require ≥ 0.20 mm clearance on every new segment.
   - Later passes allow min(0.20, the old gap), but only if the path gets no more sub-0.2 mm gaps and its worst gap does not get smaller.
2. **Leg shift.** For jogs under 1 mm, a run is moved sideways to line up with the next run. The offset is absorbed by the nearest segment parallel to the offset, or by a pad end. This works on orthogonal and diagonal runs.
3. Repeat until nothing improves.

| Metric | 45° board | De-hitched |
|---|---|---|
| Signal segments | 18,293 | 13,407 |
| Jogs (S offsets) total / under 1 mm | 8,400 / 5,694 | 4,457 / 2,217 |
| Bends | 15,211 | 10,267 |
| Signal length | 49.866 m | 49.628 m |
| Vias | 2,365 | 2,365 |
| Segments with nearest other-net gap < 0.20 mm | 799 (129 at 0.16–0.18) | 674 (112 at 0.16–0.18) |
| Track-to-object pairs < 0.20 mm | 1,030 | 867 |

- No SI net got longer: RAS0_n 24.54 → 24.15 mm, and every other SI net is unchanged. 19 non-SI nets grew by ≤ 0.5 mm from leg shifts.
- About 2,175 jogs under 1 mm remain inside paths:
  - **1,008** could only go by dropping below 0.20 mm. They were kept for margin. A test run at 0.16 mm removed just 78 more jogs and raised the < 0.2 mm pairs to 1,219.
  - **703** can't be shifted without a > 45° bend, a reversed segment, or an odd-nm offset on a diagonal.
  - **340** sit between a fixed via and the next bend. Removing them needs a via move.
  - **124** end at a multi-track pad or T-junction.
  - Most are real lane changes in the dense buses: the lane on the other side of the jog belongs to another net.
- DRC 0 errors, 0 unconnected, parity 0; 4 silk warnings (same as before). ERC 0/0. `.kicad_pro` unchanged.
- Renders: `renders/m68030-sbc-dehitch-{top,bottom,zoom}.png`. The zoom covers the same x 70–118, y 40–76 mm window as `-45deg-zoom`.

## Unverified, left as drawn

- SIMM locating holes stay NPTH as drawn (1.63 mm pin-1 end and center, 2.41 mm far end). Plating vs TE 114-1061 is unverified. No extra holes were added.
- J10 is the stock `DIN41612_C_3x32_Female_Vertical_THT`, not a HARTING-specific model.
- PGA-128 pin numbering still [VERIFY] against UM Fig. 14-1 (schematic issue, not changed here).
- No 3D models on: PGA128_13x13_MC68030, SIMM-72_TE-5822021-4, MountingHole_3.2mm_M3_Pad, the solder jumpers, TestPoint_Pad_D1.5mm. Stock footprints point at `${KICAD9_3DMODEL_DIR}`, which is not installed, so the iso render is pads and silk only.

