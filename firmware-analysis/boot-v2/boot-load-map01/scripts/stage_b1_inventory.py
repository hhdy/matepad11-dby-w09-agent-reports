#!/usr/bin/env python3
# K1_BOOT_LOAD_MAP01 Stage B1: PE32+ section map + VA/file mapping + boot-vocabulary string inventory
import struct, os, re, hashlib

WS = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf'
PE = WS + '/PREP12_WORK/W3A/abl-hos43-pe.bin'
EV = WS + '/K1_BOOT_LOAD_MAP01/evidence'

d = open(PE, 'rb').read()
print('PE file: %d B sha256=%s' % (len(d), hashlib.sha256(d).hexdigest()))

# find MZ/PE header
dos_off = d.find(b'MZ')
pe_hdr = d.find(b'PE\x00\x00', dos_off)
print('MZ @0x%X  PE signature @0x%X' % (dos_off, pe_hdr))
coff = pe_hdr + 4
machine, nsec, tsd, ptrsym, nsym, opthdrsz, chars = struct.unpack('<HHIIIHH', d[coff:coff+20])
print('COFF: machine=0x%04X nsec=%d opthdrsz=%d chars=0x%04X' % (machine, nsec, opthdrsz, chars))
opt = coff + 20
optmagic = struct.unpack('<H', d[opt:opt+2])[0]
print('optional header magic=0x%04X (%s)' % (optmagic, 'PE32+' if optmagic == 0x20B else 'PE32'))
if optmagic == 0x20B:
    entry_rva, = struct.unpack('<I', d[opt+16:opt+20])
    image_base, = struct.unpack('<Q', d[opt+24:opt+32])
    size_img, size_hdr = struct.unpack('<II', d[opt+56:opt+64])
    print('AddressOfEntryPoint RVA=0x%X ImageBase=0x%X SizeOfImage=0x%X SizeOfHeaders=0x%X' % (entry_rva, image_base, size_img, size_hdr))

# section table
secs = []
st = opt + opthdrsz
print('\n# ==== sections ====')
for i in range(nsec):
    name = d[st:st+8].rstrip(b'\x00').decode('ascii', 'replace')
    vsz, va, rsz, roff = struct.unpack('<IIII', d[st+8:st+24])
    sc = struct.unpack('<I', d[st+36:st+40])[0]
    secs.append((name, va, vsz, roff, rsz))
    print('  %-8s VA=0x%06X VSize=0x%06X FileOff=0x%06X RawSize=0x%06X chars=0x%08X %s' % (
        name, va, vsz, roff, rsz, sc, 'RW' if sc & 0xC0000000 else ('RX' if sc & 0x20000000 else '')))
    st += 40

def va2off(va):
    for (name, sva, vsz, roff, rsz) in secs:
        if sva <= va < sva + max(vsz, rsz):
            o = roff + (va - sva)
            if o < len(d):
                return o
    return None

def off2va(off):
    for (name, sva, vsz, roff, rsz) in secs:
        if rsz and roff <= off < roff + rsz:
            return sva + (off - roff)
    return None

print('\n# ==== mapping sanity ====')
for probe in (0x105b26, 0x118e68, 0xcc668, 0x62b44, 0xb4630):
    o = va2off(probe)
    print('  VA 0x%06X -> file 0x%s ; identity=%s' % (probe, ('%06X' % o) if o else 'MISS', (o == probe)))

# known-str check: " console=NULL loglevel=0" at VA 0x105b52
k = d.find(b' console=NULL loglevel=0')
print('  known string " console=NULL loglevel=0" file=0x%X VA=0x%s' % (k, ('%06X' % off2va(k)) if k >= 0 else 'MISS'))

# string inventory, boot vocabulary
print('\n# ==== boot-vocabulary strings (>=4 chars) ====')
vocab = ['ANDROID', 'bootimg', 'boot_img', 'boot.img', 'bootimage', 'boot image', 'kernel',
         'ramdisk', 'initrd', 'initram', 'dtb', 'dtbo', 'overlay', 'fdt', 'DtbFile', 'KernelFile',
         'BootFile', 'LoadImage', 'LoadFv', 'CopyMem', 'SetMem', ' AllocatePool', 'FreePages',
         'AllocatePages', 'gzip', 'gunzip', 'decomp', 'inflate', 'lzma', 'uncompress', 'unzip',
         'entry', 'Entry', 'jump', 'Jump', 'BootLinux', 'LinuxBoot', 'BootKernel', 'BootRd',
         'LoadLinux', ' cmdline', 'cmdline', 'rootparam', 'console=', 'loglevel', 'earlycon',
         'Partition', 'partition', 'ramdisk.img', 'sep', 'splice', 'image size', 'oversize',
         'too large', 'too big', 'exceed', 'memory not enough', 'OutOfMemory', 'EFI_NO_MAPPING',
         '2MB', 'align', 'Align', 'reloc', 'Reloc', 'kaslr', 'KASLR', 'phys', 'Phys',
         '0x8000', 'text_offset', 'image_size']
strs = []  # (off, va, s)
cur = bytearray(); start = 0
for i, b in enumerate(d):
    if 32 <= b < 127:
        if not cur: start = i
        cur.append(b)
    else:
        if len(cur) >= 4:
            strs.append((start, cur.decode('ascii')))
        cur = bytearray()
if len(cur) >= 4: strs.append((start, cur.decode('ascii')))
print('total strings >=4: %d' % len(strs))

hits = []
for (o, s) in strs:
    low = s.lower()
    for v in vocab:
        if v.lower() in low:
            hits.append((o, s))
            break
print('vocab hits: %d' % len(hits))
with open(os.path.join(EV, 'abl_boot_strings.txt'), 'w') as f:
    for (o, s) in hits:
        va = off2va(o)
        f.write('0x%06X VA=%s %r\n' % (o, ('0x%06X' % va) if va else '?', s))
for (o, s) in hits[:400]:
    va = off2va(o)
    print('0x%06X VA=%s %r' % (o, ('%06X' % va) if va else '?', s[:100]))
