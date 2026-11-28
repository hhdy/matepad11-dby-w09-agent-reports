#!/usr/bin/env python3
# find gBS->ExitBootServices (offset 0xE8) uses and nearby br/blr in .text
import sys
sys.path.insert(0, '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/K1_ABL_AUTH_CLOSE01_REPORT/scripts')
import dataflow_xref
from dataflow_xref import parse_insns

PE = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin'
data = open(PE, 'rb').read()
dataflow_xref.data = data

insns = parse_insns(0x1000, 0x109000)
hits = []
for idx, (a, m, o, ok) in enumerate(insns):
    if ok and m == 'ldr' and o.endswith('[x8, #0xe8]'):
        # show context: prev 8 and next 12
        ctx = insns[max(0, idx-8):idx+13]
        hits.append((a, ctx))
print('gBS->ExitBootServices (ldr x8,[x8,#0xe8]) sites: %d' % len(hits))
for (a, ctx) in hits:
    print('\n---- site 0x%06X ----' % a)
    for (ca, cm, co, cok) in ctx:
        mark = '>>' if ca == a else '  '
        print('%s 0x%06x %-8s %s' % (mark, ca, cm, co))
