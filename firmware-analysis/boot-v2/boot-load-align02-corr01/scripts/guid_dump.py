import struct
d = open('/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin', 'rb').read()
for off in (0x107F70, 0x107FA0):
    g = d[off:off+16]
    print('0x%X bytes: %s' % (off, g.hex()))
    print('  mixed-endian GUID: {%08X-%04X-%04X-%s-%s}' % (
        struct.unpack('<I', g[0:4])[0], struct.unpack('<H', g[4:6])[0],
        struct.unpack('<H', g[6:8])[0], g[8:10].hex(), g[10:16].hex()))
    # find all occurrences of this GUID in the image (implementation registration)
    occ = []
    o = 0
    while True:
        o = d.find(g, o)
        if o < 0:
            break
        occ.append(hex(o))
        o += 1
    print('  occurrences:', occ)
