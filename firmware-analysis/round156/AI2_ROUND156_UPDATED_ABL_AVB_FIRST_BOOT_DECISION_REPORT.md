# ROUND156 — Updated exact-ABL / AVB / first-boot decision (AI2 independent review)

- Reviewer: AI2, independent reviewer
- Scope: read-only review of published reports, exact-device ABL capture report, candidate DTB/overlay analysis, and official AOSP AVB source
- Disposition: **NO-GO for package release, temporary boot, and partition flash on current evidence**
- Actions: no device access, ADB, root, fastboot, recovery, reboot, partition operation, source edit, build, DTBO container creation, or package write.

## 0. Executive decision

ROUND155's statement that the exact ABL was unavailable is superseded. Window A's ROUND155 report records a byte-exact live ABL partition capture, SHA-256 verification, decompression of its embedded LZMA payload, and direct AArch64 ADRP/ADD code references to the board selector, DTBO index/cmdline, UFDT overlay application, and RAM-node updater.

This is a meaningful advance, but it is **not yet a full control-flow audit**. The ROUND156 Window A exact-control-flow report and Window B candidate-variant report named by the taskbook were not present in their respective branch trees when checked. The published ROUND155 ABL evidence gives code-reference evidence, not the complete branches/call graph needed to prove optional-overlay handling, fatality on overlay failure, target-path support, or RAM replace/append semantics. This report does not invent those missing findings.

**AVB correction:** the root vbmeta's reported flags value is 3. Under AOSP AVB definitions, bit 0 is HASHTREE_DISABLED and bit 1 is VERIFICATION_DISABLED. In the AOSP libavb implementation, the top-level vbmeta image signature/key/rollback checks occur before the VERIFICATION_DISABLED branch; that branch then skips processing all descriptors and loads requested partitions. Thus flags=3 is not equivalent to “the top-level vbmeta signature is never checked.” It does mean that, in an AOSP-like path, the boot/dtbo hash descriptors and chained vbmeta descriptors are not processed. Whether Huawei's exact ABL implements that same path, permits the relevant verification errors, or adds independent checks remains unproven.

**Orange-state correction:** ROUND151's captured live bootargs include `androidboot.verifiedbootstate=orange`. AOSP defines orange as UNLOCKED. This is direct evidence that the property was present in the captured bootargs; it is not, by itself, disassembly proof that ABL derived it from the actual unlock-state branch. The same bootargs also contain Huawei-specific `userlock=locked`; that token is not the AOSP AVB state property and cannot be used to override or resolve the AVB-state question. No direct ABL code reference to the verifiedbootstate emission branch is published.

**First-boot verdict:** candidate no-overlay boot is now **plausible at the DTB-content level**, not proven bootable. Window B's ROUND155 analysis reports that the RAM-patched 905-node base contains timer, GIC/PDC, PSCI, GCC, PMIC regulator providers, UFS host/PHY and resolved UFS supply/phandle edges; it also reports a small target-path overlay applies in host libfdt. But the candidate has no `/chosen` properties, its debug UART node is disabled, and exact ABL handoff/overlay failure semantics remain unresolved. Host-side `fdtoverlay` success does not prove Huawei UFDT accepts the same overlay or that ABL will select it.

**Three independent go/no-go decisions:**

| Activity | Decision | Reason |
|---|---|---|
| Offline package-layout experiment / unsigned scratch artifact | **NO-GO as a package deliverable; limited host-only analysis remains permissible in a separately authorized task** | Missing ROUND156 reports, exact ABL control-flow gaps, no validated AVB package/signing contract, incomplete partition/recovery proof. A scratch artifact must not be represented as flashable. |
| Temporary boot | **NO-GO** | Exact ABL temporary-boot path/acceptance is not demonstrated; no test or restore rehearsal; A-only partition layout and boot-chain risks remain. |
| Partition flash/write | **HARD NO-GO** | No complete recovery set or proven exact-stock restore route; AVB/Huawei acceptance unresolved; no write authorization. |

## 1. Evidence coverage and provenance

### 1.1 Reports read

- ROUND155 Window A, read-only boot-chain partition capture and live ABL/AVB analysis:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round155-readonly-bootchain-backup/firmware-analysis/round155/WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE_REPORT.md
- ROUND155 Window B, candidate-specific minimal overlay / first-boot analysis:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round155-candidate-overlay-minimal-plan/firmware-analysis/round155/WORKBUDDY_B_ROUND155_CANDIDATE_SPECIFIC_DTBO_MINIMAL_OVERLAY_REPORT.md
- ROUND154 Window A:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round155-readonly-bootchain-backup/firmware-analysis/round154/WORKBUDDY_A_ROUND154_MINIMAL_RAM_PATCH_AND_DTBO_BOOT_PACKAGE_GATE_REPORT.md
- ROUND154 Window B:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round155-candidate-overlay-minimal-plan/firmware-analysis/round154/WORKBUDDY_B_ROUND154_INDEPENDENT_PATCH_AND_DTBO_REPRODUCTION_REPORT.md
- ROUND151 live FDT/runtime capture:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round155-readonly-bootchain-backup/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md
- ROUND155 AI2 strategy report (historical; exact-ABL-unavailable claim is superseded):
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round155-custom-dtbo-bootchain-plan/firmware-analysis/round155/AI2_ROUND155_DTBO_SELECTION_AND_FIRST_BOOT_STRATEGY_REPORT.md

### 1.2 ROUND156 inputs not yet published

The following expected report paths were checked against their respective branch trees and were absent at review time:
- Window A branch `workbuddy/round156-abl-control-flow-avb-and-overlay-gates`: `firmware-analysis/round156/WORKBUDDY_A_ROUND156_EXACT_ABL_CONTROL_FLOW_AND_AVB_GATE_REPORT.md`.
- Window B branch `agent2/round156-candidate-dtb-firstboot-package-variants`: `firmware-analysis/round156/WORKBUDDY_B_ROUND156_CANDIDATE_FIRSTBOOT_DTB_VARIANTS_REPORT.md`.

Those branches contained taskbook/start-prompt files, not the requested result reports. The taskbook explicitly asks for these after delivery. This review cannot claim to have read either result. This is a coverage limitation, not proof that the other agents have not done work locally.

## 2. Exact ABL: corrected status and remaining control-flow gaps

### 2.1 What ROUND155 Window A directly established

The report states that the live `abl` partition was captured at 4,194,304 bytes and that host SHA-256, independent device-side streaming SHA-256, and local readback SHA-256 matched. It records an outer 32-bit ARM ELF containing a firmware volume, an LZMA GUID-defined section with an embedded AArch64 PE32+ payload, and decompressed payload SHA-256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`.

Published direct ADRP/ADD references:
- `qcom,board-id` at VA `0x000cffd3`, reference site `0x3a18c`;
- `/memory` at `0x000d083d`, reference site `0x3e650`;
- `ddr_device_type` at `0x000d08c4`, reference sites `0x3e798`, `0x3e7b4`, `0x3e834`;
- `androidboot.dtbo_idx=` / `androidboot.dtb_idx=` at `0x000d245c` / `0x000d2477`, reference site `0x42ac0`;
- `ufdt_install_blob` at `0x000e0bf9`, reference sites `0x6aaf8`, `0x6ab7c`.

The payload also contains strings for DTBO header validation, UFDT local/external fixup and fragment errors, `/chosen` update names, and `/memory` update/error messages. This establishes relevant code exists in the exact captured ABL, but not every branch or call-site relationship.

### 2.2 Boot-v2 DTB slot selection

The stock boot-v2 image contains three concatenated FDTs with `qcom,msm-id` values:

| Slot | SoC revision | `qcom,msm-id` |
|---:|---|---|
| 0 | kona v2.1 | `<0x164 0x20001>` |
| 1 | kona v2 | `<0x164 0x20000>` |
| 2 | kona v1 | `<0x164 0x10000>` |

The candidate matches slot 0's msm-id. ABL strings show boot-v2 DTB parsing and “best match” / “delete don't fit DTB” messages, while direct code references establish a board-id-related code site. This makes candidate slot 0 a plausible match, but the exact matching loop, priority order, fallback rules and candidate runtime selection are not published. Preserve the three-FDT stock layout as a conservative offline hypothesis; do not call the selector contract proven.

### 2.3 DTBO index selection and overlay behavior

Direct code-reference evidence ties ABL code to `androidboot.dtbo_idx=`, `androidboot.dtb_idx=`, and `ufdt_install_blob`. The ABL payload also contains strings for DTBO table validation, UFDT fixup/fragment errors and `ApplyOverlay: ufdt apply overlay failed`.

What this supports: ABL contains a DTBO-related selection/application implementation. What remains unproven without the missing ROUND156 Window A control-flow report or a stronger trace:
- exact runtime value/source that selected index 2 on the captured boot;
- whether DTBO is mandatory, optional, or conditionally bypassed;
- whether missing DTBO, malformed entry, failed fixup, or failed fragment application is fatal or has a fallback path;
- whether Huawei UFDT supports `target-path` in this build;
- whether a custom overlay at index 2 is accepted for this candidate;
- whether any ABL-side image hash/check beyond the observed AVB metadata is performed.

Do not infer optional overlay behavior merely because an error string exists, or mandatory overlay behavior merely because an apply function exists.

### 2.4 RAM replacement / append semantics

ABL contains direct code references to `/memory` and `ddr_device_type`, and strings for adding memory address/size information and handling unsupported cell sizes. XBL configuration also reports a 6 MiB unusable DDR window beginning at `0x80000000`.

This closes “which layer has RAM update code?” to ABL code-reference level. It does not yet prove whether the updater replaces the existing `reg`, appends tuples, normalizes/sorts intervals, or handles overlap and reserved-memory interactions in a specific way. Mutation order and whether another layer also mutates `/memory` remain unknown.

## 3. AVB: standard semantics versus Huawei-specific conclusion

### 3.1 Exact AOSP flag definitions

Official AOSP `avb_vbmeta_image.h` defines `AVB_VBMETA_IMAGE_FLAGS_HASHTREE_DISABLED = (1 << 0)` and `AVB_VBMETA_IMAGE_FLAGS_VERIFICATION_DISABLED = (1 << 1)`. The header comments define the first as disabling hashtree image verification and the second as disabling verification and preventing descriptor parsing.

Sources:
- AOSP Android 17 AVB header: https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_vbmeta_image.h
- AOSP Android 17 AVB README: https://android.googlesource.com/platform/external/avb/+/android17-release/README.md

Therefore `flags=3` sets both bits. It is not a third independent mode and is not simply a statement that all bootloader checks are disabled.

### 3.2 AOSP libavb processing order: root signature still matters

In AOSP `libavb/avb_slot_verify.c`, the implementation:
1. calls `avb_vbmeta_image_verify()` on the loaded vbmeta image;
2. handles signature/hash verification errors and the allow-verification-error policy;
3. validates the signing key and checks the rollback index;
4. only then checks `AVB_VBMETA_IMAGE_FLAGS_VERIFICATION_DISABLED`;
5. if bit 1 is set, loads requested partitions and exits without processing descriptors.

The source places signature verification at lines 786–838, key validation at 861–925, rollback check at 928–948, descriptor-skip branch at 977–995, and descriptor traversal from 997 onward.

Exact source: https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_slot_verify.c

Consequences under AOSP libavb semantics:
- **The top-level vbmeta signature is still checked.** Bit 1 does not skip the root vbmeta image's own signature check.
- Root signing-key acceptance and root rollback-index checks are also encountered before the descriptor-skip branch.
- With bit 1 set, hash descriptors, hashtree descriptors and chained-partition descriptors are not processed. Therefore root descriptors for `boot`, `ramdisk`, and `dtbo` are not used by that AOSP path to compare modified image bytes.
- Bit 0 alone disables hashtree/dm-verity behavior but does not disable ordinary hash descriptors or chain processing. In flags=3, bit 1 already causes the earlier descriptor bypass.
- AOSP unlocked-mode integration may allow verification/key/rollback errors to be non-fatal when the bootloader explicitly uses `AVB_SLOT_VERIFY_FLAGS_ALLOW_VERIFICATION_ERROR`; this is separate from the flags value.

### 3.3 What the live device evidence says

ROUND155 Window A reports live root `vbmeta` as SHA256_RSA2048, flags=3, with chain descriptors including `boot` at rollback-index location 1, `ramdisk` at 4, `dtbo` at 14, and chained vbmeta partitions including `vbmeta_system`, `vbmeta_vendor`, `vbmeta_odm`, `eng_vendor`, `eng_system`, and `version`.

The report used official AOSP `avbtool info_image` read-only. It explicitly did **not** run `verify_image`, did not obtain/use a public verification key, and did not verify the root signature. It proves parsed header/descriptor metadata and flags, not cryptographic signature validity.

Under AOSP semantics, an unchanged root vbmeta image could retain its original signature while flags=3 causes descriptor processing to be skipped. In that standard path, modified boot/dtbo payloads could be loaded without their root hash descriptors being checked, provided top-level vbmeta signature/key/rollback handling is accepted and the bootloader follows the same semantics. This is a **conditional technical possibility**, not a demonstrated Huawei acceptance path.

### 3.4 Orange state

ROUND151's captured live `/chosen/bootargs` includes `androidboot.verifiedbootstate=orange`. AOSP AVB README defines orange as UNLOCKED (Android Specific Integration section). Source: https://android.googlesource.com/platform/external/avb/+/android17-release/README.md

Evidence grading:
- **A:** captured live bootargs contain the literal `androidboot.verifiedbootstate=orange`.
- **AOSP standard meaning:** orange denotes UNLOCKED.
- **D:** no published ABL disassembly/xref shows that ABL generated this property from a live unlock-state branch; no independent bootloader state readback is included in the reviewed reports.
- The same bootargs include `userlock=locked`. That is Huawei-specific, not an AOSP AVB state variable; do not equate it with AVB LOCKED or use it to negate the orange token without Huawei-specific source.

Therefore “orange was present” is proven; “ABL's actual secure-state branch was unlocked and used permissive AVB handling” is suggested by standard semantics but not directly proven by the published ABL code evidence.

### 3.5 Huawei-specific AVB conclusion

No published evidence establishes that Huawei ABL uses AOSP `libavb` unchanged, passes the unlocked allow-verification-error flag, or performs no independent hash/authentication checks on boot, DTBO, ABL/XBL or other images. The ABL report's direct references establish DTB/DTBO and RAM code, not an AVB verification call graph.

- **Possible under AOSP semantics:** yes, flags=3 skips descriptor processing while the top-level vbmeta signature/key/rollback path remains.
- **Proven for Huawei ABL:** no.
- **Proven that modified boot and DTBO are accepted:** no.
- **Proven that root vbmeta signature need not be checked:** no; AOSP says the opposite.
- **Proven bypass / authorized signature path:** no.

## 4. Candidate first-boot minimum and overlay decision

### 4.1 Candidate base coverage reported by Window B

ROUND155 Window B measured the RAM-patched candidate base at 108,680 bytes, SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60`. It reports 905 nodes, 239 phandles and no `/__symbols__` in the base.

The first-boot minimum census identifies RAM (three windows totalling 12,185 MiB), timer at `0x17c20000`, GIC-v3/PDC, PSCI, GCC and RPMh clock/power controllers, PM8150/PM8150L regulator hierarchy, enabled UFS host and PHY, and internally resolved UFS supply/phandle, clock/reset/PHY/interconnect/power-domain references.

The report says the only two `status=okay` nodes are UFS host and PHY; 91 nodes are disabled and 811 status-unset. Display, camera, audio, WLAN, sensor and remote-DSP nodes remain disabled. This supports a deliberately minimal storage/rescue boot base, not a full functional tablet tree.

### 4.2 Important handoff omissions / dependencies

- Candidate `/chosen` has zero properties; bootargs/initrd must be injected by the bootloader. The ABL report has `/chosen` update strings for bootargs, RNG/KASLR seeds and initrd start/end, but the exact execution branch is not published.
- Candidate debug UART node `/soc@0/geniqup@ac0000/serial@a90000` is present but disabled. The live bootargs' earlycon address maps to this node. The UART overlay is an optional rescue-console enhancement in Window B's test, not proof of console availability in ABL.
- Candidate is 905 nodes, versus 3,471 nodes in the stock base and 4,566 in the live tree. This does not prove omitted nodes are all needed; it does mean candidate is not a full stock-tree substitute.
- Window B's conclusion that no stock Entry 2 fragment adds a proven first-boot essential is based on static target census against candidate and its reported initramfs inspection. It does not prove the bootloader can skip overlay application.

### 4.3 Candidate-specific target-path overlay test

Window B compiled a 199-byte overlay using `target-path = "/soc@0/geniqup@ac0000/serial@a90000"` and changing only `status` from disabled to okay. Host `fdtoverlay` returned RC=0; the merged tree differed in exactly one property; RAM tuples and all 18 reserved-memory intervals remained byte-identical; a negative nonexistent-target control failed with `FDT_ERR_NOTFOUND`.

This is a useful host-side test of target-path merging against candidate DTB. It does **not** prove Huawei UFDT target-path support, ABL entry selection, or hardware boot.

### 4.4 No-overlay versus custom-overlay

- **No-overlay:** plausible because candidate base contains reported early-boot/storage essentials and stock Entry 2 contributes no identified first-boot-essential fragment. But ABL no-DTBO path and failure/fallback behavior remain unproven. `/chosen` handoff remains ABL-dependent. Status: **plausible, not proven, not authorized**.
- **Custom target-path overlay:** host-libfdt applicability is proven for the tiny UART change. Whether Huawei UFDT accepts target-path and whether loader applies a candidate overlay is unknown. Status: **host-tested only, loader acceptance unknown**.
- **Stock Entry 2/Entry 8:** remain incompatible with candidate in reported host libfdt tests (Entry 2: 0/166 external symbols without `-@`; 10/166 with scratch `-@`; 87/144 fragment targets remain missing). Reject unchanged stock entries.
- **RAM semantics:** candidate static three-window `reg` is measured, but ABL replacement/append semantics and interaction with bootloader DDR map remain unresolved.

Do not assemble a DTBO container or boot package on the assumption that either no-overlay or custom-overlay behavior is settled.

## 5. Backup, partition inventory and recoverability

### 5.1 What ROUND155 Window A verified

Window A reports 86 unique by-name names and 86 distinct block nodes, with no alias groups; 18 requested boot-chain targets present and captured; exact byte count equal to `blockdev --getsize64` for 18/18; host SHA-256 equal to independent device-side streaming SHA-256 for 18/18; local primary-copy readback SHA-256 equal for 18/18; second independent host-volume copies for 10/10 required targets, copied and hashed.

The captured set includes `abl`, `xbl`, `xbl_config`, `boot`, `dtbo`, root and several child/recovery vbmeta images, `ramdisk`, `recovery`/ramdisk/vendor and eRecovery counterparts. This is strong evidence those 18 named images were copied byte-exactly at capture time.

### 5.2 Why this does not authorize a narrow write

- The device is A-only in the report (empty slot suffix; no _a/_b partition set), so there is no proven alternate slot fallback.
- 86 names were enumerated, but the report does not establish a complete GPT map with all partition start/size geometry and boot-control/rollback metadata.
- Root vbmeta chain references `vbmeta_odm`, `eng_vendor`, `eng_system` and `version`; those are not in the reported 18-image capture list.
- No complete all-required-partition raw backup set is demonstrated.
- No exact-stock restore route was rehearsed or proven on the device.
- The report does not establish a working temporary-boot mechanism or recoverability after an ABL/boot-chain failure.
- A valid AVB signing/authorization path for modified images is not demonstrated.

A partition name inventory and a set of hashed copies are not equivalent to a complete GPT/boot-control/recovery map. Root access and KernelSU are not evidence of recoverability.

### 5.3 Recoverability gate

Before any write could be reconsidered, require complete GPT/partition geometry and sizes, raw backups of all relevant boot-chain and AVB chain partitions, independent hashes and second-copy verification, exact stock package hashes and image-to-partition mapping, a proven authorized exact-stock restore route and offline rehearsal, rollback-index/boot-control state capture, and a user-data preservation/risk plan.

## 6. Ranked blockers and smallest next step

| Rank | Blocker | Current grade | Exit evidence |
|---:|---|---|---|
| 1 | Huawei ABL AVB verification / unlocked-state branch / independent checks | **D** | ROUND156 Window A control-flow report with disassembly and exact branch/call graph, or equivalent exact-build trace |
| 2 | ABL no-overlay / DTBO selection / UFDT target-path / failure behavior | **B/D** | same exact-build control-flow report; identify fatal vs fallback branches |
| 3 | Candidate first-boot variant and RAM updater interaction | **B/C** | ROUND156 Window B variant report; explicit `/chosen`, memory replacement/append and required-node matrix |
| 4 | Root vbmeta signature verification result and accepted key policy | **D** | cryptographic verification against correct trusted public key and exact Huawei bootloader policy evidence |
| 5 | Complete backup + exact-stock restore path | **FAIL / incomplete** | full partition/GPT/boot-control capture, all relevant backups, proven restore rehearsal |
| 6 | Device runtime acceptance | **NOT RUN / NOT AUTHORIZED** | separately authorized controlled boot after every prior gate passes |

**Smallest next step:** obtain and review the two missing ROUND156 result reports on their stated branches. In particular, Window A must publish exact ABL AVB and DTBO control-flow evidence; Window B must publish its candidate variant comparison. Do not repeat device reads or try a boot to fill a report-publication gap.

After those reports, reconcile the ABL AVB signature/key/rollback branch with flags=3 and orange bootargs; whether ABL permits no DTBO or requires a selected overlay; Huawei UFDT target-path support; whether ABL overwrites or appends RAM tuples; candidate `/chosen` and initramfs handoff requirements; and all root vbmeta chain descriptor targets versus backup/restore coverage.

## 7. Boundaries and final stop

- No device, ADB, root, fastboot, recovery, reboot, partition read/write, temporary boot or flash was performed by AI2 in ROUND156.
- No source edit, build, package generation, DTBO container modification, key extraction, AVB bypass or signing operation was performed.
- Findings are read-only review of published evidence; missing ROUND156 reports are explicitly marked missing, not inferred.
- **Final disposition: package deliverable NO-GO; temporary boot NO-GO; partition flash/write HARD NO-GO.**
- **STOP — ROUND156 AI2 review report only.**