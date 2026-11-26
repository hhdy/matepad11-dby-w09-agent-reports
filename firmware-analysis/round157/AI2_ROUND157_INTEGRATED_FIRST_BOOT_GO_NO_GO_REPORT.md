# ROUND157 — Integrated First-Boot Strategy and Go/No-Go (AI2)

- Reviewer: AI2, independent reviewer
- Target: Huawei MatePad 11 DBY-W09 / SM8250
- Scope: read-only integration of ROUND156 Window A/B, ROUND155 boot-chain capture, ROUND154 candidate reproduction and official AOSP AVB semantics
- Disposition: **offline full-kernel build CONDITIONAL GO; integrated boot.img construction NO-GO; temporary boot NO-GO; partition write HARD NO-GO**
- No device/ADB/root/fastboot/recovery/partition operation, source edit, kernel build, boot.img/DTBO construction, signing, key operation, reboot or flash was performed.

## 0. Executive decision

ROUND156 Window A and Window B reports are now published and have been read. The missing-input statement in AI2 ROUND156 is stale and is superseded.

The new evidence materially closes the ABL selector and overlay-control-flow questions:

1. The exact captured ABL walks appended boot-v2 FDT entries and also has a first-class single-FDT path. Its matching sequence is msm-id, board-id major/minor, then PMIC-id/best-match. A single candidate FDT is structurally acceptable if its required tags match; retaining three FDTs is not a proven requirement.
2. androidboot.dtbo_idx is an ABL selector output, not an input. ABL has explicit overlay skip paths, supports target-path, and returns non-fatally after overlay errors.
3. **Non-fatal does not mean atomic.** The report does not prove a failed overlay leaves the base FDT untouched. Blob installation precedes fixups/fragments, and fragment processing can fail after the apply routine has begun. No transactional rollback proof was published. Leaving stock DTBO unchanged and relying on a failed Entry 2 application is unsafe.
4. ABL actively rebuilds/writes /memory/reg from DDR configuration. The likely behavior is tuple-array replacement/rebuild, but the exact fdt_setprop versus fdt_appendprop primitive remains an acknowledged decoder gap. Candidate RAM tuples are not proven to survive boot.
5. Candidate variants A/B/C are reproducible and internally consistent on the host. B (UART enabled directly in the base DTB) is the best base-DTB candidate for future offline integration because it avoids an overlay dependency while retaining a debug console. C is the corresponding target-path overlay route if an overlay is required. Neither is a flashable or boot-ready package.
6. flags=3 sets both AOSP flag bits. Under AOSP libavb, vbmeta image authentication, key acceptance and rollback checks precede the VERIFICATION_DISABLED descriptor-skip branch. The descriptor walk is skipped. The exact Huawei ABL report still leaves top-level signature/key/rollback interaction and Huawei-specific acceptance checks unresolved; no unconditional AVB bypass is established.
7. ROUND155's 18/18 captured images are byte/hash verified, but the set is not a complete boot-chain/recovery set. Four root-vbmeta chain targets are absent from that capture list, and there is no complete GPT geometry, rollback/boot-control capture, proven restore-mode entry or actual stock restoration rehearsal.

**Final gate:** continue offline kernel engineering only after confirming the AI1 integration baseline. Do not assemble an integrated boot.img, temporary boot or write partitions on current evidence.

## 1. Evidence coverage and provenance

### 1.1 Reports read

- ROUND156 Window A — exact ABL control flow, RAM updater, AVB gate:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round156-abl-control-flow-avb-and-overlay-gates/firmware-analysis/round156/WORKBUDDY_A_ROUND156_EXACT_ABL_CONTROL_FLOW_AND_AVB_GATE_REPORT.md
- ROUND156 Window B — candidate first-boot DTB variants:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round156-candidate-dtb-firstboot-package-variants/firmware-analysis/round156/WORKBUDDY_B_ROUND156_CANDIDATE_FIRSTBOOT_DTB_VARIANTS_REPORT.md
- Prior AI2 ROUND156 report — its missing-Window-A/B statement is stale:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round156-updated-avb-first-boot-decision/firmware-analysis/round156/AI2_ROUND156_UPDATED_ABL_AVB_FIRST_BOOT_DECISION_REPORT.md
- ROUND155 Window A — live partition backup and ABL/XBL capture:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round155-readonly-bootchain-backup/firmware-analysis/round155/WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE_REPORT.md
- ROUND155 Window B — candidate-specific minimal overlay:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round155-candidate-overlay-minimal-plan/firmware-analysis/round155/WORKBUDDY_B_ROUND155_CANDIDATE_SPECIFIC_DTBO_MINIMAL_OVERLAY_REPORT.md
- ROUND154 Window A — RAM patch and boot-package gate:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round154-candidate-dtbo-symbol-fixup-boot-packaging/firmware-analysis/round154/WORKBUDDY_A_ROUND154_MINIMAL_RAM_PATCH_AND_DTBO_BOOT_PACKAGE_GATE_REPORT.md
- ROUND154 Window B — independent candidate/DTBO reproduction:
  https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round154-true-independent-ram-reserved-hash/firmware-analysis/round154/WORKBUDDY_B_ROUND154_INDEPENDENT_PATCH_AND_DTBO_REPRODUCTION_REPORT.md

### 1.2 Required AI1 integration report unavailable

The taskbook names:
kernel-baseline/round156/AI1_ROUND156_DELIVERY_REVIEW_AND_ROUND157_PLAN.md

That exact path was not found on the ROUND157 AI2 branch or the inspected repository branch trees/default branch. No contents were available to review. This is an input-coverage limitation, not evidence that AI1 did not perform the work. This report therefore does not assert AI1's current accepted source commit, build configuration or integration status. Verify and publish that report (or provide its corrected path/branch) before treating the offline full-kernel build recommendation as unconditional.

## 2. Exact ABL findings — updated from ROUND156 Window A

### 2.1 Artifact identity and confidence

ROUND155 Window A records the live ABL partition as 4,194,304 bytes, SHA-256:
b39de91b88ef13db83892cd2e8dc4b914f7f9ed86954039fb1f64fbbf8460011

Its embedded LZMA payload was decompressed and identified as AArch64 PE32+, SHA-256:
a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404

ROUND156 Window A re-hashed ABL, XBL, XBL_CONFIG and the decompressed PE payload and reports all identities matching ROUND155. Branch topology and string/data xrefs are graded A by that report; unresolved raw instruction words are not promoted to proof.

### 2.2 Boot-v2 FDT selection: multi-FDT and single-FDT

**Demonstrated by exact ABL control-flow (Window A):**

- A loop back-edge at 0x3a338 (cbnz w19, 0x39e8c) re-enters the FDT entry walk. The code has both “Single appended DTB found” and “Not the single appended DTB” branches.
- Matching sequence:
  1. qcom,msm-id;
  2. qcom,board-id, with separate major/minor checks;
  3. qcom,pmic-id, with a best-match accumulator.
- The code logs deletion of non-fitting entries and “Best match DTB tags”; no suitable match leads to “Couldn't find the suitable DTB”.
- A single appended FDT is a normal code path. There is no demonstrated requirement for at least three FDTs.

**Implication:** the candidate does not need to retain three FDTs solely because stock contains three. A single-FDT boot-v2 candidate is structurally possible if its required root tags match. Candidate msm-id <0x164 0x20001> matches stock slot 0 (kona v2.1). However, no captured ABL runtime log proves the exact board/PMIC values or that this candidate would be selected on-device. Structural acceptance is not a proven runtime match.

### 2.3 DTBO index is an ABL selector output

The “Dtbo count / LocalBoardDtMatch” logging is in the same board-match function. androidboot.dtbo_idx and androidboot.dtb_idx are referenced from the command-line builder as write/append operations. Window A found no evidence that ABL reads androidboot.dtbo_idx back as selector input.

**Conclusion:** androidboot.dtbo_idx is an output of ABL selection, not a control knob supplied by candidate bootargs. The captured live boot reported dtbo_idx=2 / Entry 2, but the exact runtime value-producing branch and candidate-specific selected index are not fully recovered.

### 2.4 Explicit no-overlay/skip path

The exact ABL has gates before the overlay call, including null/no-blob and hyp-DTBO null/bad-header paths, plus override-DTB load gates. The apply wrapper is called only after a usable overlay is found. Thus a no-overlay/skip path exists in ABL.

This does **not** prove that simply leaving stock DTBO unchanged causes the no-overlay path to be taken. If the selector loads stock Entry 2, ABL can proceed into overlay application. The candidate must not rely on a skip condition that has not been explicitly selected and verified.

### 2.5 target-path support is proven; overlay failure is non-fatal but atomicity is not

Window A identifies distinct code paths for fragment target (phandle) and target-path (string path). The target-path branch resolves a path through the UFDT path lookup routine. This directly supports the fragment form used by Window B's 199-byte UART overlay.

The ApplyOverlay wrapper validates input, calls fixup and fragment routines, routes error returns to a common return path, and its caller logs failure and rejoins normal boot flow. **Overlay application failure is non-fatal to the traced boot flow.**

However, the report does not prove failure occurs before any fragment mutates the base FDT:
- ufdt_install_blob is called before fixups/fragments;
- fragment processing is inside the apply routine and can return an error;
- no rollback/transactional restore of earlier fragment changes is demonstrated;
- no report establishes that all validation completes before any base-tree mutation.

Therefore partial application on a later fragment failure remains possible. Safe interpretation: **non-fatal return, mutation atomicity unknown** — not “failed overlay leaves the base untouched.”

**Decision on unchanged stock DTBO:** do not leave stock DTBO bytes unchanged and rely on Entry 2 failing harmlessly. Stock Entry 2 was shown incompatible with the current candidate by host-side fixup/target tests; exact ABL may continue after failure, but the resulting base tree could be partially modified. This is not an acceptable first-boot assumption.

### 2.6 /memory/reg updater: active rebuild; exact primitive unresolved

Window A identifies a dedicated active /memory updater at 0x3d9d0..0x3f358. It finds the memory node, checks address/size cell widths, derives tuples from DDR configuration / XBL handoff values, and writes address and size entries. It also writes ddr_device_type, rank and HBB properties separately.

- No explicit deletion of the whole /memory node was observed.
- There is no “skip if incoming reg is already non-zero” branch in the traced path.
- Best-supported model is rebuild/overwrite of the reg tuple array, not blind append to candidate values.
- Exact low-level fdt_setprop versus fdt_appendprop was not fully decoded, so replacement versus append semantics are not Grade A proof.
- Candidate prefilled three tuples must be treated as subject to ABL runtime rebuild, not as authoritative final RAM.

XBL config reports an unusable DDR prefix at 0x80000000 of size 0x600000 (6 MiB). The live tree reserves this prefix as hyp_region@80000000; it does not shift the first RAM base. Window A found no direct /reserved-memory rewrite in the /memory updater xrefs, but this absence-of-evidence statement is not proof no other ABL path can mutate reservations.

**RAM gate remains CONDITIONAL / NOT BOOT-SAFE-PROVEN.** Candidate RAM tuples match observed live windows arithmetically, but only controlled boot/readback could establish the actual runtime map. No such boot is authorized here.

## 3. Candidate variants A/B/C — Window B result

Window B independently rebuilt the frozen candidate variants in scratch and verified the original inputs remained unchanged.

| Variant | Description | Size | SHA-256 | Host result |
|---|---|---:|---|---|
| A | RAM-patched base, UART disabled, no overlay | 108,680 B | 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60 | exact reproduction |
| B | Same base; UART12 status changed directly to okay | 108,676 B | 47ca4ff748baf6e72bc4ab26c4369ef13a15df9443a0a8dac16135ac0a7e78c7 | exact controlled one-property change |
| C | A base plus 199-byte target-path UART overlay | 108,676 B merged DTB | 647af49b8c21198d9cba99fac444131aaf95e86c99b28af87b610fc46b30cea2 | host fdtoverlay output reproduced |
| Overlay C | target-path UART overlay | 199 B | 05494d47506a127f7826fb3db3f3319a9865fbcea5c59fd3c3f603653af1a1c2 | exact reproduction |

A/B/C contain 905 nodes, 239 phandles with no collision, one memory node, 18 reserved-memory children and the same three RAM tuples. UFS host/PHY phandle dependency closure passes static provider-cell-aware checks. All three /chosen nodes are empty. Window B proves B and C are semantically identical after host overlay application: their only difference from A is UART status changing from disabled to okay.

**Recommendation:** use **B as the preferred base-DTB variant for future offline integration** if a debug UART is desired. It avoids requiring an overlay merely to enable UART and is slightly smaller than A. A is the least-modified/no-UART alternative. C is the fallback design if the exact loader contract requires an overlay; ABL target-path support and host merge test make C technically plausible, but do not prove DTBO container selection or device acceptance.

Important qualification: B is a base-DTB choice, not proof stock DTBO will be skipped. If ABL selects and applies stock Entry 2, B remains exposed to partial-overlay risk. C likewise still needs a correct DTBO container, selector/index contract and AVB authorization. None of A/B/C is flash-ready.

The empty /chosen means bootargs, initrd start/end, RNG/KASLR and other handoff fields must be supplied by the boot chain as appropriate. ABL contains /chosen update strings, but candidate-side values and exact handoff ordering are not established by Window B. Do not invent candidate values from captured stock boot.

## 4. AVB flags=3, unlocked policy and orange state

### 4.1 Strict AOSP meaning and order

The observed root vbmeta header reports algorithm SHA256_RSA2048 and flags=3. AOSP defines:
- bit 0: AVB_VBMETA_IMAGE_FLAGS_HASHTREE_DISABLED;
- bit 1: AVB_VBMETA_IMAGE_FLAGS_VERIFICATION_DISABLED.

With both bits set, AOSP libavb skips the descriptor walk after earlier top-level vbmeta checks. In AOSP avb_slot_verify.c:
1. avb_vbmeta_image_verify authenticates the vbmeta image and extracts the signing key;
2. the top-level public key is checked through validate_vbmeta_public_key;
3. the rollback index is read and checked;
4. only then does VERIFICATION_DISABLED load requested partitions and return before descriptor traversal.

Thus under AOSP semantics, bit 1 does **not** mean the root vbmeta signature/key/rollback checks are automatically skipped. It means hash, hashtree and chained-partition descriptor processing is skipped. The root descriptors for boot/ramdisk/dtbo are not traversed on that AOSP path.

AOSP's AVB_SLOT_VERIFY_FLAGS_ALLOW_VERIFICATION_ERROR is a separate call-time policy. It can continue after public-key-rejected, verification and rollback-index errors, but not arbitrary I/O, malformed metadata or out-of-memory errors. It is needed for valid-but-unverified unlocked slots.

### 4.2 What the exact Huawei ABL report establishes — and does not

Window A reports that exact ABL bundles AOSP libavb 1.x, contains the VERIFICATION_DISABLED bit path, requires unlock-state and public-key-validation callbacks, and has explicit strings/branches including:
- Slot / allow verification error;
- State: Unlocked, AvbSlotVerify returned ..., continue boot;
- KeyMasterSetRotAndBootState;
- Huawei-specific androidboot.huawei_vbmeta.digest, AvbUpdateTaslot, ta_parts is not in vbmeta and SetVerifiedBootHash references.

This demonstrates an unlocked-state continuation policy exists in exact ABL. It does **not** establish that every modified image is accepted. Window A explicitly leaves unresolved whether the exact Huawei path short-circuits top-level signature/key/rollback checks under flags=3, and whether Huawei digest/TA/TZ rollback checks independently reject modified images. ROUND155 avbtool info_image did not run verify_image and did not validate root vbmeta signature against a trusted key.

**Conclusion:** flags=3 plus unlocked continuation makes descriptor bypass / permissive boot plausible, but there is no proven unconditional AVB bypass and no proven authorized signing/acceptance path. Do not rely on flags=3 as permission to construct or write modified images.

### 4.3 Orange state

ROUND151 live bootargs contain androidboot.verifiedbootstate=orange. AOSP defines orange as UNLOCKED (green = locked with non-user key; yellow = locked with user-set key).

ROUND156 Window A upgrades ABL-side evidence: AppendVBCommonCmdLine contains the verifiedbootstate value table (green, orange, yellow), and LoadImageAndAuthVB2 selects among these based on state/verification outcome. Therefore live orange is consistent with exact ABL's state-driven orange emission branch. The exact boolean distinction between orange and yellow remains partly undecoded.

Huawei's separate userlock=locked token is not the standard AVB verifiedbootstate field and does not negate the standard meaning of orange.

## 5. Backup completeness and restoration blockers

### 5.1 What is verified

ROUND155 Window A reports:
- 86 unique by-name names and 86 distinct block nodes, no aliases;
- 18/18 requested boot-chain targets present and captured;
- byte count equals partition size for 18/18;
- host SHA-256 equals independent device-side streaming SHA-256 for 18/18;
- primary readback hashes match for 18/18;
- second independent host-volume copies verified for 10/10 required targets.

Captured images include abl, xbl, xbl_config, boot, dtbo, vbmeta, vbmeta_system, vbmeta_vendor, vbmeta_cust, ramdisk, recovery/eRecovery images and recovery/eRecovery vbmeta images. The boot image itself has a verified capture and second copy. This is strong byte-integrity evidence for those captured partitions.

### 5.2 Exact missing items for a boot-only write

The root vbmeta chain descriptors name:
- present in capture list: boot, ramdisk, dtbo, vbmeta_system, vbmeta_vendor;
- **not present in the 18-image capture list:** vbmeta_odm, eng_vendor, eng_system, version.

Before a boot-only write could be reconsidered, the following remain missing:

1. Raw backups and independent hashes for every required chain target, including the four missing names above, plus any additional partition proven necessary by the complete chain map.
2. A complete GPT/partition geometry record (partition starts, sizes, types and mapping), not merely 86 by-name names and block-node identities.
3. Captured boot-control and rollback-index metadata, including actual stored rollback locations/values and any device-specific boot-success state.
4. A complete exact-stock firmware package/hash manifest and image-to-partition mapping.
5. A demonstrated AVB authorization/signing policy for the proposed modified image. flags=3 alone is not a signing or acceptance proof.

The device is A-only in the capture (ro.boot.slot_suffix empty; no _a/_b pair), so there is no proven alternate-slot fallback.

### 5.3 Exact missing items for recovery

The recovery and erecovery partition images were captured, but capture alone does not prove either can be entered or used to restore the original state. Missing:
- a supported, authorized way to enter the required restore mode on this exact device;
- proof that bootloader/restore path remains reachable after the proposed failure mode;
- exact-stock restoration instructions and verified image/partition mapping;
- an offline restoration rehearsal using the complete captured set;
- an actual authorized restore-route rehearsal/evidence on target, if required by the recovery plan;
- a user-data preservation and data-loss acceptance plan.

No restore rehearsal was reported. Therefore the current backup set is **not a proven recovery route**.

## 6. Distinct go/no-go decisions

| Activity | Decision | Rationale |
|---|---|---|
| (a) Offline full kernel build | **CONDITIONAL GO — separate offline task only** | It does not require a device boot or partition write and can validate source/toolchain. First verify AI1's accepted source commit, patch set, config and build manifest; the taskbook-named AI1 integration report was unavailable here. This ROUND157 review did not build anything. |
| (b) Offline integrated boot.img construction | **NO-GO** | Candidate/DTBO strategy is not closed; stock-overlay failure may partially mutate FDT; RAM updater semantics are not fully decoded; /chosen handoff is not fully specified; Huawei AVB/TA/signature acceptance and package authorization are unresolved. Do not create or label a boot.img as a first-boot or flashable artifact. |
| (c) Temporary boot | **NO-GO** | No exact supported temporary-boot route or ABL acceptance proof; A-only layout and incomplete recovery route remain. |
| (d) Partition write | **HARD NO-GO** | Incomplete chain backups/GPT/rollback metadata, no proven restore mode or rehearsal, and no demonstrated AVB authorization. No write authorization exists. |

## 7. Shortest exact next step

Do not reopen ARC/proxy/display audits.

1. Obtain/publish the missing AI1 ROUND156 integration report (or its corrected path/branch) so accepted kernel source commit, config and build inputs are explicit.
2. Ask Window A for one focused **offline ABL addendum only**: prove whether UFDT fragment application is transactional or can leave earlier fragments applied after a later failure, and decode the exact /memory/reg setter primitive (setprop versus append). Include instruction/call-site excerpts and confidence grade.
3. After step 1, run the separately authorized offline full-kernel build as a build-validation task. Do not assemble boot.img until overlay/DTBO path, RAM/handoff contract and AVB authorization are closed. Do not attempt temporary boot or partition writes.

## 8. Source references

### Project evidence
- ROUND156 Window A: exact ABL control flow and AVB gate (link in §1.1).
- ROUND156 Window B: variants A/B/C, hashes, UART diff, UFS closure and empty /chosen (link in §1.1).
- ROUND155 Window A: 18 verified partition captures, root vbmeta chain and exact ABL artifact (link in §1.1).
- ROUND155 Window B and ROUND154 Window A/B: candidate tree, stock Entry 2/8 incompatibility and independent reproduction (links in §1.1).
- Prior AI2 ROUND156: historical review; its missing-result-report statement is superseded (link in §1.1).

### Official AOSP AVB source
- avb_vbmeta_image.h: flag definitions (bit 0 and bit 1), vbmeta authentication-block/signature structure and requirement to verify against a trusted key:
  https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_vbmeta_image.h#55
- avb_slot_verify.c: vbmeta image authentication:
  https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_slot_verify.c#786
- avb_slot_verify.c: top-level public-key acceptance:
  https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_slot_verify.c#861
- avb_slot_verify.c: rollback-index check:
  https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_slot_verify.c#928
- avb_slot_verify.c: VERIFICATION_DISABLED branch and descriptor traversal:
  https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_slot_verify.c#977
- avb_slot_verify.h: ALLOW_VERIFICATION_ERROR behavior and permitted result classes:
  https://android.googlesource.com/platform/external/avb/+/master/libavb/avb_slot_verify.h#99
- AVB README: standard verifiedbootstate meanings, including orange = UNLOCKED:
  https://android.googlesource.com/platform/external/avb/+/android17-release/README.md

## 9. Final stop

- No device, ADB, root, fastboot, recovery, partition read/write, reboot or boot operation.
- No source edits, kernel build, boot.img/DTBO construction, signing, key extraction or AVB modification.
- No flashable package produced.
- **Final disposition: offline full kernel build CONDITIONAL GO; integrated boot.img NO-GO; temporary boot NO-GO; partition write HARD NO-GO.**

**STOP — ROUND157 AI2 review report only.**
