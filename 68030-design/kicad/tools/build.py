#!/usr/bin/env python3
"""Generate the m68030-sbc KiCad 9 project. Run from anywhere: python3 tools/build.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_common import *
from signals import SHEETS, TITLES, SPECREF, ORDER
from sheet_power import build_power
from sheet_clock import build_clock
from sheet_reset import build_reset
from sheet_cpu import build_cpu
from sheet_fpu import build_fpu
from sheet_glue import build_glue
from sheet_dram import build_dram
from sheet_rom import build_rom
from sheet_ide import build_ide
from sheet_expansion import build_expansion
from sheet_debug import build_debug
from sheet_duart import build_duart
from mklib import build as build_lib

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PAGES = {n: i + 2 for i, n in enumerate(ORDER)}

def build_stub(P, name):
    t = TITLES[name].replace(" — STUB", "")
    sh = P.sub(name, t + " (STUB)", PAGES[name])
    sh.comments = ["STUB SHEET - interface only. Circuit not drawn yet.", "Source: " + SPECREF.get(name, "spec.md")]
    sh.text("STUB - " + t, 38.1, 45.72, 3.0, bold=True)
    sh.text("Interface (hierarchical labels) per spec.md inter-sheet signal list.\\nCircuit to be drawn from: " + SPECREF.get(name, "spec.md") +
            "\\nUnconnected hierarchical labels on this sheet are expected ERC findings until it is drawn.", 38.1, 55.88, 1.5)
    L, R = SHEETS[name]["L"], SHEETS[name]["R"]
    for i, (n, shape) in enumerate(L):
        col, row = divmod(i, 40)
        sh.hlabel(n, shape, 76.2 + col * 76.2, 81.28 + row * 5.08, 180)
    for i, (n, shape) in enumerate(R):
        col, row = divmod(i, 40)
        sh.hlabel(n, shape, 330.2 - col * 76.2, 81.28 + row * 5.08, 0)
    return sh

def main():
    build_lib(os.path.join(OUT, "lib", "m68030-sbc.kicad_sym"))
    P = Project(OUT)
    sheets = {}
    builders = {"power": build_power, "clock": build_clock, "reset": build_reset, "cpu": build_cpu, "fpu": build_fpu, "glue_cpld": build_glue, "dram": build_dram, "rom": build_rom, "duart_spi_rtc": build_duart, "ide": build_ide, "expansion": build_expansion, "debug": build_debug}
    for n in ORDER:
        sheets[n] = builders[n](P) if n in builders else build_stub(P, n)
    # interface cross-check for drawn sheets
    for n, sh in sheets.items():
        got = {}
        for nm, shp in sh.hlabels:
            got[nm] = shp
        want = {nm: shp for nm, shp in SHEETS[n]["L"] + SHEETS[n]["R"]}
        if set(got) != set(want):
            print("INTERFACE MISMATCH", n, "missing:", sorted(set(want) - set(got)), "extra:", sorted(set(got) - set(want)))
        for nm in got:
            if nm in want and got[nm] != want[nm]:
                print("SHAPE MISMATCH", n, nm, got[nm], want[nm])
    # root layout (A2 = 594 x 420 mm)
    R = P.root
    R.comments = ["68030 Linux SBC - hierarchical top level. Design spec: ../spec.md",
                  "PGA-128/SIMM-72 footprints + pin maps: Mackerel-68k (MIT, C. Maykish)",
                  "Drawn: power, clock, reset, cpu, fpu, glue_cpld, dram, rom, duart_spi_rtc, ide, expansion, debug. No stub sheets"]
    cols = [["power", "clock", "reset"], ["cpu", "fpu"], ["glue_cpld", "rom"], ["dram", "duart_spi_rtc", "ide"], ["expansion", "debug"]]
    W = 55.88
    for ci, col in enumerate(cols):
        x = 50.8 + ci * 111.76
        y = 50.8
        for n in col:
            sh = sheets[n]
            seen = []
            for nm, shp in sh.hlabels:
                if nm not in [s[0] for s in seen]:
                    seen.append((nm, shp))
            left = [s for s in seen if s[1] in ("input", "passive")]
            right = [s for s in seen if s[1] not in ("input", "passive")]
            h = P.place_sheet(sh, x, y, W, left, right)
            y = snap(y + h + 30.48, 2.54)
    R.text("68030 Linux SBC - rev A draft (KiCad 9). Sheets in page order: 2 power, 3 clock, 4 reset, 5 cpu, 6 fpu, 7 glue_cpld, 8 dram,\\n"
           "9 rom, 10 duart_spi_rtc, 11 ide, 12 expansion, 13 debug. All sheets drawn.",
           50.8, 20.32, 2.0, bold=True)
    R.text("Attribution: lib/m68030-sbc.pretty/PGA128_13x13_MC68030 and SIMM-72_Mackerel, and the MC68030 / MC68882 pin maps,\\n"
           "are derived from Mackerel-68k by Colin Maykish (MIT License, see lib/LICENSE-mackerel-68k.txt). Pin numbers re-verified against\\n"
           "the MC68030 User's Manual sect. 14 and MC68882 BR509 - see NOTES.md.", 50.8, 368.3, 1.5)
    for i in range(4):
        x = 58.42 + i * 20.32
        h = R.sym("Mechanical:MountingHole_Pad", "H%d" % (i + 1), "M3", x, 347.98, 0, fp="MountingHole:MountingHole_3.2mm_M3_Pad",
                  ref_at=(x + 2.54, 345.44), val_at=(x + 2.54, 347.98))
        p = h.pin(1)
        R.power("GND", p[0], p[1], 0)
    R.text("Mounting holes (plated, to GND)", 50.8, 337.82, 1.27)
    files = P.write()
    print("\n".join(files))

if __name__ == "__main__":
    main()
