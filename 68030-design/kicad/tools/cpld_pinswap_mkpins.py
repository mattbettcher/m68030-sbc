# CPLD pin swap 2026-10-17 (see cpld/*/README.md 'Rev A.2 pin swap'). Work files went to /tmp/cpldwork/pins.
import json, re, sys, shutil, os
mode, out = sys.argv[1], sys.argv[2]
res = json.load(open(f'/tmp/cpldwork/pins/assign_{mode}.json'))
def port(net): return net.split('/')[-1].replace('U4_', '')
for ref, d, mod in (('U3', 'glue', 'glue'), ('U4', 'dram', 'dram')):
    src = f'{out}/{d}/{mod}.v'; v = open(src).read()
    newpin = {port(n): int(p) for n, p in res[ref]['assign'].items()}
    def rep(m):
        name = m.group(1)
        if name in newpin: return f'//PIN: {name:<15s}: {newpin[name]}'
        return m.group(0)
    v2 = re.sub(r'//PIN: ([A-Za-z0-9_]+)\s*: (\d+)', rep, v)
    pins = re.findall(r'//PIN: ([A-Za-z0-9_]+)\s*: (\d+)', v2)
    nums = [int(p) for _, p in pins]; assert len(nums) == len(set(nums)), 'dup pin'
    missing = set(newpin) - {n for n, _ in pins}; assert not missing, missing
    open(src, 'w').write(v2)
    print(ref, 'pins', len(pins), 'changed', sum(1 for n, p in pins if n in newpin))
