import pcbnew, shapely, math
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
def mm(v): return v/1e6
def poly(ps):
    out=[]
    for i in range(ps.OutlineCount()):
        o=ps.Outline(i); out.append(Polygon([(mm(o.CPoint(j).x),mm(o.CPoint(j).y)) for j in range(o.PointCount())]))
    return unary_union(out) if out else Polygon()
def crt(f,side):
    f.BuildCourtyardCaches(); return poly(f.GetCourtyard(pcbnew.F_CrtYd if side=='F' else pcbnew.B_CrtYd))
def copper(b, layer, exclude_ref):
    items=[]
    ef=b.FindFootprintByReference(exclude_ref); enets={p.GetNetname() for p in ef.Pads()}
    near=lambda t:(t.GetPosition() if t.GetClass()=='PCB_VIA' else t.GetStart())
    def own(t): return t.GetNetname() in enets and t.GetNetname() in ('GND','+5V','+3V3') and (near(t)-ef.GetPosition()).EuclideanNorm()<7e6
    for f in b.GetFootprints():
        if f.GetReference()==exclude_ref: continue
        for p in f.Pads():
            if p.IsOnLayer(layer):
                items.append((p.GetNetname(), poly(p.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE))))
            if p.GetDrillSize().x>0:
                items.append(('#hole', Point(mm(p.GetPosition().x),mm(p.GetPosition().y)).buffer(mm(p.GetDrillSize().x)/2)))
    for t in b.GetTracks():
        if own(t): continue
        if t.GetClass()=='PCB_VIA':
            items.append((t.GetNetname(), Point(mm(t.GetPosition().x),mm(t.GetPosition().y)).buffer(mm(t.GetWidth(pcbnew.F_Cu))/2)))
        elif t.GetLayer()==layer:
            items.append((t.GetNetname(), LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))]).buffer(mm(t.GetWidth())/2)))
    return items
from shapely import affinity
def find(b, f, tx, ty, rmax=6.0, step=0.4, prefer=None, margin=0.25):
    side='B' if f.GetLayer()==pcbnew.B_Cu else 'F'; layer=pcbnew.B_Cu if side=='B' else pcbnew.F_Cu
    cx,cy=f.GetPosition().x/1e6,f.GetPosition().y/1e6
    others=[crt(g,side) for g in b.GetFootprints() if g.GetReference()!=f.GetReference() and (g.GetPosition()-f.GetPosition()).EuclideanNorm()<40e6]
    others=unary_union([o for o in others if not o.is_empty])
    cu=copper(b,layer,f.GetReference())
    from shapely.strtree import STRtree
    tree=STRtree([g for n,g in cu])
    mycrt=crt(f,side)
    mypads=[poly(p.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE)) for p in f.Pads() if p.IsOnLayer(layer)]
    cands=[]; k=int(rmax/step)
    for i in range(-k,k+1):
        for j in range(-k,k+1):
            x,y=tx+i*step,ty+j*step
            cands.append(((prefer(x,y) if prefer else math.hypot(x-tx,y-ty)),x,y))
    cands.sort()
    for d,x,y in cands:
        dx,dy=x-cx,y-cy
        if not mycrt.is_empty and affinity.translate(mycrt,dx,dy).intersection(others).area>1e-4: continue
        bad=False
        for pp0 in mypads:
            pp=affinity.translate(pp0,dx,dy)
            for idx in tree.query(pp.buffer(margin)):
                if cu[idx][1].distance(pp)<margin: bad=True; break
            if bad: break
        if not bad:
            f.SetPosition(pcbnew.VECTOR2I(int(round(x*1e6)),int(round(y*1e6)))); return x,y
    f.SetPosition(pcbnew.VECTOR2I(int(round(cx*1e6)),int(round(cy*1e6))))
    return None
