#!/usr/bin/env python3
"""Apply a CPLD pin re-assignment to an existing KiCad sheet (no regeneration with build.py).

Each CPLD I/O pin has a short wire stub that ends in exactly one label. A re-assignment moves the
label *identity* (kind, name, hierarchical shape) from the net's old pin stub to its new pin stub;
the stub geometry, label position and uuid stay. Orientation/justification follow the side of the
symbol the stub is on. A bus entry on a stub is kept only if the new label belongs to the same bus
(same name prefix as the label that was there before); otherwise it is removed.

usage: cpld_pinswap_sch.py <sheet.kicad_sch> <ref> <assign.json>
assign.json: {"<net label text>": <new pin number>, ...}  (only pins that take part in the swap)
"""
import re, sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse

def rr(v): return round(float(v), 2)

def pin_ends(tree, ref):
    libs = [e for e in tree if isinstance(e, list) and e and e[0] == 'lib_symbols'][0]
    sym = [e for e in libs[1:] if e[1] == 'm68030-sbc:ATF1508AS-PLCC84'][0]
    pins = {}
    def walk(e):
        if isinstance(e, list):
            if e and e[0] == 'pin':
                at = [x for x in e if isinstance(x, list) and x[0] == 'at'][0]
                num = [x for x in e if isinstance(x, list) and x[0] == 'number'][0][1]
                pins[num] = (float(at[1]), float(at[2]))
            for x in e: walk(x)
    walk(sym)
    for e in tree:
        if isinstance(e, list) and e and e[0] == 'symbol':
            props = {x[1]: x[2] for x in e if isinstance(x, list) and x[0] == 'property'}
            if props.get('Reference') == ref:
                at = [x for x in e if isinstance(x, list) and x[0] == 'at'][0]
                assert float(at[3]) == 0 and not [x for x in e if isinstance(x, list) and x[0] == 'mirror']
                X, Y = float(at[1]), float(at[2])
                return {n: (rr(X + x), rr(Y - y)) for n, (x, y) in pins.items()}
    raise SystemExit('symbol %s not found' % ref)

def main(path, ref, assign):
    text = open(path).read(); tree = parse(text)
    ends = pin_ends(tree, ref)
    wires = []
    for e in tree:
        if isinstance(e, list) and e and e[0] == 'wire':
            pts = [x for x in e if isinstance(x, list) and x[0] == 'pts'][0]
            wires.append(tuple((rr(p[1]), rr(p[2])) for p in pts[1:3]))
    # label blocks (top level) with their positions
    lab_re = re.compile(r'\n\t\((label|hierarchical_label) "((?:[^"\\]|\\.)*)"\n(.*?)\n\t\)', re.S)
    labels = {}
    for m in lab_re.finditer(text):
        at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)\)', m.group(3))
        shape = re.search(r'\(shape (\w+)\)', m.group(3))
        uuid = re.search(r'\(uuid "([^"]+)"\)', m.group(3)).group(1)
        labels[(rr(at.group(1)), rr(at.group(2)))] = dict(kind=m.group(1), name=m.group(2), shape=shape.group(1) if shape else None,
                                                          uuid=uuid, span=m.span())
    ent_re = re.compile(r'\n\t\(bus_entry\n\t\t\(at ([\d.\-]+) ([\d.\-]+)\)\n.*?\n\t\)', re.S)
    entries = {(rr(m.group(1)), rr(m.group(2))): m.span() for m in ent_re.finditer(text)}
    # stub end (label position) for each pin
    stub = {}
    for n, p in ends.items():
        for a, b in wires:
            if a == p and b in labels: stub[n] = b
            elif b == p and a in labels: stub[n] = a
    old_pin = {}
    for n, pos in stub.items(): old_pin[labels[pos]['name']] = n
    def prefix(name): return re.sub(r'\d+(_n)?$', '', name)
    edits = []  # (span, newtext)
    for name, newpin in assign.items():
        newpin = str(newpin); src = labels[stub[old_pin[name]]]; pos = stub[newpin]; dst = labels[pos]
        if dst['name'] == name: continue
        left = pos[0] < ends[newpin][0]          # stub to the left of the symbol body
        if src['kind'] == 'label':
            ang, just = (0, 'left bottom') if left else (180, 'right bottom')
            head = f'\t(label "{name}"\n'
        else:
            ang, just = (180, 'right') if left else (0, 'left')
            head = f'\t(hierarchical_label "{name}"\n\t\t(shape {src["shape"]})\n'
        blk = (f'\n{head}\t\t(at {pos[0]:g} {pos[1]:g} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
               f'\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{dst["uuid"]}")\n\t)')
        edits.append((dst['span'], blk))
        if pos in entries:
            if not (src['kind'] == 'label' and pos in entries and prefix(name) == prefix(dst['name'])
                    and stub[old_pin[name]] in entries):
                edits.append((entries[pos], ''))
    removed = sum(1 for _, t in edits if t == '')
    for (a, b), t in sorted(edits, key=lambda e: e[0][0], reverse=True):
        text = text[:a] + t + text[b:]
    extra = 0
    if removed:
        # The stub order no longer follows the bus, so drop the rest of the bus fan-out at the CPLD as well:
        # every bus entry on a CPLD stub, and every bus segment that does not end on a hierarchical label.
        # Bus members still connect by label name (verified with a netlist diff).
        stubpos = set(stub.values())
        cut = [m.span() for m in ent_re.finditer(text) if (rr(m.group(1)), rr(m.group(2))) in stubpos]
        hl = {(rr(a), rr(b)) for a, b in re.findall(r'\(hierarchical_label "[^"]*"\n(?:\t\t\(shape \w+\)\n)?\t\t\(at ([\d.\-]+) ([\d.\-]+)', text)}
        for m in re.finditer(r'\n\t\(bus\n\t\t\(pts\n\t\t\t\(xy ([\d.\-]+) ([\d.\-]+)\)\n\t\t\t\(xy ([\d.\-]+) ([\d.\-]+)\)\n.*?\n\t\)', text, re.S):
            a = (rr(m.group(1)), rr(m.group(2))); b = (rr(m.group(3)), rr(m.group(4)))
            if a not in hl and b not in hl: cut.append(m.span())
        for a, b in sorted(cut, reverse=True): text = text[:a] + text[b:]
        extra = len(cut)
    open(path, 'w').write(text)
    print(f'{path}: {len(edits) - removed} labels rewritten, {removed} bus entries removed, {extra} more bus items removed')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], json.load(open(sys.argv[3])))
