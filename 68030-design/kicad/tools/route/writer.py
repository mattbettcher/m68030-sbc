import sys, pickle, pcbnew
sys.path.insert(0,'/tmp/route'); from router import width
def write(pcb_in, grid, state, pcb_out, lock=True, nets_only=None):
    G=pickle.load(open(grid,'rb')); S=pickle.load(open(state,'rb'))
    P,x0,y0,nx,ny=G['P'],G['x0'],G['y0'],G['nx'],G['ny']; N=nx*ny
    b=pcbnew.LoadBoard(pcb_in)
    LAY=[pcbnew.F_Cu,pcbnew.B_Cu]
    def pt(c): return pcbnew.VECTOR2I(int(round((x0+(c%nx)*P)*1e6)), int(round((y0+(c//nx)*P)*1e6)))
    nt=nv=0
    for n,paths in S['paths'].items():
        ni=b.FindNet(n) if False else None
        netinfo=b.GetNetInfo().GetNetItem(n); nn=netinfo.GetNetname(); w=int(width(nn)*1e6)
        segs=set(); vias=set()
        for p in paths:
            p=list(map(int,p))
            # split into layer runs
            run=[p[0]]
            def flush(run):
                L=run[0]//N; cs=[q%N for q in run]
                if len(cs)<2: return
                a=cs[0]; prev=cs[0]; d=None
                for c in cs[1:]:
                    dd=c-prev
                    if d is not None and dd!=d:
                        segs.add((L,min(a,prev),max(a,prev))); a=prev
                    d=dd; prev=c
                segs.add((L,min(a,prev),max(a,prev)))
            for q in p[1:]:
                if q%N==run[-1]%N and q//N!=run[-1]//N:
                    flush(run); vias.add(q%N); run=[q]
                else: run.append(q)
            flush(run)
        for (L,a,c) in segs:
            if a==c: continue
            t=pcbnew.PCB_TRACK(b); t.SetStart(pt(a)); t.SetEnd(pt(c)); t.SetWidth(w); t.SetLayer(LAY[L]); t.SetNet(netinfo); t.SetLocked(lock); b.Add(t); nt+=1
        for c in vias:
            v=pcbnew.PCB_VIA(b); v.SetPosition(pt(c)); v.SetWidth(600000); v.SetDrill(300000); v.SetNet(netinfo); v.SetLocked(lock)
            v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); b.Add(v); nv+=1
    filler=pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
    b.Save(pcb_out); print('tracks',nt,'vias',nv)
if __name__=='__main__': write(*sys.argv[1:5])
