import pcbnew, sys, math, collections, pickle, time
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree
IN, OUT = sys.argv[1], sys.argv[2]
CL=0.16e6; HCL=0.21e6; ECL=0.31e6
POWER={'GND','+5V','+3V3'}
b=pcbnew.LoadBoard(IN)
LAYERS={pcbnew.F_Cu:'F',pcbnew.B_Cu:'B'}
def sps2polys(sps):
    out=[]
    for i in range(sps.OutlineCount()):
        o=sps.Outline(i); pts=[(o.CPoint(k).x,o.CPoint(k).y) for k in range(o.PointCount())]
        if len(pts)>=3: out.append(Polygon(pts).buffer(0))
    return out
# ---------------- static obstacles
static={L:[] for L in LAYERS}   # (net, geom, hw)
pads_by_net=collections.defaultdict(list)  # (layer, net) -> polys
for f in b.GetFootprints():
    for p in f.Pads():
        for L in LAYERS:
            if p.IsOnLayer(L) and p.GetAttribute()!=pcbnew.PAD_ATTRIB_NPTH:
                s=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(s,L,0,5000,pcbnew.ERROR_OUTSIDE)
                for g in sps2polys(s):
                    static[L].append((p.GetNetname(),g,0.0)); pads_by_net[(L,p.GetNetname())].append(g)
        if p.GetDrillSizeX()>0:
            r=max(p.GetDrillSizeX(),p.GetDrillSizeY())/2; c=p.GetPosition()
            for L in LAYERS: static[L].append(('__hole__',Point(c.x,c.y).buffer(r,16),HCL-CL))
    for g in f.GraphicalItems():
        for L in LAYERS:
            if g.GetLayer()==L:
                s=pcbnew.SHAPE_POLY_SET(); g.TransformShapeToPolygon(s,L,0,5000,pcbnew.ERROR_OUTSIDE)
                for gg in sps2polys(s): static[L].append(('__fpgfx__',gg,0.0))
for d in b.GetDrawings():
    if d.GetLayer() in LAYERS: print('board copper drawing', d.GetClass())
sig=[]; vias=[]
for t in b.GetTracks():
    n=t.GetNetname()
    if t.GetClass()=='PCB_VIA':
        c=t.GetPosition(); vias.append((n,c.x,c.y,t.GetWidth(pcbnew.F_Cu)/2))
        for L in LAYERS: static[L].append((n,Point(c.x,c.y),t.GetWidth(pcbnew.F_Cu)/2))
    elif t.GetLayer() in LAYERS:
        s,e=t.GetStart(),t.GetEnd()
        if n in POWER: static[t.GetLayer()].append((n,LineString([(s.x,s.y),(e.x,e.y)]),t.GetWidth()/2))
        else: sig.append([n,t.GetLayer(),(s.x,s.y),(e.x,e.y),t.GetWidth(),t.IsLocked()])
    else: print('track on other layer',n)
edge=b.GetBoardPolygonOutlines if False else None
sps=pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(sps)
edge_lines=[]
for P in sps2polys(sps):
    edge_lines.append(P.exterior); edge_lines+=list(P.interiors)
trees={L:STRtree([g for _,g,_ in static[L]]) for L in LAYERS}
print('static',{LAYERS[L]:len(v) for L,v in static.items()},'sig segs',len(sig))
# ---------------- dynamic hash for signal tracks
CELL=1000000
class Hash:
    def __init__(s): s.cells=collections.defaultdict(set); s.items={}
    def _cells(s,bb,pad):
        x0,y0,x1,y1=bb
        for i in range(int((x0-pad)//CELL),int((x1+pad)//CELL)+1):
            for j in range(int((y0-pad)//CELL),int((y1+pad)//CELL)+1): yield (i,j)
    def add(s,k,net,a,c,w):
        g=LineString([a,c]) if a!=c else Point(a); s.items[k]=(net,g,w/2)
        for cc in s._cells(g.bounds,0): s.cells[cc].add(k)
    def rem(s,k):
        net,g,hw=s.items.pop(k)
        for cc in s._cells(g.bounds,0): s.cells[cc].discard(k)
    def query(s,bb,pad):
        r=set()
        for cc in s._cells(bb,pad): r|=s.cells.get(cc,set())
        return r
H={L:Hash() for L in LAYERS}
def clear_ok(L,net,a,c,w,ignore=()):
    g=LineString([a,c]); hw=w/2
    bb=g.bounds; pad=hw+CL+0.5e6
    for k in H[L].query(bb,pad):
        if k in ignore: continue
        n2,g2,hw2=H[L].items[k]
        if n2==net: continue
        if g.distance(g2) < hw+hw2+CL: return False
    for i in trees[L].query(g.buffer(hw+CL+1.5e6)):
        n2,g2,hw2=static[L][i]
        if n2==net: continue
        if g.distance(g2) < hw+hw2+CL: return False
    for e in edge_lines:
        if g.distance(e) < hw+ECL: return False
    return True
# ---------------- segment model
segs={}  # id -> [net,L,a,b,w,locked]
for i,s in enumerate(sig): segs[i]=s
nid=[len(sig)]
EIDX=collections.defaultdict(set)
def newseg(net,L,a,c,w,lk):
    k=nid[0]; nid[0]+=1; segs[k]=[net,L,a,c,w,lk]; H[L].add(k,net,a,c,w)
    EIDX[(net,L,a)].add(k); EIDX[(net,L,c)].add(k); return k
def delseg(k):
    s=segs.pop(k); H[s[1]].rem(k); EIDX[(s[0],s[1],s[2])].discard(k); EIDX[(s[0],s[1],s[3])].discard(k)
def acute_at(n,L,q,d,skip):
    for k in EIDX.get((n,L,q),()):
        if k in skip: continue
        o=other(segs[k],q); (wx,wy),_=unit(q,o); (dx,dy),_=unit(q,d)
        if wx*dx+wy*dy>0.01: return True
    return False
for k,s in segs.items():
    H[s[1]].add(k,s[0],s[2],s[3],s[4]); EIDX[(s[0],s[1],s[2])].add(k); EIDX[(s[0],s[1],s[3])].add(k)
viapts=collections.defaultdict(set)
for n,x,y,r in vias: viapts[n].add((x,y))
def build_nodes():
    ends=collections.defaultdict(list)
    for k,s in segs.items():
        ends[(s[0],s[1],s[2])].append(k); ends[(s[0],s[1],s[3])].append(k)
    return ends
def in_same_pad(net,L,pt):
    P=Point(pt)
    return any(g.intersects(P) for g in pads_by_net.get((L,net),[]))
def protected(ends):
    prot=set()
    bynl=collections.defaultdict(list)
    for (n,L,p),ks in ends.items(): bynl[(n,L)].append(p)
    for (n,L,p),ks in ends.items():
        if len(ks)!=2 or p in viapts[n] or in_same_pad(n,L,p): prot.add((n,L,p)); continue
    # T junctions: endpoint lying on interior of another seg of same net/layer
    for k,s in segs.items():
        n,L,a,c=s[0],s[1],s[2],s[3]
        for k2 in H[L].query(LineString([a,c]).bounds if a!=c else (a[0],a[1],a[0],a[1]),10):
            s2=segs[k2]
            if s2[0]!=n or k2==k: continue
            for p in (s2[2],s2[3]):
                if p!=a and p!=c and on_seg(p,a,c): prot.add((n,L,p))
    return prot
def on_seg(p,a,c):
    cr=(c[0]-a[0])*(p[1]-a[1])-(c[1]-a[1])*(p[0]-a[0])
    if abs(cr)>1e3*max(1,math.hypot(c[0]-a[0],c[1]-a[1])/1e3): return False
    return min(a[0],c[0])-10<=p[0]<=max(a[0],c[0])+10 and min(a[1],c[1])-10<=p[1]<=max(a[1],c[1])+10
def other(s,p): return s[3] if s[2]==p else s[2]
def unit(a,c):
    dx,dy=c[0]-a[0],c[1]-a[1]; l=math.hypot(dx,dy); return (dx/l,dy/l),l
def merge_collinear():
    m=0
    while True:
        ends=build_nodes(); prot=protected(ends); changed=False; done=set()
        for (n,L,p),ks in ends.items():
            if len(ks)!=2 or (n,L,p) in prot: continue
            k1,k2=ks
            if k1 in done or k2 in done or k1==k2: continue
            s1,s2=segs[k1],segs[k2]
            if s1[4]!=s2[4]: continue
            a=other(s1,p); c=other(s2,p)
            u1,_=unit(a,p); u2,_=unit(p,c)
            if abs(u1[0]*u2[1]-u1[1]*u2[0])>1e-9 or u1[0]*u2[0]+u1[1]*u2[1]<0: continue
            delseg(k1); delseg(k2)
            k=newseg(n,L,a,c,s1[4],s1[5]); done|={k1,k2,k}; m+=1; changed=True
        if not changed: return m
SIZES=[3.0,2.5,2.0,1.6,1.27,1.0,0.85,0.75,0.635,0.55,0.4233,0.35,0.3,0.25,0.2,0.15,0.1]
def corners(ends,prot):
    out=[]
    for (n,L,p),ks in ends.items():
        if len(ks)!=2 or (n,L,p) in prot: continue
        s1,s2=segs[ks[0]],segs[ks[1]]
        if s1[4]!=s2[4]: continue
        u1,l1=unit(p,other(s1,p)); u2,l2=unit(p,other(s2,p))
        if abs(u1[0]*u2[0]+u1[1]*u2[1])<1e-3: out.append((n,L,p,ks[0],ks[1]))
    return out
def avail(k,p,ends,prot,cset,split):
    s=segs[k]; n,L=s[0],s[1]; q=other(s,p); (ux,uy),l=unit(p,q)
    a=l
    if split and (n,L,q) in cset: a=l/2
    # interior protected points / same-net vias on the leg
    for pt in list(viapts[n])+EP.get((n,L),[]):
        if pt!=p and pt!=q and on_seg(pt,p,q): a=min(a,math.hypot(pt[0]-p[0],pt[1]-p[1]))
    # same-net pads crossed by the leg (other than at q)
    for g in pads_by_net.get((L,n),[]):
        ls=LineString([p,q])
        if ls.intersects(g) and not g.intersects(Point(q)):
            a=min(a,Point(p).distance(g)-1000)
    return max(0,a)
EP={}
stats=collections.Counter(); sizes=collections.Counter()
def chamfer_pass(split):
    ends=build_nodes(); prot=protected(ends); cl=corners(ends,prot)
    EP.clear()
    for (n_,L_,p_) in ends: EP.setdefault((n_,L_),[]).append(p_)
    cset={(n,L,p) for n,L,p,_,_ in cl}
    stats['found_pass_%s'%split]=len(cl)
    for n,L,p,k1,k2 in cl:
        if k1 not in segs or k2 not in segs: continue
        s1,s2=segs[k1],segs[k2]
        if p not in (s1[2],s1[3]) or p not in (s2[2],s2[3]): continue
        a=min(avail(k1,p,ends,prot,cset,split),avail(k2,p,ends,prot,cset,split))
        q1,q2=other(s1,p),other(s2,p); u1,_=unit(p,q1); u2,_=unit(p,q2)
        cands=[a]+[x*1e6 for x in SIZES if x*1e6<a]
        ok=None
        for c in cands:
            c=int(c)
            if c<0.1e6: break
            A=(p[0]+round(u1[0]*c),p[1]+round(u1[1]*c)); B=(p[0]+round(u2[0]*c),p[1]+round(u2[1]*c))
            if A==q1 and acute_at(n,L,q1,B,{k1}): continue
            if B==q2 and acute_at(n,L,q2,A,{k2}): continue
            if clear_ok(L,n,A,B,s1[4]): ok=(c,A,B); break
        if not ok: stats['left90']+=1; continue
        c,A,B=ok; w,lk=s1[4],s1[5]
        for k,q,X in ((k1,q1,A),(k2,q2,B)):
            delseg(k)
            if X!=q: newseg(n,L,q,X,w,lk)
        newseg(n,L,A,B,w,lk); stats['converted']+=1; sizes[round(c/1e6,2)]+=1
t0=time.time()
print('merged',merge_collinear(),'segs',len(segs))
for split in (True,False):
    for it in range(20):
        before=stats['converted']; stats['left90']=0
        chamfer_pass(split)
        print(split,it,stats['converted']-before,'left90 this pass',stats['left90'],round(time.time()-t0,1))
        if stats['converted']==before: break
print('merged after',merge_collinear(),'segs',len(segs))
ends=build_nodes(); prot=protected(ends); rem=corners(ends,prot)
print('remaining 90 corners',len(rem))
print('sizes',sorted(sizes.items()))
pickle.dump({'segs':segs,'stats':dict(stats),'sizes':dict(sizes),'remaining':len(rem)},open(OUT,'wb'))
# categorise leftover perpendicular corners at degree-2 nodes
cat=collections.Counter(); samp=collections.defaultdict(list)
for (n,L,p),ks in ends.items():
    if len(ks)!=2: continue
    s1,s2=segs[ks[0]],segs[ks[1]]
    u1,_=unit(p,other(s1,p)); u2,_=unit(p,other(s2,p))
    d=u1[0]*u2[0]+u1[1]*u2[1]
    if abs(d)<1e-3 or d>0.5:
        why='acute' if d>0.5 else ('via' if p in viapts[n] else 'in_pad' if in_same_pad(n,L,p) else 'width' if s1[4]!=s2[4] else 'tjunction' if (n,L,p) in prot else 'no_clearance')
        cat[why]+=1; samp[why].append((n,LAYERS[L],round(p[0]/1e6,2),round(p[1]/1e6,2)))
print('leftover', dict(cat)); [print(' ',k,v[:10]) for k,v in samp.items()]
