import sys, subprocess, tempfile, os
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS=None
pcb,out,x0,y0,x1,y1=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:7])
title=sys.argv[7] if len(sys.argv)>7 else ''
T=tempfile.mkdtemp()
subprocess.run(['kicad-cli','pcb','export','svg','--mode-single','--exclude-drawing-sheet','--page-size-mode','2','-l','F.Cu,B.Cu,F.SilkS,Edge.Cuts','-o',T+'/z.svg',pcb],check=True,capture_output=True)
subprocess.run(['rsvg-convert','-w','8800','-b','white',T+'/z.svg','-o',T+'/z.png'],check=True)
im=Image.open(T+'/z.png'); W,H=im.size; s=W/220.1
c=im.crop((int((x0+0.05)*s),int((y0+0.05)*s),int((x1+0.05)*s),int((y1+0.05)*s)))
c.thumbnail((2400,2400))
if title:
    d=ImageDraw.Draw(c); d.rectangle([0,0,620,40],fill='white'); d.text((8,10),title,fill='black')
c.save(out); print(out,c.size)
