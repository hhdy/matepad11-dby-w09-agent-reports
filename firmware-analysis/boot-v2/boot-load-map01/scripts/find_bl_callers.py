#!/usr/bin/env python3
import struct, sys
d = open('/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin','rb').read()
target = int(sys.argv[1], 16)
callers = []
for off in range(0x1000, 0x109000, 4):
    w = struct.unpack('<I', d[off:off+4])[0]
    if (w >> 26) == 0x25:  # BL
        imm = w & 0x03FFFFFF
        if imm & 0x02000000: imm -= 0x04000000
        tgt = off + (imm << 2)
        if tgt == target:
            callers.append(off)
print('BL callers of 0x%X: %d' % (target, len(callers)), [hex(c) for c in callers])
