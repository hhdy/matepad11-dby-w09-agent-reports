#!/usr/bin/env python3
"""Selectively extract ONLY allowlisted plain-text entries from a split ZIP.

Read-only on source volumes. Writes extracted text + SHA-256 manifest to
<out_dir>/text_evidence. Never executes any file. Refuses oversized entries.
"""
import os, sys, zlib, hashlib, json, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('vz', os.path.join(HERE, 'Verify-XiaomiSplitZip.py'))
vz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vz)

MAX_TEXT_BYTES = 256 * 1024
ALLOW = {
    'readme.txt', 'images.sha256',
    'flash_all.bat', 'flash_all.sh',
    'flash_all_except_storage.bat', 'flash_all_except_storage.sh',
}


def main():
    if len(sys.argv) != 3:
        print('usage: Extract-XiaomiText.py <last_volume.zip> <out_dir>')
        sys.exit(2)
    zip_path, out_dir = sys.argv[1], sys.argv[2]
    ev_dir = os.path.join(out_dir, 'text_evidence')
    os.makedirs(ev_dir, exist_ok=True)
    parts = vz.detect_parts(zip_path)
    z = vz.SplitZip(parts)
    extracted = []
    try:
        eocd_off, _ = vz.find_eocd(z)
        info, cd_abs, cd_size, n = vz.parse_zip64(z, eocd_off)
        cd = z.read(cd_abs, cd_size)
        p = 0
        for i in range(n):
            hdr = cd[p:p+46]
            flags = vz.u16(hdr, 8); method = vz.u16(hdr, 10)
            crc = vz.u32(hdr, 16); csize = vz.u32(hdr, 20); usize = vz.u32(hdr, 24)
            fnlen = vz.u16(hdr, 28); exlen = vz.u16(hdr, 30); comlen = vz.u16(hdr, 32)
            disk_start = vz.u16(hdr, 34); local_off = vz.u32(hdr, 42)
            name = vz.decode_name(cd[p+46:p+46+fnlen], flags, cd[p+46+fnlen:p+46+fnlen+exlen])
            ep = 0
            extra = cd[p+46+fnlen:p+46+fnlen+exlen]
            while ep + 4 <= len(extra):
                hid, hlen = vz.u16(extra, ep), vz.u16(extra, ep+2)
                if hid == 0x0001:
                    q = ep + 4
                    if usize == 0xFFFFFFFF: usize = vz.u64(extra, q); q += 8
                    if csize == 0xFFFFFFFF: csize = vz.u64(extra, q); q += 8
                    if local_off == 0xFFFFFFFF: local_off = vz.u64(extra, q); q += 8
                ep += 4 + hlen
            base = name.replace('\\', '/').split('/')[-1].lower()
            if base not in ALLOW or name.endswith('/'):
                p += 46 + fnlen + exlen + comlen
                continue
            if usize > MAX_TEXT_BYTES:
                raise RuntimeError(f'{name}: text entry too large ({usize})')
            risks = vz.path_risks(name)
            if risks:
                raise RuntimeError(f'{name}: unsafe path {risks}')
            abs_local = z.starts[disk_start] + local_off
            lfh = z.read(abs_local, 30)
            lfnlen = vz.u16(lfh, 26); lexlen = vz.u16(lfh, 28)
            data_off = abs_local + 30 + lfnlen + lexlen
            comp = z.read(data_off, csize)
            raw = zlib.decompress(comp, -15) if method == 8 else comp
            if (zlib.crc32(raw) & 0xFFFFFFFF) != crc or len(raw) != usize:
                raise RuntimeError(f'{name}: CRC/size mismatch')
            out_name = f'entry_{i+1:02d}_' + name.replace('\\', '/').split('/')[-1]
            out_path = os.path.join(ev_dir, out_name)
            with open(out_path, 'wb') as f:
                f.write(raw)
            extracted.append({
                'archive_path': name,
                'local_path': os.path.basename(out_path),
                'uncompressed_size': usize,
                'sha256': hashlib.sha256(raw).hexdigest(),
                'note': 'flash script - read as text only, NEVER executed' if base.startswith('flash_') else 'text document',
            })
            p += 46 + fnlen + exlen + comlen
    finally:
        z.close()
    manifest = {'extracted_count': len(extracted), 'files': extracted,
                'policy': 'allowlisted plain text only; no binaries; no execution'}
    with open(os.path.join(ev_dir, 'extraction_manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(json.dumps({'extracted': len(extracted)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
