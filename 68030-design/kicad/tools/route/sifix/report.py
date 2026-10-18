import pcbnew, sys, collections, heapq, math
def load(path):
    b=pcbnew.LoadBoard(path)
    L=collections.defaultdict(lambda:[0.0,0,0.0])
    for t in b.GetTracks():
        n=t.GetNetname()
        if t.GetClass()=='PCB_VIA': L[n][1]+=1
        else:
            L[n][0]+=t.GetLength()/1e6
            if t.GetLayer()==pcbnew.F_Cu: L[n][2]+=t.GetLength()/1e6
    return b,L
def graph(b,net):
    G=collections.defaultdict(list); key=lambda p:(round(p.x/1e4),round(p.y/1e4))
    segs=[t for t in b.GetTracks() if t.GetNetname()==net and t.GetClass()=='PCB_TRACK']
    pts=set()
    for t in segs:
        a,c=key(t.GetStart()),key(t.GetEnd()); l=t.GetLength()/1e6
        G[a].append((c,l)); G[c].append((a,l)); pts|={a,c}
    # T-junctions: endpoint lying on another segment
    for t in segs:
        s,e=t.GetStart(),t.GetEnd()
        for p in list(pts):
            P=pcbnew.VECTOR2I(p[0]*10000,p[1]*10000)
            if t.HitTest(P,0) and p not in (key(s),key(e)):
                d1=(P-s).EuclideanNorm()/1e6; d2=(P-e).EuclideanNorm()/1e6
                G[p]+= [(key(s),d1),(key(e),d2)]; G[key(s)].append((p,d1)); G[key(e)].append((p,d2))
    pads={}
    for f in b.GetFootprints():
        for pd in f.Pads():
            if pd.GetNetname()==net:
                k=('pad',f.GetReference()+'.'+pd.GetNumber()); pads[k[1]]=k
                for p in pts:
                    if pd.HitTest(pcbnew.VECTOR2I(p[0]*10000,p[1]*10000)): G[k].append((p,0)); G[p].append((k,0))
    return G,pads
def dij(G,src):
    d={src:0}; pr={}; h=[(0,src)]
    while h:
        c,u=heapq.heappop(h)
        if c>d[u]: continue
        for v,w in G[u]:
            if c+w<d.get(v,1e9): d[v]=c+w; pr[v]=u; heapq.heappush(h,(c+w,v))
    return d,pr
def stubs(b,net,main_a,main_b,others):
    G,pads=graph(b,net)
    d,pr=dij(G,pads[main_a]); path=set(); u=pads[main_b]
    while u in pr: path.add(u); u=pr[u]
    path.add(pads[main_a]); out={'main':round(d[pads[main_b]],1)}
    for o in others:
        if o not in pads: continue
        dd,_=dij(G,pads[o]); out[o]=round(min(dd.get(p,1e9) for p in path),1)
    return out
if __name__=='__main__':
    for path in sys.argv[1:]:
        b,L=load(path); print('==',path)
        for n in ['/CLK_CPU','/clock/CLKB_CPU','/CLK_GLUE','/clock/CLKB_GLUE','/CLK_EXP','/clock/CLKB_EXP','/CLK_DRAMC','/clock/CLKB_DRAMC','/CLK_LA','/clock/CLKB_LA','/clock/CLK_FPU_CPU','/clock/CLKB_FPU','/CLK_FPU','/DRAM_CLK','Net-(X2-OUT)','/clock/CLKB_X3','Net-(X3-OUT)','/clock/OSC_CPU','/RAS0_n','/CAS3_n','/WE_n','/dram/U4_RAS0_n','/dram/U4_CAS3_n','/dram/U4_WE_n']:
            v=L[n]; print('  %-22s %6.1f mm %2d vias  F %3.0f%%'%(n,v[0],v[1],100*v[2]/v[0] if v[0] else 0))
        for n,ra,rb,ot in [('/RAS0_n','R816.2','J1.44',['TP801','J13.37']),('/CAS3_n','R823.2','J1.42',['TP806','J13.38']),('/WE_n','R824.2','J1.47',['TP807','J13.39'])]:
            try: print('  stubs',n,stubs(b,n,ra,rb,[o if '.' in o else o+'.1' for o in ot]))
            except Exception as e: print('  stubs',n,'ERR',e)
        u4=b.FindFootprintByReference('U4'); pin={p.GetNetname():p for p in u4.Pads()}
        ds=[]
        for i in range(804,825):
            r=b.FindFootprintByReference(f'R{i}'); p1=[p for p in r.Pads() if p.GetNumber()=='1'][0]
            ds.append((f'R{i}',round((pin[p1.GetNetname()].GetPosition()-p1.GetPosition()).EuclideanNorm()/1e6,1)))
        print('  R-to-U4 (pad1 centre to U4 pin centre, mm):',ds)
        tot=sum(v[0] for n,v in L.items() if n not in ('GND','+5V','+3V3')); vias=sum(v[1] for n,v in L.items() if n not in ('GND','+5V','+3V3'))
        print('  total signal %.2f m, %d vias'%(tot/1000,vias))
