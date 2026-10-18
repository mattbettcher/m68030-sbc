# CPLD pin swap 2026-10-17 (see cpld/*/README.md 'Rev A.2 pin swap'). Work files went to /tmp/cpldwork/pins.
import os, sys, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew, cpld_pinswap_opt as O
KD = '/workspace/68030-design/kicad'
b = pcbnew.LoadBoard(f'{KD}/m68030-sbc.kicad_pcb')
mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
FIX = set(sys.argv[2].split(',')) if len(sys.argv) > 2 and sys.argv[2] else set()
orig = {}
def apply(ref, assign):
    fp = b.FindFootprintByReference(ref); pads = {p.GetNumber(): p for p in fp.Pads()}
    nets = NETOBJ[ref]
    for net, pin in assign.items(): pads[pin].SetNet(nets[net])
res = {}
U4OUT = {'/dram/U4_MA%d' % i for i in range(12)} | {'/dram/U4_RAS%d_n' % i for i in range(4)} | {'/dram/U4_CAS%d_n' % i for i in range(4)} | {'/dram/U4_WE_n', '/dram/MUX_SEL', '/DSACK0_n', '/DSACK1_n'}
NETOBJ = {}
for ref in ('U3', 'U4'):
    S = O.setup(b, ref, KD); orig[ref] = {n: p for n, p in zip(S['sigs'], S['pins'])}
    pads = {p.GetNumber(): p for p in b.FindFootprintByReference(ref).Pads()}
    NETOBJ[ref] = {n: pads[p].GetNet() for n, p in orig[ref].items()}
    d, x = O.evaluate(S, orig[ref]); res[ref] = dict(before=(round(d), x))
for rnd in range(2):
    for ref in ('U3', 'U4'):
        S = O.setup(b, ref, KD); S['cur'] = orig[ref]; S['orig'] = orig[ref]
        # re-derive current assignment from the board (after earlier rounds)
        lock = True if mode == 'lab' else (U4OUT if (mode.startswith('u4outlock') and ref == 'U4') else False)
        a = O.optimise(S, lab_lock=lock, seed=rnd, fixed=(FIX if ref == 'U4' else ()))
        apply(ref, a); res[ref]['assign'] = a
for ref in ('U3', 'U4'):
    S = O.setup(b, ref, KD); a = res[ref]['assign']
    d, x = O.evaluate(S, {n: p for n, p in zip(S['sigs'], S['pins'])})
    res[ref]['after'] = (round(d), x)
    res[ref]['orig'] = orig[ref]
    print(ref, 'before', res[ref]['before'], 'after', res[ref]['after'],
          'moved', sum(1 for n in a if a[n] != orig[ref][n]), 'of', len(a))
json.dump(res, open(f'/tmp/cpldwork/pins/assign_{mode}.json', 'w'), indent=1)
