m68030-sbc fab package (generated 2026-10-18, kicad-cli 9.0.2)
Source: mattbettcher/m68030-sbc main 518235d, kicad/m68030-sbc.kicad_pcb sha1 e88d2ee4be5342bb682cc3360b67b241962ccb94
(the zones were refilled before DRC and plotting; the copy used for plotting has identical design data)

Board: 220.0 x 175.0 mm, 4 layers, 1.6 mm, ENIG (from the job file)
Stack-up: L1 F.Cu signal / L2 In1.Cu GND plane / L3 In2.Cu +5V plane (+3V3 island) / L4 B.Cu signal
Min track 0.20 mm; design-rule clearance 0.15 mm (measured track-to-copper minimum 0.162 mm); plane clearance 0.20 mm
Vias: 2685 (2365 at 0.6/0.3 mm, 320 at 0.75/0.35 mm); min drill 0.30 mm; PTH and NPTH are in separate Excellon files (mm)

gerbers/  Gerbers with Protel extensions, gerber job file, PTH/NPTH .drl files and drill map PDFs
          (inner layers renamed to m68030-sbc-In1_Cu.g1 / -In2_Cu.g2; the .gbrjob was updated to match)
check/    gerbv renders of the In1 (GND) and In2 (+5V/+3V3) gerbers, to show the planes are filled
          topleft.png: annotated top-left corner (H1 M3 mounting hole, J10 NPTH), all intended
m68030-sbc-bom.csv  BOM grouped by value+footprint. The Section column is one of Fitted / DNP / PCB feature (no part) / Extra (not a footprint)
m68030-sbc-pos.csv  placement file (mm, both sides, DNP and PCB-only features excluded; bottom-side coordinates not mirrored)
m68030-sbc-drc.rpt  DRC report (0 errors, 0 unconnected, parity 0; 4 silkscreen warnings)
