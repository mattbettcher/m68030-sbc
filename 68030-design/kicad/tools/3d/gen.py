# Simple parametric 3D models for m68030-sbc footprints without stock KiCad models.
# Coordinates: footprint-local, X right, model Y = -footprint Y, Z up from board top (z=0).
import cadquery as cq, json, os
import os
HERE=os.path.dirname(os.path.abspath(__file__)); KICAD=os.path.normpath(os.path.join(HERE,'..','..'))
OUT=os.path.join(KICAD,'3dmodels','m68030-sbc.3dshapes')
PADS=json.load(open(os.path.join(HERE,'pads.json')))  # footprint-local pad coords, from dump_pads.py
BLACK=cq.Color(0.10,0.10,0.10); DARK=cq.Color(0.16,0.16,0.17); GOLD=cq.Color(0.86,0.68,0.20)
CER=cq.Color(0.80,0.78,0.72); PCBG=cq.Color(0.05,0.35,0.15); WHITE=cq.Color(0.92,0.92,0.88); SILV=cq.Color(0.75,0.75,0.78)
def box(cx,cy,z0,sx,sy,sz,fillet=0):
    w=cq.Workplane('XY').box(sx,sy,sz).translate((cx,-cy,z0+sz/2))
    if fillet: w=w.edges('|Z').fillet(fillet)
    return w
def pins(pads, size=0.5, z0=-3.0, z1=0.0, round_=True, sel=lambda p:True):
    w=None
    for x,y,d,npth,num in pads:
        if npth or not sel((x,y,d,npth,num)): continue
        s=(cq.Workplane('XY').circle(size/2).extrude(z1-z0) if round_ else cq.Workplane('XY').rect(size,size).extrude(z1-z0)).translate((x,-y,z0))
        w=s if w is None else w.union(s,clean=False)
    return w
def save(assy,name):
    p=os.path.join(OUT,name+'.step'); assy.export(p,'STEP'); print('wrote',p,os.path.getsize(p))
def padc(pads):
    xs=[p[0] for p in pads if not p[3]]; ys=[p[1] for p in pads if not p[3]]; return ((min(xs)+max(xs))/2,(min(ys)+max(ys))/2)

# ---------- PGA-128 socket + MC68030 ceramic PGA ----------
P=PADS['U1']; cx,cy=padc(P)
s=box(cx,cy,0,35.4,35.4,3.0,0.5).cut(box(cx,cy,-0.1,12,12,3.2))      # low-profile socket body with centre window
a=cq.Assembly(); a.add(s,name='socket',color=BLACK); a.add(pins(P,0.9,-3.0,0.0),name='tails',color=GOLD)
save(a,'PGA-128_13x13_Socket_LowProfile')
a=cq.Assembly()
a.add(box(cx,cy,3.1,34.54,34.54,2.2,0.4),name='body',color=CER)
a.add(box(cx,cy,5.3,22.0,22.0,0.35,1.0),name='lid',color=GOLD)
a.add(box(cx-15.0,cy-15.0,5.3,1.2,1.2,0.05),name='pin1',color=GOLD)   # pin-1 (A1) corner mark
a.add(pins(P,0.46,0.0,3.1),name='pins',color=GOLD)
save(a,'PGA-128_13x13_MC68030')

# ---------- PLCC THT sockets + PLCC chips ----------
CHIP={32:(11.43,13.97),44:(16.59,16.59),68:(24.21,24.21),84:(29.31,29.31)}
for ref,n in (('U5',32),('U6',44),('U2',68),('U3',84)):
    P=PADS[ref]; cx,cy=padc(P)
    xs=[p[0] for p in P]; ys=[p[1] for p in P]
    ow=max(xs)-min(xs)+5.6; oh=max(ys)-min(ys)+5.6         # = footprint F.Fab outline size (pads + 2.8 mm each side)
    cw,ch=CHIP[n]
    frame=box(cx,cy,0,ow,oh,4.0,0.6).cut(box(cx,cy,1.2,cw+1.4,ch+1.4,3.0)).cut(box(cx,cy,-0.1,cw-6,ch-6,1.4))
    frame=frame.cut(box(cx,cy-(ch+1.4)/2,2.6,4,3.0,1.6))   # front notch (extraction slot) on the pin-1 side
    a=cq.Assembly(); a.add(frame,name='socket',color=BLACK); a.add(pins(P,0.5,-3.0,1.2,False),name='pins',color=GOLD)
    save(a,f'PLCC-{n}_THT-Socket')
    a=cq.Assembly()
    body=box(cx,cy,1.6,cw,ch,3.0,0.3)
    a.add(body,name='body',color=DARK)
    a.add(box(cx,cy-ch/2+1.6,4.6,1.0,1.0,0.02),name='pin1dot',color=SILV)   # pin-1 dimple mark (top-centre side, PLCC convention)
    # J-lead hints along the 4 sides
    leads=None; per_x=(n//4) if n!=32 else 7; per_y=(n//4) if n!=32 else 9
    for side in range(4):
        cnt=per_x if side%2==0 else per_y
        for i in range(cnt):
            off=(i-(cnt-1)/2)*1.27
            if side==0: l=box(cx+off,cy-ch/2-0.35,1.4,0.45,0.7,2.0)
            elif side==2: l=box(cx+off,cy+ch/2+0.35,1.4,0.45,0.7,2.0)
            elif side==1: l=box(cx+cw/2+0.35,cy+off,1.4,0.7,0.45,2.0)
            else: l=box(cx-cw/2-0.35,cy+off,1.4,0.7,0.45,2.0)
            leads=l if leads is None else leads.union(l,clean=False)
    a.add(leads,name='leads',color=SILV)
    save(a,f'PLCC-{n}_Chip_InSocket')

# ---------- 72-pin SIMM vertical socket + module ----------
P=PADS['J1']; cx=47.625; cy=1.27; L=115.57; W=7.37
sock=box(cx,cy,0,L,W,9.5,0.5).cut(box(cx,cy,3.5,108.6,1.9,6.2))
for ex in (-10.16+2.5, 105.41-2.5):
    sock=sock.cut(box(ex,cy,6.0,3.0,W+1,4.0))
a=cq.Assembly(); a.add(sock,name='housing',color=WHITE)
a.add(pins(P,0.6,-3.0,3.5,False),name='contacts',color=GOLD)
for ex in (-10.16+2.5, 105.41-2.5): a.add(box(ex,cy,4.0,2.2,W+0.4,8.0),name=f'latch{int(ex)}',color=SILV)
save(a,'SIMM-72_TE-5822021-4_Socket')
a=cq.Assembly()
a.add(box(cx,cy,4.0,107.95,1.27,25.4),name='pcb',color=PCBG)
for i in range(8):
    x=cx-107.95/2+8+i*12.6
    a.add(box(x,cy-0.64-0.6,10.0,7.6,1.2,17.1),name=f'dram{i}',color=DARK)
a.add(box(cx,cy-0.64-0.02,4.0,96.0,0.04,3.2),name='fingers',color=GOLD)
save(a,'SIMM-72_Module_8chip')

# ---------- Littelfuse NANO2 451/453 and Bourns SRP1770TA ----------
a=cq.Assembly()
a.add(box(0,0,0.15,4.2,2.69,2.54),name='body',color=WHITE)
for ex in (-2.55,2.55): a.add(box(ex,0,0.0,1.0,2.69,2.69),name=f'cap{ex}',color=SILV)
save(a,'Fuse_Littelfuse-NANO2-451_453')
a=cq.Assembly()
a.add(box(0,0,0.1,16.9,16.9,6.9,1.0),name='body',color=DARK)
for ex in (-7.675,7.675): a.add(box(ex,0,0.0,2.6,11.5,0.25),name=f'term{ex}',color=SILV)
save(a,'L_Bourns_SRP1770TA_16.9x16.9mm')
