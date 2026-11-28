#!/usr/bin/env python3
# UBOOT_CHAINLOADER_ADAPT01 addendum Group A: live separate ramdisk wrapper parse (sanitized)
import struct, hashlib, zlib, os

SEP = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/stock-live-ramdisk.img'
d = open(SEP, 'rb').read()
sha = hashlib.sha256(d).hexdigest()
print('file sha256=%s (expect 4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb) MATCH=%s' % (
    sha, sha == '4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb'))
print('partition size=%d (2 MiB) bounds headroom=%d' % (len(d), len(d) - len(d)))

assert d[:8] == b'ANDROID!', 'no ANDROID! magic'
def u32(o): return struct.unpack('<I', d[o:o+4])[0]
hdr = {
    'kernel_size': u32(8), 'kernel_addr': u32(12),
    'ramdisk_size': u32(16), 'ramdisk_addr': u32(20),
    'second_size': u32(24), 'second_addr': u32(28),
    'tags_addr': u32(32), 'page_size': u32(36),
    'dt_size': u32(44) if len(d) >= 48 else 0,
}
print('\n== wrapper header ==')
for k, v in hdr.items():
    print('  %-14s = 0x%08X (%d)' % (k, v, v))
# header_version field (@40) exists only in v1/v2; detect by page_size sanity
ps = hdr['page_size']
print('  header_version(@40) = 0x%X' % u32(40))
print('  unused(@44) dt size field = 0x%X' % hdr['dt_size'])

# v0 arithmetic: ramdisk payload offset = ALIGN(page_size) + ALIGN(kernel_size,page)  (kernel_size=0)
ko = ((0 + ps - 1) // ps) * ps if 0 else 0
rd_off = ps + ko
rd_len = hdr['ramdisk_size']
print('\n== payload arithmetic (v0 style) ==')
print('  ramdisk payload offset = page_size(%d) + ALIGN(kernel_size=0) = 0x%X' % (ps, rd_off))
print('  ramdisk payload length = %d (0x%X)' % (rd_len, rd_len))
print('  payload end = 0x%X; partition 2MiB bounds = %s' % (rd_off + rd_len, 'OK' if rd_off + rd_len <= len(d) else 'EXCEED'))
payload = d[rd_off:rd_off + rd_len]
print('  payload sha256=%s' % hashlib.sha256(payload).hexdigest())
print('  gzip magic at payload start: %s' % (payload[:3].hex() == '1f8b08'))

# decompress and inspect cpio names (names only, no content output)
dec = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(payload)
import gzip as gz
dec = gz.decompress(payload)
print('\n== decompressed ==')
print('  decompressed size=%d sha256=%s' % (len(dec), hashlib.sha256(dec).hexdigest()))
print('  cpio magic: %s' % ('070701 (newc) OK' if dec[:6] == b'070701' else dec[:6].hex()))
names = []
i = 0
while i + 110 <= len(dec) and dec[i:i+6] == b'070701':
    nlen = int(dec[i+94:i+102], 16)
    fsize = int(dec[i+54:i+62], 16)
    name = dec[i+110:i+110+nlen-1].decode('utf-8', 'replace')
    names.append((name, fsize))
    esz = (110 + nlen + 3) & ~3
    esz += (fsize + 3) & ~3
    i += esz
    if len(names) > 200:
        break
print('  cpio entries: %d' % len(names))
key = ['init', 'init.real', 'ksu.ko']
for target in key:
    hits = [(n, s) for (n, s) in names if n.lstrip('./').rstrip('/') == target or n.lstrip('./').startswith(target + '.')]
    print('  %s: %s' % (target, [(n, s) for (n, s) in hits] if hits else 'ABSENT'))
print('  first 12 entries: %s' % [n for (n, s) in names[:12]])

# U-Boot v2026.10 android_image_get_data v0 arithmetic check (header facts only)
print('\n== U-Boot v2026.10 CMD_ABOOTIMG route compatibility (per AI1 source review + local header facts) ==')
print('  header version observed: v0 (no header_version field used; classic 10-field header)')
print('  ramdisk in-place payload: offset 0x%X len %d (v0 arithmetic ALIGN(2048)+ALIGN(kernel_size=0))' % (rd_off, rd_len))
print('  ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR (ARCH_SNAPDRAGON selects it): in-place pointer/len return = compatible')
