# ROUND143 — 2号 AI independent ARM64 boot-handoff / FDT memory-gate audit

- Executor: **2号 AI** (independent AI collaborator)
- Assigned by: **1号 AI (ChatGPT)**
- Not the executor: 2号 Agent; WorkBuddy Agent
- Target: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel: Android 17 ACK `android17-6.18.33_r00`
- Pinned ACK commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Candidate content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Mode: independent source/report review; public GitHub / pinned upstream source only; no device or private Agent workspace
- Report branch: `ai2/round143-arm64-fdt-memory-handoff-audit`
- Report path: `firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md`

## 0. Role split and why this task is parallel

This is a **2号 AI** review assignment. Do not describe yourself as 2号 Agent or WorkBuddy Agent.

- 2号 Agent is separately executing ROUND142, which is limited to reading its own ROUND140 retained build logs and candidate source tree. Do not access or request access to its private workspace.
- WorkBuddy Agent has completed ROUND137–ROUND139 local evidence collection. Do not ask it to repeat those rounds.
- 1号 AI owns candidate-source integration and the final independent disposition.
- ROUND143 is deliberately limited to the boot-time ARM64/FDT/memory handoff path. It does not repeat ROUND141's general architecture risk review and does not require any local build.

The purpose is to determine, from the exact pinned kernel source, what the current candidate DTB can and cannot supply to Linux, what additional information an EFI handoff could provide, and what exact evidence is still required before first boot can be considered.

## 1. Required prior evidence (read before analysis)

1. ROUND137 ABL artifact / trace audit:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round137/round137-hos43-abl-existing-artifact-and-trace-audit.md
2. ROUND138 DTBO variant / live-FDT delta audit:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round138/round138-dtbo-variant-and-live-fdt-delta-audit.md
3. ROUND139 HOS4.3 PMIC/UFS and boot/AVB static evidence audit:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md
4. ROUND140 independent build and candidate DTB audit:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round140-independent-preboot-tests/firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md
5. ROUND141 AI2 preboot risk review:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round141-candidate-preboot-risk-review/firmware-analysis/round141/AI2_ROUND141_CANDIDATE_PREBOOT_ARCHITECTURE_RISK_REVIEW.md
6. ROUND141 AI1 disposition:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round141/AI1_ROUND141_INDEPENDENT_REVIEW_AND_ROUND142_DISPOSITION.md

Do not treat report summaries as raw device evidence. Clearly tag each conclusion as one of:
- direct pinned-source evidence;
- direct published report evidence;
- inference constrained by those sources;
- unknown / not available.

## 2. Pinned source rules

Use only the exact ACK commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` for kernel implementation claims. The source repository identified by ROUND141 is `aosp-mirror/kernel_common`. Do not silently use current mainline or a newer Android common branch.

Likely relevant paths to inspect and verify at this exact commit (find the actual implementation paths if any differ):
- `Documentation/arch/arm64/booting.rst`
- `arch/arm64/kernel/head.S`
- `arch/arm64/kernel/setup.c`
- `arch/arm64/kernel/efi.c`
- `drivers/firmware/efi/libstub/arm64-stub.c`
- `drivers/firmware/efi/libstub/fdt.c`
- `drivers/of/fdt.c`
- `drivers/of/of_reserved_mem.c`
- `drivers/of/address.c`
- `Documentation/devicetree/bindings/reserved-memory/reserved-memory.yaml`

Use immutable source links containing the pinned commit and provide exact line numbers / symbol names. A path name or paraphrase without a commit-anchored source reference is insufficient.

## 3. Workstream A — distinguish AArch64 direct entry from EFI-stub handoff

Trace the two possible handoff paths as far as the pinned source supports.

### A1. Direct AArch64 boot protocol
Establish:
- required entry register contract (including what x0 must contain and what x1–x3 must be);
- how the kernel finds and validates the FDT;
- whether RAM availability is obtained from DT `/memory` tuples in this path;
- what the pinned source does with a memory tuple whose decoded size is zero;
- whether an alternate path can provide usable RAM when the DT has no non-zero memory tuple.

Do not assume that the vendor uses direct entry. Do not state that a zero-sized tuple is universally fatal unless all alternative memory sources and the actual entry path have been ruled out.

### A2. EFI-stub / EFI memory-map handoff
Establish from pinned source:
- how the AArch64 EFI stub is entered and how the EFI memory map is retained/published;
- exact FDT `/chosen` properties or other metadata used by the kernel to recover EFI memory-map information;
- whether and where EFI memory descriptors contribute to memblock or usable RAM;
- whether EFI metadata can compensate for an empty/zero-sized DT `/memory` tuple in this exact kernel build;
- which properties are mandatory, optional, or version/architecture-dependent;
- which evidence would distinguish actual EFI-stub entry from merely having an EFI-capable Image or from an ABL that internally uses UEFI services but launches the kernel through the non-EFI entry.

Explicitly separate:
1. ABL internally using UEFI;
2. loading an EFI PE/COFF Image;
3. entering the kernel through the EFI stub;
4. kernel actually receiving a valid EFI memory map.
These are not interchangeable claims.

### A3. Evidence mapping to DBY-W09
Compare the pinned-source contract to the accepted project facts:
- ROUND140 candidate DTB `/memory@80000000` has `reg = <0 0x80000000 0 0>` (one zero-size tuple).
- ROUND141 confirms `early_init_dt_scan_memory()` skips zero-size tuples.
- ROUND137 found no ABL binary or final ABL→Linux FDT trace in the authorized corpus.
- The only partial bootloader-published property is `ro.boot.dtbo_idx=2`; it is not proof of EFI entry or a memory map.
- No complete `/chosen/linux,uefi-*` property capture or equivalent EFI map data has been established.

Give a clear verdict for the current candidate:
- what is definitely absent from the candidate DTB;
- what could still be supplied by a proven EFI handoff;
- what is presently unknown;
- whether there is any evidence that the target ABL uses that path.

## 4. Workstream B — reserved-memory and usable-memory semantics

Trace the exact pinned-source handling of:
- root `#address-cells`, `#size-cells`, and `ranges` for `/reserved-memory`;
- static `reg` reservations;
- dynamic reservations using `size`, `alignment`, and `alloc-ranges`;
- `no-map`, `reusable`, and any mutually exclusive/invalid combinations;
- `linux,usable-memory-range` and its effect/order relative to ordinary memory scanning;
- reservation setup order relative to memblock / CMA / initrd / other early consumers, where applicable.

For each behavior, cite the exact pinned source function(s) and line ranges. Explain what each property actually does; do not infer that a reserved-memory child automatically reserves memory unless the binding and code path support that claim.

### B1. Compare evidence without mixing unlike trees
Keep these reported facts separate:
- ROUND138/139 HOS4.3 base FDT #0: 37 direct `/reserved-memory` children.
- ROUND140 candidate DTB: 18 direct `/reserved-memory` children.
- ROUND137 live filesystem listing: `st_nlink=39`, interpreted as 37 direct child directories; this is not a readable final FDT and provides no `reg` ranges.
- The actual post-ABL FDT handed to Linux remains unavailable.

Do not call 18-versus-37 a proven defect. Do not copy all vendor reservation nodes into the candidate. Determine which exact per-node fields are required to compare ownership safely: node path/name, `compatible`, `reg` or dynamic `size`, `alignment`, `alloc-ranges`, `no-map`, `reusable`, status, phandles, and consumer references as relevant.

### B2. Candidate safety implications
State whether the current candidate DTB alone proves:
- a valid usable RAM map;
- no overlap between usable RAM and reserved regions;
- that every vendor-required firmware carveout is preserved;
- that Linux will not allocate over modem / ADSP / secure / framebuffer / bootloader-owned memory;
- that EFI memory descriptors (if present) do or do not override the DT reserved-memory map.

Do not mark any item PASS without evidence.

## 5. Workstream C — define the minimum sufficient evidence bundle to close this gate

Produce an exact evidence checklist with three classes:

1. **Required from final post-ABL FDT**:
   - all non-zero usable RAM tuples and cell encoding;
   - complete `/reserved-memory` node tree and every child's properties needed to compute actual ranges;
   - relevant `/chosen` boot metadata;
   - FDT total size, root compatibility/model, and evidence this is the exact FDT passed to Linux (not merely the HOS package base DTB).
2. **Required to identify the handoff route**:
   - entry method (direct arm64 entry or EFI stub);
   - x0 / EFI-stub handoff evidence as applicable;
   - EFI system table / memory-map metadata and descriptor parsing evidence if EFI;
   - exact `/chosen/linux,uefi-*` values if that is how this pinned source consumes the map;
   - distinguish bootloader UEFI implementation from kernel EFI-stub entry.
3. **Required to compare the vendor map**:
   - board-variant identity and actual selected DTBO identity;
   - matching HOS4.3 base FDT + overlay selection evidence;
   - per-reservation range/flags/owner/consumer comparison, not child counts.

For each item, say whether it can be obtained from already-published artifacts, requires a future explicitly authorized read-only device capture, or requires an authoritative firmware artifact (e.g. actual ABL binary or final FDT dump). Do not prescribe permission bypass, root escalation or partition writes.

Output a minimum viable decision rule:
- which conditions must all be true before the memory/FDT gate can be marked PASS;
- which conditions are immediate FAIL;
- which conditions remain UNKNOWN and therefore keep first boot blocked.

## 6. Required report structure

Create:
`firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md`

The report must include:
1. executor identity exactly: **2号 AI**;
2. commit-pinned source index with links, line numbers, and symbol names;
3. direct-entry path trace;
4. EFI-stub and EFI memory-map path trace;
5. zero-sized `/memory` tuple impact with all conditions;
6. reserved-memory parser/runtime semantics;
7. candidate-vs-vendor evidence matrix;
8. evidence bundle and decision rules;
9. unresolved questions and explicit NOT FOUND items;
10. final status.

Allowed final statuses:
- **PASS — SOURCE CONTRACT AND EVIDENCE CHECKLIST COMPLETE** (this is a source-audit status only, not boot readiness);
- **PARTIAL — PINNED SOURCE TRACE COMPLETE, TARGET HANDOFF UNKNOWN**;
- **BLOCKED — PINNED SOURCE OR REQUIRED PROJECT EVIDENCE UNAVAILABLE**.

The report must prominently state:
**This task cannot authorize or establish first device boot. First boot remains BLOCKED / NOT AUTHORIZED.**

## 7. Strict prohibitions

- No device connection, USB, ADB, fastboot, recovery, serial, bootloader, reboot or device-side test.
- No root, partition reads, FDT read from the live device, privilege escalation, or permission bypass.
- No access to either local Agent's private workspace.
- No compilation, Kbuild, Kleaf, Bazel, dtc, dtbs_check, or runtime test.
- No source, DTS, DTBO, patch, config, candidate tree or Image modification.
- No firmware/dependency download and no network dependency fetch. Reading public pinned source via GitHub is permitted; do not fetch build inputs.
- No speculative regulator, memory range, reserved node, boot mode or AVB fixup.
- No flash, package, signing, AVB operation, or claim of boot readiness.

If a fact cannot be proven from the cited source or published evidence, write UNKNOWN / NOT FOUND. Do not use generic mainline behavior to fill a pinned-source gap.

## 8. Handoff and stop condition

Upload only this sanitized Markdown report to:
- branch: `ai2/round143-arm64-fdt-memory-handoff-audit`
- path: `firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md`

Read the uploaded file back from that branch and verify the content/blob identity. Then stop and wait for AI1 review. Do not automatically open another round or delegate work to either local Agent.
