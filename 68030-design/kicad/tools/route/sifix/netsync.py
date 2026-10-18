import pcbnew, re, sys
b=pcbnew.LoadBoard(sys.argv[1]); s=open(sys.argv[2]).read()
pad2net={}
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]+)"\)(.*?)(?=\(net \(code|\Z)', s, re.S):
    for ref,pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"', m.group(2)): pad2net[(ref,pin)]=m.group(1)
ch=[]
for f in b.GetFootprints():
    for p in f.Pads():
        k=(f.GetReference(),p.GetNumber())
        if k not in pad2net: continue
        nn=pad2net[k]
        if p.GetNetname()!=nn:
            ni=b.FindNet(nn)
            if ni is None:
                ni=pcbnew.NETINFO_ITEM(b,nn); b.Add(ni)
            ch.append((k,p.GetNetname(),nn)); p.SetNet(ni)
for c in ch: print(c)
b.Save(sys.argv[3])
