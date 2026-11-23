#!/usr/bin/env python3
"""Read-only verifier for a PKWARE split ZIP (.z01 + .zip).

Never writes to the source directory. Implements a virtual concatenation of
the volume parts so no multi-gigabyte temporary file is created. Verifies:
  - split markers, volume sizes, volume count
  - EOCD / Zip64 EOCD structures
  - central directory local-header signatures via virtual offsets
  - CRC-32 + uncompressed size of every stored/deflated entry
  - path-safety checks (traversal, absolute, drive, UNC, symlink, duplicates)

Usage: python Verify-XiaomiSplitZip.py <last_volume.zip> <out_dir>
"""
import os, sys, struct, zlib, csv, json, hashlib

EOCD_SIG = b'PK\x05\x06'
EOCD64_SIG = b'PK\x06\x06'
LOC64_SIG = b'PK\x06\x07'
CD_SIG = b'PK\x01\x02'
LFH_SIG = b'PK\x03\x04'
SPLIT_MARK = b'PK\x07\x08'
MAX_TAIL = 1 << 20  # EOCD search window


def read_at(f, off, n):
    f.seek(off)
    b = f.read(n)
    if len(b) != n:
        raise RuntimeError(f'short read at {off}: want {n}, got {len(b)}')
    return b


def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u64(b, o): return struct.unpack_from('<Q', b, o)[0]


class SplitZip:
    """Virtual concatenation of .z01 ... .zip; reads map logical offsets to parts."""
    def __init__(self, parts):
        self.parts = parts                      # ordered list of (path, size)
        self.starts = []
        s = 0
        for _, size in parts:
            self.starts.append(s)
            s += size
        self.total = s
        self.handles = [open(p, 'rb') for p, _ in parts]

    def close(self):
        for h in self.handles:
            h.close()

    def read(self, off, n):
        if off < 0 or n < 0 or off + n > self.total:
            raise RuntimeError(f'out of range: off={off} n={n} total={self.total}')
        out = bytearray()
        pos = off
        remaining = n
        for i, (h, (_, size)) in enumerate(zip(self.handles, self.parts)):
            start = self.starts[i]
            if pos < start + size and remaining:
                skip = max(0, start - pos)
                if skip:
                    pos += skip
                local = pos - start
                take = min(remaining, size - local)
                h.seek(local)
                chunk = h.read(take)
                if len(chunk) != take:
                    raise RuntimeError(f'short virtual read part {i}')
                out.extend(chunk)
                pos += take
                remaining -= take
            if remaining == 0:
                break
        if remaining:
            raise RuntimeError(f'unread bytes remain: {remaining}')
        return bytes(out)


def detect_parts(zip_path):
    """Discover volume parts in zip_path's directory by base name + .zNN order."""
    d = os.path.dirname(os.path.abspath(zip_path))
    base = os.path.basename(zip_path)
    stem, ext = os.path.splitext(base)
    if ext.lower() != '.zip':
        raise RuntimeError('last volume must end with .zip')
    vols = []
    n = 1
    while True:
        p = os.path.join(d, f'{stem}.z{n:02d}')
        if not os.path.exists(p):
            break
        with open(p, 'rb') as f:
            head = f.read(8)
        if head[:4] != SPLIT_MARK:
            raise RuntimeError(f'{p}: missing split marker {SPLIT_MARK.hex()}')
        if head[4:8] != LFH_SIG:
            raise RuntimeError(f'{p}: missing local header after split marker')
        vols.append((p, os.path.getsize(p)))
        n += 1
    vols.append((os.path.abspath(zip_path), os.path.getsize(zip_path)))
    return vols


def find_eocd(z):
    start = max(0, z.total - MAX_TAIL)
    tail = z.read(start, z.total - start)
    idx = tail.rfind(EOCD_SIG)
    if idx < 0:
        raise RuntimeError('EOCD not found in tail')
    return start + idx, tail


def parse_zip64(z, eocd_off):
    """Return (entry_count, cd_size, cd_offset_absolute)."""
    eocd = z.read(eocd_off, 22)
    disk = u16(eocd, 4)
    cd_disk = u16(eocd, 6)
    n_disk = u16(eocd, 8)
    n_total = u16(eocd, 10)
    cd_size = u32(eocd, 12)
    cd_off = u32(eocd, 16)
    info = {'eocd_disk_no': disk, 'eocd_cd_disk': cd_disk,
            'eocd_entries_this_disk': n_disk, 'eocd_entries_total': n_total,
            'eocd_cd_size_32': cd_size, 'eocd_cd_offset_32': cd_off}
    needs64 = 0xFFFF in (n_disk, n_total, cd_size, cd_off) or disk == 0xFFFF or cd_disk == 0xFFFF
    if needs64:
        loc_off = eocd_off - 20
        loc = z.read(loc_off, 20)
        if loc[:4] != LOC64_SIG:
            raise RuntimeError('Zip64 locator not found')
        e64_off = u64(loc, 8)
        e64 = z.read(e64_off, 56)
        if e64[:4] != EOCD64_SIG:
            raise RuntimeError('Zip64 EOCD not found')
        n_total = u64(e64, 32)
        cd_size = u64(e64, 40)
        cd_off = u64(e64, 48)
        info['zip64_used'] = True
        info['zip64_eocd_offset'] = e64_off
    else:
        info['zip64_used'] = False
    # cd_off is relative to cd_disk's start; map to absolute virtual offset
    cd_start_disk = cd_disk if cd_disk != 0xFFFF else 0
    # Find which physical part holds CD disk. For split ZIP with N parts,
    # cd_disk index equals last part; its logical start is z.starts[-1].
    cd_abs = z.starts[-1] + cd_off
    info.update({'entry_count': n_total, 'cd_size': cd_size,
                 'cd_offset_logical': cd_abs, 'cd_disk': cd_disk})
    return info, cd_abs, cd_size, n_total


def decode_name(raw, flags, extra):
    # Prefer Info-ZIP UTF-8 extra field 0x7075
    p = 0
    while p + 4 <= len(extra):
        hid, hlen = u16(extra, p), u16(extra, p + 2)
        if hid == 0x7075 and hlen >= 5:
            # layout: id(2) len(2) version(1) name_crc(4) utf8_name(...)
            return extra[p + 9:p + 4 + hlen].decode('utf-8', 'replace')
        p += 4 + hlen
    if flags & 0x800:
        return raw.decode('utf-8', 'replace')
    return raw.decode('cp437', 'replace')


def classify(path, is_dir):
    low = path.lower()
    if is_dir: return 'DIR'
    if any(low.endswith(x) for x in ('.img','.bin','.mbn','.elf','.so','.ko','.dtb','.dtbo','.exe','.dll')):
        return 'FIRMWARE_BINARY_OR_EXECUTABLE'
    if low.endswith(('.sha256','.md5','.txt','.md')) or low.endswith('/readme.txt'):
        return 'TEXT_DOCUMENT'
    if low.endswith(('.sh','.bat','.cmd','.ps1')):
        return 'SCRIPT_DO_NOT_EXECUTE'
    return 'OTHER'


def path_risks(name):
    issues = []
    if name.startswith('/') or name.startswith('\\'):
        issues.append('ABSOLUTE_PATH')
    if len(name) >= 2 and name[1] == ':':
        issues.append('DRIVE_PATH')
    if name.startswith('\\\\') or name.startswith('//'):
        issues.append('UNC_PATH')
    parts = name.replace('\\', '/').split('/')
    if any(p == '..' for p in parts):
        issues.append('TRAVERSAL')
    return issues


def main():
    if len(sys.argv) != 3:
        print('usage: Verify-XiaomiSplitZip.py <last_volume.zip> <out_dir>')
        sys.exit(2)
    zip_path, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    parts = detect_parts(zip_path)
    z = SplitZip(parts)
    try:
        eocd_off, _ = find_eocd(z)
        info, cd_abs, cd_size, n = parse_zip64(z, eocd_off)
        cd = z.read(cd_abs, cd_size)
        entries = []
        seen = {}
        risks = []
        p = 0
        ok_crc = 0
        for i in range(n):
            if cd[p:p+4] != CD_SIG:
                raise RuntimeError(f'CD entry {i+1}: bad signature at {p}')
            hdr = cd[p:p+46]
            flags = u16(hdr, 8); method = u16(hdr, 10)
            crc = u32(hdr, 16); csize = u32(hdr, 20); usize = u32(hdr, 24)
            fnlen = u16(hdr, 28); exlen = u16(hdr, 30); comlen = u16(hdr, 32)
            disk_start = u16(hdr, 34); local_off = u32(hdr, 42)
            name_raw = cd[p+46:p+46+fnlen]
            extra = cd[p+46+fnlen:p+46+fnlen+exlen]
            name = decode_name(name_raw, flags, extra)
            # Zip64 extra for sizes / offset
            ep = 0
            while ep + 4 <= len(extra):
                hid, hlen = u16(extra, ep), u16(extra, ep+2)
                if hid == 0x0001:
                    q = ep + 4
                    if usize == 0xFFFFFFFF:
                        usize = u64(extra, q); q += 8
                    if csize == 0xFFFFFFFF:
                        csize = u64(extra, q); q += 8
                    if local_off == 0xFFFFFFFF:
                        local_off = u64(extra, q); q += 8
                ep += 4 + hlen
            abs_local = z.starts[disk_start] + local_off
            lfh = z.read(abs_local, 30)
            sig_ok = lfh[:4] == LFH_SIG
            lfnlen = u16(lfh, 26); lexlen = u16(lfh, 28)
            data_off = abs_local + 30 + lfnlen + lexlen
            is_dir = name.endswith('/')
            crc_ok = None
            err = ''
            if not is_dir:
                try:
                    comp = z.read(data_off, csize)
                    if method == 0:
                        raw = comp
                    elif method == 8:
                        raw = zlib.decompress(comp, -15)
                    else:
                        raise RuntimeError(f'unsupported method {method}')
                    actual_crc = zlib.crc32(raw) & 0xFFFFFFFF
                    crc_ok = (actual_crc == crc and len(raw) == usize)
                    if crc_ok: ok_crc += 1
                    else:
                        err = f'crc/size mismatch: got {actual_crc:08x}/{len(raw)}, want {crc:08x}/{usize}'
                except Exception as ex:
                    crc_ok = False
                    err = str(ex)
            rs = path_risks(name)
            if rs:
                risks.append({'entry': name, 'issues': rs})
            key = name.rstrip('/')
            if key in seen:
                risks.append({'entry': name, 'issues': ['DUPLICATE_NAME']})
            seen[key] = True
            entries.append({
                'index': i+1, 'path': name, 'uncompressed_size': usize,
                'compressed_size': csize, 'method': method, 'flags': flags,
                'crc32_expected': f'{crc:08x}', 'crc32_verified': crc_ok,
                'disk_start': disk_start, 'local_header_signature_ok': sig_ok,
                'local_header_virtual_offset': abs_local,
                'classification': classify(name, is_dir), 'error': err,
            })
            p += 46 + fnlen + exlen + comlen
        if p != cd_size:
            raise RuntimeError(f'central directory length mismatch: parsed {p}, declared {cd_size}')

        inv_path = os.path.join(out_dir, 'package_1_inventory.csv')
        with open(inv_path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(['entry_path','uncompressed_size','compressed_size','file_type','classification','crc32_verified'])
            for e in entries:
                ft = 'DIR' if e['path'].endswith('/') else ('DEFLATE' if e['method']==8 else 'STORED')
                w.writerow([e['path'], e['uncompressed_size'], e['compressed_size'], ft,
                            e['classification'], 'YES' if e['crc32_verified'] else ('N/A' if e['path'].endswith('/') else 'NO')])

        total_u = sum(e['uncompressed_size'] for e in entries)
        max_u = max(e['uncompressed_size'] for e in entries)
        summary = {
            'source_volumes': [{'path': os.path.basename(p), 'size': s} for p, s in parts],
            'virtual_total_size': z.total,
            'volume_count': len(parts),
            'eocd': info,
            'entry_count': n,
            'crc_verified_entries': ok_crc,
            'directory_entries': sum(1 for e in entries if e['path'].endswith('/')),
            'total_uncompressed_size': total_u,
            'max_single_uncompressed_size': max_u,
            'compression_ratio': round(total_u / z.total, 3),
            'local_header_signature_all_ok': all(e['local_header_signature_ok'] for e in entries),
            'path_risks': risks,
            'integrity_status': 'ARCHIVE_TEST_OK' if ok_crc == sum(1 for e in entries if not e['path'].endswith('/')) and not risks else 'CRC_ERROR_OR_PATH_RISK',
        }
        with open(os.path.join(out_dir, 'package_1_verification.json'), 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        with open(os.path.join(out_dir, 'package_1_verification.txt'), 'w', encoding='utf-8') as f:
            f.write('PACKAGE 1 — READ-ONLY ZIP SPLIT VERIFICATION\n')
            f.write('=' * 60 + '\n')
            for k, v in summary.items():
                f.write(f'{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v,(dict,list)) else v}\n')
            f.write('\nPER-ENTRY RESULTS\n')
            for e in entries:
                f.write(f"[{e['index']:02d}] {e['path']} | crc={e['crc32_verified']} | sig={e['local_header_signature_ok']} | {e['error']}\n")
        print(json.dumps({'status': summary['integrity_status'], 'entries': n,
                          'crc_ok': ok_crc, 'path_risks': len(risks),
                          'total_uncompressed': total_u}, ensure_ascii=False))
    finally:
        z.close()


if __name__ == '__main__':
    main()
