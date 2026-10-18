import numpy as np, ctypes, pickle, fnmatch, sys, time, collections, json
lib=ctypes.CDLL('/tmp/route/libastar.so')
fp=np.ctypeslib.ndpointer(np.float32,flags='C'); up=np.ctypeslib.ndpointer(np.uint8,flags='C'); ip=np.ctypeslib.ndpointer(np.int32,flags='C')
lib.route.argtypes=[ctypes.c_int,ctypes.c_int,fp,fp,up,up,ctypes.c_float,fp,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ip,ctypes.c_int,ctypes.c_long]
lib.route.restype=ctypes.c_int
CLKPAT=['/CLK_*','/DRAM_CLK','/clock/CLKB_*','/clock/CLK_FPU*','/dram/U4_*','/dram/MA*','/dram/RAS*','/dram/CAS*','/dram/WE*','/CAS*','/RAS*','/WE_n']
def width(nn): return 0.25 if any(fnmatch.fnmatchcase(nn,p) for p in CLKPAT) else 0.2
INF=np.float32(1e30)
class Router:
    def __init__(s, gp):
        G=pickle.load(open(gp,'rb')); s.G=G
        s.nx,s.ny=G['nx'],G['ny']; s.N=s.nx*s.ny
        s.own=np.stack(G['own']).reshape(2,-1).astype(np.int32); s.vown=G['vown'].reshape(-1).astype(np.int32)
        nets=collections.defaultdict(list)
        for k,(net,nn,x,y,smd) in G['padinfo'].items(): nets[net].append(k)
        s.nets={n:ks for n,ks in nets.items() if len(ks)>=2}
        s.name={n:G['padinfo'][ks[0]][1] for n,ks in s.nets.items()}
        s.term={k:np.array([li*s.N+j*s.nx+i for (li,j,i) in tl],np.int64) for k,tl in G['terms'].items()}
        s.occ=np.zeros(2*s.N,np.float32); s.hist=np.zeros(2*s.N,np.float32)
        s.use={}   # net -> np.array of occupied lc (unique)
        s.paths={} # net -> list of path arrays
        s.fixed=set()
        s.dm=np.array([1.0,1.0,1.0,1.0],np.float32)
        s.path=np.zeros(200000,np.int32)
        s.layerpen={}
        s.alpha={}
        # neighbor offsets for via footprint
    def footprint(s, lcs_via):
        out=[]
        for lc in lcs_via:
            c=lc% s.N; x=c%s.nx; y=c//s.nx
            for (dx,dy) in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
                x2,y2=x+dx,y+dy
                if 0<=x2<s.nx and 0<=y2<s.ny:
                    out+=[y2*s.nx+x2, s.N+y2*s.nx+x2]
        return out
    def ripup(s,n):
        if n in s.use: s.occ[s.use[n]]-=1; del s.use[n]
        s.paths.pop(n,None)
    def commit(s,n,paths):
        cells=set()
        for p in paths:
            cells.update(p.tolist())
            for a,b in zip(p[:-1],p[1:]):
                if a% s.N==b% s.N: cells.update(s.footprint([a]))
        u=np.fromiter(cells,np.int64); s.use[n]=u; s.occ[u]+=1; s.paths[n]=paths
    def costs(s,n,pf):
        legal=((s.own==0)|(s.own==n)).reshape(-1)
        a=s.alpha.get(n,1.0)
        c=(1.0+a*s.hist)*(1.0+a*pf*s.occ)
        lp=s.layerpen.get(n)
        if lp is not None: c=c*np.repeat(np.array(lp,np.float32),s.N)
        c=np.where(legal,c,INF).astype(np.float32)
        # via cost: base + footprint congestion both layers
        pen=(a*pf*s.occ*(1.0+a*s.hist)).reshape(2,s.ny,s.nx); t=pen[0]+pen[1]
        f=t.copy(); f[1:,:]+=t[:-1,:]; f[:-1,:]+=t[1:,:]; f[:,1:]+=t[:,:-1]; f[:,:-1]+=t[:,1:]
        vl=((s.vown==0)|(s.vown==n))
        v=np.where(vl, s.VIA+f.reshape(-1), INF).astype(np.float32)
        return c,v
    VIA=10.0; BEND=0.6
    def route_net(s,n,pf,maxexp=4000000):
        keys=s.nets[n]
        c,v=s.costs(n,pf)
        src=np.zeros(2*s.N,np.uint8)
        # start from pad closest to centroid
        pts=np.array([[s.G['padinfo'][k][2],s.G['padinfo'][k][3]] for k in keys]); cen=pts.mean(0)
        order=np.argsort(((pts-cen)**2).sum(1))
        first=keys[order[0]]; src[s.term[first]]=1
        remaining=[k for k in keys if k!=first]
        paths=[]; fails=[]
        while remaining:
            tgt=np.zeros(2*s.N,np.uint8)
            owner={}
            for k in remaining:
                tgt[s.term[k]]=1
                for lc in s.term[k].tolist(): owner[lc]=k
            allt=np.concatenate([s.term[k] for k in remaining]); cc=allt% s.N
            xs=cc% s.nx; ys=cc//s.nx
            L=lib.route(s.nx,s.ny,c,v,src,tgt,s.BEND,s.dm,int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max()),1.0,s.path,len(s.path),maxexp)
            if L<0: fails+=remaining; break
            p=s.path[:L][::-1].copy(); paths.append(p)
            k=owner[int(p[-1])]; remaining.remove(k)
            src[p]=1
            # via cells: mark both layers
            for a,b in zip(p[:-1],p[1:]):
                if a% s.N==b% s.N: src[a% s.N]=1; src[s.N+a% s.N]=1
            src[s.term[k]]=1
        return paths,fails
    def overflow(s):
        return int((s.occ>1).sum())
    def conflicted(s):
        bad=s.occ>1
        return [n for n,u in s.use.items() if bad[u].any()]
