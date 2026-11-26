# ROUND155 — WorkBuddy Window A: Read-only boot-chain partition capture

Executor: WorkBuddy Window A (1号 Agent). Window B is a separate WorkBuddy chat window and was not accessed.

Taskbook: `WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE_TASKBOOK.md`
Start prompt: `START_PROMPT_WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE.md`

**Status: completed and stopped at the report point.** No flash, write, erase, format, reboot, fastboot, recovery entry, mount/unmount, remount, SELinux/property change, temporary boot, bootloader unlock/lock, personal-data partition read, or full-UFS dump was performed. No raw binary, full host path, private log, serial/IMEI/MAC/panel ID, or user data is included in this report.

---

## 1. Executive summary

| Item | Result | Evidence |
|---|---|---|
| Root gate (once, `su -c id`) | **PASS** | `uid=0(root) gid=0(root) groups=0(root) context=u:r:ksu:s0` |
| by-name discovery (no assumed path) | **PASS** | 2 directories, 86 unique names, 86 unique block nodes, **0 alias groups** |
| Targets present | **18 / 18** | no `_a`/`_b` variants (A-only layout; `ro.boot.slot_suffix` empty) |
| Byte count == `blockdev --getsize64` | **PASS 18/18** | re-checked immediately before each read |
| Host SHA-256 == independent device-side SHA-256 (second read) | **PASS 18/18** | streaming `sha256sum` on device |
| Local readback SHA-256 | **PASS 18/18** | primary copy re-read |
| Second host location (10 required targets) | **PASS 10/10** | distinct host volume, copied then hashed |
| ABL/XBL static attribution | **PASS (code-level)** | LZMA payload decompressed; ADRP/ADD xrefs to selector and `/memory` updater |
| AVB chain | **PASS** | official `avbtool` 1.3.0 (AOSP source, host-only, read-only `info_image`) |
| `vbmeta_cust` anomaly on live copy | **CONFIRMED** | empty auth block, `Algorithm: NONE`, no descriptors, footer points past partition |
| Stop conditions | **NONE TRIGGERED** | no hash mismatch, no byte mismatch, no capacity change, no read error |

**Headline result:** the two blockers left open by ROUND153/ROUND154 — (a) who selects the DTBO entry and (b) who mutates the RAM map — now have direct code-reference evidence in the *live* ABL. The selector is in ABL, and ABL contains an explicit `/memory` node updater writing `ddr_device_type`, `ddr_device_rank_ch%d`, and `ddr_device_hbb_ch%d_rank%d`. The exact run-time input value that chose entry 2 is still not recovered (no ABL log was captured), but the mechanism is no longer "unknown layer".

---

## 2. Preflight and device identity

All device interaction used `adb exec-out su -c '<cmd>'` (byte-exact stdout; no CRLF translation), the same root method verified in ROUND151.

| Check | Value |
|---|---|
| ADB binary | pre-existing `D:\Tools\platform-tools\adb.exe`, version 1.0.41 / 37.0.3-16887417 |
| Device state | `device` (one device, transport stable) |
| `ro.product.model` / `name` / `device` | `DBY-W09` / `DBY-W09` / `HWDBY` |
| `ro.boot.slot_suffix` | empty (A-only layout; no `_a`/`_b` partition names in by-name) |
| `ro.build.version.release` | 12 |
| Root tools | `/system/bin/{blockdev,readlink,stat,dd,sha256sum}` all present |
| by-name directory 1 | `/dev/block/by-name` (86 entries) |
| by-name directory 2 | `/dev/block/platform/soc/1d84000.ufshc/by-name` (80 entries) |
| Alias check | across both directories: 86 names → 86 distinct block nodes; **no name pair resolves to the same node**, so every target was read exactly once |

Target selection used a whitelist of the taskbook stems (`abl`, `xbl`, `xbl_config`, `boot`, `dtbo`, `vbmeta*`, `ramdisk`, `recovery`, `erecovery`) plus every recovery-related alias found in the listing. No userdata/persist/metadata/frp/devinfo/modem/keystore partition was read; no full-device dump was made.

---

## 3. Partition inventory and capture verification

### 3.1 Method (taskbook §4)

1. `readlink -f <by-name>/<name>` → resolved block node; confirmed `/dev/block/*` + `stat -L` = `block device`, mode 600, owner root:root.
2. `blockdev --getsize64 <node>` recorded, then re-read immediately before the copy as a capacity-change gate.
3. `adb exec-out su -c 'dd if=<node> bs=4M status=none'` → host file, **no `of=` on the device**, no staging on tablet storage.
4. Received byte count compared to the declared partition size (exact equality required).
5. Host-side SHA-256; independent **device-side streaming SHA-256 in a second read pass** (`sha256sum <node>`); equality required.
6. Primary copy re-read and hashed again.
7. For `boot`, `dtbo`, all present root/child vbmeta, `recovery`, `erecovery`: a second copy on a different host volume, copied and hashed.

**Deviation from the taskbook's example command (recorded, not hidden):** the example included `iflag=fullblock`. Device Toybox is `0.8.4-android` and its `dd` accepts only `count_bytes` / `skip_bytes` as `iflag` values; `iflag=fullblock` returned the literal error `dd: bad iflag=fullblock` (24 bytes). The command was changed to `dd if=<node> bs=4M status=none`. **No gate was relaxed**: exact byte count and both independent hashes remained mandatory, and a trial run on `abl` was used to prove the flow before the full run.

### 3.2 Verified targets

Every row below passed: byte count == size, host hash == device hash (second pass), primary readback hash == host hash.

| Partition | Block node | Bytes | SHA-256 (verified, both reads) | 2nd location |
|---|---|---:|---|---|
| `abl` | sde6 | 4 194 304 | `b39de91b88ef13db83892cd2e8dc4b914f7f9ed86954039fb1f64fbbf8460011` | n/a |
| `boot` | sde9 | 100 663 296 | `7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8` | yes |
| `dtbo` | sde13 | 25 165 824 | `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c` | yes |
| `erecovery` | sda16 | 100 663 296 | `956417584d2deb409761316f262732859e356a15cb5fe85436df3d5f141c5548` | yes |
| `erecovery_ramdisk` | sda17 | 37 748 736 | `b6fa03712bc979964f6f1a703a841a201e6116edfe80e994b280ab7b62ab2295` | n/a |
| `erecovery_vbmeta` | sda23 | 1 048 576 | `ed04c8480c9b9438445c03179e16012aefa69b4169a194a82e260b246a65c73f` | yes |
| `erecovery_vendor` | sda18 | 25 165 824 | `6b3e7ed5c6146496a0d7a2de9182f3731ee4840de579e0e53f29c36426241551` | n/a |
| `ramdisk` | sda22 | 2 097 152 | `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb` | n/a |
| `recovery` | sda19 | 100 663 296 | `956417584d2deb409761316f262732859e356a15cb5fe85436df3d5f141c5548` | yes |
| `recovery_ramdisk` | sda20 | 37 748 736 | `b6fa03712bc979964f6f1a703a841a201e6116edfe80e994b280ab7b62ab2295` | n/a |
| `recovery_vbmeta` | sda24 | 1 048 576 | `bf59d55d664b9f6295273b10701845b9e4e3f184b6e7c5140f29681d1c5b507b` | yes |
| `recovery_vendor` | sda21 | 25 165 824 | `6b3e7ed5c6146496a0d7a2de9182f3731ee4840de579e0e53f29c36426241551` | n/a |
| `vbmeta` | sde12 | 1 048 576 | `e9b6e8ac9dbcc31ce30234f2cb8ab129c7b2912c7531caef70ea2a2547a2741d` | yes |
| `vbmeta_cust` | sda28 | 1 048 576 | `eb517a9776581677d6550d35689301b19c8a528fb9c8070d0180c9d8d3fe511f` | yes |
| `vbmeta_system` | sda25 | 1 048 576 | `8cf59433d16973adf542ec570c1656a773cdf77a0efb82f6544a7ce9fa735bf6` | yes |
| `vbmeta_vendor` | sda26 | 1 048 576 | `375ec9c09cc829736359b86b2b09179b46995fba68a661d0cbf2e11df6c61a0a` | yes |
| `xbl` | sdb1 | 4 018 176 | `7819d2af26438a817600080dc2340006fd3b9a5b6ea7a60509f3faf2e5d201c2` | n/a |
| `xbl_config` | sdb2 | 4 325 376 | `5c63be1b477669a4f693dd98ad31954884a0907ebf1ae94b5c4a36ef9a34aa5c` | n/a |

Notable identity pairs: `recovery` == `erecovery` (same bytes and hash), `recovery_ramdisk` == `erecovery_ramdisk`, `recovery_vendor` == `erecovery_vendor`; the two recovery vbmeta images differ. These are recorded as observed facts, not inferred aliases (the block nodes are distinct).

---

## 4. ABL / XBL static analysis (offline, exact copies only)

### 4.1 Container formats

| Image | Format | Key facts |
|---|---|---|
| `abl` | ELF **32-bit ARM**, EXEC, statically linked, no section headers | entry `0x9fa00000`; one `LOAD` @ file `0x3000`, vaddr `0x9fa00000`, filesz/memsz `0x90000`, RWE, align 0x1000 |
| `xbl` | ELF **64-bit AArch64**, EXEC, no section headers | entry `0x148157a8`; 15 `LOAD` segments; `QC_IMAGE_VERSION_STRING=BOOT.XF.3.2-00363-SM8250-1` |
| `xbl_config` | ELF **64-bit ARM**, EXEC, no section headers | entry `0x148d0000`; 4 `LOAD` segments |

`abl` contains exactly one `_FVH` at file offset `0x3028`. The FV uses the Qualcomm-shifted header variant (signature at `+0x28`, attributes `0x3feff`, header length `0x48`, block map 1152 × 512 = `0x90000`), GUID `8c8ce578-8a3d-4f1c-9935-896185c32dd3`. One FFS file: GUID `9e21fd93-9c72-4c15-8c4b-e77f1db2d792`, type `0x0b`, size `0x62359`; the remainder of the FV is `0xff` padding.

### 4.2 Why the first strings pass found nothing — and the decompression

A direct `strings` pass over the outer `abl` image gave **0 hits** for `dtbo`, `fdt`, `board-id`, `msm-id`, `rootparam`, `memory`, `slot`. A negative conclusion at that point would have been wrong.

The single FFS file contains a GUID-defined section (type `0x02`) with extraction GUID `ee4e5898-3914-4259-9d6e-dc7bd79403cf` (LZMA), data offset `0x18`, declared uncompressed size `2 597 064`. Decompressing that payload locally produced a **PE32+ AArch64** image (machine `0xaa64`, imagebase `0`, sections `.text` RVA/raw `0x1000` size `0x108000`, `.data` `0x109000`, `.reloc` `0x277000`), sha256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`. MZ at `0xb8`, PE at `0xf10`. All subsequent ABL findings come from this decompressed, hash-identified payload.

### 4.3 Selector and RAM fixup: strings and code references

Decompressed ABL strings (counts): `dtbo` 38, `fdt` 38, `dtb` 77, `board-id` 7, `boardid` 13, `msm-id` 5, `fixup` 8, `slot` 89, `qcom` 123, `memory` 102, `chosen` 8, `reserved-memory` 3.

Directly relevant message/format strings include:

- selection: `qcom,board-id`, `qcom,msm-id`, `qcom,pmic-id`, `Best match DTB tags ...`, `Delete don't fit DTB entry ...`, `Device tree exact match the board: ...`, `Boardsocid = %x, Dtsocid = %x`, `BoardVariant = %x, DtVariant = %x`, `ERROR: Couldn't find the suitable DTB!`;
- DTBO table: `Dtbo count = %u LocalBoardDtMatch = %x`, `DT Total number of entries: %d, DTB version: %d`, `Dtbo hdr magic mismatch %x, with %x`, `BootLinux: failed to get dtbo image`, `androidboot.dtbo_idx=`, `androidboot.dtb_idx=`;
- boot-v2 DTB slot: `Boot Image Header Info...`, `DTB Size : 0x%x`, `Single appended DTB found`, `Not the single appended DTB`, `DTB offset goes beyond kernel size.`, `Error: Appended Soc Device Tree blob not found`;
- overlay fixups: `ufdt_install_blob (0x%08jx)`, `failed to perform local fixups in overlay`, `failed to perform fixups in overlay`, `failed to apply fragments`, `/__local_fixups__`, `/__symbols__`, `/__fixups__`, `ApplyOverlay: ufdt apply overlay failed`;
- RAM mutation: `/memory`, `ERROR: Could not find memory node ...`, `ERROR: Cannot update memory node`, `Failed to add the memory information addr: %d`, `Failed to add the memory information size: %d`, `ddr_device_type is added to memory node`, `ddr_device_rank_ch%d added to memory node`, `ddr_device_hbb_ch%d_rank%d added to memory node`, `Error unsupported cell size value: #address-cell %d#size-cell`, `DDR deviceType:%d`, `HwDdrSize = %dGB, qcom,is-low-ram = %d`, `BaseAddr[%d] = 0x%lx, TestSize = 0x%x` (plus `ddr_device_rank_ch` / `ddr_device_hbb_ch` field names);
- `/chosen` update: `bootargs`, `rng-seed`, `kaslr-seed`, `linux,initrd-start`, `linux,initrd-end`; `/reserved-memory/splash_region`, `/reserved-memory/demura_region_0/1`.

Strings alone are C-level evidence. To avoid claiming a path without code, AArch64 `ADRP`/`ADD` pairs in `.text` were decoded and resolved to their computed targets (imagebase 0, so RVA == file offset). Confirmed direct code references:

| String | VA | Referencing instruction site(s) |
|---|---|---|
| `qcom,board-id` | `0x000cffd3` | `0x3a18c` |
| `/memory` | `0x000d083d` | `0x3e650` |
| `ddr_device_type` | `0x000d08c4` | `0x3e798`, `0x3e7b4`, `0x3e834` |
| `ddr_device_rank_ch…` | `0x000d08ed` | `0x3e7b4`, `0x3e834` |
| `androidboot.dtbo_idx=` / `dtb_idx=` | `0x000d245c` / `0x000d2477` | `0x42ac0` |
| `ufdt_install_blob` | `0x000e0bf9` | `0x6aaf8`, `0x6ab7c` |

Note on method limits: the vendored LLVM 22 `llvm-objdump` could not parse this PE (`The end of the file was unexpectedly encountered`) and the host GNU objdump has no AArch64 backend; therefore the xrefs above were produced by decoding `ADRP` (opcode mask `0x9f000000` == `0x90000000`) and follow-up `ADD` (mask `0xffc00000` == `0x91000000`) directly from bytes. This proves code references to the strings; it does **not** reconstruct the full call graph or the exact run-time argument values.

### 4.4 XBL configuration strings (direct, uncompressed)

`xbl` strings include the liveDDR handoff configuration:

```
[Config]
MaxMemoryRegions = 74
UnusableDDRMemoryAtBeginning = 1
UnusableDDRMemoryStartAddr = 0x80000000
UnusableDDRMemorySizeAtBeginning = 0x600000
[MemoryMap]
0x805D0000  IPC SHM        ...   0x9FA00000  ABOOT FV ...
```

Also present: `/chosen`, `/reserved-memory/splash_region`, `LcdkitInitPanelInfo:uBoardId %u hw_get_dts_info failed`, and `boardid` occurrences. No `dtbo`, `fdt`, `msm-id`, or `rootparam` strings were found in XBL or xbl_config. FDT magic bytes (`d00dfeed`/`edfe0dd0`) were not present in any of the three outer images; the ABL selector constructs/passes FDT buffers rather than embedding one.

### 4.5 Evidence grading

- **A (direct code/disassembly):** ADRP/ADD references from ABL `.text` to `qcom,board-id`, `/memory`, `ddr_device_type`, `androidboot.dtbo_idx=`, `ufdt_install_blob`; ABL ELF/PE/FV/LZMA layout; XBL MemoryMap config strings.
- **B (implementation strings inside the exact executable payload):** DTBO table validation, hash/override/overlay messages, `ddr_device_*` node writes, boot-v2 `DTB Size` handling, `/chosen` updates.
- **C (inference, not asserted as fact):** which input value selected entry 2 on this boot; whether ABL is the *only* component that can touch the memory node; whether the ABL write order matches the three tuples seen in the live FDT.

Per taskbook §5, no selector or RAM-mutation path is claimed beyond the code references above. Signing keys were not extracted and no key material is reported.

---

## 5. AVB / package chain (read-only `info_image`)

`avbtool` was not installed. The official AOSP `avbtool.py` (version 1.3.0) was fetched to the local host workspace only and used solely for `info_image`; nothing was installed on the device and no verification was disabled. An initial hand-written parser produced nonsensical offsets and was discarded rather than reported.

### 5.1 Root vbmeta (`vbmeta`, SHA256_RSA2048, flags 3, pubkey sha1 `5295a515…`, release `avbtool 1.1.0`)

Chain descriptors (partition → rollback index location → key sha1 prefix): `boot`→1 `b570ac9c…`, `ramdisk`→4 `b570ac9c…`, `vbmeta_system`→2 `10a82975…`, `vbmeta_vendor`→3 `0ae75cdb…`, `vbmeta_odm`→5 `38d22f00…`, `eng_vendor`→9 `265089c4…`, `eng_system`→10 `b680e5c9…`, `dtbo`→14 `b570ac9c…`, `version`→6 `75b3cace…`. All rollback indices reported 0.

### 5.2 Per-image results

| Image | Footer / original size | VBMeta size | Algorithm / key sha1 | Notable descriptors |
|---|---|---|---|---|
| `dtbo` | footer v1.0, 25 165 824 / 2 963 810 | 1 472 | SHA256_RSA2048 `b570ac9c…` | hash sha256 over dtbo, digest `71cca12c…`; prop fingerprint `qti/kona/kona:11/RP1A.200720.011/…:user/dev-keys` |
| `recovery` | footer v1.0, / 49 614 848 | 1 344 | SHA256_RSA2048 `b570ac9c…` | hash sha256, partition name `recovery`, digest `9769e7bd…` |
| `erecovery` | footer v1.0, / 49 614 848 | 1 344 | SHA256_RSA2048 `b570ac9c…` | **identical** hash descriptor to `recovery` (same name/salt/digest) |
| `recovery_vbmeta` | none | — | SHA256_RSA2048 `c433b845…` | chain: `recovery`→23, `dtbo`→14, `recovery_ramdisk`→17, `recovery_vendor`→18 |
| `erecovery_vbmeta` | none | — | SHA256_RSA2048 `d88afbac…` | chain: `erecovery`→25, `dtbo`→14, `erecovery_ramdisk`→26, `erecovery_vendor`→27 |
| `vbmeta_system` | none | — | SHA256_RSA2048 `10a82975…` | hashtree sha1, `system` image size 3 525 328 896, salt `9f3a79b7…`, root `c2a62d1d…`; props `SKQ1.220804.001`, patch `2022-08-01` |
| `vbmeta_vendor` | none | — | SHA256_RSA2048 `0ae75cdb…` | hashtree sha1, `vendor` image size 947 318 784, salt `9f3a79b7…`, root `45c810cc…`; props `RP1A.200720.011`, patch `2018-06-19` |
| `vbmeta_cust` | footer v1.0, 1 048 576 / **10 375 168** | 1 344 | **NONE**, no key | **no descriptors**; auth block 0 bytes, aux block 0 bytes, release `avbtool 1.3.0`, footer at offset `0xfffc0` pointing to a VBMeta offset **past the 1 MiB partition** |

`vbmeta_cust` anomaly (previously seen only in an offline image) is **confirmed on the live partition copy**: it is a footer-only shell with no authentication block, no descriptors, and an original-size/offset field that exceeds the partition size. This is recorded as an observation; no conclusion is drawn about bootloader enforcement, and no image was modified.

### 5.3 Live `boot` differs from the firmware-package `boot.img`

| Field | Live `boot` | Firmware-package `boot.img` (ROUND153/154 reference) |
|---|---|---|
| SHA-256 | `7a95c897…` | `027f88fd…` |
| kernel size | 22 256 282 | 22 264 379 |
| ramdisk size | 519 986 | 519 986 |
| header version / size | v2 / 1660 | v2 / 1660 |
| `dtb_size` / `dtb_addr` | 1 664 243 / `0x1f00000` | identical |
| AVB footer | **absent** (`AVBf` not found) | present at offset 100 663 232 |
| FDT slot sha256 (3 FDTs) | `df2730f3…`, `f3dcba83…`, `6cda6739…` | **identical** |
| FDT slot start | `0x15ba000` | `0x15bc000` (shifted 0x2000 by kernel page alignment) |

Three appended FDTs (msm-id `0x20001`/`0x20000`/`0x10000`, board-id `0/0`) plus a 173-byte tail are present in both. The data differ only in the kernel region and AVB footer; the *DTB payload that R153/R154 analysed is byte-identical to the live device*. This closes the "reference image may not be the live one" worry for DTB content, while showing that the live boot image is not the signed package image.

`dtbo` live hash `51a5d7b8…` matches the firmware-package `dtbo.img` exactly.

---

## 6. What this closes, and what remains

**Closed by this round:**
1. *Which layer selects the DTBO entry* — ABL contains the board/msm/pmic matching code, DTBO table validation, `androidboot.dtbo_idx=`/`dtb_idx=` cmdline writes and ufdt overlay application, with code references.
2. *Which layer rewrites the RAM map* — ABL contains `/memory` update code writing `ddr_device_type`, `ddr_device_rank_ch%d`, `ddr_device_hbb_ch%d_rank%d` and cell-size checks; XBL separately supplies a DDR MemoryMap config with a 6 MiB unusable window at `0x80000000`.
3. *Is the analysed DTB the live one* — yes: all three FDTs in the live boot slot hash-identical to the firmware package.
4. *Does the vbmeta_cust anomaly exist live* — yes.

**Still open (not guessed):**
- The exact run-time value/chain that selected entry 2 (`dtbo_idx=2`, board-id `0x200e`) on this boot. No ABL log was captured; this needs a boot log or an ABL trace, not more static strings.
- Whether ABL is the *only* mutator of `/memory`, and the precise ordering relative to the three observed tuples.
- Selector behaviour for a candidate boot image with a different DTB set (ROUND154 Task C showed stock entry 2 cannot apply to the candidate base).
- Full AVB verification (`verify_image`) — deliberately not run; no public verification key was obtained or used, and no keys were extracted.

**No change was made to the device.** The two host copies remain local and are not part of this delivery.

---

## 7. Self-caught pitfalls

1. `iflag=fullblock` is unsupported by device Toybox dd; a 24-byte error string would have been mistaken for a short read. Fixed by command adjustment with all gates intact.
2. `stat -Lc` needs a format argument; the first inventory recorded the Toybox usage error in the metadata column. Re-run with an explicit format before any capture.
3. The outer `abl` strings pass was empty; concluding "no DTBO logic in ABL" from that would have been a false negative. The LZMA/UEFI FV payload had to be decompressed.
4. The first AVB attempt used a hand-written parser with assumed offsets and produced impossible values; discarded in favour of the official AOSP tool.
5. `llvm-objdump` cannot parse the extracted PE; the xrefs were established by decoding AArch64 instructions directly, and the limitation is stated rather than hidden.

---

## 8. Deliverable

Only this sanitized report is published. Raw binaries, host paths, tooling scripts, and all intermediate evidence remain in the local Window A workspace. Read-back verification of the uploaded blob is recorded in the delivery manifest committed alongside this report.
