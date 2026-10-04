import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from project import *

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
C1210 = "Capacitor_SMD:C_1210_3225Metric"
LED0805 = "LED_SMD:LED_0805_2012Metric"
TP = "TestPoint:TestPoint_Pad_D1.5mm"
HDR2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
HDR3 = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
SW6 = "Button_Switch_THT:SW_PUSH_6mm_H5mm"
OSC14 = "Oscillator:Oscillator_DIP-14"

def R(sh, ref, val, x, y, rot=0, fp=R0603, **kw):
    return sh.sym("Device:R", ref, val, x, y, rot, fp=fp, **kw)
def C(sh, ref, val, x, y, rot=0, fp=C0603, **kw):
    return sh.sym("Device:C", ref, val, x, y, rot, fp=fp, **kw)
def CP(sh, ref, val, x, y, rot=0, fp="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", **kw):
    return sh.sym("Device:C_Polarized", ref, val, x, y, rot, fp=fp, **kw)

def hv(sh, p1, p2):
    """L route: horizontal from p1 then vertical to p2"""
    return sh.wire(p1, (p2[0], p1[1]), p2)
def vh(sh, p1, p2):
    return sh.wire(p1, (p1[0], p2[1]), p2)

def cap_row(sh, specs, x0, y, pitch, top="+5V", bot="GND", rail_extra_left=0, power_at="left"):
    """vertical caps in a row; top pins joined by a rail to `top` power symbol, each bottom pin gets a GND symbol.
    specs: list of (ref, value, fp, kind) kind in 'C','CP'. returns list of parts and rail y"""
    parts = []
    for i, sp in enumerate(specs):
        ref, val, fp = sp[0], sp[1], sp[2]
        kind = sp[3] if len(sp) > 3 else "C"
        x = x0 + i * pitch
        kw = sp[4] if len(sp) > 4 else {}
        p = (CP if kind == "CP" else C)(sh, ref, val, x, y, 0, fp=fp, **kw)
        parts.append(p)
    tops = [p.pin(1) for p in parts]
    ry = tops[0][1] - 2.54
    for t in tops:
        sh.wire(t, (t[0], ry))
    xl = tops[0][0] - rail_extra_left
    sh.wire((xl, ry), (tops[-1][0], ry))
    if top:
        px = xl if power_at == "left" else tops[-1][0]
        sh.power(top, px, ry, 0)
    for p in parts:
        b = p.pin(2)
        sh.power(bot, b[0], b[1], 0)
    return parts, ry

def pullup_bank(sh, specs, x, y0, pitch=5.08, rail="+5V", label_len=7.62, hier=None):
    """horizontal resistors stacked vertically; left pins on a vertical rail to `rail`, right pins -> labels.
    specs: list of (ref, value, net). returns parts"""
    parts = []
    for i, (ref, val, net) in enumerate(specs):
        yy = y0 + i * pitch
        p = R(sh, ref, val, x, yy, 90, ref_at=(x - 0.635, yy - 1.905), val_at=(x + 0.635, yy - 1.905), just="right")
        p.s["val_just"] = "left"
        parts.append(p)
        a = p.pin(2); b = p.pin(1)
        # pin1 is left for rot 90
        left, right = (b, a) if b[0] < a[0] else (a, b)
        sh.wire(left, (left[0] - 2.54, left[1]))
        sh.wire(right, (right[0] + label_len, right[1]))
        if hier:
            sh.hlabel(net, hier, right[0] + label_len, right[1], 0)
        else:
            sh.label(net, right[0] + label_len, right[1], 0)
    lx = parts[0].pin(1)[0] - 2.54
    ytop = y0 - 2.54 * 2
    sh.wire((lx, ytop), (lx, y0 + (len(specs) - 1) * pitch))
    sh.power(rail, lx, ytop, 0)
    return parts
