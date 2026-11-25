# HOS4.3 firmware evidence — DBY-W09 (MatePad 11 2021, KONA / SM8250)

Collected under task **HOS43-UPLOAD-01** by the Local Agent. Purpose: give the
Second AI direct GitHub access to first-hand HOS4.3 firmware evidence for the
Linux 6.18.33 ACK port, specifically the Stage A Phase E/F open items.

## Provenance
- Source: a locally extracted HarmonyOS 4.3 OTA package for DBY-W09 (GMS variant).
  The vendor `说明.txt` states "Harmony OS 4.3 / DBY-W09 / GMS".
- The original directory held 45 files: 43 partition images under `images/`,
  one ~6.7 GiB vendor ZIP, and `说明.txt`.
- All uploaded images are **byte-identical copies**. SHA-256 of every source
  file was computed locally and recorded in `SHA256SUMS.txt` and
  `inventory/full-file-inventory.csv`. No image was split, compressed,
  re-packed or modified.

## What is here
- `boot/` — ramdisk images (header-v0) and recovery ramdisk
- `dtbo/` — original `dtbo.img` (AOSP dt_table, 9 entries)
- `avb/` — vbmeta chain images (vbmeta, cust, hw_product, odm, system, vendor)
- `bootloader/` — XBL/XBL_CONFIG/AOP/HYP/TZ/DEVCFG/QUFW/UEFISECAPP/... ELF images
- `other-hardware/` — small ancillary partition images + source `说明.txt`
- `inventory/` — full inventory, large-file list, skipped-file list
- `MANIFEST.csv` — repo path → source relative path → size → SHA-256
- `SHA256SUMS.txt` — SHA-256 of every uploaded byte-identical file
- `HOS43_UPLOAD_REPORT.md` — full analysis and boundary statement

Directories `dtb/`, `kernel/`, `modules/`, `ufs/`, `pmic-rpmh/`, `memory/`,
`init-fstab/` are intentionally empty at the partition level: this OTA ships
no standalone `.dtb`/`.dts`, kernel `Image`, `System.map` or `.ko` images.
Those artifacts live inside `super.img` and `boot.img` (see the report).

## Size policy
GitHub Contents API rejects large base64 payloads (a 96 MiB image returned
HTTP 422 "file too large"). Files above a 60 MiB raw threshold are NOT
uploaded; their path, size and SHA-256 are recorded in
`inventory/large-files.csv`. The largest omitted files are `super.img`
(6.6 GiB, system/vendor/odm/product), the vendor ZIP (6.7 GiB),
`boot.img`/`recovery.img`/`erecovery.img` (96 MiB each), and `dsp.img` (64 MiB).

## Boundaries
- Read-only analysis. No device, ADB, fastboot, flashing, unlock or root.
- No claim that any DTBO entry is the one ABL selects at runtime.
- No inference of physical RAM/reserved-memory addresses or PMIC input rails.
- No HOS4.2 data substituted for HOS4.3 evidence.
- Firmware filenames alone do not prove which file HOS4.3 actually boots.
