#!/usr/bin/env python3
# GATE01 core A: AVBf footer + child vbmeta analysis (read-only) for stock recovery / candidate / recovery_vbmeta
import struct, hashlib

R155 = '/mnt/d/workbuddy/2026-11-25-22-04-11/r155/copies-primary/'
CAND = '/home/kerneldev/build/rcand/recovery-uboot-candidate.img'
FILES = {
    'stock_recovery': R155 + 'recovery.img',
    'candidate': CAND,
    'recovery_vbmeta': R155 + 'recovery_vbmeta.img',
}

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

def find_all(data, magic):
    out = []
    o = 0
    while True:
        o = data.find(magic, o)
        if o < 0:
            break
        out.append(o)
        o += 1
    return out

for name, path in FILES.items():
    d = open(path, 'rb').read()
    print('== %s == (%d B, sha %s)' % (name, len(d), sha(path)[:16]))
    # AVBf footer search (end-64 is canonical location, but scan whole file)
    footers = find_all(d, b'AVBf')
    print('  AVBf occurrences: %s' % ([hex(x) for x in footers] if footers else 'NONE'))
    if footers:
        for o in footers:
            if o + 64 <= len(d):
                magic_, ver_major, ver_minor, orig_size, vbmeta_off, vbmeta_size, = struct.unpack('>4sIIQQQ', d[o:o+36])
                print('    @0x%X: ver=%d.%d original_size=%d vbmeta_offset=0x%X vbmeta_size=%d' %
                      (o, ver_major, ver_minor, orig_size, vbmeta_off, vbmeta_size))
                if d[vbmeta_off:vbmeta_off+4] == b'AVB0':
                    print('      child vbmeta @0x%X: magic AVB0 OK' % vbmeta_off)
    # VBMeta header search (AVB0 anywhere)
    vbmetas = find_all(d, b'AVB0')
    print('  AVB0 occurrences: %s' % ([hex(x) for x in vbmetas[:6]] if vbmetas else 'NONE'))
    for o in vbmetas[:3]:
        algo = struct.unpack('>I', d[o+28:o+32])[0]
        desc_off = struct.unpack('>Q', d[o+104:o+112])[0]
        desc_size = struct.unpack('>Q', d[o+112:o+120])[0]
        rb = struct.unpack('>Q', d[o+120:o+128])[0]
        flags = struct.unpack('>I', d[o+128:o+132])[0]
        print('    @0x%X: algo=%d rollback=%d flags=%d desc_off=0x%X desc_size=%d' %
              (o, algo, rb, flags, desc_off, desc_size))
        ds = d[o+desc_off:o+desc_off+desc_size]
        # simple descriptor walk
        i = 0
        while i + 4 <= len(ds):
            tag = struct.unpack('>Q', ds[i:i+8])[0]
            nlen = struct.unpack('>Q', ds[i+8:i+16])[0] >> 32 if False else struct.unpack('>I', ds[i+12:i+16])[0]
            if tag == 3:  # chain partition
                plen = struct.unpack('>Q', ds[i+8:i+16])[0]
                pname = ds[i+36:i+36+64].split(b'\x00')[0].decode()
                rbloc = struct.unpack('>Q', ds[i+16:i+24])[0]
                print('      descriptor@+%d: CHAIN partition=%s rb_loc=%d' % (i, pname, rbloc))
                i += (plen + 63) // 64 * 64
            elif tag == 2:  # kernel cmdline
                plen = struct.unpack('>Q', ds[i+8:i+16])[0]
                i += (plen + 63) // 64 * 64
            elif tag == 4:  # hash
                plen = struct.unpack('>Q', ds[i+8:i+16])[0]
                pname = ds[i+36:i+36+64].split(b'\x00')[0].decode()
                imgsz = struct.unpack('>Q', ds[i+40:i+48])[0]
                print('      descriptor@+%d: HASH partition=%s image_size=%d' % (i, pname, imgsz))
                i += (plen + 63) // 64 * 64
            elif tag == 1:  # hashtree
                plen = struct.unpack('>Q', ds[i+8:i+16])[0]
                pname = ds[i+36:i+36+64].split(b'\x00')[0].decode()
                print('      descriptor@+%d: HASHTREE partition=%s' % (i, pname))
                i += (plen + 63) // 64 * 64
            else:
                i += 64
    print()
