import pcbnew, math
P=2.54/6; X0=94.76; Y0=63.76
b=pcbnew.LoadBoard('/tmp/route/m68030-sbc.kicad_pcb')
tracks=list(b.GetTracks())
uid=lambda t:t.m_Uuid.AsString()
moved=[]
for f in b.GetFootprints():
    ref=f.GetReference()
    if not any(ref.startswith(p) for p in ('U','J','X','SW','Y')) or ref=='U1': continue
    pads=list(f.Pads())
    if not pads: continue
    p1=min(pads,key=lambda p:(p.GetNumber()!='1', p.GetNumber()))
    x=p1.GetPosition().x/1e6; y=p1.GetPosition().y/1e6
    dx=round((x-X0)/P)*P+X0-x; dy=round((y-Y0)/P)*P+Y0-y
    if abs(dx)<1e-4 and abs(dy)<1e-4: continue
    d=pcbnew.VECTOR2I(int(round(dx*1e6)),int(round(dy*1e6)))
    att={}
    for t in tracks:
        if t.GetClass()=='PCB_TRACK':
            for p in pads:
                if t.GetNetCode()==p.GetNetCode() and (p.HitTest(t.GetStart()) or p.HitTest(t.GetEnd())): att[uid(t)]=t
    for t in list(att.values()):
        for v in tracks:
            if v.GetClass()=='PCB_VIA' and v.GetNetCode()==t.GetNetCode() and (v.GetPosition()==t.GetStart() or v.GetPosition()==t.GetEnd()): att[uid(v)]=v
    f.Move(d)
    for t in att.values(): t.Move(d)
    moved.append((ref,round(dx,3),round(dy,3),len(att)))
b.Save('/tmp/route/base2.kicad_pcb')
print(len(moved)); print(moved)
