import re,sys
SRC=sys.argv[1]; DST=sys.argv[2]
P='${KIPRJMOD}/3dmodels/m68030-sbc.3dshapes/'
MAP={
 'U1':['PGA-128_13x13_Socket_LowProfile','PGA-128_13x13_MC68030'],
 'U2':['PLCC-68_THT-Socket','PLCC-68_Chip_InSocket'],
 'U3':['PLCC-84_THT-Socket','PLCC-84_Chip_InSocket'],
 'U4':['PLCC-84_THT-Socket','PLCC-84_Chip_InSocket'],
 'U5':['PLCC-32_THT-Socket','PLCC-32_Chip_InSocket'],
 'U6':['PLCC-44_THT-Socket','PLCC-44_Chip_InSocket'],
 'J1':['SIMM-72_TE-5822021-4_Socket','SIMM-72_Module_8chip'],
 'F1':['Fuse_Littelfuse-NANO2-451_453'],
 'L1':['L_Bourns_SRP1770TA_16.9x16.9mm'],
}
def mblock(path):
    return (f'\t\t(model "{path}"\n\t\t\t(offset\n\t\t\t\t(xyz 0 0 0)\n\t\t\t)\n\t\t\t(scale\n\t\t\t\t(xyz 1 1 1)\n\t\t\t)\n\t\t\t(rotate\n\t\t\t\t(xyz 0 0 0)\n\t\t\t)\n\t\t)\n')
lines=open(SRC,newline='').read().split('\n')
out=[];i=0;done=set()
while i<len(lines):
    l=lines[i]
    if l.startswith('\t(footprint '):
        j=i+1
        while lines[j]!='\t)': j+=1
        blk=lines[i:j+1]
        txt='\n'.join(blk)
        m=re.search(r'\(property "Reference" "([^"]+)"',txt); ref=m.group(1) if m else None
        if ref in MAP:
            nb=[];k=0
            while k<len(blk)-1:
                if blk[k].startswith('\t\t(model '):
                    while blk[k]!='\t\t)': k+=1
                    k+=1; continue
                nb.append(blk[k]); k+=1
            ins=''.join(mblock(P+n+'.step') for n in MAP[ref]).rstrip('\n').split('\n')
            blk=nb+ins+['\t)']; done.add(ref)
        out+=blk; i=j+1; continue
    out.append(l); i+=1
open(DST,'w',newline='').write('\n'.join(out))
print('updated',sorted(done),'missing',sorted(set(MAP)-done))
