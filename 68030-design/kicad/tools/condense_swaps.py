#!/usr/bin/env python3
"""Option B part swaps: edit Footprint / Value / MPN / Note fields only, in place.
Does not regenerate sheets (tools/build.py is NOT run)."""
import re
OSC_FP = "m68030-sbc:Oscillator_SMD_ECS-3951M_7.0x5.0mm_DIP14PinMap"
SWAPS = {
 "clock.kicad_sch": {
  "X1": {"Footprint": OSC_FP, "MPN": "ECS-3951M-250-BN-TR",
         "Note": "ECS-3951M-BN 5 V HCMOS 7x5 SMD, 25.000 MHz. Pad1 tri-state tied +5V = enabled (>2.2 V)"},
  "X2": {"Footprint": OSC_FP, "MPN": "ECS-3951M-500-BN-TR",
         "Note": "ECS-3951M-BN 5 V HCMOS 7x5 SMD, 50.000 MHz. Pad1 tri-state tied +5V = enabled (>2.2 V)"},
  "X3": {"Footprint": OSC_FP, "MPN": "ECS-3951M-200-BN-TR [VERIFY freq vs 68882 grade]",
         "Note": "DNP. ECS-3951M-BN 5 V 7x5 SMD; 20 MHz suits MC68882FN20A. Pad1 tied +5V"},
 },
 "ide.kicad_sch": {r: {"Value": "SN74ACT245DW", "Footprint": "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
        "MPN": "SN74ACT245DW", "Note": "TI SCAS452H SOIC (DW). Same 245 pinout as the N part. Reel: SN74ACT245DWR [VERIFY stock]"}
        for r in ("U11", "U12", "U13")},
 "duart_spi_rtc.kicad_sch": {
  "BT1": {"Footprint": "Battery:BatteryHolder_Keystone_3034_1x20mm", "MPN": "Keystone 3034",
          "Note": "SMD CR2032 retainer. Pad 1 (+) = outer tabs, pad 2 (-) = centre pad"}},
 "power.kicad_sch": {
  "F1": {"Value": "T5A 0454005.MR", "Footprint": "Fuse:Fuse_Littelfuse-NANO2-451_453",
         "MPN": "Littelfuse 0454005.MR",
         "Note": "NANO2 454 Slo-Blo 5 A, 125 V AC/DC, 50 A @125 V interrupt. Pad layout 1.96x3.15 / 2.95 gap matches datasheet"}},
}

def set_prop(blk, key, val):
    pat = re.compile(r'(\(property "%s" ")([^"]*)(")' % re.escape(key))
    if pat.search(blk):
        return pat.sub(lambda m: m.group(1) + val + m.group(3), blk, count=1), True
    return blk, False

for fn, refs in SWAPS.items():
    t = open(fn, encoding="utf-8").read()
    out, pos, done = [], 0, set()
    for m in re.finditer(r'\n\t\(symbol\n', t):
        s = m.start()
        e = t.find('\n\t)', s) + 3
        blk = t[s:e]
        r = re.search(r'\(property "Reference" "([^"]+)"', blk)
        if not r or r.group(1) not in refs:
            continue
        ref = r.group(1)
        new = blk
        for k, v in refs[ref].items():
            new, ok = set_prop(new, k, v)
            if not ok:
                print('  skip (field absent, not added):', ref, k)
        out.append(t[pos:s]); out.append(new); pos = e; done.add(ref)
    out.append(t[pos:])
    open(fn, "w", encoding="utf-8").write("".join(out))
    print(fn, sorted(done), "missing", sorted(set(refs) - done))
