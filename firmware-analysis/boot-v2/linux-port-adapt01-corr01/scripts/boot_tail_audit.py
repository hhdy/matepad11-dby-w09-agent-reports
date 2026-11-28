#!/usr/bin/env python3
# Stage C: Full 96 MiB stock boot tail audit + header comparison stock vs PREP10
import struct, hashlib, os

STOCK = '/mnt/d/workbuddy/2026-11-25-22-04-11/r155/copies-primary/boot.img'
PREP10 = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/K1_HOST_CANDIDATE_PREP/dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img'

stock = open(STOCK, 'rb').read()
prep = open(PREP10, 'rb').read()
PART_SIZE = 100663296
PREP10_SIZE = len(prep)

print('stock boot: %d B sha256=%s' % (len(stock), hashlib.sha256(stock).hexdigest()))
print('PREP10 boot: %d B sha256=%s' % (len(prep), hashlib.sha256(prep).hexdigest()))
print('partition capacity: %d B (%d MiB)' % (PART_SIZE, PART_SIZE//(1024*1024)))

# ===== Parse both boot v2 headers =====
def parse_hdr(data, label):
    magic = data[0:8]
    (ksz, kaddr, rsz, raddr, ssz, saddr, tags, page, hv, osver) = struct.unpack('<10I', data[8:48])
    name = data[48:64].rstrip(b'\x00')
    cmdline = data[64:576].rstrip(b'\x00')
    imgid = data[576:608]
    extra = data[608:1632].rstrip(b'\x00')
    rec_dtbo_sz = struct.unpack('<I', data[1632:1636])[0]
    rec_dtbo_off = struct.unpack('<Q', data[1636:1644])[0]
    hdr_size = struct.unpack('<I', data[1644:1648])[0]
    dtb_sz = struct.unpack('<I', data[1648:1652])[0]
    dtb_addr = struct.unpack('<Q', data[1652:1660])[0]
    print('\n== %s ==' % label)
    print('  magic=%r kernel_size=%d kernel_addr=0x%x ramdisk_size=%d ramdisk_addr=0x%x' % (magic, ksz, kaddr, rsz, raddr))
    print('  second_size=%d second_addr=0x%x tags_addr=0x%x page_size=%d header_version=%d os_version=0x%x' % (ssz, saddr, tags, page, hv, osver))
    print('  name=%r' % name)
    print('  cmdline_len=%d cmdline=%r' % (len(cmdline), cmdline[:80]))
    print('  extra_cmdline=%r' % extra[:80])
    print('  img_id=%s' % imgid.hex()[:40])
    print('  recovery_dtbo_size=%d recovery_dtbo_offset=%d header_size=%d dtb_size=%d dtb_addr=0x%x' % (rec_dtbo_sz, rec_dtbo_off, hdr_size, dtb_sz, dtb_addr))
    # payload layout
    off = page
    k_off = off; off = ((off + ksz + page - 1) // page) * page
    r_off = off; off = ((off + rsz + page - 1) // page) * page
    s_off = off; off = ((off + ssz + page - 1) // page) * page
    d_off = off; off = ((off + dtb_sz + page - 1) // page) * page
    payload_end = off
    print('  layout: kernel@0x%x ramdisk@0x%x second@0x%x dtb@0x%x payload_end=0x%x' % (k_off, r_off, s_off, d_off, payload_end))
    return dict(ksz=ksz, rsz=rsz, ssz=ssz, dtb_sz=dtb_sz, page=page, hv=hv,
                cmdline=cmdline, extra=extra, imgid=imgid, k_off=k_off, r_off=r_off,
                d_off=d_off, payload_end=payload_end, osver=osver, hdr_size=hdr_size)

sh = parse_hdr(stock, 'STOCK 96MiB')
ph = parse_hdr(prep, 'PREP10')

# ===== Compare headers =====
print('\n# ==== header comparison ====')
for k in ['ksz', 'rsz', 'ssz', 'dtb_sz', 'page', 'hv', 'osver', 'hdr_size']:
    if sh[k] == ph[k]:
        print('  %-12s SAME (%s)' % (k, sh[k]))
    else:
        print('  %-12s DIFF stock=%s prep=%s' % (k, sh[k], ph[k]))
same_cmd = sh['cmdline'] == ph['cmdline']
print('  cmdline     %s (stock_len=%d prep_len=%d)' % ('SAME' if same_cmd else 'DIFF', len(sh['cmdline']), len(ph['cmdline'])))
if not same_cmd:
    # find diff
    for i in range(min(len(sh['cmdline']), len(ph['cmdline']))):
        if sh['cmdline'][i] != ph['cmdline'][i]:
            print('    first_diff @%d: stock=%r prep=%r' % (i, sh['cmdline'][i:i+30], ph['cmdline'][i:i+30]))
            break
    print('    prep prefix: %r' % ph['cmdline'][:20])
    print('    stock prefix: %r' % sh['cmdline'][:20])

# ===== Stock boot tail audit =====
print('\n# ==== stock boot tail audit ====')
tail_start = sh['payload_end']
tail = stock[tail_start:]
print('stock payload_end=0x%x (%d), tail_size=%d B (%.2f MiB)' % (tail_start, tail_start, len(tail), len(tail)/(1024*1024)))
# Check last 64B for AVBf
last64 = stock[-64:]
print('last 64 bytes: %s' % last64.hex())
if last64[:4] == b'AVBf':
    print('  AVB footer DETECTED at end of file')
    magic, maj, mi, auth_off, aux_off, aux_sz, desc_off, desc_sz = struct.unpack('>4sIIQQQQQ', last64[:40])
    print('  footer: magic=AVBf major=%d minor=%d' % (maj, mi))
else:
    print('  AVB footer NOT found at last 64 B')
# Check non-zero ranges in tail
nz_ranges = []
in_nz = False
for i, b in enumerate(tail):
    if b != 0:
        if not in_nz:
            nz_start = i
            in_nz = True
    else:
        if in_nz:
            nz_ranges.append((nz_start, i))
            in_nz = False
if in_nz:
    nz_ranges.append((nz_start, len(tail)))
# Merge close ranges
merged = []
for s, e in nz_ranges:
    if merged and s - merged[-1][1] < 64:
        merged[-1][1] = e
    else:
        merged.append([s, e])
print('tail non-zero ranges (merged <64B gap): %d' % len(merged))
for s, e in merged[:20]:
    abs_s = tail_start + s
    abs_e = tail_start + e
    seg = stock[abs_s:abs_e]
    seg_sha = hashlib.sha256(seg).hexdigest()[:16]
    print('  [0x%x, 0x%x) %d B sha=%s first16=%r' % (abs_s, abs_e, e-s, seg_sha, seg[:16]))
# Check specific ranges
for sz_label, sz_bytes in [('last 4KiB', 4096), ('last 64KiB', 65536), ('last 1MiB', 1048576)]:
    seg = stock[-sz_bytes:]
    nz = sum(1 for b in seg if b != 0)
    print('last %s: %d non-zero bytes out of %d' % (sz_label, nz, sz_bytes))
# Check if PREP10 would fit
print('PREP10 payload_end=0x%x (%d) — stock payload_end=0x%x (%d)' % (ph['payload_end'], ph['payload_end'], sh['payload_end'], sh['payload_end']))
print('PREP10 fits in partition: %s (46,563,215 < 100,663,296)' % (PREP10_SIZE < PART_SIZE))
print('PREP10 vs stock payload_end: PREP10_end=%d stock_end=%d diff=%d' % (ph['payload_end'], sh['payload_end'], sh['payload_end'] - ph['payload_end']))

# ===== What PREP10 prefix write preserves =====
print('\n# ==== prefix write [0,46563215) preserves [46563215,100663296) ====')
preserved = stock[PREP10_SIZE:]
nz_preserved = sum(1 for b in preserved if b != 0)
print('preserved region: %d B, non-zero bytes=%d (%.1f%%)' % (len(preserved), nz_preserved, 100.0*nz_preserved/len(preserved)))
print('preserved region sha256=%s' % hashlib.sha256(preserved).hexdigest())
# Check if preserved region starts with all zeros
first_1k = preserved[:1024]
print('first 1KiB of preserved region all-zero: %s' % (first_1k == b'\x00' * 1024))
