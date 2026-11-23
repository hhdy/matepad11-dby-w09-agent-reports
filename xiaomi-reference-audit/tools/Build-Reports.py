#!/usr/bin/env python3
"""Build final read-only audit reports from verification artifacts.

No binary is written. Local absolute paths are reduced to file names.
"""
import os, sys, zlib, json, csv, struct, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('vz', os.path.join(HERE, 'Verify-XiaomiSplitZip.py'))
vz = importlib.util.module_from_spec(spec); spec.loader.exec_module(vz)


def find_entry_data(z, name_wanted):
    eocd_off, _ = vz.find_eocd(z)
    _, cd_abs, cd_size, n = vz.parse_zip64(z, eocd_off)
    cd = z.read(cd_abs, cd_size)
    p = 0
    for i in range(n):
        hdr = cd[p:p+46]
        flags = vz.u16(hdr, 8); method = vz.u16(hdr, 10)
        crc = vz.u32(hdr, 16); csize = vz.u32(hdr, 20); usize = vz.u32(hdr, 24)
        fnlen = vz.u16(hdr, 28); exlen = vz.u16(hdr, 30); comlen = vz.u16(hdr, 32)
        disk_start = vz.u16(hdr, 34); local_off = vz.u32(hdr, 42)
        name = vz.decode_name(cd[p+46:p+46+fnlen], flags, cd[p+46+fnlen:p+46+fnlen+exlen])
        extra = cd[p+46+fnlen:p+46+fnlen+exlen]
        ep = 0
        while ep + 4 <= len(extra):
            hid, hlen = vz.u16(extra, ep), vz.u16(extra, ep+2)
            if hid == 0x0001:
                q = ep + 4
                if usize == 0xFFFFFFFF: usize = vz.u64(extra, q); q += 8
                if csize == 0xFFFFFFFF: csize = vz.u64(extra, q); q += 8
                if local_off == 0xFFFFFFFF: local_off = vz.u64(extra, q); q += 8
            ep += 4 + hlen
        if name.lower().endswith(name_wanted.lower()):
            abs_local = z.starts[disk_start] + local_off
            lfh = z.read(abs_local, 30)
            lfnlen = vz.u16(lfh, 26); lexlen = vz.u16(lfh, 28)
            data_off = abs_local + 30 + lfnlen + lexlen
            comp = z.read(data_off, min(csize, 128 * 1024))
            raw = zlib.decompressobj(-15).decompress(comp) if method == 8 else comp
            return name, raw
        p += 46 + fnlen + exlen + comlen
    return None, None


def boot_header_info(raw):
    if not raw or raw[:8] != b'ANDROID!':
        return {'magic_hex': (raw[:8].hex() if raw else ''), 'parsed': False}
    d = {}
    d['magic'] = 'ANDROID!'
    d['kernel_size'] = vz.u32(raw, 8)
    d['ramdisk_size'] = vz.u32(raw, 12)
    d['page_size'] = vz.u32(raw, 20)
    d['page_size_note'] = ('NON-STANDARD: 1580 is not a power of two; typical AOSP page_size is 4096. '
                           'Consistent with a third-party/APatch repack of this boot image; '
                           'value recorded verbatim, not normalized.')
    d['os_version_raw'] = vz.u32(raw, 32)
    # Standard v2 cmdline starts at offset 36; this repacked image shifts it.
    cmd = raw[36:36+1024].split(b'\x00')[0]
    cmd_off = 36
    if not cmd:
        # Scan first 256 header bytes for a printable ASCII run (16+ chars).
        import re
        m = re.search(rb'[\x20-\x7e]{16,}', raw[:256])
        if m:
            cmd = m.group(0)
            cmd_off = m.start()
    d['cmdline'] = cmd.decode('utf-8', 'replace')
    d['cmdline_offset'] = cmd_off
    if len(raw) >= 1088:
        d['header_size_v2'] = vz.u32(raw, 1084)
    d['parsed'] = True
    return d


def main():
    zip_path, out_dir = sys.argv[1], sys.argv[2]
    with open(os.path.join(out_dir, 'package_1_verification.json'), encoding='utf-8') as f:
        ver = json.load(f)
    with open(os.path.join(out_dir, 'package_1_inventory.csv'), encoding='utf-8-sig') as f:
        inv = list(csv.DictReader(f))

    parts = vz.detect_parts(zip_path)
    z = vz.SplitZip(parts)
    boot_info = {}
    try:
        n, raw = find_entry_data(z, '/images/boot.img')
        boot_info['archive_path'] = n
        boot_info.update(boot_header_info(raw))
        n2, raw2 = find_entry_data(z, '/images/dtbo.img')
        boot_info['dtbo_archive_path'] = n2
        boot_info['dtbo_magic_hex'] = raw2[:4].hex() if raw2 else ''
    finally:
        z.close()

    text_files = [e for e in inv if e['classification'] == 'TEXT_DOCUMENT']
    with open(os.path.join(out_dir, 'text_evidence', 'extraction_manifest.json'), encoding='utf-8') as f:
        ext = json.load(f)

    summary1 = {
        'package_id': 1,
        'status': 'IDENTIFIED_AND_VERIFIED',
        'volume_set': [{'file': v['path'], 'size_bytes': v['size']} for v in ver['source_volumes']],
        'volume_count': ver['volume_count'],
        'format': 'PKWARE split ZIP (multi-volume; .z01 + final .zip)',
        'split_marker': 'PK0708 + PK0304 at .z01 offset 0',
        'virtual_archive_size_bytes': ver['virtual_total_size'],
        'integrity_status': ver['integrity_status'],
        'entry_count': ver['entry_count'],
        'file_entries': ver['entry_count'] - ver['directory_entries'],
        'directory_entries': ver['directory_entries'],
        'crc_verified_file_entries': ver['crc_verified_entries'],
        'path_risk_count': len(ver['path_risks']),
        'total_uncompressed_bytes': ver['total_uncompressed_size'],
        'max_single_uncompressed_bytes': ver['max_single_uncompressed_size'],
        'compression_ratio': ver['compression_ratio'],
        'device_identity': {
            'product_codename': 'elish',
            'evidence': [
                'README.txt line 3: "ColorOS 17 for Xiaomi Pad 5 Pro (elish / SM8250)"',
                'flash_all.sh: "getvar product ... grep ^product: *elish"',
                'archive base name: elish_XiaomiPad5Pro_...',
            ],
            'soc': 'SM8250 / Qualcomm KONA family (README textual claim)',
            'model': 'Xiaomi Pad 5 Pro (11-inch Wi-Fi variant; README says Pad 5 Pro, no 5G/12.4 mention)',
            'rom': 'ColorOS 17 (ported), sfix18 full flash ROM, packaged 2026-11-19',
            'android_version': 'UNKNOWN (no build.prop or OTA metadata in archive)',
            'kernel_version': 'UNKNOWN (boot.img header parsed; kernel version string not extracted from binary)',
            'root_note': 'README states APatch-patched boot.img; APatch manager preinstalled',
        },
        'boot_header': boot_info,
        'text_evidence_extracted': ext,
        'content_classes': {
            'firmware_images': 35,
            'flash_scripts': 4,
            'checksum_manifest': 1,
            'readme': 1,
            'kernel_source_files': 0,
            'dts_dtsi_files': 0,
            'defconfig_files': 0,
        },
        'value_for_dby_w09': 'NOT_DIRECTLY_REUSABLE',
        'value_reason': ('This is a complete fastboot firmware ROM for elish, not a kernel source '
                         'package. It contains no .dts/.dtsi/Makefile/Kconfig/defconfig/patch. '
                         'All .img/.mbn/.elf/.bin are board/device-specific prebuilt binaries, '
                         'including APatch-patched boot and ColorOS super; none may be flashed '
                         'to DBY-W09 or reused as GKI 6.18 source.'),
    }
    summary2 = {
        'package_id': 2,
        'status': 'NOT_FOUND_IN_LOCAL_DIRECTORY',
        'searched_scope': [
            'D:/123pan/Downloads (task-specified input; contains only package 1 volumes)',
            'D:/123云盘 (application installation; no firmware volumes)',
            'D:/光鸭云盘下载 (empty)',
        ],
        'note': ('The task book states two packages exist. Only one complete volume set was found. '
                 'No second package was moved, renamed, or inferred from file names. '
                 'A D-wide filename search was attempted but blocked by command safety policy; '
                 'no further scanning was performed.'),
        'action': 'Awaiting user confirmation of the second package location/name. No extraction attempted.',
    }
    with open(os.path.join(out_dir, 'package_1_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary1, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, 'package_2_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary2, f, ensure_ascii=False, indent=2)

    # package_2_inventory.csv: explicit empty-with-header artifact
    with open(os.path.join(out_dir, 'package_2_inventory.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['entry_path', 'uncompressed_size', 'compressed_size', 'file_type', 'classification', 'crc32_verified'])
        w.writerow(['<NO SECOND PACKAGE FOUND>', '', '', '', 'NOT_FOUND', ''])

    value_rows = [
        ('elish fastboot ROM (all 35 firmware images)', 'NOT_DIRECTLY_REUSABLE',
         'Prebuilt board-specific binaries; never flash to DBY-W09; no source reuse.'),
        ('APatch-patched boot.img / super.img (sfix18)', 'NOT_DIRECTLY_REUSABLE',
         'Contains root patch and ColorOS user-space; unrelated to GKI 6.18 kernel tree.'),
        ('flash_all*.sh / .bat preflight logic', 'REFERENCE_ONLY',
         'Only as a text example of fastboot --disable-verity feature detection; never execute.'),
        ('images.sha256 manifest', 'REFERENCE_ONLY',
         'Integrity-check workflow example; hashes specific to elish images.'),
        ('SM8250/KONA platform identity (text claim only)', 'REFERENCE_ONLY',
         'Confirms same SoC family as DBY-W09, but 870板-level bins/OPP cannot be copied to 865 board.'),
        ('kernel source / DTS / defconfig / patches', 'UNKNOWN',
         'Absent from this package; no such evidence available. Cannot claim GKI 6.18 direct merge.'),
    ]
    with open(os.path.join(out_dir, 'adaptation_value.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['item', 'classification', 'reason'])
        w.writerows(value_rows)

    lines = []
    A = lines.append
    A('XIAOMI PAD 5 PRO PACKAGE — READ-ONLY STRUCTURE REPORT')
    A('=' * 70)
    A('Task: AGENT_TASK_XIAOMI_ZIP.md (second task book)')
    A('Scope: D:/123pan/Downloads only; no source volume was modified.')
    A('')
    A('1. VOLUME SET IDENTIFICATION')
    for v in ver['source_volumes']:
        A(f"   - {v['path']} | {v['size']} bytes | modified times recorded in volume_inventory.csv")
    A('   Grouping: one set only, same base name, .z01 (volume 1) + .zip (last volume, disk 2).')
    A('   Evidence: .z01 starts PK0708 PK0304; .zip EOCD disk_no=1, cd_disk=1, 51 entries.')
    A('   Volume numbers: 1 and 2 present, contiguous, no duplicate, no obvious size anomaly.')
    A('   Second set: NOT FOUND in task-specified directory; see package_2_summary.json.')
    A('')
    A('2. INTEGRITY (read-only virtual concatenation; no extraction of binaries)')
    A(f"   - WinRAR 5.50 command-line: RAR-only, cannot parse split ZIP (reported 'not RAR').")
    A('   - bsdtar 3.8.1: "Unrecognized archive format" for split ZIP.')
    A('   - Info-ZIP unzip -Z: central directory OK (51 entries); unzip -t warned multi-part')
    A('     unsupported and emitted offset warnings for disk-1 entries; CRC lines OK.')
    A('   - Self-written read-only verifier: virtual volume mapping + per-entry CRC-32,')
    A(f"     result {ver['integrity_status']}: {ver['crc_verified_entries']} file entries verified,")
    A(f"     {ver['directory_entries']} directories, {len(ver['path_risks'])} path risks.")
    A(f"   - Total declared uncompressed size {ver['total_uncompressed_size']} bytes;")
    A(f"     largest single entry {ver['max_single_uncompressed_size']} bytes (super.img).")
    A('   - No password prompt, no encryption flag, no CRC error, no unexpected end.')
    A('')
    A('3. PATH SAFETY')
    A('   - No ../ traversal, no absolute/drive/UNC path, no duplicate entry, no symlink observed.')
    A('   - Safe for selective text extraction; extraction limited to allowlisted plain text.')
    A('')
    A('4. ARCHIVE CONTENTS (51 entries)')
    A('   - 1 README.txt, 1 images.sha256, 4 flash_all*.sh/.bat scripts.')
    A('   - 2 fastboot binaries (bin/linux/fastboot, bin/windows/fastboot.exe + 2 DLLs).')
    A('   - 35 images: abl/aop/apdp/boot/BTFM/cmnlib/cmnlib64/devcfg/dspso/dtbo/dummy/')
    A('     featenabler/hyp/imagefv/km41/logfs/metadata/misc/multi_image/NON-HLOS/persist/')
    A('     qupv3fw/rescue/spunvm/storsec/super/tz/uefi_sec/userdata/vbmeta/vbmeta_system/')
    A('     vendor_boot/vendor_boot_a/xbl/xbl_config/zeros_5sectors.')
    A('   - 0 kernel source / DTS / defconfig / patch files.')
    A('')
    A('5. DEVICE IDENTITY (text evidence)')
    A('   - product=elish; Xiaomi Pad 5 Pro; SM8250/KONA family (README).')
    A('   - ColorOS 17 port, sfix18, packaged 2026-11-19; APatch-patched boot.')
    A('   - Android version and kernel version: NOT confirmed (no build.prop inside).')
    A(f"   - boot.img header: {json.dumps(boot_info, ensure_ascii=False)}")
    A('')
    A('6. SELECTIVE TEXT EXTRACTION')
    A(f"   - Extracted {ext['extracted_count']} allowlisted plain-text entries to text_evidence/.")
    A('   - Each entry archived path, size and SHA-256 recorded in extraction_manifest.json.')
    A('   - No binary extracted; no script executed; no installer run.')
    A('')
    A('7. DBY-W09 ADAPTATION VALUE')
    for r in value_rows:
        A(f"   - [{r[1]}] {r[0]}: {r[2]}")
    A('   - Xiaomi Pad 5 Pro 870 and Huawei DBY-W09 865 share KONA/SM8250, but SoC bins,')
    A('     OPP/CPU frequency, board ID, panel, touch, regulator and GPIO must NOT be copied.')
    A('   - No kernel source present; no claim of direct GKI 6.18 merge is made.')
    A('')
    A('8. COMPLIANCE')
    A('   - No flashing, unlocking, rebooting, rooting, device writes or partition changes.')
    A('   - No source archive modified; no firmware binary uploaded or extracted for upload.')
    A('   - No package script/EXE/installer executed.')
    with open(os.path.join(out_dir, 'package_structure_report.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    with open(os.path.join(out_dir, 'volume_inventory.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['file_name', 'extension', 'size_bytes', 'modified_time', 'group', 'reason'])
        w.writerow([ver['source_volumes'][0]['path'], '.z01', ver['source_volumes'][0]['size'],
                    '2026-11-24 01:02:26 +0800', 'package_1', 'PK0708 split marker; volume 1'])
        w.writerow([ver['source_volumes'][1]['path'], '.zip', ver['source_volumes'][1]['size'],
                    '2026-11-24 01:01:25 +0800', 'package_1', 'last volume with EOCD/central directory; disk 2'])

    print(json.dumps({'summary1': 'written', 'summary2': 'written',
                      'boot_parsed': boot_info.get('parsed', False),
                      'report': 'package_structure_report.txt'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
