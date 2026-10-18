import pcbnew, sys, math, collections
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree
POWER={'GND','+5V','+3V3'}
def sps2polys(sps):
    out=[]
    for i in range(sps.OutlineCount()):
        o=sps.Outline(i); pts=[(o.CPoint(k).x,o.CPoint(k).y) for k in range(o.PointCount())]
        if len(pts)>=3: out.append(Polygon(pts).buffer(0))
    return out
def run(path, SI=None):
    b=pcbnew.LoadBoard(path)
    LAY=(pcbnew.F_Cu,pcbnew.B_Cu)
    objs={L:[] for L in LAY}  # (net, geom(with width buffered) )
    for f in b.GetFootprints():
        for p in f.Pads():
            for L in LAY:
                if p.IsOnLayer(L) and p.GetAttribute()!=pcbnew.PAD_ATTRIB_NPTH:
                    s=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(s,L,0,5000,pcbnew.ERROR_OUTSIDE)
                    for g in sps2polys(s): objs[L].append((p.GetNetname(),g,'pad'))
    segs=[]; nv=0; L_tot=0; netlen=collections.Counter()
    for t in b.GetTracks():
        n=t.GetNetname()
        if t.GetClass()=='PCB_VIA':
            c=t.GetPosition(); g=Point(c.x,c.y).buffer(t.GetWidth(pcbnew.F_Cu)/2,16)
            for L in LAY: objs[L].append((n,g,'via'))
            if n not in POWER: nv+=1
        else:
            s,e=t.GetStart(),t.GetEnd(); g=LineString([(s.x,s.y),(e.x,e.y)]).buffer(t.GetWidth()/2,8)
            objs[t.GetLayer()].append((n,g,'trk')); netlen[n]+=t.GetLength()/1e6
            if n not in POWER: segs.append((n,t.GetLayer(),(s.x,s.y),(e.x,e.y),g)); L_tot+=t.GetLength()
    trees={L:STRtree([o[1] for o in objs[L]]) for L in LAY}
    hist=collections.Counter(); pairs=0
    for n,L,a,c,g in segs:
        best=1e9
        for i in trees[L].query(g.buffer(0.2e6)):
            n2,g2,k=objs[L][i]
            if n2==n: continue
            d=g.distance(g2)
            if d<0.2e6-1: pairs+=1
            best=min(best,d)
        hist['<0.16' if best<0.16e6-1 else '0.16-0.18' if best<0.18e6-1 else '0.18-0.2' if best<0.2e6-1 else '>=0.2']+=1
    # bends and jogs
    ends=collections.defaultdict(list)
    for i,(n,L,a,c,g) in enumerate(segs):
        ends[(n,L,a)].append((i,c)); ends[(n,L,c)].append((i,a))
    def d(a,c):
        dx,dy=c[0]-a[0],c[1]-a[1]; l=math.hypot(dx,dy); return (dx/l,dy/l) if l else (0,0)
    bends=0
    for (n,L,p),v in ends.items():
        if len(v)==2:
            u1=d(v[0][1],p); u2=d(p,v[1][1])
            if u1[0]*u2[0]+u1[1]*u2[1]<0.9999: bends+=1
    jogs=0; jog1=0
    for i,(n,L,a,c,g) in enumerate(segs):
        ea=ends[(n,L,a)]; ec=ends[(n,L,c)]
        if len(ea)!=2 or len(ec)!=2: continue
        pa=[q for j,q in ea if j!=i]; pc=[q for j,q in ec if j!=i]
        if len(pa)!=1 or len(pc)!=1: continue
        din=d(pa[0],a); dout=d(c,pc[0]); ds=d(a,c)
        if din[0]*dout[0]+din[1]*dout[1]>0.9999 and abs(din[0]*ds[0]+din[1]*ds[1])<0.9999:
            off=abs(din[0]*(c[1]-a[1])-din[1]*(c[0]-a[0]))/1e6
            jogs+=1; jog1+= off<1.0
    r=dict(segments=len(segs),jogs_total=jogs,jogs_lt1mm=jog1,bends=bends,length_m=round(L_tot/1e9,3),vias=nv,seg_gap_hist=dict(hist),pairs_lt_0p2=pairs)
    return r, netlen
if __name__=='__main__':
    for p in sys.argv[1:]:
        r,_=run(p); print(p, r)
