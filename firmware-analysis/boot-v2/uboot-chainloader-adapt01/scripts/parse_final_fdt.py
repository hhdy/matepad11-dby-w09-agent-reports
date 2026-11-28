#!/usr/bin/env python3
# §19 CORR: final-FDT banks via fdtget + full decode; sorted/gaps/overlap/total
import subprocess, re

F = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/final-fdt-capture/hos43-final-fdt.dtb'

def fdtget(path, prop=None, typ=None):
    cmd = ['fdtget', '-t', 'x' if typ == 'x' else None, F, path] + ([prop] if prop else [])
    cmd = [c for c in cmd if c]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

rc, ac, _ = fdtget('/', '#address-cells', 'x')
rc2, sc, _ = fdtget('/', '#size-cells', 'x')
rc3, reg, _ = fdtget('/memory', 'reg', 'x')
print('#address-cells=%s #size-cells=%s (fdtget rc=%d/%d)' % (ac, sc, rc, rc2))
print('/memory/reg raw cells: %s' % reg)
cells = [int(c, 16) for c in reg.split()]
ac_n, sc_n = int(ac, 0), int(sc, 0)
assert len(cells) % (ac_n + sc_n) == 0, 'cell count mismatch'
banks = []
for i in range(0, len(cells), ac_n + sc_n):
    a = cells[i:i+ac_n]; s = cells[i+ac_n:i+ac_n+sc_n]
    base = 0
    for c in a: base = (base << 32) | c
    size = 0
    for c in s: size = (size << 32) | c
    banks.append((base, size))
print('decoded banks: %d' % len(banks))
for (b, s) in banks:
    print('  base=0x%012x size=0x%012x end=0x%012x (%.3f GiB)' % (b, s, b + s, s / 2**30))
total = sum(s for (_, s) in banks)
print('TOTAL = %d bytes = %.3f GiB = %.2f GB' % (total, total / 2**30, total / 10**9))
sb = sorted(banks)
print('sorted: %s' % ('YES' if sb == banks else 'NO (reg order unsorted)'))
overlaps = []
gaps = []
prev_end = None
for (b, s) in sb:
    if prev_end is not None:
        if b < prev_end:
            overlaps.append((hex(prev_end), hex(b)))
        elif b > prev_end:
            gaps.append((hex(prev_end), hex(b), hex(b - prev_end)))
    prev_end = b + s
print('overlaps: %s' % (overlaps if overlaps else 'none'))
print('gaps: %s' % (gaps if gaps else 'none'))
zero = [b for (b, s) in banks if s == 0]
print('zero-size banks: %d' % len(zero))
print('overflow check (base+size > 2^64): none' if all(b + s < 2**64 for (b, s) in banks) else 'OVERFLOW')
# top-level /memory presence via decompile (no-@ node)
txt = subprocess.run(['dtc', '-I', 'dtb', '-O', 'dts', F], capture_output=True, text=True).stdout
m = re.search(r'^\tmemory \{', txt, re.M)
print('top-level node named `memory` (no @): %s' % ('PRESENT' if m else 'ABSENT'))
print('node has device_type=memory: %s' % ('YES' if 'device_type = "memory"' in txt else 'NO'))
