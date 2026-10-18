import pcbnew, sys, math, collections
POWER={'GND','+5V','+3V3'}
for path in sys.argv[1:]:
    b=pcbnew.LoadBoard(path)
    ends=collections.defaultdict(list); vias=set(); L=0; nv=0
    for t in b.GetTracks():
        if t.GetNetname() in POWER: continue
        if t.GetClass()=='PCB_VIA': vias.add((t.GetNetname(),t.GetPosition().x,t.GetPosition().y)); nv+=1; continue
        s,e=t.GetStart(),t.GetEnd(); L+=t.GetLength()
        ends[(t.GetNetname(),t.GetLayer(),s.x,s.y)].append((e.x-s.x,e.y-s.y))
        ends[(t.GetNetname(),t.GetLayer(),e.x,e.y)].append((s.x-e.x,s.y-e.y))
    c=collections.Counter(); where=collections.defaultdict(list)
    for (n,ly,x,y),vs in ends.items():
        if len(vs)!=2: c['junction/end(deg %d)'%len(vs) if len(vs)>2 else 'end']+=1; continue
        (a,b_),(cc,d)=vs
        ang=math.degrees(math.acos(max(-1,min(1,(a*cc+b_*d)/math.hypot(a,b_)/math.hypot(cc,d)))))
        k='%d'%round(ang); tag='via' if (n,x,y) in vias else ''
        c[k+('@via' if tag else '')]+=1
        if round(ang) in (90,45) : where[k].append((n,ly,round(x/1e6,2),round(y/1e6,2)))
    print(path, 'len %.3f m'%(L/1e9), 'vias',nv, dict(c))
    for k,v in where.items(): print(' ',k,len(v),v[:12])
