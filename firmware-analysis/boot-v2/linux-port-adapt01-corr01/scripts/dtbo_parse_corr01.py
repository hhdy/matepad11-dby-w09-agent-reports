#!/usr/bin/env python3
# CORR01 Stage A: corrected DTBO table parser with proper id/rev/custom field mapping
# Per AOSP dt_table_entry:
#   struct dt_table_entry {
#       uint32_t dt_size;    // @0
#       uint32_t dt_offset;  // @4
#       uint32_t id;         // @8
#       uint32_t rev;        // @12
#       uint32_t custom[4];  // @16,@20,@24,@28
#   };
import struct, hashlib, os

DTBO = '/mnt/d/workbuddy/2026-11-25-22-04-11/r155/copies-primary/dtbo.img'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dtbo_entries_corr01')
os.makedirs(OUT, exist_ok=True)

d = open(DTBO, 'rb').read()
print('DTBO total size: %d B' % len(d))

magic, total_size, hdr_size, entry_size, num_entries, entries_offset, page_size, version = struct.unpack('>8I', d[:32])
print('header: magic=0x%08X total_size=%d hdr_size=%d entry_size=%d num_entries=%d entries_offset=%d page_size=%d version=%d' % (
    magic, total_size, hdr_size, entry_size, num_entries, entries_offset, page_size, version))
assert magic == 0xD7B7AB1E

# Check if entries_offset is non-zero (some DTBO versions have it)
entries_start = entries_offset if entries_offset > 0 else hdr_size

for i in range(num_entries):
    eo = entries_start + i * entry_size
    (dt_size, dt_offset, _id, _rev, c0, c1, c2, c3) = struct.unpack('>8I', d[eo:eo+32])
    blob = d[dt_offset:dt_offset+dt_size]
    sha = hashlib.sha256(blob).hexdigest()
    fdt_magic = struct.unpack('>I', blob[:4])[0] if dt_size >= 4 else 0
    # FDT total_size from header
    fdt_total = struct.unpack('>I', blob[4:8])[0] if dt_size >= 8 else 0
    has_rootparam = blob.find(b'rootparam') >= 0
    print('\n--- Entry %d ---' % i)
    print('  dt_size=%d dt_offset=%d id=0x%08X rev=0x%08X custom=[0x%08X,0x%08X,0x%08X,0x%08X]' % (
        dt_size, dt_offset, _id, _rev, c0, c1, c2, c3))
    print('  FDT magic=0x%08X fdt_total_size=%d blob_sha256=%s' % (fdt_magic, fdt_total, sha[:32]))
    print('  rootparam_present=%s' % has_rootparam)
    # Board variant identification
    for variant, marker in [('VD', b'DBY_W09_VD'), ('VG', b'DBY_W09_VG')]:
        if marker in blob:
            pos = blob.find(marker)
            print('  VARIANT %s found @overlay+0x%x' % (variant, pos))
    # Check bounds
    end = dt_offset + dt_size
    if end > len(d):
        print('  WARNING: entry end 0x%x > file size 0x%x' % (end, len(d)))
    # Save
    out_path = os.path.join(OUT, 'entry_%d_id0x%08X_rev0x%08X.dtbo' % (i, _id, _rev))
    with open(out_path, 'wb') as f:
        f.write(blob)

# Table boundary checks
print('\n# ==== boundary checks ====')
max_end = 0
overlaps = []
prev_end = 0
entries_info = []
for i in range(num_entries):
    eo = entries_start + i * entry_size
    dt_size, dt_offset = struct.unpack('>II', d[eo:eo+8])
    end = dt_offset + dt_size
    entries_info.append((i, dt_offset, dt_size, end))
    if dt_offset < prev_end:
        overlaps.append((i, dt_offset, prev_end))
    prev_end = max(prev_end, end)
    max_end = max(max_end, end)
print('max_end=0x%x (%d) vs dt_size_field=%d vs file_size=%d' % (max_end, max_end, dt_size, len(d)))
print('overlaps:', overlaps if overlaps else 'none')
# Check alignment
for (i, doff, dsz, dend) in entries_info:
    align = doff % page_size if page_size else 0
    if align != 0:
        print('  entry %d offset 0x%x not page-aligned (mod %d = %d)' % (i, doff, page_size, align))
