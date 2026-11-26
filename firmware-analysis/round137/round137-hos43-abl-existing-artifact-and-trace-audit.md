# ROUND137 — HOS4.3 ABL existing-artifact and runtime-trace availability audit

- **Executor:** WorkBuddy Agent (local, offline, read-only)
- **Dispatched by:** AI1 (ChatGPT). AI2 was not assigned any work in this round.
- **Target:** Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250, HOS 4.3
- **Related kernel project:** ACK `android17-6.18.33_r00`, pinned `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- **Taskbook:** `firmware-analysis/round137/AGENT_TASKBOOK_HOS43_ABL_EXISTING_ARTIFACT_AUDIT.md` (git blob `508cd1500c29c0ac803a88ee0b4f414646055ecb`)
- **Date of execution:** 2026-11-26 (Asia/Shanghai)
- **Scope:** availability/metadata audit only. No device access, no new extraction, no download, no build, no source/patch/DTS/schema/config change.

---

## 0. Result at a glance

| Question | Answer |
|---|---|
| Is an ABL binary (`abl.elf` / `abl.img` / `abl.mbn` / `abl.bin` / `abl/`) present in the authorized corpus? | **NO — not present anywhere** |
| Is an ABL entry recorded in any existing package/partition inventory? | **NO** (two independent 42/43-row inventories, neither contains `abl`) |
| Does the device expose an `abl` partition name? | **YES** — `abl -> /dev/block/sde6` (partition node only; no image was pulled) |
| Is an ABL build/version string available? | **NO** (`ro.bootloader=[unknown]`; fastboot `getvar` unavailable; no binary to read) |
| Is any ABL→Linux runtime handoff trace recorded? | **ONE PARTIAL ITEM** — bootloader-published `ro.boot.dtbo_idx=2` (see §5.2) |
| Final outcome | **`BLOCKED — ABL ARTIFACT/TRACE NOT PRESENT`** (artifact absent; the single partial trace in §5.2 does not constitute handoff evidence) |

**Most consequential side finding (for AI1 attention):** the bootloader-published DTBO index on the device is **2**, which maps through the existing verified DTBO table to **board-id 8206 (0x200E) / `DBY_W09_VD`** — not **`DBY_W09_VG` / 0x206A (entry 8)**, which is the variant all prior board-DTS/rootparam comparisons in this project were built on. Details and the limits of this claim are in §6. This taskbook did not authorize and did not perform any change based on it.

---

## 1. Evidence roots inspected (sanitized)

Only previously established, project-authorized HOS4.3 evidence locations were read. No arbitrary drive search, no personal-directory enumeration.

| ID | Sanitized root | What it is | Rows/files seen |
|---|---|---|---|
| E1 | `<workspace>/MatePad11_HOS43_LocalCheck_20261123_230849` | Accepted HOS4.3 extracted-package read-only inventory + 11 allow-listed copies | `package_inventory.csv` 43 rows; `selected_files/` 11 images; `copied_files_sha256.csv` 11 rows |
| E2 | `<workspace>/MatePad11_HOS43_LocalCheck_20261123_230810` | First run of the same script (path-safety bug → 0 copies) | `REPORT_README.txt` only; 0 binary copies |
| E3 | `<workspace>/_fw_upload` | Independent earlier firmware inventory set | `partition_inventory.csv` 42 rows; `firmware_analysis.txt`; `selected_images_sha256.csv`; `summary.json` |
| E4 | `<workspace>/DBY-W09_FirmwareAnalysis` | Earlier copy of the same inventory/analysis pair | `partition_inventory.csv` 42 rows; `firmware_analysis.txt`; `payloads/` |
| E5 | `<workspace>/Agent_Round2_Report/device` | Accepted read-only ADB collection (getprop / partition names / DT listings / fastboot attempt) | 11 text/metadata files |
| E6 | `<workspace>/github_upload/round1-adb`, `round2-adb` | Uploaded copies of the same device collections (same content as E5 where overlapping) | duplicate-content verification only |
| E7 | `<round3-work>/dtb_work` | ROUND3/R7/R8 established local binary work copies: 9 DTBO entries + 4 boot FDT candidates | 13 files, opened read-only, mtimes unchanged (2026-11-24 01:18) |
| E8 | `<workspace>/_r65/round65-first-stage-fstab-vbmeta-cust-and-boot-tool-audit.md` | Accepted ROUND65 report (local copy) — cited, not re-run | §5 "actual ABL selection evidence" |

Note: E7 is the exact directory named as the sole input in `AGENT_TASK_ROUND7.md` (§1) and `AGENT_TASK_ROUND8.md` (§1); it is a project-established evidence location, not an arbitrary path. It was read only; no file was rewritten, renamed, repaired or re-extracted.

---

## 2. Question A — is an ABL artifact already present?

### 2.1 Filename search (exact patterns from the taskbook)

| Pattern searched | Roots | Hits |
|---|---|---|
| `abl.elf` | E1, E2 (recursive) | **0** |
| `abl.img` | E1, E2 (recursive) | **0** |
| `abl.mbn` | E1, E2 (recursive) | **0** |
| `abl.bin` | E1, E2 (recursive) | **0** |
| `*abl*` (case-insensitive, any file or directory) | E1, E2 (recursive) | **0** |

The 11 actually-copied images in E1 are: `boot.img`, `dtbo.img`, `ramdisk.img`, `recovery.img`, `recovery_ramdisk.img`, `vbmeta.img`, `vbmeta_cust.img`, `vbmeta_hw_product.img`, `vbmeta_odm.img`, `vbmeta_system.img`, `vbmeta_vendor.img`. **No ABL image among them.**

### 2.2 Inventory / partition-manifest search

Two independent inventories were checked row by row for an ABL entry:

| Inventory | Rows | `abl` entry? | Notes |
|---|---|---|---|
| E1 `package_inventory.csv` | 43 | **No** | contains `xbl.img` (4,018,176 B), `xbl_config.img` (4,325,376 B), `tz.img`, `uefisecapp.img`, `hyp.img`, `qupfw.img`, `devcfg.img`, `aop.img`, `storsec.img`, `keymaster.img`, `featenabler.img` |
| E3 `partition_inventory.csv` | 42 | **No** | same partition set, different classification vocabulary |

Per the taskbook, an ABL binary was **not** inferred from `xbl.img`, `xbl_config.img`, `tz.img` or `uefisecapp.img`. Their presence is recorded above only as inventory fact.

### 2.3 Device-side partition fact (not an artifact)

E5/E6 record the device block-name symlink table captured read-only via `adb shell ls -l /dev/block/by-name`:

```
lrwxrwxrwx 1 root root 15 2026-11-23 01:20 abl -> /dev/block/sde6
```

This proves an `abl` **partition exists on the device**. It is **not** an ABL binary, not a copy, and carries no version or content information. No partition read/pull was performed (taskbook §3 forbids it, and a prior pull attempt of a root-only node was already refused by the OS).

### 2.4 Verdict for A

**No ABL artifact is present in the authorized corpus.** There is no `abl.*` file, no `abl/` directory, no inventory row, and no "already-extracted equivalent file identified by an existing partition manifest". The only ABL-related local fact is the device partition symlink in §2.3.

---

## 3. Question B — ABL metadata (not applicable)

Because no ABL binary exists, no file type, size, SHA-256, or build/version string could be produced for an ABL artifact. Nothing was executed, patched, disassembled, repacked or uploaded.

---

## 4. Question C — ABL / runtime handoff traces already recorded

Each required item is classified strictly:

- **DIRECT EVIDENCE** = a same-boot record produced by the bootloader path itself and captured read-only.
- **INDIRECT LEAD** = a structural symptom consistent with a bootloader action, but not proof of policy or of the specific selection.
- **NOT FOUND** = no authorized local record.

| # | Required item | Status | What the corpus actually contains |
|---|---|---|---|
| C1 | ABL build / version | **NOT FOUND** | `[ro.bootloader]: [unknown]` (E5 getprop). fastboot `getvar` is **NOT AVAILABLE** — device was in adb mode and no reboot was issued (E5 `fastboot_getvar_redacted.txt`). No ABL binary to read strings from. |
| C2 | Selected DTBO entry and exact selection result | **DIRECT EVIDENCE (partial)** | `[ro.boot.dtbo_idx]: [2]` — a bootloader-published cmdline value surfaced by Android init (E5 getprop line 753; identical in E6). Index→identity mapping resolved against the existing verified DTBO table; see §5 and §6. **Limit:** this is the selection *result*; ABL's internal matching logic/log is still unobserved. |
| C3 | `/rootparam` contents after ABL overlay | **INDIRECT LEAD (structure) / NOT FOUND (values)** | The live device DT contains a `/rootparam` node with 7 properties (`hardware_version`, `huawei,modem_id`, `name`, `phandle`, `qcom,board_name`, `qcom,boardid`, `qcom,product_name`) — directory listing only. **Every value read was `Permission denied`** (`cat /sys/firmware/devicetree/base/rootparam/...`, and `/proc/device-tree/*`). No value was obtained, and none is reproduced here. |
| C4 | Final post-ABL FDT passed to Linux | **INDIRECT LEAD (structure) / NOT FOUND (content)** | `/sys/firmware/fdt` exists at **800,316 B, mode `-r--------` (root-only)**; `adb pull` failed with `Permission denied` (E5 `live_dtb_status.txt`, `live.dtb.sha256` = NOT AVAILABLE). Root-node listing is readable: `chosen/` with `bootargs` (1507 B), `linux,initrd-start` (8 B), `linux,initrd-end` (8 B), `kaslr-seed` (8 B); `reserved-memory/` 39 children; `soc/` 527 children; `rootparam/`; `memory/` (`reg` 48 B, unread). **No FDT bytes were obtained.** |
| C5 | Classic arm64 direct entry vs EFI-stub entry | **NOT FOUND** | Only inference exists: ROUND20/75 established the stock kernel has **no** PE/COFF EFI header and is gzip-compressed, so normal ARM64 FDT entry is the compatibility-first assumption; "Layer 3 — ABL invokes that entry" remained UNKNOWN (ROUND65 §5). The live DT shows no `uefi`/EFI-related root node, which is consistent with but not proof of the classic path. No boot log or entry-route record exists. |
| C6 | Kernel entry register evidence that x0 = FDT physical address | **NOT FOUND** | Requires a boot log, ABL log, or debugger capture. None exists in the corpus. |

### 4.1 Explicitly *not* claimed

- `ro.bootimage.build.date` / `build.fingerprint` / `build.id` (`Fri Aug 30 08:39:29 CST 2024`, `huawei202408300839`, `SKQ1.220804.001`) describe the **boot image**, not ABL. They are recorded here only to prevent them from being mistaken for an ABL version.
- The `abl -> sde6` symlink (§2.3) is **not** treated as an ABL artifact.
- No ABL behaviour was inferred from `xbl*`, `tz`, `uefisecapp`, or from any board-id resemblance.

---

## 5. Cross-referenced DTBO table used to interpret C2

The DTBO table was **not** re-parsed from raw firmware in this round; the values below come from the already-accepted ROUND3/ROUND7 parser output (`round3_summary.json`, `device_tree_inventory.csv`) and were independently re-confirmed read-only this round by a stdlib FDT structure scan of the existing `dtb_work` copies (mtimes unchanged).

| entry index | root `qcom,board-id` | `qcom,board_name` | `qcom,product_name` | `hardware_version` | rootparam overlay |
|---|---|---|---|---|---|
| 0 | (8200, 0) = 0x2008 | DBY_W09_VA | DBY-W09 | SH0DBSLM | present |
| 1 | (8296, 0) = 0x2068 | DBY_W09_VF | DBY-W09 | SH1DBSLMA | present |
| **2** | **(8206, 0) = 0x200E** | **DBY_W09_VD** | **DBY-W09** | **SH1DBSLM** | **present** |
| 3 | (8208, 0) = 0x2010 | DBY_W09_VC | DBY-W09 | SH1DBSLM | present |
| 4 | (8202, 0) = 0x200A | DBY_W09_VB | DBY-W09 | SH1DBSLM | present |
| 5 | (8238, 0) = 0x202E | DBY_W09_VI | DBY-W09 | SH1DBSLMA | present |
| 6 | (8302, 0) = 0x206E | DBY_W09_VH | DBY-W09 | SH1DBSLM | present |
| 7 | (8240, 0) = 0x2030 | DBY_W09_VE | DBY-W09 | SH1DBSLM | present |
| 8 | (8298, 0) = 0x206A | DBY_W09_VG | DBY-W09 | SH1DBSLM | present |

Decimal→hex is stated for readability only; **the parser-recorded decimal pair is authoritative**. Note that entry 2 (8206 → 0x200E) and entry 6 (8302 → 0x206E) are distinct values — an earlier draft of this report mis-converted 8206 to 0x206E; the corrected value is 0x200E and the correction is recorded here deliberately rather than silently.

All nine entries carry a `rootparam` overlay whose target is a phandle reference (`target-phandle` form, target not resolved in this round) and whose overlay subtree carries the five rootparam-characteristic property **names**. Therefore the mere existence of `/rootparam` on the live DT cannot discriminate which entry was applied — only its values could, and those values were unreadable (§4/C3).

Mandatory caveat: **a DTBO entry whose board ID resembles DBY-W09 is not proof it was selected.** The basis for C2 is the bootloader-published index, not resemblance.

---

## 6. The one material trace: `ro.boot.dtbo_idx = 2`

### 6.1 What is directly evidenced

`ro.boot.dtbo_idx` is the Android property through which a bootloader publishes `androidboot.dtbo_idx` on the kernel command line — i.e. the index of the DTBO entry it actually applied in **that** boot. The captured value is **2**.

Interpreted against the table in §5, the boot reported **entry index 2 → board-id 8206 (0x200E) → `DBY_W09_VD` → hardware_version `SH1DBSLM`**.

### 6.2 What follows for the project

All prior board-level work in this project (ROUND8 entry-8 fragment analysis, ROUND23/24 rootparam composite, the `DBY_W09_VG` naming in board-DTS discussions) was built on **entry 8 = `DBY_W09_VG` / 0x206A**, which ROUND19/21 explicitly labelled "a candidate, not a fact". The device now reports index **2**, i.e. the **`VD`** variant. This is a genuine discrepancy in premise, not a contradiction of any prior measurement: the prior work measured entry 8 correctly, it simply may have measured the wrong entry relative to this unit's runtime selection.

### 6.3 Limits of this finding (must not be over-read)

1. **No ABL log or binary** confirms *why* index 2 was chosen; only the published result is visible.
2. The device reports `[ro.boot.verifiedbootstate]: [orange]` and `[ro.boot.flash.locked]: [0]` — the unit is unlocked/verity-degraded. Current `dtbo` partition content was **not** verified against the extracted package (no partition read is authorized). Therefore "index 2" describes the **current** boot state and cannot be asserted as "the factory HOS4.3 default" with certainty.
3. `dtbo_idx` conveys the *index*, not the entry's board-id. The mapping index→board-id comes from the extracted package's table (§5); if the on-device `dtbo` partition differed from that package, the mapping would not hold.
4. This finding does **not** establish: which fragments the ABL actually applied, the final FDT, the entry route, or RAM acceptance. It changes no Phase status by itself and no decision was taken on it.

---

## 7. Direct evidence vs. lead — summary

| Item | DIRECT | INDIRECT LEAD | NOT FOUND |
|---|---|---|---|
| ABL binary | — | — | ✔ (absent by exhaustive filename + inventory check) |
| ABL partition exists on device | ✔ (`abl -> sde6` symlink record) | — | — |
| ABL build/version | — | — | ✔ (`ro.bootloader=unknown`; getvar N/A) |
| DTBO entry actually selected (index) | ✔ (`ro.boot.dtbo_idx=2`) | — | — |
| DTBO selection *policy/matching log* | — | ✔ (index implies a match occurred) | ✔ (no log) |
| `/rootparam` node presence post-overlay | ✔ (live DT directory listing) | — | — |
| `/rootparam` values post-overlay | — | — | ✔ (Permission denied) |
| Final post-ABL FDT content | — | ✔ (root-node + `chosen` listing, `fdt` 800,316 B root-only) | ✔ (bytes unobtainable) |
| Classic FDT vs EFI-stub entry | — | ✔ (no EFI header in stock kernel; no `uefi` node) | ✔ (no boot/entry record) |
| x0 = FDT physical address at entry | — | — | ✔ |

---

## 8. Exact missing item (blocking)

To advance the bootloader-specific gate without new firmware collection or device contact, the corpus still lacks:

1. **An ABL image or ABL log from this exact HOS4.3 build** (`abl.elf` / `abl.img` / `abl.mbn`, or a bootloader console log), and/or
2. **A captured final post-ABL FDT** (the 800,316-byte `/sys/firmware/fdt`, or an equivalent same-boot capture) **plus** the `/rootparam` values, **plus** an entry-route indicator (a boot log line, or a debugger/fastboot-side record) establishing whether the classic ARM64 FDT path or the EFI-stub path was taken and whether x0 carried the FDT address.

Neither exists in the authorized corpus. The `abl` partition cannot be read without a partition pull, which this taskbook forbids and which a prior attempt already showed is permission-blocked.

---

## 9. Final outcome

```
BLOCKED — ABL ARTIFACT/TRACE NOT PRESENT
```

Rationale: no ABL binary or partition image exists anywhere in the authorized evidence corpus (§2), and the runtime handoff evidence required by C1/C3-values/C4-content/C5/C6 is absent (§4). The single partial trace `ro.boot.dtbo_idx=2` (§6) is reported because it is real and material, but it does not satisfy the handoff-trace requirement and is not presented as a substitute for an ABL artifact. Per the START prompt, `xbl`/`tz` were **not** offered as substitutes.

---

## 10. Compliance statement

- No device connection, USB, ADB, fastboot, recovery, serial or bootloader shell was used in this round. **Zero** commands were issued to any device.
- No reboot, unlock, root, remount, flash, partition write or `fastboot boot` occurred.
- No ADB pull that previously failed with `Permission denied` was retried; no privilege escalation was attempted.
- No firmware/update package was extracted, unpacked, or downloaded; no tool or package was installed; nothing was built.
- No raw ABL / boot / ramdisk / DTB / DTBO / vbmeta / firmware bytes were uploaded. Only this Markdown report is uploaded.
- No source, patch, DTS, schema, Kconfig, config, test, manifest or previously accepted log was modified. ROUND64/65 inventories were cited, not re-run.
- The only local binary reads were read-only FDT structure scans of pre-existing `dtb_work` copies (E7); their mtimes remain 2026-11-24 01:18 (§Appendix A). No file was rewritten.
- Sensitive values (serials, MACs, IMEIs, `huawei,modem_id`, `qcom,boardid` raw bytes, signatures, keys) were **not** printed. Only non-unique model/variant strings and board-id pairs are reported.

---

## Appendix A — Evidence file identity (read-only, unchanged)

| File (E7) | size (B) | SHA-256 | mtime |
|---|---|---|---|
| `dtbo_entry_2.dtbo` | 329,240 | `0633a6fbeebbad45c0f5572faf222c779e1cd51d253a6ef8282592a730ba3c8b` | 2026-11-24 01:18:00 |
| `dtbo_entry_8.dtbo` | 329,352 | `a7946352a86ab6e47b5ee79d84e5d6c4cf4e548c96b0221cec909f32ebd9d21d` | 2026-11-24 01:18:01 |
| `boot_fdt_candidate_0.dtb` | 556,524 | `df2730f3d2e9bdabad874c3ef7399534c5c6070b046c4524224aa461ba2c70f7` | 2026-11-24 01:18:01 |

Package-side identity already recorded by the accepted inventory (`copied_files_sha256.csv`, E1), quoted for reference only:
`dtbo.img` = 25,165,824 B, SHA-256 `51A5D7B81BC149765C1B4038E9ABA5917392CD7370E029EA9F1B2933A8970C0C`;
`boot.img` = 100,663,296 B, SHA-256 `027F88FD6F318523925CA27A4D681D17A9BBCA904B0C471CCC05E651D3DA19B8`.

## Appendix B — Invariant observations from the live-DT directory listing (no values)

- `/sys/firmware/fdt`: 800,316 B, mode `-r--------`, root-only → not readable by the collecting shell.
- `chosen/`: `bootargs` (1507 B), `linux,initrd-start` (8 B), `linux,initrd-end` (8 B), `kaslr-seed` (8 B) — existence/size only.
- `rootparam/`: 7 entries as listed in §4/C3 — names only.
- `reserved-memory/`: 39 child directories; `soc/`: 527 child directories; `memory/`: `reg` 48 B (unread).
- Boot image header (already recorded by the accepted inventory): Android boot header v2, kernel 22,264,379 B, ramdisk 519,986 B, DTB 1,664,243 B at region offset 22,790,144 (a multi-DTB container: kona v2.1 / v2 / v1). The live FDT is 800,316 B, i.e. **not** byte-equal in size to that embedded DTB region; the reason is not established by any record and is **not** inferred here.

## Appendix C — Round-65 citation (already accepted, not re-run)

ROUND65 §5 recorded, before this round: *"Which of the nine DTBO entries HOS4.3 ABL selected: no direct same-boot evidence … `0x206a` is explicitly 'a candidate, not a fact'"*, and *"no ABL binary/authoritative log was available"*. This round confirms the artifact finding and **adds** the `ro.boot.dtbo_idx=2` trace that ROUND65 did not have.
