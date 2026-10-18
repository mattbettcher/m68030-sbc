import pcbnew, sys, math
b=pcbnew.LoadBoard(sys.argv[1])
MOVED=sys.argv[3].split(',')
def bb(it):
    r=it.GetBoundingBox(); return (r.GetX()/1e6,r.GetY()/1e6,r.GetRight()/1e6,r.GetBottom()/1e6)
def inter(a,c,m=0.12): return not (a[2]+m<=c[0] or c[2]+m<=a[0] or a[3]+m<=c[1] or c[3]+m<=a[1])
def obstacles(layer, skip):
    obs=[]
    cu = pcbnew.F_Cu if layer==pcbnew.F_SilkS else pcbnew.B_Cu
    for f in b.GetFootprints():
        for g in f.GraphicalItems():
            if g.GetLayer()==layer and g is not skip:
                if g.GetClass()=='PCB_TEXT' and not g.IsVisible(): continue
                obs.append(bb(g))
        for t in (f.Reference(), f.Value()):
            if t.GetLayer()==layer and t.IsVisible() and t.m_Uuid.AsString()!=skip.m_Uuid.AsString():
                obs.append(bb(t))
        for p in f.Pads():
            if p.IsOnLayer(cu): obs.append(bb(p))
    for d in b.GetDrawings():
        if d.GetLayer()==layer and d.m_Uuid.AsString()!=skip.m_Uuid.AsString(): obs.append(bb(d))
    return obs
moved=hid=0
for ref in MOVED:
    f=b.FindFootprintByReference(ref)
    if not f: continue
    t=f.Reference()
    if not t.IsVisible(): continue
    obs=obstacles(t.GetLayer(), t)
    if not any(inter(bb(t),o) for o in obs): continue
    c=f.GetPosition(); best=None
    fb=bb(f)
    for r in [0.0,0.5,1.0,1.5,2.0,2.5,3.0,4.0,5.0]:
        for ang in range(0,360,30):
            for rot in (0,90):
                dx=r*math.cos(math.radians(ang)); dy=r*math.sin(math.radians(ang))
                # candidate positions relative to footprint bbox edges
                for base in [((fb[0]+fb[2])/2,fb[1]-0.8),((fb[0]+fb[2])/2,fb[3]+0.8),(fb[0]-1.5,(fb[1]+fb[3])/2),(fb[2]+1.5,(fb[1]+fb[3])/2)]:
                    t.SetPosition(pcbnew.VECTOR2I(int((base[0]+dx)*1e6),int((base[1]+dy)*1e6)))
                    t.SetTextAngle(pcbnew.EDA_ANGLE(rot,pcbnew.DEGREES_T))
                    tb=bb(t)
                    if tb[0]<0.5 or tb[1]<0.5 or tb[2]>219.5 or tb[3]>174.5: continue
                    if not any(inter(tb,o) for o in obs): best=True; break
                if best: break
            if best: break
        if best: break
    if best: moved+=1
    else: t.SetVisible(False); hid+=1; print('hidden',ref)
# board texts (connector labels) that collide: shift them
for d in list(b.GetDrawings()):
    if d.GetClass()!='PCB_TEXT' or d.GetLayer() not in (pcbnew.F_SilkS,pcbnew.B_SilkS): continue
    obs=obstacles(d.GetLayer(), d)
    if not any(inter(bb(d),o) for o in obs): continue
    p0=d.GetPosition(); ok=False
    for r in [0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0]:
        for ang in range(0,360,45):
            d.SetPosition(pcbnew.VECTOR2I(int(p0.x+r*1e6*math.cos(math.radians(ang))),int(p0.y+r*1e6*math.sin(math.radians(ang)))))
            if not any(inter(bb(d),o) for o in obs): ok=True; break
        if ok: break
    if not ok: d.SetPosition(p0)
    print('text',repr(d.GetText()[:20]),'moved' if ok else 'stuck')
print('moved',moved,'hidden',hid)
b.Save(sys.argv[2])
