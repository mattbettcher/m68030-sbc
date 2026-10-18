# Build routing grid from board: owner arrays per layer (F,B), via owner, pad terminals, nets.
import pcbnew, numpy as np, shapely, pickle, sys, math
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
P = 2.54/6
CL = 0.16; TW2 = 0.125; VR = 0.30; VD = 0.30; HOLE_CL = 0.2; H2H = 0.25; EDGE = 0.30
POWER = {'GND', '+5V', '+3V3'}
def mm(v): return v/1e6
def poly_of(ps):
    polys=[]
    for i in range(ps.OutlineCount()):
        o=ps.Outline(i); pts=[(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
        holes=[]
        for h in range(ps.HoleCount(i)):
            hh=ps.Hole(i,h); holes.append([(mm(hh.CPoint(j).x),mm(hh.CPoint(j).y)) for j in range(hh.PointCount())])
        polys.append(Polygon(pts,holes))
    return unary_union(polys)
def build(pcb, out):
    b=pcbnew.LoadBoard(pcb)
    LAY=[pcbnew.F_Cu, pcbnew.B_Cu]
    x0 = 94.76 - math.floor(94.76/P)*P; y0 = 63.76 - math.floor(63.76/P)*P
    nx = int((220-x0)/P)+1; ny=int((175-y0)/P)+1
    X = x0+np.arange(nx)*P; Y=y0+np.arange(ny)*P
    XX,YY=np.meshgrid(X,Y)
    own=[np.zeros((ny,nx),np.int32) for _ in LAY]
    vown=np.zeros((ny,nx),np.int32)
    def cells(geom):
        x1,y1,x2,y2=geom.bounds
        i1=max(0,int(math.floor((x1-x0)/P))); i2=min(nx-1,int(math.ceil((x2-x0)/P)))
        j1=max(0,int(math.floor((y1-y0)/P))); j2=min(ny-1,int(math.ceil((y2-y0)/P)))
        if i2<i1 or j2<j1: return None
        sx=XX[j1:j2+1,i1:i2+1]; sy=YY[j1:j2+1,i1:i2+1]
        m=shapely.contains_xy(geom,sx,sy)
        return (slice(j1,j2+1),slice(i1,i2+1),m)
    def apply(arr,geom,net):
        r=cells(geom)
        if r is None: return
        sj,si,m=r; sub=arr[sj,si]
        if net<=0: sub[m]=-1; return
        z=m&(sub==0); sub[z]=net
        bad=m&(sub!=net); sub[bad]=-1
    shapely.prepare
    holes=[]  # (x,y,r)
    terms={}  # (ref,pad)-> list of (L,j,i)
    padinfo={}
    netname={}
    for f in b.GetFootprints():
        for pidx,p in enumerate(f.Pads()):
            net=p.GetNetCode(); nn=p.GetNetname(); netname[net]=nn
            if nn.startswith('unconnected-'): net=0
            if p.HasHole() if hasattr(p,'HasHole') else p.GetDrillSize().x>0:
                d=p.GetDrillSize(); holes.append((mm(p.GetPosition().x),mm(p.GetPosition().y),mm(max(d.x,d.y))/2, p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH))
            key=(f.GetReference(),p.GetNumber(),pidx); tl=[]
            for li,L in enumerate(LAY):
                if not p.IsOnLayer(L): continue
                try: g=poly_of(p.GetEffectivePolygon(L, pcbnew.ERROR_INSIDE))
                except TypeError: g=poly_of(p.GetEffectivePolygon(pcbnew.ERROR_INSIDE))
                if g.is_empty: continue
                apply(own[li], g.buffer(CL+TW2, 8), net)
                apply(vown, g.buffer(CL+VR, 8), net if p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD else net)
                # via never inside any pad copper
                apply(vown, g.buffer(VR*0.5), -1)
                if net>0:
                    r=cells(g.buffer(-TW2))
                    lst=[]
                    if r is not None:
                        sj,si,m=r; jj,ii=np.nonzero(m); lst=[(li,j+sj.start,i+si.start) for j,i in zip(jj,ii)]
                    if not lst:
                        r=cells(g); 
                        if r is not None:
                            sj,si,m=r; jj,ii=np.nonzero(m); lst=[(li,j+sj.start,i+si.start) for j,i in zip(jj,ii)]
                    if not lst:
                        c=g.centroid; i=int(round((c.x-x0)/P)); j=int(round((c.y-y0)/P)); lst=[(li,j,i)]
                        print('STUBTERM',key,file=sys.stderr)
                    tl+=lst
            if net>0 and nn not in POWER:
                terms[key]=tl; padinfo[key]=(net,nn,mm(p.GetPosition().x),mm(p.GetPosition().y),p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD)
    for t in b.GetTracks():
        net=t.GetNetCode()
        if t.GetClass()=='PCB_VIA':
            pt=Point(mm(t.GetPosition().x),mm(t.GetPosition().y)); r=mm(t.GetWidth(pcbnew.F_Cu))/2
            for li in range(2): apply(own[li], pt.buffer(r+CL+TW2,16), net)
            apply(vown, pt.buffer(r+CL+VR,16), net)
            holes.append((pt.x,pt.y,mm(t.GetDrillValue())/2,False))
        else:
            if t.GetLayer() not in LAY: continue
            li=LAY.index(t.GetLayer()); w=mm(t.GetWidth())
            ls=LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))])
            apply(own[li], ls.buffer(w/2+CL+TW2,8), net)
            apply(vown, ls.buffer(w/2+CL+VR,8), net)
    # footprint copper graphics on F/B (rare)
    for f in b.GetFootprints():
        for g in f.GraphicalItems():
            if g.GetLayer() in LAY and g.GetClass()=='PCB_SHAPE':
                bb=g.GetBoundingBox(); li=LAY.index(g.GetLayer())
                apply(own[li], box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())).buffer(CL+TW2+0.1), -1)
                apply(vown, box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())).buffer(CL+VR+0.1), -1)
    for (hx,hy,hr,npth) in holes:
        pt=Point(hx,hy)
        apply(vown, pt.buffer(hr+H2H+VD/2,16), -1)
        if npth:
            for li in range(2): apply(own[li], pt.buffer(hr+HOLE_CL+TW2,16), -1)
    # edge
    inner=box(0,0,220,175)
    for li in range(2):
        m=~shapely.contains_xy(inner.buffer(-(EDGE+TW2)),XX,YY); own[li][m]=-1
    vown[~shapely.contains_xy(inner.buffer(-(EDGE+VR)),XX,YY)]=-1
    # force terminals
    for key,tl in terms.items():
        net=padinfo[key][0]
        for (li,j,i) in tl: own[li][j,i]=net
    pickle.dump(dict(P=P,x0=x0,y0=y0,nx=nx,ny=ny,own=own,vown=vown,terms=terms,padinfo=padinfo,netname=netname),open(out,'wb'))
    print('grid',nx,ny,'free F',(own[0]==0).mean(),'free B',(own[1]==0).mean(),'pads',len(terms))
if __name__=='__main__': build(sys.argv[1], sys.argv[2])
