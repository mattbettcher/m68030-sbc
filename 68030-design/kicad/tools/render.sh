#!/bin/sh
# regenerate project, run ERC, export PDF/SVG/PNG
set -e
cd "$(dirname "$0")/.."
python3 tools/build.py >/dev/null
kicad-cli sch erc --severity-all --format json -o /tmp/erc.json m68030-sbc.kicad_sch >/dev/null
rm -rf out && mkdir -p out/svg
kicad-cli sch export pdf -o out/m68030-sbc.pdf m68030-sbc.kicad_sch >/dev/null
kicad-cli sch export svg -o out/svg m68030-sbc.kicad_sch >/dev/null
for f in out/svg/*.svg; do rsvg-convert -b white -w 4200 "$f" -o "out/$(basename "$f" .svg).png"; done
# every sheet is drawn; keep all renders
