import sys, time, pickle, numpy as np, fnmatch, os
sys.path.insert(0,'/tmp/sifix/r'); from router import Router, width
R=Router(os.environ.get('GRID','/tmp/route/grid.pkl'))
def prio(n):
    nn=R.name[n]; refs={k[0] for k in R.nets[n]}
    if nn.startswith('/CLK') or nn.startswith('/clock/') or nn=='/DRAM_CLK' or 'X3' in nn: return 0
    if nn.startswith('/dram/') or nn.startswith('/RAS') or nn.startswith('/CAS') or nn=='/WE_n' or 'J1' in refs: return 1
    if 'U1' in refs: return 2
    if refs & {'U2','U3','U5','U6','J11','J12','J13','J10'}: return 3
    return 4
for n in R.nets:
    if prio(n)==0: R.layerpen[n]=(1.0,4.0)   # clocks prefer F.Cu (over In1 GND)
CRIT=os.environ.get('CRIT')
if CRIT:
    for n in R.nets:
        nn=R.name[n]
        if prio(n)==0 or nn.startswith('/dram/') or nn.startswith('/RAS') or nn.startswith('/CAS') or nn=='/WE_n': R.alpha[n]=float(CRIT)
order=sorted(R.nets, key=lambda n:(prio(n), len(R.nets[n])))
state=os.environ.get('STATE','/tmp/route/state.pkl')
PRE=pickle.load(open(state,'rb')) if (os.path.exists(state) and '--fresh' not in sys.argv) else None
FIX=os.environ.get('FIX')
fixed=[]
def iscrit(n):
    nn=R.name[n]
    return prio(n)==0 or nn.startswith('/dram/') or nn.startswith('/RAS') or nn.startswith('/CAS') or nn=='/WE_n'
if FIX:
    import numpy as _np
    crit=[n for n in R.nets if iscrit(n) and (len(R.nets[n])==2 or R.name[n] in ('/RAS0_n','/CAS3_n','/WE_n')) and not R.name[n].startswith('/dram/U4_T')]
    def span(n):
        p=_np.array([[R.G['padinfo'][k][2],R.G['padinfo'][k][3]] for k in R.nets[n]]); return (p.max(0)-p.min(0)).sum()
    crit.sort(key=span)
    for n in crit:
        if PRE is not None:
            ps=PRE['paths'][n]; f=[]
        else:
            ps,f=R.route_net(n,1e6)
        if f:
            print('not fixed (blocked):',R.name[n], flush=True); continue
        R.commit(n,ps)
        for lc in R.use[n].tolist(): R.own.reshape(-1)[lc]=n
        cells=set()
        for p in ps:
            for a,b2 in zip(p[:-1],p[1:]):
                if a% R.N==b2% R.N:
                    c=a% R.N; x=c%R.nx; y=c//R.nx
                    for dx in (-1,0,1):
                        for dy in (-1,0,1):
                            if 0<=x+dx<R.nx and 0<=y+dy<R.ny: R.vown[(y+dy)*R.nx+x+dx]= -1 if R.vown[(y+dy)*R.nx+x+dx] not in (0,n) else n
        for p in ps:
            for lc in p.tolist():
                c=lc% R.N; x=c%R.nx; y=c//R.nx
                for dx,dy in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
                    if 0<=x+dx<R.nx and 0<=y+dy<R.ny:
                        q=(y+dy)*R.nx+x+dx
                        if R.vown[q] not in (0,n): R.vown[q]=-1
                        else: R.vown[q]=n
        fixed.append(n)
    # remove from occupancy (now hard obstacles)
    for n in fixed: R.occ[R.use[n]]-=1
    print('fixed',len(fixed),'crit nets pre-routed', flush=True)
    order=[n for n in order if n not in fixed]
    fixedpaths={n:R.paths[n] for n in fixed}
    for n in fixed: del R.use[n]
it0=0; pf=0.5; dirty=set()
if os.path.exists(state) and '--fresh' not in sys.argv:
    S=pickle.load(open(state,'rb')); R.hist=S['hist']; it0=S['it']+1; pf=S['pf']
    for n,ps in S['paths'].items():
        if n not in fixed: R.commit(n,ps)
    if FIX: fixedpaths={n:S['paths'][n] for n in fixed}
    dirty=set()
    for n,ps in R.paths.items():
        allc=np.concatenate(ps) if ps else np.zeros(0,np.int64)
        legal=((R.own.reshape(-1)[allc]==0)|(R.own.reshape(-1)[allc]==n)).all() if len(allc) else False
        vias=[a% R.N for p in ps for a,b in zip(p[:-1],p[1:]) if a% R.N==b% R.N]
        vl=all(R.vown[v] in (0,n) for v in vias)
        sc=set(allc.tolist())
        reach=all(any(t in sc for t in R.term[k].tolist()) for k in R.nets[n])
        if not (legal and vl and reach): dirty.add(n)
    for n in R.nets:
        if n not in R.paths: dirty.add(n)
    if CRIT: dirty|={n for n in R.nets if prio(n)<=1}
    print('dirty nets', len(dirty), [R.name[n] for n in dirty][:40])
maxit=int(sys.argv[1]) if len(sys.argv)>1 and sys.argv[1].isdigit() else 30
HINC=float(os.environ.get("HINC","0.3")); PFMAX=float(os.environ.get("PFMAX","1e9"))
log=open(state+'.log','a')
for it in range(it0, it0+maxit):
    t=time.time()
    cf=set(R.conflicted())|(dirty if it==it0 else set())
    todo = order if it==0 and not R.paths else [n for n in order if n in cf or n not in R.paths]
    fails=0; failnets=[]
    for n in todo:
        R.ripup(n)
        ps,f=R.route_net(n,pf)
        R.commit(n,ps)
        if f: fails+=len(f); failnets.append(R.name[n])
    ov=R.overflow()
    R.hist += np.where(R.occ>1, HINC*(R.occ-1), 0).astype(np.float32)
    msg=f'it {it} pf {pf:.2f} routed {len(todo)} overflow {ov} conflicted_nets {len(R.conflicted())} unreached_pads {fails} {time.time()-t:.0f}s'
    print(msg, flush=True); log.write(msg+'\n'); log.flush()
    allp=dict(R.paths)
    if FIX: allp.update(fixedpaths)
    pickle.dump(dict(hist=R.hist,it=it,pf=min(pf*1.4,PFMAX),paths=allp,fails=failnets),open(state,'wb'))
    pf=min(pf*1.4,PFMAX)
    if ov==0 and fails==0: print('CONVERGED'); break
