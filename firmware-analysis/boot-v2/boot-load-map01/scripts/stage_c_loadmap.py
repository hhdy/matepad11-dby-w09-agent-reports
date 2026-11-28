#!/usr/bin/env python3
# K1_BOOT_LOAD_MAP01 Stage C: apply decoded ABL placement math to stock & PREP10
import struct, hashlib, os

WS = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf'
STOCK = WS + '/PREP12_WORK/W3A/stock-live-boot.img'
PREP10 = WS + '/K1_HOST_CANDIDATE_PREP/dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img'
PART = 100663296  # boot partition size

def parse_hdr(data):
    (ksz, kaddr, rsz, raddr, ssz, saddr, tags, page, hv, osver) = struct.unpack('<10I', data[8:48])
    dtb_sz = struct.unpack('<I', data[1648:1652])[0]
    dtb_addr = struct.unpack('<Q', data[1652:1660])[0]
    return dict(ksz=ksz, rsz=rsz, ssz=ssz, page=page, hv=hv, dtb_sz=dtb_sz)

stock = open(STOCK, 'rb').read()
prep = open(PREP10, 'rb').read()
sh = parse_hdr(stock); ph = parse_hdr(prep)

def round_down_page(x, page):
    return (x - 1) & ~(page - 1)

def abl_layout(buf_size, ksz, rsz, page, dtb_sz, gz_uncompressed=None, label=''):
    # decoded ABL math (0x374AC-0x37508):
    A = rsz                      # slot-0x38 = u32@hdr+0x10 = ramdisk_size
    B = dtb_sz                   # slot-0x28 = dtb-related size (v2 branch)
    C = page                     # slot-0x44 = u32@hdr+0x24 = page_size
    total = A + B + C
    rounded = round_down_page(total, page) + page      # 0x374E8-0x374F4
    kernel_load = buf_size*0 + 0x80000                 # offset within ImageBuffer (64-bit path)
    k2_end = buf_size                                   # k2 = ImageBuffer + ImageSize
    R = k2_end - rounded                                # RamdiskLoadAddress (offset)
    D = R - page - 0x200000                             # DeviceTreeLoadAddress (offset)
    cap = D - kernel_load                               # x27 capacity check (must be >0)
    # kernel extent (relative offsets)
    kext = kernel_load + (gz_uncompressed or ksz)
    print('== %s ==' % label)
    print('  ImageBuffer size        : %d B (0x%X)' % (buf_size, buf_size))
    print('  kernel_size             : %d (0x%X)  %s' % (ksz, ksz, ('(gz uncompressed=%d/0x%X)' % (gz_uncompressed, gz_uncompressed)) if gz_uncompressed else '(raw Image)'))
    print('  KernelLoadAddress       : ImageBuffer + 0x%05X' % kernel_load)
    print('  kernel end offset       : 0x%X' % kext)
    print('  RamdiskLoadAddress (R)  : ImageBuffer + 0x%X  (end - 0x%X)' % (R, rounded))
    print('  DeviceTreeLoadAddr (D)  : ImageBuffer + 0x%X  (R - 4K - 2M)' % D)
    print('  capacity check D-kLoad  : 0x%X (%d) %s' % (cap, cap, 'PASS' if cap > 0 else 'FAIL'))
    print('  overlap kernel vs R/D   : %s (kernel_end 0x%X %s R 0x%X)' % (
        'NONE' if kext < D else 'OVERLAP', kext, '<' if kext < D else '>=', D))
    return dict(kernel_load=kernel_load, kext=kext, R=R, D=D, cap=cap)

# normal boot: ImageBuffer = whole-partition allocation (LoadImageAndAuth reads full partition)
print('# ==== NORMAL BOOT (boot partition written, ImageBuffer = 96 MiB partition buffer) ====')
s = abl_layout(PART, sh['ksz'], sh['rsz'], sh['page'], sh['dtb_sz'], gz_uncompressed=57470992, label='STOCK normal boot (gz kernel)')
p = abl_layout(PART, ph['ksz'], ph['rsz'], ph['page'], ph['dtb_sz'], label='PREP10 normal boot (raw Image)')

# fastboot boot: ImageBuffer = downloaded image (46,563,215 B for PREP10)
print('\n# ==== FASTBOOT BOOT (RAM download; ImageBuffer = download buffer) ====')
pf = abl_layout(len(prep), ph['ksz'], ph['rsz'], ph['page'], ph['dtb_sz'], label='PREP10 fastboot boot (download buffer = file size)')
# what download size would be needed?
need = 0x80000 + ph['ksz'] + (p['R'] - p['kext'])  # kernel offset+size + headroom in front of R
print('\nPREP10: required ImageBuffer >= D+kernelsize+margin; file=%d' % len(prep))
print('  D needs: kernel_load(0x80000) + ksz(%d) + gap-to-R(%d) + DTB-region(2M+4K+dtb) ' % (ph['ksz'], p['R']-p['kext']))
minbuf = p['kext'] + (p['R'] - p['kext']) + 0x201000 + ph['dtb_sz']
print('  minimum coherent ImageBuffer ~ %d B (0x%X) vs download 46,563,215 (0x%X) -> fastboot RAM boot of PREP10 as-is: %s' % (
    minbuf, minbuf, len(prep), 'fits' if len(prep) >= minbuf else 'DOES NOT FIT (capacity check FAILS)'))

# literal header ranges for the CSV
import csv
rows = []
def rng(name, img, start, size, src):
    rows.append([name, img, hex(start), hex(start+size), size, src])
rng('kernel(literal hdr)', 'stock', sh['ksz']*0+0x8000, sh['ksz'], 'boot header kernel_addr=0x8000 (UNUSED by ABL for 64-bit)')
rng('kernel(literal hdr)', 'prep10', 0x8000, ph['ksz'], 'boot header kernel_addr=0x8000 (UNUSED by ABL for 64-bit)')
rng('ramdisk(literal hdr)', 'stock', 0x2000000, sh['rsz'], 'header ramdisk_addr=0x2000000 (UNUSED)')
rng('ramdisk(literal hdr)', 'prep10', 0x2000000, ph['rsz'], 'header ramdisk_addr=0x2000000 (UNUSED)')
rng('dtb(literal hdr)', 'stock', 0x1F00000, sh['dtb_sz'], 'header dtb_addr=0x1F00000 (UNUSED)')
rng('dtb(literal hdr)', 'prep10', 0x1F00000, ph['dtb_sz'], 'header dtb_addr=0x1F00000 (UNUSED)')
rng('kernel(ABL actual off)', 'stock', 0x80000, 57470992, 'ImageBuffer+0x80000 (csel@0x374AC, gz decompressed)')
rng('kernel(ABL actual off)', 'prep10', 0x80000, ph['ksz'], 'ImageBuffer+0x80000 (csel@0x374AC, raw CopyMem@0x37818)')
rng('ramdisk(ABL actual off)', 'stock', s['R'], sh['rsz'], 'end-rounded (0x374D0-0x37508)')
rng('ramdisk(ABL actual off)', 'prep10', p['R'], ph['rsz'], 'end-rounded (0x374D0-0x37508)')
rng('dtb(ABL actual off)', 'stock', s['D'], sh['dtb_sz'], 'R-4K-2M (0x374FC-0x37508)')
rng('dtb(ABL actual off)', 'prep10', p['D'], ph['dtb_sz'], 'R-4K-2M (0x374FC-0x37508)')
with open(WS + '/K1_BOOT_LOAD_MAP01/stock_vs_prep10_load_ranges.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['object', 'image', 'start(rel ImageBuffer)', 'end(rel)', 'size_B', 'evidence'])
    w.writerows(rows)
print('\nCSV written: %d rows' % len(rows))
