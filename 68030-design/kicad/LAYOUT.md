# m68030-sbc first-pass layout

KiCad 9.0.2. Board file stays `(version 20241229)`, `generator_version "9.0"`.
No commit. Schematics were not regenerated. `tools/build.py` was not run.

## Board

- Outline 275 x 215 mm, square corners (no radius), Edge.Cuts width 0.1 mm.
  Origin is the top-left corner, +Y down. Spec did not set a size; this is the
  smallest rectangle that fit the parts with connectors on the edges.
- Mounting: H1–H4, M3 (`MountingHole_3.2mm_M3_Pad`, net GND), centers
  (8, 8), (267, 8), (8, 207), (267, 207) mm.

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

In2 also has a +3V3 island, priority 1, about x 106.7–147.9 mm, y 161.3–213 mm
(J9 / U9 / U22 / U23). No hole was cut in the +5V outline; the higher priority
knocks +5V out. +5V SMD/PTH pins inside that island are escaped on F.Cu to vias
outside it (U9.3, R1002.1, R1003.1, C1002.1, J9.2).

Impedance (not a controlled-impedance order): a 0.25 mm F.Cu trace over the
0.20 mm prepreg to the GND plane is about 59 ohm (IPC-2141 style, Er 4.3).
Bottom traces would reference +5V, so clocks and DRAM were intended to stay on
top. They are not routed yet. Default netclass: 0.20 mm trace, 0.15 mm
clearance, via 0.60/0.30. The power stitches used here are 0.30 mm traces and
0.75/0.35 vias.

## Placement

Courtyard-center style anchors are in the board; footprint anchors below are
KiCad origins (mm).

- Top edge: J1 SIMM (anchor 92.4, 7.2), J4/J5 JTAG (44.9, 16.8) and (216.9, 16.8), rot 90.
- Left edge: J10 DIN 41612 (9.7, 55.6), J2 barrel jack (15.0, 163.0). The jack opening is the footprint's −X side, so it faces out.
- Right edge: J11/J12/J13 LA headers, anchors x=266.7, y=25.9 / 85.9 / 145.9.
- Bottom edge: J7/J8 (29.6, 208) and (53.6, 208), SW1–SW3, J9 SPI (122.9, 207.3, rot 90), J6 IDE (160.9, 204.8, rot 90).
- CPU cluster: U4 DRAM CPLD under the SIMM (150, 36.8), U3 glue (100, 92.8), U2 FPU (150, 95.3), U1 PGA (anchor 192.8, 86.8; body center ~208, 102). 40×40 mm stick-on heatsink rectangle on F.Fab and User.Comments, centered on the PGA.
- U5 flash (99.3, 144.9), U6 DUART (133.3, 151.7), Y1 (112, 174.4, rot 90).
- Clocks near the middle: U10 (180, 142), X1 (150, 142), X2 (214, 144), X3 DNP (228, 166).
- Power bottom-left, away from the oscillators: U8 (53.9, 168), J2 on the left edge.
- Expansion buffers just right of J10. IDE buffers above J6.
- C501–C510 (the ten 100 nF CPU caps) are on the bottom, in a ring outside the PGA. 0805 does not fit between the PGA pads (1.42 mm pad on 2.54 mm pitch) and stacking was not allowed. Spec §6.3 "under the socket" is not met.

## Routing

Only GND, +5V, and +3V3 have tracks or vias (302 segments, 299 vias). Every other net is unrouted on purpose. A first signal route (clocks and short DRAM stubs) was thrown out: it crossed the power stitches and DRC showed dozens of shorts. FreeRouting was not used (Java is not installed; the jar lives in a different project that was left untouched).

## Unverified, left as drawn

- SIMM locating holes stay NPTH as drawn (1.63 mm pin-1 end and center, 2.41 mm far end). Plating vs TE 114-1061 is unverified. No extra holes were added.
- J10 is the stock `DIN41612_C_3x32_Female_Vertical_THT`, not a HARTING-specific model.
- PGA-128 pin numbering still [VERIFY] against UM Fig. 14-1 (schematic issue, not changed here).
- No 3D models on: PGA128_13x13_MC68030, SIMM-72_TE-5822021-4, MountingHole_3.2mm_M3_Pad, the solder jumpers, TestPoint_Pad_D1.5mm. Stock footprints point at `${KICAD9_3DMODEL_DIR}`, which is not installed, so the iso render is pads and silk only.
