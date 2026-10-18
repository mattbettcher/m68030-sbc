# Dump footprint-local pad coordinates (x, y, drill, is_npth, number) for the footprints gen.py models.
import pcbnew, json, math, os
HERE=os.path.dirname(os.path.abspath(__file__)); KICAD=os.path.normpath(os.path.join(HERE,'..','..'))
b=pcbnew.LoadBoard(os.path.join(KICAD,'m68030-sbc.kicad_pcb'))
out={}
for r in 'U1 U2 U3 U5 U6 J1'.split():
    f=b.FindFootprintByReference(r); pos=f.GetPosition(); a=-math.radians(f.GetOrientationDegrees())
    out[r]=[(round(((p.GetPosition().x-pos.x)*math.cos(a)+(p.GetPosition().y-pos.y)*math.sin(a))/1e6,4),
             round((-(p.GetPosition().x-pos.x)*math.sin(a)+(p.GetPosition().y-pos.y)*math.cos(a))/1e6,4),
             round(p.GetDrillSizeX()/1e6,3), p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH, p.GetNumber()) for p in f.Pads()]
json.dump(out,open(os.path.join(HERE,'pads.json'),'w'))
print({k:len(v) for k,v in out.items()})
