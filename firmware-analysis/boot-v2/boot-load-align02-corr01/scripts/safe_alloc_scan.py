#!/usr/bin/env python3
# ALIGN02_CORR01 Stage C v2: safe gBS-based slot scanner.
# Tracks any reg loaded from [x?,#0xFE8] (=gBS global); ABI-aware: bl/blr preserve x19-x28, clobber x0-x17.
import sys
sys.path.insert(0, '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/K1_ABL_AUTH_CLOSE01_REPORT/scripts')
import dataflow_xref
from dataflow_xref import parse_insns

PE = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin'
data = open(PE, 'rb').read()
dataflow_xref.data = data

SLOT_NAMES = {
    0x18: 'RaiseTPL', 0x28: 'AllocatePages', 0x30: 'FreePages', 0x38: 'GetMemoryMap',
    0x40: 'AllocatePool', 0x48: 'FreePool', 0xE8: 'ExitBootServices', 0xF8: 'Stall',
    0x100: 'SetWatchdogTimer', 0x140: 'LocateProtocol', 0x158: 'CalculateCrc32',
    0x160: 'CopyMem', 0x168: 'SetMem',
}
CLOBBERED = set('x%d' % i for i in range(0, 18)) | set('w%d' % i for i in range(0, 18))

insns = parse_insns(0x1000, 0x109000)
gbs = set()
results = []
gbs_loads = 0
for (a, m, o, ok) in insns:
    if not ok:
        gbs -= CLOBBERED
        continue
    if m == 'ldr' and '#0xfe8]' in o:
        rd = o.split(',')[0].strip()
        gbs.add(rd)
        gbs_loads += 1
        continue
    if m == 'ldr' and '[' in o:
        rd = o.split(',')[0].strip()
        base = o[o.find('[')+1:o.find(']')]
        parts = [p.strip() for p in base.split(', ')]
        rn = parts[0]
        off = 0
        if len(parts) > 1 and parts[1].startswith('#'):
            try:
                off = int(parts[1].replace('#', ''), 0)
            except ValueError:
                pass
        if rn in gbs and off != 0:
            results.append((a, off, SLOT_NAMES.get(off, 'slot+0x%X' % off), rn))
    if m in ('bl', 'blr'):
        gbs -= CLOBBERED
    elif m in ('b', 'ret') or m.startswith('b.'):
        gbs.clear()

alloc = [r for r in results if r[2] == 'AllocatePages']
pool = [r for r in results if r[2] == 'AllocatePool']
print('gBS pointer loads: %d' % gbs_loads)
print('gBS-based slot loads: %d' % len(results))
print('AllocatePages sites (gBS-proven): %d' % len(alloc))
for (a, off, name, rn) in alloc:
    print('  0x%06X base=%s' % (a, rn))
print('AllocatePool sites (gBS-proven): %d' % len(pool))
for (a, off, name, rn) in pool:
    print('  0x%06X base=%s' % (a, rn))
from collections import Counter
c = Counter(r[2] for r in results)
print('slot histogram:', dict(c))
bad = [r for r in results if r[0] in (0x30858, 0x55944)]
print('counterexamples 0x30858/0x55944 counted: %d (must be 0) %s' % (len(bad), bad))
