#!/usr/bin/env python3
"""Footprint for the TE Connectivity 5822021-4 72-position SIMM socket (vertical, tin, metal latches).
Source: TE customer drawing ENG_CD_5822021_B1 (datasheets/TE_5822021_CD.pdf), "RECOMMENDED P.C. BOARD HOLE
PATTERN, SOCKET SIDE":
  contacts dia 1.02 +/-0.08 [.040], pitch 1.27 [.050], two staggered rows 2.54 apart, A = 95.25 (pin 1 .. pin 72);
  housing 115.57 (B) x 7.37; holes 8.26 [.325] beyond the outer contacts: dia 1.63 +/-0.03 at the pin-1 end and
  at the centre (47.625 from pin 1, between pins 36 and 37), dia 2.41 +/-0.03 at the pin-72 end.
Contact layout is the same as Mackerel-68k's SIMM-72 footprint (pin 1 at 0,0; odd pins row y=0, even pins y=2.54),
which is TE's view rotated 180 deg.  Fixes vs the Mackerel footprint: contact drill 0.762 -> 1.02, centre hole
2.45 -> 1.63, pin-72-end hole 2.45 -> 2.41 (pin-1-end hole 1.63 was already right).
The three locating holes are made non-plated here [VERIFY against TE application spec 114-1061 before layout]."""
import os, uuid
NS = uuid.UUID("5a1d2c1e-7a55-4f0e-9d6a-68030c0ffee1")
def U(k): return str(uuid.uuid5(NS, k))
def pinxy(n):
    x = (n - 1) * 1.27 if n <= 36 else 50.8 + (n - 37) * 1.27
    return round(x, 4), (0.0 if n % 2 else 2.54)
PAD, DRILL = 1.65, 1.02
yc = 1.27
x1, x2 = -10.16, 105.41                  # housing: holes at -8.255 / 103.505, B = 115.57
y1, y2 = yc - 3.685, yc + 3.685          # housing width 7.37
L = ['(footprint "SIMM-72_TE-5822021-4"', '\t(version 20241229)', '\t(generator "m68030-sbc-mkfp")', '\t(generator_version "9.0")',
     '\t(layer "F.Cu")',
     '\t(descr "72-pin SIMM socket, TE 5822021-4 (vertical, metal latch). Hole pattern per TE drawing ENG_CD_5822021_B1: contacts 1.02 mm, 1.27 mm pitch staggered 2.54 mm; locating holes 1.63 (pin-1 end, centre) and 2.41 (pin-72 end)")',
     '\t(tags "SIMM 72 DRAM socket TE 822021")',
     f'\t(property "Reference" "REF**" (at 47.625 {y1-1.5:.3f} 0) (layer "F.SilkS") (uuid "{U("ref")}") (effects (font (size 1 1) (thickness 0.15))))',
     f'\t(property "Value" "SIMM-72_TE-5822021-4" (at 47.625 {y2+1.5:.3f} 0) (layer "F.Fab") (uuid "{U("val")}") (effects (font (size 1 1) (thickness 0.15))))',
     f'\t(property "Footprint" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U("fp")}") (effects (font (size 1.27 1.27) (thickness 0.15))))',
     f'\t(property "Datasheet" "https://www.te.com/usa-en/product-5822021-4.html" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U("ds")}") (effects (font (size 1.27 1.27) (thickness 0.15))))',
     f'\t(property "Description" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U("desc")}") (effects (font (size 1.27 1.27) (thickness 0.15))))',
     '\t(attr through_hole)']
def line(a, b, layer, w, key):
    return f'\t(fp_line (start {a[0]:.3f} {a[1]:.3f}) (end {b[0]:.3f} {b[1]:.3f}) (stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{U(key)}"))'
def rect(xa, ya, xb, yb, layer, w, key):
    return [line((xa, ya), (xb, ya), layer, w, key + "t"), line((xb, ya), (xb, yb), layer, w, key + "r"),
            line((xb, yb), (xa, yb), layer, w, key + "b"), line((xa, yb), (xa, ya), layer, w, key + "l")]
L += rect(x1, y1, x2, y2, "F.Fab", 0.1, "fab")
L += rect(x1 - 0.12, y1 - 0.12, x2 + 0.12, y2 + 0.12, "F.SilkS", 0.12, "silk")
L += rect(x1 - 0.5, y1 - 0.5, x2 + 0.5, y2 + 0.5, "F.CrtYd", 0.05, "crt")
L.append(line((-1.5, y1 - 0.9), (1.5, y1 - 0.9), "F.SilkS", 0.2, "pin1mark"))   # pin-1 marker above pin 1
L.append(f'\t(fp_text user "1" (at -2.6 {y1-0.9:.3f} 0) (layer "F.SilkS") (uuid "{U("p1t")}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
L.append(f'\t(fp_text user "72" (at 95.25 {y2-1.0:.3f} 0) (layer "F.Fab") (uuid "{U("p72t")}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
L.append(f'\t(fp_text user "${{REFERENCE}}" (at 47.625 {yc:.3f} 0) (layer "F.Fab") (uuid "{U("reft")}") (effects (font (size 1 1) (thickness 0.15))))')
for n in range(1, 73):
    x, y = pinxy(n)
    shape = "rect" if n == 1 else "circle"
    L.append(f'\t(pad "{n}" thru_hole {shape} (at {x} {y}) (size {PAD} {PAD}) (drill {DRILL}) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (uuid "{U("pad%d" % n)}"))')
for k, (x, d) in enumerate([(-8.255, 1.63), (47.625, 1.63), (103.505, 2.41)]):
    L.append(f'\t(pad "" np_thru_hole circle (at {x} {yc}) (size {d} {d}) (drill {d}) (layers "*.Cu" "*.Mask") (uuid "{U("hole%d" % k)}"))')
L.append(")")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "m68030-sbc.pretty", "SIMM-72_TE-5822021-4.kicad_mod")
open(out, "w").write("\n".join(L) + "\n")
print("wrote", os.path.normpath(out))
