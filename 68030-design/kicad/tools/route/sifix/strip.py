import pcbnew
b=pcbnew.LoadBoard('/workspace/68030-design/kicad/backup/pre-sifix-20261018/m68030-sbc.kicad_pcb')
items=[t for t in b.GetTracks() if t.GetNetname() not in ('GND','+5V','+3V3')]
for t in items: b.Remove(t)
print('removed',len(items)); b.Save('/tmp/sifix/_strip.kicad_pcb')
