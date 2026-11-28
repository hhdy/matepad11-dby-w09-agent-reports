#!/usr/bin/env python3
# §17.4: parse final-FDT: memory/memreserve/reserved-memory/chosen + comparisons
import subprocess, re, struct

F = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/final-fdt-capture/hos43-final-fdt.dtb'
raw = open(F, 'rb').read()
hdr = raw[:28]
print('file bytes read:', len(raw))
magic, totalsize, off_struct, off_strings, off_memrsv, ver, last_comp = struct.unpack('>7I', hdr)
print('FDT header: magic=0x%08X totalsize=%d off_struct=0x%X off_strings=0x%X off_memrsv=0x%X version=%d last_comp=%d' %
      (magic, totalsize, off_struct, off_strings, off_memrsv, ver, last_comp))
# memreserve map
n_rsv = struct.unpack('>I', open(F, 'rb').read(48)[40:44])[0]
print('memreserve entries: %d' % n_rsv)
raw = open(F, 'rb').read()
for i in range(min(n_rsv, 10)):
    a, s = struct.unpack('>QQ', raw[off_memrsv + 16*i: off_memrsv + 16*i + 16])
    print('  memreserve[%d] = base=0x%x size=0x%x' % (i, a, s))

txt = subprocess.run(['dtc', '-I', 'dtb', '-O', 'dts', F], capture_output=True, text=True).stdout
open('/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/final-fdt-capture/final-fdt.dts', 'w').write(txt)

print('\n== /memory ==')
m = re.search(r'memory@[0-9a-f]+ \{[^}]*?device_type = "memory";[^}]*?reg = <([^>]+)>;', txt, re.S)
if m:
    v = [int(x, 16) for x in re.findall(r'0x[0-9a-f]+', m.group(1))]
    banks = []
    for i in range(0, len(v), 4):
        base = (v[i] << 32) | v[i+1]; size = (v[i+2] << 32) | v[i+3]
        banks.append((base, size))
    banks.sort()
    total = 0; prev_end = 0; overlap = 0; zero = 0
    for i, (b, s) in enumerate(banks):
        e = b + s
        if s == 0: zero += 1
        if b < prev_end: overlap += 1
        print('  bank[%d] base=0x%012x size=0x%012x end=0x%012x (%.2f GiB)' % (i, b, s, e, s/2**30))
        total += s; prev_end = e
    print('  TOTAL RAM = %.3f GiB  zero_banks=%d overlaps=%d sorted=%s' % (total/2**30, zero, overlap, banks == sorted(banks)))
else:
    print('  /memory ABSENT')

print('\n== /reserved-memory children ==')
seg = txt[txt.find('reserved-memory {'):]
seg = seg[:seg.find('\n\t};')]
kids = re.findall(r'\n\t\t([a-zA-Z0-9_]+@[0-9a-f]+|\S+) \{\n((?:\t\t\t[^\n]+\n)+)\t\t\};', seg)
print('children with body: %d' % len(kids))
for (name, body) in kids:
    reg = re.search(r'reg = <([^>]+)>', body)
    if reg:
        v = [int(x, 16) for x in re.findall(r'0x[0-9a-f]+', reg.group(1))]
        base = (v[0] << 32) | v[1] if len(v) >= 4 else v[0]
        size = (v[2] << 32) | v[3] if len(v) >= 4 else v[1]
    else:
        base = size = None
    fl = []
    if 'no-map' in body: fl.append('no-map')
    if 'reusable' in body: fl.append('reusable')
    cm = re.search(r'compatible = "([^"]+)"', body)
    if cm: fl.append('compat=' + cm.group(1))
    print('  %-30s base=%s size=%s %s' % (name, hex(base) if base is not None else '-', hex(size) if size is not None else '-', ' '.join(fl)))

print('\n== /chosen initrd ==')
c = re.search(r'chosen \{([^}]*)\}', txt, re.S)
if c:
    body = c.group(1)
    for prop in ('linux,initrd-start', 'linux,initrd-end'):
        pm = re.search(re.escape(prop) + r' = <([^>]+)>', body)
        if pm:
            v = [int(x, 16) for x in re.findall(r'0x[0-9a-f]+', pm.group(1))]
            val = (v[0] << 32) | v[1] if len(v) >= 2 else v[0]
            print('  %s = 0x%012x' % (prop, val))
    bm = re.search(r'bootargs = "([^"]*)"', body)
    if bm:
        ba = bm.group(1)
        print('  bootargs len=%d (first 80 chars, sanitized): %s' % (len(ba), ba[:80].replace('\n', ' ')))
