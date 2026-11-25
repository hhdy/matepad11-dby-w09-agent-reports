# ROUND24 — HOS4.3 reserved-memory and memory-region dependency inventory

Owner: local WorkBuddy Agent; read-only local firmware/source audit
Device: Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250
Kernel: ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## 0. Purpose

The HOS4.3 base FDT contains 34 reserved-memory children. The current ACK board DTS rev2 candidate contains no reserved-memory reconstruction. The same-device public Linux 7.0 reference has only four HOS4.2-derived reserved-memory nodes, including a splash_region path reportedly looked up by ABL. Do not copy its addresses into HOS4.3.

ROUND24 must use the existing ROUND19 decompiled HOS4.3 base DTB and nine DTBO work copies to inventory the reserved-memory tree and all consumer references. The goal is to identify categories, exact node labels/names, no-map/reusable flags, and devices that reference each carveout, while keeping every physical reg tuple out of the uploaded report. Cross-reference the pinned ACK SM8250 DTSI and the current main board rev2 candidate to identify which hardware consumers are absent or deferred.

## 1. Strict boundaries

- Reuse only existing ROUND19 local decompiled files and prior ROUND18 source tree. Do not re-extract firmware, deploy WSL, repo sync, download or install tools.
- Read only; do not modify source, DTS, DTBO, firmware, .config, patches, branches or reports.
- Do not run olddefconfig, Kconfig, Kleaf, Bazel, dtc builds or kernel builds in this round.
- Do not create a memory map or write any physical RAM address into a candidate DTS.
- Do not expose any raw physical address/range, serial, MAC, IMEI or key material in the uploaded report. Hashes may be used locally but redact physical coordinates in all output.
- Do not connect to the tablet or use ADB/fastboot/recovery, reboot, unlock, root, flash or write partitions.
- Do not touch ack18-dby-w09-dts-draft, ai-parallel/stagea-port-until-boot or PR #1.

## 2. Work package A — enumerate HOS4.3 /reserved-memory

From the existing base_2.dts decompiled in ROUND19, report all 34 child nodes by:
- node path/name (omit unit-address suffix only if it encodes a physical address; if so replace the suffix with [redacted]);
- compatible, if present;
- phandle label/id only if not address-derived or identifying; do not upload raw phandle if unnecessary;
- reg: report only tuple count, address/size cell counts and total byte size class (e.g. 4 KiB, 1 MiB, tens of MiB), never base address or end address;
- flags/properties: no-map, reusable, alignment, alloc-ranges, linux,cma-default, status, shared-dma-pool, removed-dma-pool or vendor qcom/huawei tags;
- inferred category with evidence: XBL/ABL/AOP/SMEM/mailbox, PIL firmware, modem, ADSP/CDSP/SLPI, GPU, camera, display/splash, secure/QSEE/TrustZone, ramoops/crash log, CMA/DMA pool, or unknown.

Do not force an inferred category where no compatible/property/consumer confirms it. Mark UNKNOWN rather than guess.

## 3. Work package B — resolve every memory-region consumer

Scan the already-decompiled HOS4.3 base DTS and nine overlay DTS texts for:
- memory-region and memory-region-names properties;
- qcom,mem*, huawei,*mem*, qcom,peripheral-mem*, qcom,firmware-name / PIL / remoteproc references;
- ramoops, qcom,rmtfs, qcom,smem, shared-dma-pool, linux,cma and reserved-memory compatible references;
- any phandle referencing one of the 34 reserved-memory children.

For each reference, report consumer node path/name (sanitize unit-address suffixes), compatible, property name and target reserved node label/name. Do not report physical coordinates.

Treat base tree and each DTBO separately. Do not apply or merge all nine overlays. If a node is introduced or changed in a DTBO, report which entry index and board-id candidate; runtime selection remains UNKNOWN.

## 4. Work package C — compare with current ACK rev2 board candidate

Inspect the main-branch dby-w09-ack18-board.dts.rev2.candidate and exact pinned ACK sm8250.dtsi:
- Does the candidate currently define /memory? Does it define /reserved-memory?
- Which memory-region consumer devices are enabled or disabled in the candidate?
- Which consumers are deliberately deferred (panel, camera, DSP, GPU, WLAN, audio, etc.)?
- Does the UFS Host/PHY first-stage path reference any reserved-memory region?
- Does UFS require any secure/DMA shared pool from base HOS4.3 tree?
- Are there generic SM8250 reserved-memory nodes in sm8250.dtsi that should be inherited?

Do not add nodes or values. Produce a gap matrix only.

## 5. Work package D — compare same-device public Linux reference without copying addresses

Use only the project knowledge already recorded or the public same-device Linux 7.0 DTS reference if already available in local cache. It has four reserved-memory entries in HOS4.2-era source, including splash_region and DFPS/crash entries. Compare by semantic node purpose only. Do not copy its physical ranges because it is HOS4.2 and has no proof of compatibility with HOS4.3.

Specifically answer whether the public reference demonstrates ABL dynamically creating memory and reserved-memory nodes, or only consuming a board DTS that predeclares those four nodes. Use explicit source evidence; if not shown, say UNKNOWN.

## 6. Work package E — implications for first boot

Classify each category into:
- boot-critical before UFS/system first-stage mount;
- required only when corresponding subsystem is enabled (GPU/display/DSP/camera etc.);
- firmware/ABL-owned reservation whose omission may overlap secure or remoteproc memory;
- vendor diagnostics / crash logging;
- unresolved.

Do not claim a subsystem is safe to omit merely because its driver is disabled in the initial candidate. Consider whether firmware already occupies the physical range before Linux boot.

Give a recommendation whether the current minimal rev2 board DTS is acceptable for a first kernel/UFS-only boot, or whether a subset of HOS4.3 reservations must be preserved first. If the actual final ABL FDT is unavailable and no evidence proves ABL adds reservations, keep this gate BLOCKED rather than invent data.

## 7. Deliverable

Upload one UTF-8 sanitized report only:
firmware-analysis/round24/round24-hos43-reserved-memory-and-consumer-map.txt
to firmware-audit-v1.

Include PASS/PARTIAL/BLOCKED per work package, exact source file paths and line numbers, 34-node inventory with physical coordinates redacted, complete consumer map, current candidate gap matrix, and a precise boundary statement.

Do not upload DTS/DTB/DTBO binaries, raw physical addresses, parser code, firmware or sensitive device identifiers.

## 8. Stop rule

After the single report is uploaded, stop. Do not edit DTS, change Kconfig, build kernel, package/sign or contact the device.