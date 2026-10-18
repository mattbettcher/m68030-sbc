import pcbnew,os,re,collections,json,sys
import os
HERE=os.path.dirname(os.path.abspath(__file__)); KICAD=os.path.normpath(os.path.join(HERE,'..','..'))
b=pcbnew.LoadBoard(sys.argv[1] if len(sys.argv)>1 else os.path.join(KICAD,'m68030-sbc.kicad_pcb'))
D=os.environ.get('KICAD9_3DMODEL_DIR','/usr/share/kicad/3dmodels'); PRJ=KICAD
def res(p):
    q=p.replace('${KICAD9_3DMODEL_DIR}',D).replace('${KICAD8_3DMODEL_DIR}',D).replace('${KICAD7_3DMODEL_DIR}',D).replace('${KICAD6_3DMODEL_DIR}',D).replace('${KISYS3DMOD}',D).replace('${KIPRJMOD}',PRJ)
    if not q.startswith('/'): q=os.path.join(PRJ,q)
    return q
rows=[]
for f in b.GetFootprints():
    ms=[(m.m_Filename, os.path.exists(res(m.m_Filename)), m.m_Show, (round(m.m_Offset.x,3),round(m.m_Offset.y,3),round(m.m_Offset.z,3)), (m.m_Rotation.x,m.m_Rotation.y,m.m_Rotation.z), (m.m_Scale.x,m.m_Scale.y,m.m_Scale.z)) for m in f.Models()]
    rows.append(dict(ref=f.GetReference(),fpid=f.GetFPIDAsString(),val=f.GetValue(),side='B' if f.IsFlipped() else 'F',rot=f.GetOrientationDegrees(),models=ms))
json.dump(rows,open(os.path.join(HERE,'fps.json'),'w'),indent=0)
c=collections.Counter()
for r in rows:
    st='none' if not r['models'] else ('ok' if all(m[1] for m in r['models']) else 'broken')
    c[st]+=1
print(c)
bylib=collections.defaultdict(list)
for r in rows:
    st='none' if not r['models'] else ('ok' if all(m[1] for m in r['models']) else 'BROKEN')
    bylib[(r['fpid'],st,tuple(m[0] for m in r['models']))].append(r['ref'])
for k,v in sorted(bylib.items()): print(k[1],k[0],'|',' '.join(k[2]) or '-','|',len(v),' '.join(v[:12]))
