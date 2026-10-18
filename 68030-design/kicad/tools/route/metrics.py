import pcbnew, collections, fnmatch, sys
b=pcbnew.LoadBoard(sys.argv[1])
L=collections.defaultdict(lambda:[0.0,0])
for t in b.GetTracks():
    n=t.GetNetname()
    if n in ('GND','+5V','+3V3'): continue
    if t.GetClass()=='PCB_VIA': L[n][1]+=1
    else: L[n][0]+=t.GetLength()/1e6
print('signal m %.2f vias %d segs %d'%(sum(v[0] for v in L.values())/1000, sum(v[1] for v in L.values()), sum(1 for t in b.GetTracks() if t.GetClass()=='PCB_TRACK' and t.GetNetname() not in ('GND','+5V','+3V3'))))
crit=[n for n in L if 'CLK' in n or n.startswith('/dram/MA') or 'RAS' in n or 'CAS' in n or 'WE_n' in n or 'X3' in n]
print(' '.join('%s=%.0f/%d'%(n.split('/')[-1],L[n][0],L[n][1]) for n in sorted(crit)))
print('crit total mm %.0f vias %d'%(sum(L[n][0] for n in crit), sum(L[n][1] for n in crit)))
