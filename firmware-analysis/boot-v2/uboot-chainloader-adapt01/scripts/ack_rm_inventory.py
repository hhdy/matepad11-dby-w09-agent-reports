#!/usr/bin/env python3
# §17.6 local-only: enumerate ACK VD DTB reserved-memory children (37 expected) + U-Boot control DTB 6 nodes
import subprocess, re

WS = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf'
ACK = WS + '/K1_BOOT_LOAD_MAP01/evidence/prep_dtb.bin'
UB = '/home/kerneldev/build/u-boot-2026.10/build/u-boot.dtb'

def cells(dts_text):
    out = []
    cur = None
    for line in dts_text.splitlines():
        m = re.match(r'\t(\S+)@\s*([0-9a-f]+) \{', line)
        if m and 'reserved-memory' not in line:
            cur = m.group(1) + '@' + m.group(2)
            continue
        if cur:
            m2 = re.search(r'reg = <([^>]+)>', line)
            if m2:
                vals = [int(x, 16) for x in re.findall(r'0x[0-9a-f]+', m2.group(1))]
                # #address-cells=2 #size-cells=2 typical
                if len(vals) >= 4:
                    base = (vals[0] << 32) | vals[1]
                    size = (vals[2] << 32) | vals[3]
                else:
                    base, size = vals[0], vals[1]
                flags = []
                if 'no-map' in dts_text[max(0, dts_text.find(line)-400):dts_text.find(line)+200]:
                    flags.append('no-map?')
                out.append((cur, hex(base), hex(size)))
                cur = None
    return out

txt = subprocess.run(['dtc', '-I', 'dtb', '-O', 'dts', ACK], capture_output=True, text=True).stdout
seg = txt[txt.find('reserved-memory {'):]
seg = seg[:seg.find('\n\t};')]
children = re.findall(r'\n\t\t([a-zA-Z0-9_]+@[0-9a-f]+) \{\n\t\t\treg = <([^>]+)>;', seg)
print('ACK VD DTB reserved-memory children: %d' % len(children))
for (name, reg) in children:
    v = [int(x, 16) for x in re.findall(r'0x[0-9a-f]+', reg)]
    base = (v[0] << 32) | v[1] if len(v) >= 4 else v[0]
    size = (v[2] << 32) | v[3] if len(v) >= 4 else v[1]
    flags = []
    block_start = seg.find(name)
    block = seg[block_start:block_start+400]
    if 'no-map' in block: flags.append('no-map')
    if 'reusable' in block: flags.append('reusable')
    print('  %-28s base=0x%012x size=0x%x %s' % (name, base, size, ','.join(flags)))
# memreserve
mr = re.findall(r'/memreserve/\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+);', txt)
print('ACK DTB /memreserve/ entries: %d %s' % (len(mr), mr[:6]))
