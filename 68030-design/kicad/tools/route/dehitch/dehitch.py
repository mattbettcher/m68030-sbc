import pcbnew, sys, math, collections, pickle, time
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points
from shapely.strtree import STRtree
IN, OUT = sys.argv[1], sys.argv[2]
MAXPASS=int(sys.argv[3]) if len(sys.argv)>3 else 8
import os
CLMIN=0.16e6; PREF=float(os.environ.get("PREF","0.20"))*1e6; HCL=0.21e6; ECL=0.31e6; W=40
POWER={'GND','+5V','+3V3'}
b=pcbnew.LoadBoard(IN)
LAYERS={pcbnew.F_Cu:'F',pcbnew.B_Cu:'B'}
def sps2polys(sps):
    out=[]
    for i in range(sps.OutlineCount()):
        o=sps.Outline(i); pts=[(o.CPoint(k).x,o.CPoint(k).y) for k in range(o.PointCount())]
        if len(pts)>=3: out.append(Polygon(pts).buffer(0))
    return out
static={L:[] for L in LAYERS}   # (net, geom, hw, kind)
pads_by_net=collections.defaultdict(list)
for f in b.GetFootprints():
    for p in f.Pads():
        for L in LAYERS:
            if p.IsOnLayer(L) and p.GetAttribute()!=pcbnew.PAD_ATTRIB_NPTH:
                s=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(s,L,0,5000,pcbnew.ERROR_OUTSIDE)
                for g in sps2polys(s):
                    static[L].append((p.GetNetname(),g,0.0,'pad')); pads_by_net[(L,p.GetNetname())].append(g)
        if p.GetDrillSizeX()>0:
            r=max(p.GetDrillSizeX(),p.GetDrillSizeY())/2; c=p.GetPosition()
            for L in LAYERS: static[L].append(('__hole__',Point(c.x,c.y).buffer(r,16),0.0,'hole'))
    for g in f.GraphicalItems():
        for L in LAYERS:
            if g.GetLayer()==L:
                s=pcbnew.SHAPE_POLY_SET(); g.TransformShapeToPolygon(s,L,0,5000,pcbnew.ERROR_OUTSIDE)
                for gg in sps2polys(s): static[L].append(('__fpgfx__',gg,0.0,'gfx'))
sig=[]; viapts=collections.defaultdict(set)
for t in b.GetTracks():
    n=t.GetNetname()
    if t.GetClass()=='PCB_VIA':
        c=t.GetPosition(); viapts[n].add((c.x,c.y))
        for L in LAYERS: static[L].append((n,Point(c.x,c.y),t.GetWidth(pcbnew.F_Cu)/2,'via'))
    elif t.GetLayer() in LAYERS:
        s,e=t.GetStart(),t.GetEnd()
        if n in POWER: static[t.GetLayer()].append((n,LineString([(s.x,s.y),(e.x,e.y)]),t.GetWidth()/2,'trk'))
        else: sig.append([n,t.GetLayer(),(s.x,s.y),(e.x,e.y),t.GetWidth(),t.IsLocked()])
sps=pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(sps)
edge_lines=[]
for P in sps2polys(sps): edge_lines.append(P.exterior); edge_lines+=list(P.interiors)
trees={L:STRtree([g for _,g,_,_ in static[L]]) for L in LAYERS}
CELL=1000000
class Hash:
    def __init__(s): s.cells=collections.defaultdict(set); s.items={}
    def _cells(s,bb,pad):
        x0,y0,x1,y1=bb
        for i in range(int((x0-pad)//CELL),int((x1+pad)//CELL)+1):
            for j in range(int((y0-pad)//CELL),int((y1+pad)//CELL)+1): yield (i,j)
    def add(s,k,net,a,c,w):
        g=LineString([a,c]); s.items[k]=(net,g,w/2)
        for cc in s._cells(g.bounds,0): s.cells[cc].add(k)
    def rem(s,k):
        net,g,hw=s.items.pop(k)
        for cc in s._cells(g.bounds,0): s.cells[cc].discard(k)
    def query(s,bb,pad):
        r=set()
        for cc in s._cells(bb,pad): r|=s.cells.get(cc,set())
        return r
H={L:Hash() for L in LAYERS}
def seg_gap(L,net,a,c,hw,cap=0.3e6,need=None):
    """min gap to other-net copper (capped). if need given, return early False/True"""
    if NOCHK and need is not None: return True
    g=LineString([a,c]) if a!=c else Point(a); best=cap
    bb=g.bounds
    for k in H[L].query(bb,hw+cap+0.2e6):
        n2,g2,hw2=H[L].items[k]
        if n2==net: continue
        d=g.distance(g2)-hw-hw2
        if d<best:
            best=d
            if need is not None and best<need-1: BLK[0]='track'; return False
    for i in trees[L].query(g.buffer(hw+cap+0.4e6)):
        n2,g2,hw2,kind=static[L][i]
        if n2==net: continue
        d=g.distance(g2)-hw-hw2
        if kind=='hole': d-= (HCL-CLMIN)   # holes need 0.21 instead of 0.16
        if d<best:
            best=d
            if need is not None and best<need-1: BLK[0]=kind if kind!='trk' else 'power track'; return False
    for e in edge_lines:
        d=g.distance(e)-hw-(ECL-CLMIN)
        if d<best:
            best=d
            if need is not None and best<need-1: BLK[0]='edge'; return False
    return True if need is not None else best
segs={}; nid=[0]; EIDX=collections.defaultdict(set)
def newseg(net,L,a,c,w,lk):
    k=nid[0]; nid[0]+=1; segs[k]=[net,L,a,c,w,lk]; H[L].add(k,net,a,c,w)
    EIDX[(net,L,a)].add(k); EIDX[(net,L,c)].add(k); return k
def delseg(k):
    s=segs.pop(k); H[s[1]].rem(k); EIDX[(s[0],s[1],s[2])].discard(k); EIDX[(s[0],s[1],s[3])].discard(k)
for s in sig: newseg(*s)
def on_seg_interior(p,a,c):
    if p==a or p==c: return False
    cr=(c[0]-a[0])*(p[1]-a[1])-(c[1]-a[1])*(p[0]-a[0]); l=math.hypot(c[0]-a[0],c[1]-a[1])
    if l==0 or abs(cr)/l>20: return False
    t=((p[0]-a[0])*(c[0]-a[0])+(p[1]-a[1])*(c[1]-a[1]))/l/l
    return 0<t<1
# ---- split at T points, interior vias, and pad crossings; collect fixed nodes
FIX=set()
NOCHK=False
BLK=['']
def split_all():
    cnt=0
    for k in list(segs.keys()):
        if k not in segs: continue
        n,L,a,c,w,lk=segs[k]
        pts=set()
        for k2 in H[L].query(LineString([a,c]).bounds,10):
            if k2==k or segs[k2][0]!=n: continue
            for p in (segs[k2][2],segs[k2][3]):
                if on_seg_interior(p,a,c): pts.add(p)
        for p in viapts[n]:
            if on_seg_interior(p,a,c): pts.add(p)
        ls=LineString([a,c])
        for g in pads_by_net.get((L,n),[]):
            if ls.intersects(g) and not g.contains(Point(a)) and not g.contains(Point(c)):
                q=ls.interpolate(ls.project(g.centroid)); p=(int(round(q.x)),int(round(q.y)))
                if g.contains(Point(p)) and p!=a and p!=c: pts.add(p); FIX.add((n,L,p))
        if not pts: continue
        ordered=sorted(pts,key=lambda p:(p[0]-a[0])**2+(p[1]-a[1])**2)
        delseg(k); prev=a
        for p in ordered+[c]:
            if p!=prev: newseg(n,L,prev,p,w,lk)
            prev=p
        for p in ordered: FIX.add((n,L,p))
        cnt+=1
    return cnt
def in_same_pad(n,L,p):
    P=Point(p); 
    for g in pads_by_net.get((L,n),[]):
        if g.intersects(P): return g
    return None
def is_fixed(n,L,p):
    return len(EIDX[(n,L,p)])!=2 or (n,L,p) in FIX or p in viapts[n] or in_same_pad(n,L,p) is not None
def other(s,p): return s[3] if s[2]==p else s[2]
def paths():
    seen=set(); out=[]
    nodes=[(n,L,p) for (n,L,p),ks in EIDX.items() if ks and is_fixed(n,L,p)]
    fixedset=set(nodes)
    for (n,L,p) in nodes:
        for k in list(EIDX[(n,L,p)]):
            if k in seen: continue
            V=[p]; K=[]; cur=p; kk=k
            while True:
                seen.add(kk); K.append(kk); nxt=other(segs[kk],cur); V.append(nxt)
                if (n,L,nxt) in fixedset or is_fixed(n,L,nxt): break
                ks=[x for x in EIDX[(n,L,nxt)] if x!=kk]
                if not ks or ks[0] in seen: break
                cur=nxt; kk=ks[0]
            out.append((n,L,V,K))
    return out
# ---- octilinear helpers
def odir(a,c):
    dx,dy=c[0]-a[0],c[1]-a[1]
    if dx==0 and dy==0: return None
    if dy==0 or dx==0 or abs(abs(dx)-abs(dy))<=3:
        return int(round(math.degrees(math.atan2(dy,dx))/45.0))%8
    return None
def turn_ok(d1,d2):
    if d1 is None or d2 is None: return True
    t=(d2-d1)%8; return t in (0,1,7)
def conns(P,Q):
    d=odir(P,Q)
    if d is not None: return [[P,Q]]
    dx,dy=Q[0]-P[0],Q[1]-P[1]; m=min(abs(dx),abs(dy)); sx=1 if dx>0 else -1; sy=1 if dy>0 else -1
    D=(sx*m,sy*m)
    return [[P,(P[0]+D[0],P[1]+D[1]),Q],[P,(Q[0]-D[0],Q[1]-D[1]),Q]]
def plen(pts): return sum(math.hypot(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1))
def cost(pts):
    nseg=len(pts)-1; nd=sum(1 for i in range(nseg) if odir(pts[i],pts[i+1]) not in (0,2,4,6))
    return nseg+0.01*nd+1e-9*plen(pts)
UV={0:(1,0),1:(1,1),2:(0,1),3:(-1,1),4:(-1,0),5:(-1,-1),6:(0,-1),7:(1,-1)}
def pad_points(g,through,d,hw,toward):
    """points X inside eroded pad g such that X->through has direction d (X = through - k*UV[d]), nearest 'toward'."""
    ge=g.buffer(-0.05e6)
    if ge.is_empty: return None
    ux,uy=UV[d]; far=(through[0]-ux*40e6,through[1]-uy*40e6)
    inter=LineString([through,far]).intersection(ge)
    if inter.is_empty: return None
    q=nearest_points(inter,Point(toward))[0]
    k=int(round(max(abs(q.x-through[0]),abs(q.y-through[1]))))
    if k<=0: return None
    X=(through[0]-ux*k,through[1]-uy*k)
    if not ge.contains(Point(X)): return None
    return X
def solve(n,L,V,hw,ogap,freedom,gapcache):
    N=len(V)-1
    def req(i,j):
        if MODE=='strict' and j>i+1: return PREF
        return max(CLMIN,min(PREF,min(ogap[i:j])))
    def ok(pts,i,j):
        r=req(i,j)
        for a in range(len(pts)-1):
            key=(n,L,pts[a],pts[a+1],r)
            if key not in gapcache: gapcache[key]=seg_gap(L,n,pts[a],pts[a+1],hw,need=r)
            if not gapcache[key]: return False
        return True
    INF=1e18; dp={(0,None):(0.0,None,None)}
    g0=freedom[0]; gN=freedom[1]
    if g0 is not None:
        for j in range(1,min(N,W)+1):
            for d in range(8):
                X=pad_points(g0,V[j],d,hw,V[0])
                if X is None or X==V[0]: continue
                pts=[X,V[j]]
                if ok(pts,0,j):
                    c=cost(pts); st=(j,d)
                    if c<dp.get(st,(INF,))[0]: dp[st]=(c,('start',),pts)
    order=sorted(set(i for i,_ in dp.keys()))
    best_end=None
    for i in range(N+1):
        sts=[(st,v) for st,v in dp.items() if st[0]==i]
        if not sts: continue
        for j in range(i+1,min(N,i+W)+1):
            for pts in conns(V[i],V[j]):
                dirs=[odir(pts[a],pts[a+1]) for a in range(len(pts)-1)]
                if any(x is None for x in dirs): continue
                if len(dirs)==2 and not turn_ok(dirs[0],dirs[1]): continue
                c=None
                for (si,dl),v in sts:
                    if not turn_ok(dl,dirs[0]): continue
                    if c is None:
                        if not ok(pts,i,j): break
                        c=cost(pts)
                    st=(j,dirs[-1]); nc=v[0]+c
                    if nc<dp.get(st,(INF,))[0]-1e-12: dp[st]=(nc,(i,dl),pts)
        if gN is not None and i<N and i>=N-W:
            for (si,dl),v in sts:
                for d in range(8):
                    if not turn_ok(dl,d): continue
                    X=pad_points(gN,V[i],(d+4)%8,hw,V[N])  # X such that X->V[i] has dir d+4 => V[i]->X dir d
                    if X is None or X==V[N]: continue
                    pts=[V[i],X]
                    if ok(pts,i,N):
                        nc=v[0]+cost(pts)
                        if best_end is None or nc<best_end[0]: best_end=(nc,(i,dl),pts)
    ends=[(v[0],st) for st,v in dp.items() if st[0]==N]
    cands=[]
    if ends:
        c,st=min(ends); cands.append((c,st,None))
    if best_end: cands.append((best_end[0],None,best_end))
    if not cands: return None
    c,st,be=min(cands,key=lambda x:x[0])
    chain=[]
    if be: chain.append(be[2]); st=be[1]
    while st is not None and st!=(0,None):
        v=dp[st]; chain.append(v[2]); st=v[1] if v[1]!=('start',) else None
    pts=[]
    for piece in reversed(chain):
        pts+= piece if not pts else piece[1:]
    return c,pts
SI={'/CLK_CPU','/CLK_GLUE','/CLK_EXP','/CLK_DRAMC','/CLK_LA','/clock/CLK_FPU_CPU','/CLK_FPU','/DRAM_CLK','Net-(X2-OUT)','/clock/CLKB_X3','/clock/OSC_CPU','/RAS0_n','/CAS3_n','/WE_n'}
stats=collections.Counter()
t0=time.time()
print('split',split_all(),'segs',len(segs),flush=True)
for MODE in ('strict','relaxed'):
  for ps in range(MAXPASS):
      imp=0; P=paths(); gapcache={}
      for (n,L,V,K) in P:
          if any(k not in segs for k in K) or len(K)<2 and True:
              # single-segment paths can still benefit from pad freedom
              if any(k not in segs for k in K): continue
          ws={segs[k][4] for k in K}
          if len(ws)!=1: stats['mixed_width']+=1; continue
          w=ws.pop(); hw=w/2; lk=segs[K[0]][5]
          if V[0]==V[-1]: continue
          ogap=[seg_gap(L,n,V[i],V[i+1],hw) for i in range(len(V)-1)]
          def free(p):
              if len(EIDX[(n,L,p)])!=1 or p in viapts[n] or (n,L,p) in FIX: return None
              return in_same_pad(n,L,p)
          fr=(free(V[0]),free(V[-1]))
          oldc=cost(V); oldl=plen(V)
          # remove own segments from hash while solving (same net anyway, but keeps hash clean)
          r=solve(n,L,V,hw,ogap,fr,gapcache)
          if r and plen(r[1])>oldl+1:
              r=solve(n,L,V,hw,ogap,(None,None),gapcache)
          if not r or r[0]>=oldc-1e-9 or plen(r[1])>oldl+1: continue
          pts=r[1]
          if MODE=='relaxed':
              ng=[seg_gap(L,n,pts[a],pts[a+1],hw) for a in range(len(pts)-1) if pts[a]!=pts[a+1]]
              if sum(g<PREF-1 for g in ng)>sum(g<PREF-1 for g in ogap) or min(ng)<min(ogap)-1: stats['relaxed_rejected']+=1; continue
          for k in K: delseg(k)
          for a in range(len(pts)-1):
              if pts[a]!=pts[a+1]: newseg(n,L,pts[a],pts[a+1],w,lk)
          imp+=1; stats['segs_removed']+=len(K)-(len(pts)-1)
          gapcache={}  # geometry changed
      print(MODE,'pass',ps,'paths',len(P),'improved',imp,dict(stats),round(time.time()-t0,1),flush=True)
      if imp==0: break

def simplify(V,fixedfn):
    out=[V[0]]
    for p in V[1:]:
        if p==out[-1]: continue
        out.append(p)
    changed=True
    while changed:
        changed=False
        for i in range(1,len(out)-1):
            if fixedfn(out[i]) : continue
            d1=odir(out[i-1],out[i]); d2=odir(out[i],out[i+1])
            if d1 is not None and d1==d2: del out[i]; changed=True; break
    return out
def valid_poly(V):
    ds=[odir(V[i],V[i+1]) for i in range(len(V)-1)]
    if any(d is None for d in ds): return False
    return all(turn_ok(ds[i],ds[i+1]) for i in range(len(ds)-1))
def try_shifts(n,L,V,hw,ogap,free0,freeN,origfix,only=None):
    oldset=set((V[i],V[i+1]) for i in range(len(V)-1))
    gmap={(V[i],V[i+1]):ogap[i] for i in range(len(V)-1)}
    def jogs(V):
        out=[]
        for i in range(1,len(V)-2):
            d=odir(V[i-1],V[i]); dm=odir(V[i],V[i+1]); d2=odir(V[i+1],V[i+2])
            if d is None or d!=d2 or dm==d: continue
            J=(V[i+1][0]-V[i][0],V[i+1][1]-V[i][1])
            if d%2==0: o=(0,J[1]) if d in (0,4) else (J[0],0)
            else:
                p=UV[(d+2)%8]; b2=J[0]*p[0]+J[1]*p[1]
                if b2%2: continue
                o=(b2//2*p[0],b2//2*p[1])
            if o==(0,0): continue
            if abs(o[0])+abs(o[1])<1e6: out.append((i,o))
        return out
    def cand(V,i,o,side):
        od=odir((0,0),o); 
        if side=='back':
            a=None
            for k in range(i-1,0,-1):
                dk=odir(V[k-1],V[k])
                if dk in (od,(od+4)%8): a=k; break
            if a is None:
                if free0 is not None and free0.buffer(-0.05e6).contains(Point(V[0][0]+o[0],V[0][1]+o[1])): a=0
                else: BLK[0]='end:'+('via' if V[0] in viapts[n] else 'pad/junction'); return None
            NV=V[:a]+[(v[0]+o[0],v[1]+o[1]) for v in V[a:i+1]]+V[i+1:]
            if a>0 and odir(NV[a-1],NV[a]) not in (odir(V[a-1],V[a]),None) : return None
        else:
            bb=None
            for k in range(i+2,len(V)-1):
                dk=odir(V[k],V[k+1])
                if dk in (od,(od+4)%8): bb=k; break
            if bb is None:
                N=len(V)-1
                if freeN is not None and freeN.buffer(-0.05e6).contains(Point(V[N][0]-o[0],V[N][1]-o[1])): bb=N
                else: BLK[0]='end:'+('via' if V[N] in viapts[n] else 'pad/junction'); return None
            NV=V[:i+1]+[(v[0]-o[0],v[1]-o[1]) for v in V[i+1:bb+1]]+V[bb+1:]
            if bb<len(V)-1 and odir(NV[bb],NV[bb+1]) not in (odir(V[bb],V[bb+1]),None): return None
        NV=simplify(NV,lambda p: p in origfix)
        if NV[0]!=V[0] and free0 is None: return None
        if NV[-1]!=V[-1] and freeN is None: return None
        if not valid_poly(NV): return None
        # clearance on new segments
        oldmin=min(ogap)
        for a2 in range(len(NV)-1):
            sg=(NV[a2],NV[a2+1])
            if sg in oldset: continue
            r=max(CLMIN,min(PREF,oldmin)) if MODE!='strict' else PREF
            if MODE=='loose': r=CLMIN
            if not seg_gap(L,n,sg[0],sg[1],hw,need=r): return None
        return NV
    changed=False
    for it in range(60 if only is None else 1):
        J=jogs(V); done=False
        if only is not None: J=[x for x in J if x[0]==only]
        for i,o in J:
            cs=[c for c in (cand(V,i,o,'back'),cand(V,i,o,'forward')) if c]
            if not cs: continue
            V=min(cs,key=plen); done=True; changed=True; break
        if not done: break
    return V,changed
def shift_pass():
    imp=0
    for (n,L,V,K) in paths():
        if any(k not in segs for k in K): continue
        ws={segs[k][4] for k in K}
        if len(ws)!=1 or V[0]==V[-1] or len(V)<4: continue
        w=ws.pop(); hw=w/2; lk=segs[K[0]][5]
        ogap=[seg_gap(L,n,V[i],V[i+1],hw) for i in range(len(V)-1)]
        def free(p):
            if len(EIDX[(n,L,p)])!=1 or p in viapts[n] or (n,L,p) in FIX: return None
            return in_same_pad(n,L,p)
        origfix=set(V[1:-1])&set(p for p in V[1:-1] if is_fixed(n,L,p))
        NV,ch=try_shifts(n,L,V,hw,ogap,free(V[0]),free(V[-1]),origfix)
        if not ch: continue
        if n in SI and plen(NV)>plen(V)+1: stats['shift_si_reject']+=1; continue
        ng=[seg_gap(L,n,NV[a],NV[a+1],hw) for a in range(len(NV)-1)]
        if sum(g<PREF-1 for g in ng)>sum(g<PREF-1 for g in ogap) or min(ng)<min(ogap)-1: stats['shift_gap_reject']+=1; continue
        for k in K: delseg(k)
        for a in range(len(NV)-1): newseg(n,L,NV[a],NV[a+1],w,lk)
        imp+=1; stats['shift_segs_removed']+=len(K)-(len(NV)-1)
    return imp
for rnd in range(5):
    MODE='relaxed' if rnd<2 else 'loose'
    si=shift_pass(); print('shift round',rnd,'paths improved',si,dict(stats),round(time.time()-t0,1),flush=True)
    imp2=0
    for ps in range(4):
        P=paths(); gapcache={}; imp=0
        for (n,L,V,K) in P:
            if any(k not in segs for k in K): continue
            ws={segs[k][4] for k in K}
            if len(ws)!=1 or V[0]==V[-1]: continue
            w=ws.pop(); hw=w/2; lk=segs[K[0]][5]
            ogap=[seg_gap(L,n,V[i],V[i+1],hw) for i in range(len(V)-1)]
            def free(p):
                if len(EIDX[(n,L,p)])!=1 or p in viapts[n] or (n,L,p) in FIX: return None
                return in_same_pad(n,L,p)
            r=solve(n,L,V,hw,ogap,(free(V[0]),free(V[-1])),gapcache)
            oldl=plen(V)
            if r and plen(r[1])>oldl+1: r=solve(n,L,V,hw,ogap,(None,None),gapcache)
            if not r or r[0]>=cost(V)-1e-9 or plen(r[1])>oldl+1: continue
            pts=[p for i,p in enumerate(r[1]) if i==0 or p!=r[1][i-1]]
            ng=[seg_gap(L,n,pts[a],pts[a+1],hw) for a in range(len(pts)-1)]
            if sum(g<PREF-1 for g in ng)>sum(g<PREF-1 for g in ogap) or min(ng)<min(ogap)-1: continue
            for k in K: delseg(k)
            for a in range(len(pts)-1): newseg(n,L,pts[a],pts[a+1],w,lk)
            imp+=1; gapcache={}
        imp2+=imp
        if imp==0: break
    print('  dp after shift improved',imp2,round(time.time()-t0,1),flush=True)
    if si==0 and imp2==0 and rnd>=2: break
pickle.dump({'segs':segs,'stats':dict(stats)},open(OUT,'wb'))

# ---- classify remaining jogs
NOCHK=True; MODE='relaxed'
def path_jogs(V):
    out=[]
    for i in range(1,len(V)-2):
        din=odir(V[i-1],V[i]); dm=odir(V[i],V[i+1]); dout=odir(V[i+1],V[i+2])
        if din is not None and din==dout and dm!=din:
            ux,uy=UV[din]; l=math.hypot(ux,uy)
            off=abs(ux*(V[i+1][1]-V[i][1])-uy*(V[i+1][0]-V[i][0]))/l/1e6
            if off<1.0: out.append((i,off))
    return out
cls=collections.Counter(); ex=collections.defaultdict(list)
def endtype(n,L,p):
    if p in viapts[n]: return 'via'
    if len(EIDX[(n,L,p)])>2 or (n,L,p) in FIX: return 'junction'
    if in_same_pad(n,L,p) is not None: return 'pad' if len(EIDX[(n,L,p)])==1 else 'pad(multi)'
    return 'other'
MODE='relaxed'
for (n,L,V,K) in paths():
    J=path_jogs(V)
    if not J: continue
    ws={segs[k][4] for k in K}; hw=ws.pop()/2
    def free(p):
        if len(EIDX[(n,L,p)])!=1 or p in viapts[n] or (n,L,p) in FIX: return None
        return in_same_pad(n,L,p)
    f0,fN=free(V[0]),free(V[-1])
    origfix=set(p for p in V[1:-1] if is_fixed(n,L,p))
    for (i,off) in J:
        reasons=[]
        for side in ('back','forward'):
            PREF=0.16e6; BLK[0]='other'
            # single-jog shift test at DRC minimum
            def one(V=V,i=i,side=side):
                J2=[(i,(0,V[i+1][1]-V[i][1]) if odir(V[i-1],V[i]) in (0,4) else (V[i+1][0]-V[i][0],0))]
                return J2
            jo=one()[0][1]
            # reuse try_shifts machinery on a single jog by calling cand through try_shifts on a trimmed copy is complex; emulate:
            NV,ch=try_shifts(n,L,V,hw,[0.16e6]*(len(V)-1),f0,fN,origfix,only=i)
            reasons.append('ok@0.16' if ch else BLK[0]); break
        PREF=0.20e6
        r=reasons[0]
        why={'ok@0.16':'removable only by going below 0.2 mm (kept for margin)','track':'lane change in a dense bundle: neighbouring lane is another net','pad':'blocked by a pad','via':'blocked by a via','hole':'blocked by a hole','power track':'blocked by a power track','edge':'board edge','gfx':'footprint copper','diagonal run':'jog on a diagonal run'}.get(r, 'fixed ends: no segment can absorb the shift (%s)'%r if r.startswith('end') else r)
        cls[why]+=1; ex[why].append((n,LAYERS[L],round(V[i][0]/1e6,2),round(V[i][1]/1e6,2),round(off,2)))
print('remaining in-path jogs <1mm by reason:',dict(cls))
for k,v in ex.items(): print(' ',k,v[:6])
pickle.dump({'cls':dict(cls),'ex':dict(ex)},open(OUT+'.cls','wb'))
