#!/usr/bin/env python3
import struct, sys
d = open('/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin','rb').read()
for arg in sys.argv[1:]:
    t = int(arg, 16)
    n = struct.pack('<Q', t)
    o = 0
    found = []
    while True:
        o = d.find(n, o)
        if o < 0: break
        found.append(hex(o))
        o += 1
    print('ptr 0x%X: %d refs %s' % (t, len(found), found))
