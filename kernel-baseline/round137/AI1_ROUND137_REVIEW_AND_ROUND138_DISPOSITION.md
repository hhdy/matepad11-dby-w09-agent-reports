# AI1 ROUND137 Review and ROUND138 Disposition — DTBO Variant Conflict

- Reviewer: AI1 (ChatGPT)
- Date: 2026-11-26
- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel baseline: ACK android17-6.18.33_r00, pinned commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- R3 candidate tree remains: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- Reviewed WorkBuddy report: firmware-analysis/round137/round137-hos43-abl-existing-artifact-and-trace-audit.md
  - branch: firmware-audit-v1
  - blob: 9b7eb105b66780554dd59672d0053296f48c069d
  - report outcome: BLOCKED — ABL ARTIFACT/TRACE NOT PRESENT

## 1. AI1 disposition

ACCEPTED WITH A MATERIAL VARIANT / HANDOFF FINDING.

ROUND137 correctly reports that no ABL binary exists in the authorized corpus and that the final post-ABL FDT bytes, /rootparam values, exact ABL entry route, and x0 handoff record are unavailable. The absence of an ABL binary does not negate the evidence found in the already-existing device property snapshot.

The most important partial trace is:
- captured Android boot property: ro.boot.dtbo_idx=2;
- when mapped against the previously extracted HOS4.3 package DTBO table, index 2 corresponds to board-id decimal 8206 / 0x200E, variant DBY_W09_VD;
- entry 8 corresponds to decimal 8298 / 0x206A, variant DBY_W09_VG.

This mapping is conditional because the actual device dtbo partition was not read and verified byte-identical to the extracted package. The device snapshot also reports unlocked / orange verified-boot state. Therefore:
- DIRECT: the existing device snapshot contains ro.boot.dtbo_idx=2;
- CONDITIONAL: if the device DTBO table matches the existing extracted package, that index maps to entry 2 / VD;
- NOT ESTABLISHED: factory-default selection, ABL matching policy, current on-device DTBO bytes, final applied fragments, final /rootparam values.

No device read, ADB retry, partition pull, or permission bypass is authorized by this review.

## 2. Concrete conflict with the current board-DTS / rootparam candidate

AI1 independently retrieved the exact R3 patch22 Git blob:
- patch22 blob: ab0108364c835d87ac35ca670347d9d0001a821d;
- resulting board DTS blob: 58293f7a62a50f8109886c92ce4b9cd14d7980e2.

The candidate board DTS sets:
qcom,board-id = <0 0>;

Its accompanying comment says the separate DBY-W09 DTBO is selected by board-id 0x206a and fills /rootparam.

The previously tested independent rootparam overlay draft is:
dts/dby-w09-ack18-rootparam.dtso.draft, branch ack18-dby-w09-dts-draft, blob 72a27c5646ed49d952b83a963fbacccfbf711570.

That overlay explicitly contains:
- root qcom,board-id = <0x206a 0>;
- rootparam qcom,boardid = <0x08 0x02 0x09 0x08>;
- qcom,board_name = "DBY_W09_VG";
- qcom,product_name = "DBY-W09";
- hardware_version = "SH1DBSLM";
- a generic huawei,modem_id sentinel.

ROUND23's composite test only proved syntax, symbol/fixup, and fdtoverlay mechanics for this VG overlay. It explicitly recorded that the composite root qcom,board-id remained <0 0>; a DTBO root property does not automatically propagate into the base tree through a fragment-only apply. ROUND23 did not create a DT table, did not prove the table entry metadata, and did not prove ABL selection.

AI1 decision: this VG rootparam overlay must not be treated as a confirmed overlay for the current tablet or packaged as-is. Do not yet replace it with VD values: exact entry-2 rootparam payload values and fixup behavior must first be compared directly using the existing local entry-2 artifact.

The 23-patch R3 candidate remains unchanged. This finding affects the unvalidated boot/DTBO packaging contract, not the already-passed offline build identity or Kleaf result.

## 3. A second material memory-structure delta

ROUND24's direct enumeration of the extracted HOS4.3 base FDT found 37 immediate /reserved-memory child nodes.

ROUND137's existing live-device DT directory listing records:
- /sys/firmware/fdt: 800,316 bytes, root-only and unreadable to the collecting shell;
- live /reserved-memory/: 39 child directories;
- live /memory/reg: 48 bytes, unread;
- /rootparam values: Permission denied.

This is a structural count delta of 2 between the previously parsed base FDT and the live device-tree directory listing. It may indicate additional nodes or a different effective tree, but the report does not expose the names/values and the original FDT bytes were not obtained. Do not claim the ABL added exactly two reservations; other explanations remain possible. Do not copy a guessed 39-node map or assume the original 37-node base map equals the final handoff.

This makes the need for a trustworthy final FDT stronger, not weaker. The RAM-map gate remains BLOCKED.

## 4. Existing report inconsistency that ROUND138 must resolve

The evidence corpus contains differing statements about /rootparam:
- ROUND7 dtbo_board_rootparam_matrix.csv marks rootparam_present=False for every entry.
- ROUND8 explicitly resolves fragment@143 in entry 8 to /rootparam.
- ROUND137 states all nine entries contain a rootparam overlay target and the corresponding property-name set, while also noting the target was not resolved in that round.

These may be different meanings of "rootparam present" (literal node versus fragment/fixup target), or a reporting inconsistency. ROUND138 must distinguish:
1. literal /rootparam node in the overlay FDT;
2. a fragment whose target is resolved by __fixups__ to base symbol rootparam;
3. the actual __overlay__ payload properties and values;
4. table entry ID/rev fields (separate from overlay-root qcom,board-id).

Do not silently pick one older statement.

## 5. ROUND138 is assigned to WorkBuddy Agent

The next useful operation requires the already-existing local binary work copies (E7) and existing E5 device-property text. It is therefore assigned to WorkBuddy Agent, not AI2.

ROUND138 will:
- verify the existing local dtbo_entry_2.dtbo and dtbo_entry_8.dtbo hashes against ROUND137's appendix;
- compare entry 2 and entry 8 rootparam fragment/fixup/payload semantics;
- produce a nine-entry rootparam presence/target matrix that resolves the ROUND7/8/137 terminology conflict;
- compare entry 2 vs entry 8 UFS Host / UFS PHY / PMIC supply-relevant overlay changes;
- confirm the provenance and capture metadata of the existing ro.boot.dtbo_idx=2 line from the already-collected device snapshot, without any new device access;
- record the 39-vs-37 live/base reserved-memory count delta and whether any already-existing directory listing provides a sanitized node-name reconciliation;
- state clearly whether entry 2 is a more plausible variant reference for this device, while preserving the caveat that the actual on-device DTBO partition is unverified.

No firmware re-extraction, ABL partition pull, ADB/fastboot, device connection, source modification, DTB/DTBO compilation, image packaging, AVB operation or flashing is allowed.

## 6. Stop rules and current project state

- Do NOT modify patch22, any of the 23 R3 patches, the R3 tree SHA, board DTS, rootparam DTBO, DTBO table, boot/ramdisk, AVB or kernel config before ROUND138 is reviewed.
- Do NOT rebuild the Image or rerun R3. It is already accepted as PASS — BUILD/DTB INTEGRATION ONLY.
- Do NOT reattempt the permission-denied /sys/firmware/fdt pull or read the abl partition.
- Do NOT use the public HOS4.2 Linux 7.0 DTBO as proof of HOS4.3 Android 17 selection.
- No real-device test is authorized.

Current gates:
- ROUND135 R3 offline build/DTB integration: PASS.
- ABL binary/version and final FDT/entry route: BLOCKED.
- DTBO index identity: PARTIAL / CONDITIONAL (index 2 property is captured; package mapping depends on unverified device table identity).
- rootparam variant for this tablet: BLOCKED pending ROUND138 and final FDT values.
- RAM/reserved-memory final handoff: BLOCKED (37 base vs 39 live structural count, unread values).
- PMIC input parent rails: BLOCKED.
- UFS MMCX/MX runtime corner proof: BLOCKED.
- Boot / ramdisk / DTBO / AVB package contract: BLOCKED.
- Phase G / first real boot: NOT RUN.

The first real-device test remains prohibited until these boot, memory, power, UFS and reversible recovery conditions are independently closed and separately authorized.
