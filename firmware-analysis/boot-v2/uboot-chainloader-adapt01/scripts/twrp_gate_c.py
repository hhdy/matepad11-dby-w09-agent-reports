#!/usr/bin/env python3
# Gate C: TWRP image inspection (twrp.img extracted from zip)
import struct
d = open('/tmp/twrp_x/twrp.img', 'rb').read()
print('twrp.img size=%d magic=%r' % (len(d), d[:8]))
print('AVBf occurrences:', [hex(o) for o in [i for i in range(len(d)-4) if d[i:i+4] == b'AVBf']] or 'NONE')
o = d.find(b'AVBf')
if o >= 0:
    ver_maj, ver_min = struct.unpack('>II', d[o+4:o+12])
    orig, voff, vsize = struct.unpack('>QQQ', d[o+12:o+36])
    print('  footer ver=%d.%d original_size=%d vbmeta_offset=0x%X vbmeta_size=%d' % (ver_maj, ver_min, orig, voff, vsize))
    print('  vbmeta magic at offset:', d[voff:voff+4])
    if d[voff:voff+4] == b'AVB0':
        flags = struct.unpack('>I', d[voff+0x78:voff+0x7C])[0]
        rb = struct.unpack('>Q', d[voff+0x70:voff+0x78])[0]
        print('  child vbmeta: flags=%d rollback=%d' % (flags, rb))
# boot header fields
ksz, kaddr, rsz, raddr, ssz, saddr, tags, page, hv = struct.unpack('<9I', d[8:44])
print('bootimg hdr: kernel_size=%d ramdisk_size=%d page=%d hv=%d' % (ksz, rsz, page, hv))
print('cmdline:', d[64:160].decode('ascii', 'replace').rstrip('\x00')[:90])
