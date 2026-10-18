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
- No edge GND stitch vias: with GND only on In1 they have nothing to stitch to
  (DRC flags them as dangling). Add them back if F/B GND pours are added.

## DRC (kicad-cli, schematic parity on)

0 errors, 0 parity issues, 499 unconnected (signals, intentional), 5 warnings
(3 silk_overlap, 2 silk_over_copper, reference texts that could not be moved).

## Silkscreen connector labels

`tools/add_connector_labels.py` (group `connector_labels`), re-run on the new
placement. All function labels and pin names placed; JP801/JP802 use the
two-line legend. The jumpers that carry labels get 2.4 mm (JP3 3.2 mm) of
room in `condense_layout.py` (`LABEL_ROOM`).

## Routing

Signals unrouted on purpose. Test autoroute: see "Autoroute test" below.

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

## Unverified, left as drawn

- SIMM locating holes stay NPTH as drawn (1.63 mm pin-1 end and center, 2.41 mm far end). Plating vs TE 114-1061 is unverified. No extra holes were added.
- J10 is the stock `DIN41612_C_3x32_Female_Vertical_THT`, not a HARTING-specific model.
- PGA-128 pin numbering still [VERIFY] against UM Fig. 14-1 (schematic issue, not changed here).
- No 3D models on: PGA128_13x13_MC68030, SIMM-72_TE-5822021-4, MountingHole_3.2mm_M3_Pad, the solder jumpers, TestPoint_Pad_D1.5mm. Stock footprints point at `${KICAD9_3DMODEL_DIR}`, which is not installed, so the iso render is pads and silk only.

