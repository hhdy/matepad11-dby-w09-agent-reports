#!/usr/bin/env python3
# quick disasm probe
import sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
d = open('/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin','rb').read()
start = int(sys.argv[1], 16); n = int(sys.argv[2])
md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
off = start
cnt = 0
while cnt < n and off + 4 <= len(d):
    got = False
    for i in md.disasm(d[off:off+4], off):
        print('0x%06x %-10s %s' % (i.address, i.mnemonic, i.op_str))
        got = True
    if not got:
        print('0x%06x .word 0x%08x' % (off, int.from_bytes(d[off:off+4],'little')))
    off += 4
    cnt += 1
