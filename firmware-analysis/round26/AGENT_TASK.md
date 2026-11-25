# ROUND26 — compare inherited SM8250 reserved-memory against HOS4.3 base FDT

Owner: local WorkBuddy Agent; local offline read-only comparison
Device: Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250
Kernel: ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## Purpose

ROUND24 proved the HOS4.3 base FDT has 37 /reserved-memory children and the current board rev2 candidate inherits generic reserved-memory definitions from the pinned ACK sm8250.dtsi. Those generic nodes have not yet been proven to match the actual HOS4.3 ranges.

This round must perform a local-only exact interval comparison between every reserved-memory tuple in the pinned ACK sm8250.dtsi and HOS4.3 ROUND19 base_2.dts. Do not upload any physical address or raw tuple. Report only whether two intervals are EXACT_MATCH, SAME_BASE_DIFFERENT_SIZE, OVERLAP, HOS_ONLY, ACK_ONLY, or NO_CLEAR_MATCH, plus coarse size class.

The aim is to determine whether blindly inheriting the generic SoC reserved-memory nodes is safe, or whether the device DTS must explicitly override or disable some inherited generic reservations before any boot test.

## Inputs

- Existing ROUND19 decompiled HOS4.3 base_2.dts work copy.
- Exact pinned ROUND18 ACK source file arch/arm64/boot/dts/qcom/sm8250.dtsi.
- Current main dts/dby-w09-ack18-board.dts.rev2.candidate (read-only).
- ROUND24 report firmware-analysis/round24/round24-hos43-reserved-memory-and-consumer-map.txt.

## Hard boundaries

- Reuse existing local files only. No re-extraction, WSL deployment, repo sync, download, install or external device access.
- Read-only; do not modify source, DTS, config, firmware, build files, patch files, reports or branches.
- Do not run dtc, Kconfig, Kleaf/Bazel, kernel build, boot packing, AVB or signing.
- No ADB/fastboot/recovery, reboot, unlock, root, flash or partition write.
- Do not upload raw physical start/end addresses, raw reg tuples, hashes of coordinates, serials, MACs, IMEI or keys.
- Do not make RAM/reserved-memory edits or recommend guessed addresses.

## Work package A — enumerate ACK SM8250 reserved-memory definitions

For every immediate child under the pinned sm8250.dtsi /reserved-memory block:
- sanitize node unit-address suffix;
- record node label/name, compatible, no-map/reusable, size/alloc-ranges style, and coarse size class only;
- keep exact interval only in local memory for comparison;
- note whether node has any consumer in sm8250.dtsi via memory-region or another exact phandle reference.

Include all actual child nodes, not merely the first five.

## Work package B — compare with HOS4.3 intervals

Use ROUND19 base_2.dts and ROUND24's 37-node inventory.
- parse each fixed reg tuple and each dynamic size/alloc-ranges pool separately;
- compare actual intervals in memory without printing them;
- for every ACK child report one class: EXACT_MATCH / SAME_BASE_DIFFERENT_SIZE / OVERLAP / ACK_ONLY / NO_CLEAR_MATCH;
- for every HOS4.3 child report whether it has an exact ACK equivalent or is HOS_ONLY;
- dynamic size/alloc-ranges pools without a fixed address cannot be claimed equal to fixed HOS reg tuples;
- identify duplicate or nested ranges, overlaps, and same-name/different-range cases;
- report only coarse size class (KiB, low MiB, tens of MiB, hundreds of MiB), never byte count or address.

Be exact about the number of nodes compared and any parser limitation. Do not assume node names imply interval equivalence.

## Work package C — what rev2 actually inherits

Map which generic ACK nodes become part of the compiled board DTB because rev2 includes sm8250.dtsi:
- identify all inherited no-map carveouts;
- identify all inherited shared-dma-pool/CMA nodes;
- identify consumers enabled in the base SoC DTSI even if the minimal board file leaves some top-level devices disabled;
- distinguish the mere presence of a reserved node from whether its consumer probes;
- identify whether any ACK inherited fixed interval overlaps a different HOS4.3 reservation or an ordinary HOS4.3 RAM region (if RAM ranges are not known, report UNKNOWN).

## Work package D — safe recommendation

Classify each inherited ACK node as:
- exact same interval as HOS4.3;
- safe structural alias/name difference only;
- overlapping/different size;
- unmatched / potentially unsafe;
- no fixed interval because dynamic pool;
- unresolved without final ABL FDT.

Answer:
1. Is inheriting the pinned upstream sm8250.dtsi reserved-memory tree safer than omitting all 37 HOS4.3 reservations?
2. Does it risk reserving the wrong physical ranges or overlapping ABL/secure firmware memory?
3. Can a minimal UFS-only candidate safely keep those generic nodes?
4. What must remain blocked until the final post-ABL FDT is known?

Do not delete/replace any node or invent an override. Any proposed change is design-only and must name the exact node and evidence, without addresses.

## Deliverable

Upload one UTF-8 sanitized report only:
firmware-analysis/round26/round26-sm8250-vs-hos43-reserved-memory-interval-audit.txt
to branch firmware-audit-v1.

The report must contain:
- PASS/PARTIAL/BLOCKED for each work package;
- complete sanitized ACK/HOS reserved-node comparison table;
- exact number of tuples compared;
- match/overlap classifications only, no raw coordinates;
- implications for the current rev2 candidate and the final memory gate;
- statement that all physical coordinates were compared locally and redacted from upload.

Do not upload scripts, raw DTS/DTB/DTBO or physical memory ranges.

## Stop rule

After the one report is uploaded, stop. Do not edit DTS, patch driver, build, package/sign or contact the device.