#!/usr/bin/env python3
# K1_BOOT_LOAD_MAP01 Stage A: boot v2 header parse + ARM64 Image header + literal load ranges
import struct, hashlib, os

WS = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf'
STOCK = WS + '/PREP12_WORK/W3A/stock-live-boot.img'
PREP10 = WS + '/K1_HOST_CANDIDATE_PREP/dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img'
SEPRAM = WS + '/PREP12_WORK/W3A/stock-live-ramdisk.img'
EV = WS + '/K1_BOOT_LOAD_MAP01/evidence'

def sha(b): return hashlib.sha256(b).hexdigest()

def parse_hdr(data):
    assert data[:8] == b'ANDROID!', 'bad magic'
    (ksz, kaddr, rsz, raddr, ssz, saddr, tags, page, hv, osver) = struct.unpack('<10I', data[8:48])
    cmdline = data[64:576].rstrip(b'\x00')
    imgid = data[576:608].hex()
    hdr_size = struct.unpack('<I', data[1644:1648])[0]
    dtb_sz = struct.unpack('<I', data[1648:1652])[0]
    dtb_addr = struct.unpack('<Q', data[1652:1660])[0]
    off = page
    k_off = off; off = ((off + ksz + page - 1) // page) * page
    r_off = off; off = ((off + rsz + page - 1) // page) * page
    s_off = off; off = ((off + ssz + page - 1) // page) * page
    d_off = off
    return dict(ksz=ksz, kaddr=kaddr, rsz=rsz, raddr=raddr, ssz=ssz, saddr=saddr,
                tags=tags, page=page, hv=hv, osver=osver, cmdline=cmdline, imgid=imgid,
                hdr_size=hdr_size, dtb_sz=dtb_sz, dtb_addr=dtb_addr,
                k_off=k_off, r_off=r_off, d_off=d_off)

stock = open(STOCK, 'rb').read()
prep = open(PREP10, 'rb').read()
sh, ph = parse_hdr(stock), parse_hdr(prep)

for label, h in (('STOCK', sh), ('PREP10', ph)):
    print('== %s boot v2 ==' % label)
    print('  kernel_size=%d kernel_addr=0x%08X ramdisk_size=%d ramdisk_addr=0x%08X dtb_size=%d dtb_addr=0x%08X' %
          (h['ksz'], h['kaddr'], h['rsz'], h['raddr'], h['dtb_sz'], h['dtb_addr']))
    print('  page=%d hv=%d hdr_size=%d osver=0x%08X tags=0x%08X imgid=%s' %
          (h['page'], h['hv'], h['hdr_size'], h['osver'], h['tags'], h['imgid']))

# extract payloads
pk = prep[ph['k_off']:ph['k_off']+ph['ksz']]
pr = prep[ph['r_off']:ph['r_off']+ph['rsz']]
pd = prep[ph['d_off']:ph['d_off']+ph['dtb_sz']]
sk = stock[sh['k_off']:sh['k_off']+sh['ksz']]
sr = stock[sh['r_off']:sh['r_off']+sh['rsz']]
sd = stock[sh['d_off']:sh['d_off']+sh['dtb_sz']]
for name, blob in (('prep_kernel', pk), ('prep_ramdisk', pr), ('prep_dtb', pd),
                   ('stock_kernel', sk), ('stock_ramdisk', sr), ('stock_dtb', sd)):
    open(os.path.join(EV, name + '.bin'), 'wb').write(blob)
    print('%-14s %10d B sha256=%s first16=%s' % (name, len(blob), sha(blob)[:32], blob[:16].hex()))

# ARM64 Image header parse (for both kernels)
print('\n# ==== ARM64 Image headers ====')
def parse_arm64(blob, label):
    print('== %s (%d B) ==' % (label, len(blob)))
    magic = struct.unpack('<I', blob[56:60])[0]
    if magic != 0x644d5241:
        print('  NOT raw ARM64 Image: magic=0x%08X (expect 0x644d5241 "ARM\\x64") first8=%s' % (magic, blob[:8].hex()))
        # check gzip
        if blob[:2] == b'\x1f\x8b':
            import gzip, io
            raw = gzip.decompress(blob)
            m2 = struct.unpack('<I', raw[56:60])[0]
            print('  GZIP payload -> decompressed %d B, inner magic=0x%08X (%s)' %
                  (len(raw), m2, 'ARM64-IMAGE' if m2 == 0x644d5241 else 'unknown'))
            print('  inner text_offset=%d image_size=%d flags=%d' % (
                struct.unpack('<Q', raw[8:16])[0], struct.unpack('<Q', raw[16:24])[0], struct.unpack('<Q', raw[24:32])[0]))
            return None
        return None
    code0, code1 = struct.unpack('<II', blob[0:8])
    text_offset, image_size, flags = struct.unpack('<QQQ', blob[8:32])
    print('  magic=0x%08X OK  code0=0x%08X code1=0x%08X' % (magic, code0, code1))
    print('  text_offset=0x%X image_size=0x%X(%d) flags=0x%X' % (text_offset, image_size, image_size, flags))
    print('  file_size=%d vs image_size=%d (image_size includes BSS; file=%s)' %
          (len(blob), image_size, 'smaller-ok' if len(blob) <= image_size else 'BIGGER-THAN-IMAGE_SIZE'))
    return dict(text_offset=text_offset, image_size=image_size, flags=flags)

pa = parse_arm64(pk, 'PREP10 kernel payload')
sa = parse_arm64(sk, 'stock kernel payload')

# literal load ranges, half-open [start, end)
print('\n# ==== literal load ranges (header fields taken at face value, no base) ====')
def rng(name, start, size):
    print('  %-18s [0x%08X, 0x%08X) size=%d' % (name, start, start+size, size))
    return (start, start+size)
print('-- PREP10 --')
rk = rng('kernel', ph['kaddr'], ph['ksz'])
rd = rng('dtb', ph['dtb_addr'], ph['dtb_sz'])
rr = rng('embedded_ramdisk', ph['raddr'], ph['rsz'])
print('-- STOCK --')
skr = rng('kernel', sh['kaddr'], sh['ksz'])
sdr = rng('dtb', sh['dtb_addr'], sh['dtb_sz'])
srr = rng('embedded_ramdisk', sh['raddr'], sh['rsz'])
def overlap(a, b):
    return not (a[1] <= b[0] or b[1] <= a[0])
print('\n# ==== overlaps ====')
for a_name, a, b_name, b, who in [
    ('PREP10 kernel', rk, 'PREP10 dtb', rd, 'PREP10'),
    ('PREP10 kernel', rk, 'PREP10 emb_ramdisk', rr, 'PREP10'),
    ('PREP10 dtb', rd, 'PREP10 emb_ramdisk', rr, 'PREP10'),
    ('STOCK kernel', skr, 'STOCK dtb', sdr, 'STOCK'),
    ('STOCK kernel', skr, 'STOCK emb_ramdisk', srr, 'STOCK'),
    ('STOCK dtb', sdr, 'STOCK emb_ramdisk', srr, 'STOCK'),
]:
    if overlap(a, b):
        lo, hi = max(a[0], b[0]), min(a[1], b[1])
        print('  %s: %s x %s OVERLAP [0x%08X, 0x%08X) = %d B' % (who, a_name, b_name, lo, hi, hi-lo))
    else:
        print('  %s: %s x %s none (gap=%d)' % (who, a_name, b_name, max(a[0],b[0])-min(a[1],b[1]) if a[1]<=b[0] else b[0]-a[1]))

# separate ramdisk content sniff
print('\n# ==== separate ramdisk (partition) content ====')
sep = open(SEPRAM, 'rb').read()
print('size=%d sha256=%s' % (len(sep), sha(sep)))
print('first 64 B: %s' % sep[:64].hex())
# find first gzip magic
gz = sep.find(b'\x1f\x8b\x08')
print('first gzip magic (1f 8b 08) at offset: 0x%X' % gz if gz >= 0 else 'no gzip magic')
if gz >= 0:
    import gzip, io
    try:
        raw = gzip.decompress(sep[gz:])
        print('decompressed from 0x%X: %d B, first32=%s' % (gz, len(raw), raw[:32].hex()))
        open(os.path.join(EV, 'separate_ramdisk_inner.bin'), 'wb').write(raw)
        print('inner magic: %s' % ('cpio-070701' if raw[:6] == b'070701' else raw[:6].hex()))
    except Exception as e:
        print('gzip decompress failed: %s' % e)
# check android bootimg hdr inside? some vendors store bootimg in ramdisk partition
if sep[:8] == b'ANDROID!':
    print('separate ramdisk partition starts with ANDROID! header')
