import pcbnew, pickle, sys
IN,PK,OUT=sys.argv[1:4]
POWER={'GND','+5V','+3V3'}
b=pcbnew.LoadBoard(IN); m=pickle.load(open(PK,'rb'))
old=[t for t in b.GetTracks() if t.GetClass()=='PCB_TRACK' and t.GetNetname() not in POWER]
nets=b.GetNetsByName()
for k,(n,L,a,c,w,lk) in m['segs'].items():
    if a==c: continue
    t=pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(int(a[0]),int(a[1]))); t.SetEnd(pcbnew.VECTOR2I(int(c[0]),int(c[1])))
    t.SetWidth(int(w)); t.SetLayer(L); t.SetNet(nets[n]); t.SetLocked(lk); b.Add(t)
for t in old: b.Remove(t)
b.Save(OUT); print('wrote',len(m['segs']),'removed',len(old))
