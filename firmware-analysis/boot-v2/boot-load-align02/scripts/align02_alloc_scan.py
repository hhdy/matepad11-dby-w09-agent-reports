#!/usr/bin/env python3
# ALIGN02 Stage B: enumerate gBS->AllocatePages (+0x28) / AllocatePool (+0x40) sites in .text with function context
import sys
sys.path.insert(0, '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/K1_ABL_AUTH_CLOSE01_REPORT/scripts')
import dataflow_xref
from dataflow_xref import parse_insns

PE = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin'
data = open(PE, 'rb').read()
dataflow_xref.data = data
print('PE bytes @0xCF145..0xCF165: %r' % data[0xCF145:0xCF165])

insns = parse_insns(0x1000, 0x109000)
sites = {'alloc_pages': [], 'alloc_pool': []}
for idx, (a, m, o, ok) in enumerate(insns):
    if ok and m == 'ldr' and o.endswith('[x8, #0x28]'):
        sites['alloc_pages'].append(a)
    if ok and m == 'ldr' and o.endswith('[x8, #0x40]'):
        sites['alloc_pool'].append(a)
print('\ngBS->AllocatePages (+0x28) sites: %d' % len(sites['alloc_pages']))
for a in sites['alloc_pages']:
    print('  0x%06X' % a)
print('gBS->AllocatePool (+0x40) sites: %d' % len(sites['alloc_pool']))
for a in sites['alloc_pool']:
    print('  0x%06X' % a)
