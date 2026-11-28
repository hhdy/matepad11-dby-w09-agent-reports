#!/usr/bin/env python3
# find movz wN, #0x8000 / movz wM, #0x80000(lsl16) pairs across .text (kernel load offset selector)
import struct
d = open('/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin','rb').read()

def decode_movz(w):
    if (w >> 23) != 0xA5:  # sf=0 opc=10 100101 -> 0b10100101 in bits 31..23
        return None
    hw = (w >> 21) & 3
    imm = (w >> 5) & 0xFFFF
    rd = w & 0x1F
    return (rd, imm << (16 * hw))

hits = []
for off in range(0x1000, 0x109000 - 16, 4):
    words = [struct.unpack('<I', d[off+i:off+i+4])[0] for i in (0, 4, 8)]
    vals = [decode_movz(w) for w in words]
    for i in range(3):
        if vals[i] and vals[i][1] == 0x8000:
            for j in range(3):
                if j != i and vals[j] and vals[j][1] == 0x80000:
                    hits.append((off, [hex(x) for x in (0,0)]) if False else (off, i, j))
print('movz #0x8000 / #0x80000 pairs: %d' % len(hits))
for (off, i, j) in hits:
    print('  0x%06X (word%d=0x8000, word%d=0x80000)' % (off, i, j))
