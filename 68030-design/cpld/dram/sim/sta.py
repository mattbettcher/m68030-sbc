import re,sys,collections
vo=open(sys.argv[1]).read(); sdo=open(sys.argv[2]).read()
# SDF delays: inst -> {inpin: delay_ns}
dl=collections.defaultdict(dict)
for m in re.finditer(r'\(INSTANCE (\S+)\)\s*\(DELAY \(ABSOLUTE(.*?)\)\s*\)\s*\)', sdo, re.S):
    for p in re.finditer(r'\(IOPATH (\(posedge (\w+)\)|\w+) (\w+) \(\s*(\d+):', m.group(2)):
        src=p.group(2) or p.group(1); dl[m.group(1)][(src,p.group(3))]=int(p.group(4))/1000
cells=[]  # (type, inst, out_net, {inpin:net})
for m in re.finditer(r'^(\w+) (\w+) \((.*?)\);', vo, re.M):
    t,i,args=m.groups()
    if t=='module': continue
    if '.' in args:
        d=dict(re.findall(r'\.(\w+)\((\w+)\)',args))
        if t=='DFFEARS': cells.append((t,i,d['Q'],{'CLK':d['CLK']},d['D']))
        elif t=='TRI': cells.append((t,i,d['Q'],{'A':d['A'],'EN':d['EN']},None))
        elif t=='BIBUF': cells.append((t,i,d['PAD'],{'A':d['A'],'EN':d['EN']},None))
    else:
        a=[x.strip() for x in args.split(',')]
        outp='QN' if t=='INV' else 'Q'
        ins={('A' if t in('INV','BUF') else f'A{k+1}'):n for k,n in enumerate(a[1:])}
        cells.append((t,i,a[0],ins,None))
drv={c[2]:c for c in cells}
memo={}
def arr(net,stack=()):
    if net in memo: return memo[net]
    if net not in drv or net in ('gnd','vcc'): memo[net]=(0.0,[net]); return memo[net]
    t,i,o,ins,_=drv[net]
    if t=='DFFEARS':
        c,p=arr(ins['CLK']); r=(c+dl[i].get(('CLK','Q'),1.0),p+[i+'.Q']); memo[net]=r; return r
    if net in stack: return (0.0,['LOOP'])
    best=(0.0,[net])
    for pin,n in ins.items():
        a,p=arr(n,stack+(net,))
        op='QN' if t=='INV' else ('PAD' if t=='BIBUF' else 'Q')
        d=dl[i].get((pin,op),0.0)
        if a+d>=best[0]: best=(a+d,p+[i])
    memo[net]=best; return best
outs=re.search(r'module \w+\((.*?)\);',vo,re.S).group(1).replace('\n','').split(',')
outs=[o.strip() for o in outs]
print("Pin-to-pad (and clock-to-pad) arrival, ns, from fitter SDF (ATF1508AS -7 model):")
for o in sorted(outs):
    if o in drv: a,p=arr(o); print(f"  {o:14s} {a:5.1f}   via {p[0]}")
print("Worst register D arrival + setup (ns):")
worst=[]
for c in cells:
    if c[0]=='DFFEARS':
        a,p=arr(c[4]); su=3.0; worst.append((a+su,c[2],p[0]))
for w in sorted(worst,reverse=True)[:6]: print(f"  {w[1]:10s} {w[0]:5.1f}  from {w[2]}")
