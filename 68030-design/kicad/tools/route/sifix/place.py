import pcbnew, re, sys, math
P=2.54/6; X0=94.76; Y0=63.76
SRC='/tmp/sifix/_strip.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
POWER=('GND','+5V','+3V3')
tracks=list(b.GetTracks()); uid=lambda t:t.m_Uuid.AsString()
def attached(f):
    att={}
    for t in tracks:
        if t.GetClass()=='PCB_TRACK':
            for p in f.Pads():
                if t.GetNetCode()==p.GetNetCode() and (p.HitTest(t.GetStart()) or p.HitTest(t.GetEnd())): att[uid(t)]=t
    for t in list(att.values()):
        for v in tracks:
            if v.GetClass()=='PCB_VIA' and v.GetNetCode()==t.GetNetCode() and (v.GetPosition()==t.GetStart() or v.GetPosition()==t.GetEnd()): att[uid(v)]=v
    return list(att.values())
def V(x,y): return pcbnew.VECTOR2I(int(round(x*1e6)),int(round(y*1e6)))
def place(ref,x,y,rot=None,layer=None,pad1toward=None):
    f=b.FindFootprintByReference(ref); att=attached(f)
    if layer=='B' and f.GetLayer()!=pcbnew.B_Cu: assert not att; f.Flip(f.GetPosition(),False)
    if layer=='F' and f.GetLayer()!=pcbnew.F_Cu: assert not att; f.Flip(f.GetPosition(),False)
    c=f.GetPosition()
    if rot is not None:
        d=rot-f.GetOrientationDegrees()
        if abs(d)>1e-6:
            f.Rotate(c, pcbnew.EDA_ANGLE(d, pcbnew.DEGREES_T))
            for t in att: t.Rotate(c, pcbnew.EDA_ANGLE(d, pcbnew.DEGREES_T))
    dv=V(x,y)-f.GetPosition(); f.Move(dv)
    for t in att: t.Move(dv)
    if pad1toward is not None:
        p1=[p for p in f.Pads() if p.GetNumber()=='1'][0]; p2=[p for p in f.Pads() if p.GetNumber()=='2'][0]
        tx,ty=pad1toward
        d1=(p1.GetPosition()-V(tx,ty)).EuclideanNorm(); d2=(p2.GetPosition()-V(tx,ty)).EuclideanNorm()
        if d1>d2:
            assert not att
            f.Rotate(f.GetPosition(), pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T))
    return f
def padpos(ref,num):
    f=b.FindFootprintByReference(ref); p=[p for p in f.Pads() if p.GetNumber()==num][0]; return p.GetPosition().x/1e6,p.GetPosition().y/1e6
def u4pin(net):
    f=b.FindFootprintByReference('U4'); p=[p for p in f.Pads() if p.GetNetname()==net][0]; return p.GetPosition().x/1e6,p.GetPosition().y/1e6
# 2. DRAM series R
left=[('R810','MA6',20.2),('R809','MA5',22.7),('R805','MA1',29.45),('R807','MA3',31.15),('R804','MA0',32.85),('R808','MA4',34.55),('R806','MA2',36.25),('R812','MA8',37.95),('R813','MA9',40.5)]
for r,nm,y in left: place(r,91.2,y,0,'B',pad1toward=u4pin('/dram/U4_'+nm))
top=[('R811','MA7',97.3),('R815','MA11',99.8),('R814','MA10',101.4),('R819','RAS3_n',103.0),('R817','RAS1_n',104.6),('R818','RAS2_n',106.2),('R820','CAS0_n',107.8),
     ('R823','CAS3_n',117.6),('R821','CAS1_n',120.2),('R824','WE_n',122.7),('R816','RAS0_n',124.3)]
for r,nm,x in top: place(r,x,13.9,90,'B',pad1toward=u4pin('/dram/U4_'+nm))
place('R822',128.8,25.2,0,'B',pad1toward=u4pin('/dram/U4_CAS2_n'))
# 3. TPs for RAS0/CAS3/WE next to the SIMM-side path
for r,x,y in [('TP806',130.0,14.4),('TP807',132.6,14.4),('TP801',135.2,14.4),('TP803',137.8,14.65)]: place(r,x,y)
# 4. clock block
ux,uy=62.0,38.0
f=b.FindFootprintByReference('U10'); place('U10',ux,uy,0)
p1=padpos('U10','1'); dx=round((p1[0]-X0)/P)*P+X0-p1[0]; dy=round((p1[1]-Y0)/P)*P+Y0-p1[1]; ux+=dx; uy+=dy; place('U10',ux,uy,0)
for r,pin in [('R304','18'),('R302','16'),('R301','14'),('R303','12')]:
    x,y=padpos('U10',pin); place(r,x+3.3,y,0,pad1toward=(x,y))
for r,pin in [('R305','3'),('R306','5')]:
    x,y=padpos('U10',pin); place(r,x-3.3,y,0,pad1toward=(x,y))
place('C301',ux+4.65,uy-8.2,90)
place('C302',ux-0.5,uy-8.0,0)
place('X1',ux-0.9,uy+11.1,0)
place('C305',ux-0.9,uy+16.0,0)
place('C306',ux-5.5,uy+16.6,0)
place('C304',168.11,93.71,0)
x,y=padpos('X2','8'); place('R307',x,y-2.6,90,pad1toward=(x,y))
x,y=padpos('X3','8'); place('R308',x,y-2.6,90,pad1toward=(x,y))
import legal
def u4d(ref,net):
    f=b.FindFootprintByReference(ref); ux,uy=u4pin(net)
    def pref(x,y):
        c=f.GetPosition(); p1=[p for p in f.Pads() if p.GetNumber()=='1'][0]
        ox=p1.GetPosition().x/1e6-c.x/1e6; oy=p1.GetPosition().y/1e6-c.y/1e6
        return math.hypot(x+ox-ux,y+oy-uy)
    return pref
fixlist=[(r,'/dram/U4_'+nm) for r,nm,_ in left]+[(r,'/dram/U4_'+nm) for r,nm,_ in top]+[('R822','/dram/U4_CAS2_n')]
for r,net in fixlist:
    f=b.FindFootprintByReference(r); x0,y0=f.GetPosition().x/1e6,f.GetPosition().y/1e6
    res=legal.find(b,f,x0,y0,rmax=5.0,step=0.2,prefer=u4d(r,net),margin=0.45)
    print('R',r,res, 'd=%.1f'%u4d(r,net)(*res) if res else 'NONE')
for r in ['R301','R302','R303','R304','R305','R306','R307','R308','C301','C302','X1','C305','C306','TP806','TP807','TP801','TP803','C304']:
    f=b.FindFootprintByReference(r); x0,y0=f.GetPosition().x/1e6,f.GetPosition().y/1e6
    att=attached(f); before=f.GetPosition()
    res=legal.find(b,f,x0,y0,rmax=4.0,step=0.2)
    dv=f.GetPosition()-before
    for t in att: t.Move(dv)
    print(r,(round(x0,2),round(y0,2)),'->',res)
b.Save(sys.argv[1]); print('saved')
