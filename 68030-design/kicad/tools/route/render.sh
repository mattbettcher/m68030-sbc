#!/bin/bash
# render.sh board.kicad_pcb outprefix
set -e
B=$1; O=$2; T=$(mktemp -d)
kicad-cli pcb export svg --mode-single --exclude-drawing-sheet --page-size-mode 2 -l F.Cu,F.SilkS,Edge.Cuts -o $T/top.svg $B >/dev/null
kicad-cli pcb export svg --mode-single --exclude-drawing-sheet --page-size-mode 2 --mirror -l B.Cu,B.SilkS,Edge.Cuts -o $T/bot.svg $B >/dev/null
rsvg-convert -w 3000 -b white $T/top.svg -o ${O}-top.png
rsvg-convert -w 3000 -b white $T/bot.svg -o ${O}-bottom.png
ls -la ${O}-top.png ${O}-bottom.png
