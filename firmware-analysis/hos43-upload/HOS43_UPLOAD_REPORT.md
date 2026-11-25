# HOS43_UPLOAD_REPORT — HOS4.3 firmware evidence collection

Task: **HOS43-UPLOAD-01** · Role: Local Agent · Mode: read-only analysis,
file selection, byte-identical staging, GitHub upload. No device access.

## 1. Source directory overview
- Root: `D:\解锁bl\鸿蒙4.3\` (local, already extracted; NOT re-extracted here).
- Contents: `DBY_W09_HarmonyOS_4.3_GMS_By_WQSQW-dc2605192e6e.zip` (7,229,903,744 B),
  `images/` (43 partition images), `说明.txt` (411 B).
- `说明.txt` (paraphrased, vendor text): Harmony OS 4.3, model DBY-W09, GMS
  variant, author credit, flash-via-toolbox instructions. It is a consumer
  firmware package, not a developer build.
- All 45 files were hashed; full list and byte sizes in
  `inventory/full-file-inventory.csv`.

## 2. Selected file count and total size
- Total source files scanned: **45**.
- Uploaded (byte-identical): **33 files**, 262,689,179 B (250.5 MiB).
- Recorded-but-not-uploaded (large): **12 files** (see §5).
- Sensitive-partition files present in source: **0** (no persist/modemst/fsg/
  fsc/oeminfo/userdata/frp/metadata images in this package).

## 3. Uploaded files
See `MANIFEST.csv` (repo path, source path, size, SHA-256) and
`SHA256SUMS.txt`. Groups: boot/ramdisk (3), dtbo (1), vbmeta/AVB (8),
bootloader ELF (11), other-hardware (10 incl. `说明.txt`).

## 4. Not uploaded and why
12 files exceed the 60 MiB raw threshold imposed by the GitHub Contents API
(base64 transport expands the request by ~33%; a 96 MiB test upload returned
HTTP 422 "file too large"). Git-over-HTTPS from this host failed at the TLS
layer, so no Git-LFS/large-blob path was available. Per the taskbook, large
files were **not split, compressed or repacked**; they are fully recorded by
path/size/SHA-256 in `inventory/large-files.csv`.

## 5. Large-file list with SHA-256
Full machine-readable list: `inventory/large-files.csv`. Highlights:

| File | Size (MiB) | SHA-256 |
|---|---:|---|
| images/super.img | 6785.1 | D6EF478D5BBACBF95281D8CC7E4FEEA9AF46DA278A5EA256F778F2DF87A5226B |
| vendor ZIP | 6895.0 | 190518AA733A94B45A0B212D8069F6373F03C2B6C9FAD0E4CCB861FD9E304856 |
| images/preload.img | 1400.0 | 36F9E88F4629C9958ED5460FC0170E7DE0905B74B02776548F731DBA467B100A |
| images/version.img | 576.0 | 09F4F1A315748E926C581BB8FA5031F3221773C2FF89CB60BC79D9DDDE06616E |
| images/preas.img | 296.0 | C7EF003A5CE5CF8E864CF5B04152C61F47A04D9ABAFA9C87E9C90A9ABD7C7D88 |
| images/patch.img | 256.0 | FF6813AE3FF689AB8F25D34D70166BEF029C2F0715F2C3849A1B8A59A9A969D1 |
| images/modem.img | 188.0 | 6F13F4CFA50AA5DEC4D65CF504DED5659C9DA22F6E27EE62793346A592E3AE25 |
| images/cache.img | 104.0 | 8A4818CAEA227625C29855C13411B73D35D639054B0CF8EE98DF7D832BA65FA0 |
| images/boot.img | 96.0 | 027F88FD6F318523925CA27A4D681D17A9BBCA904B0C471CCC05E651D3DA19B8 |
| images/recovery.img | 96.0 | 956417584D2DEB409761316F262732859E356A15CB5FE85436DF3D5F141C5548 |
| images/erecovery.img | 96.0 | 956417584D2DEB409761316F262732859E356A15CB5FE85436DF3D5F141C5548 |
| images/dsp.img | 64.0 | D1C54E38BF972FA502C097F9D67BF36710E816F214DCB9B2C0F8D261969DF286 |

Note: `recovery.img` and `erecovery.img` have identical SHA-256 — a real
fact of this package, not a copy error.

## 6. DTB / DTBO identification
- No standalone `*.dtb`, `*.dtbo`, `*.dts`, `*.dtso` at the partition-image
  level. Device trees are inside `boot.img` (header-v2 dtb field) and
  `dtbo.img`.
- `dtbo.img` (25,165,824 B, SHA-256 51A5D7B8…): classic AOSP `dt_table_header`
  magic `0xd7b7ab1e`, total_size 2,963,810 B, header_size 32, dt_entry_size 32,
  **dt_entry_count 9**, dt_entries_offset 32, **page_size 4096**, version 0.
- Nine DT table entries were parsed; `id=0x00000000`, `rev=0x00000000`,
  `custom=all-zero` for every entry. Per-taskbook, these are recorded as
  observed; no inference that HOS4.3 ABL selects any entry. Board identity
  (`DBY_W09_VG`, board-id 0x206a, etc.) lives inside each overlay DTB's
  `/rootparam`, not in the dt_table_entry metadata — consistent with
  ROUND19/23 findings. The decompiled per-entry DTS already exists in
  ROUND19 work copies; not re-extracted here.

## 7. Boot-chain file identification
- `boot.img` / `recovery.img` / `erecovery.img`: magic `ANDROID!`, **header v2**
  (header_version at 0x28 = 2), page_size 4096, os_version 0x02000000,
  kernel_size ≈ 22.26 MB, ramdisk_size 32768 B (tiny, consistent with a
  separate `ramdisk.img`). Not uploaded (96 MiB each).
- `ramdisk.img`: magic `ANDROID!`, **header v0**, page_size 2048. Uploaded.
- `vendor_boot.img` / `init_boot.img`: **absent** in this package.
- Bootloader/ELF images (first bytes `7f 45 4c 46` = ELF):
  `xbl.img`, `xbl_config.img`, `aop.img`, `hyp.img`, `tz.img`, `devcfg.img`,
  `qupfw.img`, `uefisecapp.img`, `storsec.img`, `keymaster.img` — all uploaded.
  These are XBL/XBL_CONFIG/AOP/HYP/TZ/DEVCFG/QUPFW/UEFISECAPP/STORSEC/KEYMASTER,
  relevant to FDT handoff and memory init. `bluetooth.img` starts with an FAT
  boot sector (`eb 3c 90 4d 53 44 4f 53`), not ELF.

## 8. UFS / PM8150 / RPMh / MMCX / MX / AUX evidence
- No standalone text config for UFS/PMIC/RPMh exists at the partition level in
  this OTA; those live inside `super.img` (vendor/odm) and the kernel in
  `boot.img`. Neither is safely uploadable here (super.img 6.6 GiB; boot.img
  96 MiB API-rejected), and this task explicitly forbids unpacking/repacking.
- Therefore: **no new HOS4.3 UFS/PMIC text evidence was added by this upload**.
  Existing evidence remains the ROUND11/13/14/18/22/51/64 reports (already on
  `firmware-audit-v1`). `说明.txt` and partition names contain no such content.
- Status: UFS/PHY/RPMh/MMCX remain covered by prior reports; this collection
  provides the raw `super.img`/`boot.img` SHA-256 for provenance only.

## 9. Memory and reserved-memory evidence
- The HOS4.3 base FDT (`/reserved-memory`, 37 direct children by current
  decompilation) and `/memory` analysis come from ROUND19/20/24, already
  uploaded. This OTA adds no standalone memory-layout text file.
- `super.img`/`boot.img` are recorded by hash only. No physical RAM address,
  carveout range or PMIC rail was inferred in this task.

## 10. AVB and partition information
- 8 vbmeta images collected: `vbmeta`, `vbmeta_cust`, `vbmeta_hw_product`,
  `vbmeta_odm`, `vbmeta_system`, `vbmeta_vendor`, `recovery_vbmeta`,
  `erecovery_vbmeta` (all 1 MiB). Byte-identical, SHA-256 in `SHA256SUMS.txt`.
- AVB footer magic `AVBf` was detected at EOF in `boot.img`, `dtbo.img`,
  `recovery.img`, `vbmeta_cust.img`. The footer layout in this HOS image is
  Huawei-customized: standard AOSP field offsets yield implausible values, so
  this report records only the **presence** of the magic and does not decode
  offsets/sizes or publish any key/signature/salt/digest/rollback data.
  Detailed AVB parsing remains in ROUND19/64 reports.
- 43 partition names are enumerated in `inventory/full-file-inventory.csv`.

## 11. Still-unconfirmed items
- Which DTBO entry HOS4.3 ABL selects at runtime (0x206a is one candidate).
- Whether ABL injects `/memory` or `/reserved-memory` into the final FDT;
  no final post-ABL FDT is available. Classic-FDT vs EFI-stub path remains
  UNKNOWN (ROUND20/42/43).
- UFS/PHY/RPMh/PMIC electrical input topology: prior reports mark these
  BLOCKED; no new evidence here.
- `boot.img`/`super.img` raw bytes are not on GitHub due to size; a Second AI
  needing them must obtain the original package out of band. Their SHA-256
  values here allow verification.

## 12. Cross-reference to existing reports
- Compared against reports present on `firmware-audit-v1`: ROUND64 (final
  memory/PMIC inputs; bootv2/ramdisk/DTBO/AVB) and ROUND65 (first-stage fstab;
  vbmeta_cust anomaly; boot-tool contract). This upload's DTBO table layout,
  boot header v2, vbmeta_cust AVB footer presence and reserved-memory pointers
  are consistent with those reports.
- ROUND70 / ROUND74 / ROUND75 referenced in the taskbook are **not present**
  on `firmware-audit-v1` at the time of collection (branch contains rounds
  1–21, 61, 64, 65 only). No comparison was fabricated for missing reports.

## 13. Branch, commit and links
- Branch: `hos43-firmware-evidence` (created from `main` @ 6de45832af030f38339b6273ea8506c9181e84f9).
- Final HEAD commit (after all uploads): `dd9fafebe77206c3b6400e4bdd505841f52a02c6`.
  Tree: `35a9aff34d3fc2abc8b99087de1808dd9b8e8256`.
- 40 new commits on this branch (7 documents + 33 images); each file was
  uploaded byte-identically and its SHA-256 re-verified by raw GET readback
  (33/33 match, 0 failures).
- Report path on branch: `firmware-analysis/hos43-upload/HOS43_UPLOAD_REPORT.md`.
- Per-file links: `https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/hos43-firmware-evidence/firmware-analysis/hos43-upload/<path>`

## Boundaries
Read-only; no device/ADB/fastboot/flash; no repacking; no HOS4.2 substitution;
no address/rail inference; no claim of runtime DTBO selection. All uploads are
byte-identical and SHA-256 verified.
