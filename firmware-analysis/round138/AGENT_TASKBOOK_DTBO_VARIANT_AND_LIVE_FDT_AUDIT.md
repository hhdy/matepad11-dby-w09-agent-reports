# ROUND138 — WorkBuddy Agent taskbook: HOS4.3 DTBO entry-2 vs entry-8 variant and live-FDT delta audit

- Executor: WorkBuddy Agent (local executor only; not AI2)
- Dispatched by: AI1 (ChatGPT)
- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Firmware scope: existing extracted HOS4.3 package and previously collected read-only device records
- Kernel: ACK android17-6.18.33_r00, pinned 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- R3 candidate tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- Nature: local offline read-only comparison; no new firmware extraction and no device access.

## 0. Role and mission

This task belongs to WorkBuddy Agent because it requires access to previously existing local binary work copies and prior device text captures. It is not an AI2 task.

ROUND137 found a material discrepancy:
- existing device snapshot reports ro.boot.dtbo_idx=2;
- existing extracted HOS4.3 DTBO table maps entry 2 to board-id 8206 / 0x200E / DBY_W09_VD;
- entry 8 is board-id 8298 / 0x206A / DBY_W09_VG;
- current board-DTS comment and separately tested rootparam overlay were based on VG / entry 8.

The exact device DTBO partition has not been read. The index-to-variant mapping is conditional on the on-device DTBO table matching the existing extracted package. This task must not overstate that relationship.

Goal: use already-existing local copies and logs to compare entries 2 and 8 thoroughly enough to determine whether prior VG assumptions need to be revised, without touching the device or changing source.

## 1. Authoritative existing inputs — use only these

The existing ROUND137 report identifies:
- E1: existing HOS4.3 extracted-package workspace <workspace>/MatePad11_HOS43_LocalCheck_20261123_230849;
- E5: already-collected device text/metadata under <workspace>/Agent_Round2_Report/device;
- E7: already-established binary work copies under <round3-work>/dtb_work:
  - dtbo_entry_0.dtbo ... dtbo_entry_8.dtbo;
  - boot_fdt_candidate_0.dtb and other boot FDT candidates.

Known E7 identity from ROUND137 Appendix A:
- entry 2: 329,240 bytes, SHA-256 0633a6fbeebbad45c0f5572faf222c779e1cd51d253a6ef8282592a730ba3c8b;
- entry 8: 329,352 bytes, SHA-256 a7946352a86ab6e47b5ee79d84e5d6c4cf4e548c96b0221cec909f32ebd9d21d;
- base FDT candidate 0: 556,524 bytes, SHA-256 df2730f3d2e9bdabad874c3ef7399534c5c6070b046c4524224aa461ba2c70f7.

Do not search arbitrary drives or enumerate personal directories. If any listed path is missing, stop that subtask and record BLOCKED. Do not recover missing files by re-extracting firmware.

## 2. Task A — establish entry 2 / entry 8 identities

Using already-installed read-only tools and only existing E7 files:
1. Recompute file size and SHA-256 for entry 2, entry 8 and base FDT candidate 0.
2. Compare byte identities against ROUND137 Appendix A. Do not modify or touch timestamps.
3. Read DTBO FDT root metadata: compatible, root qcom,board-id, model.
4. Keep DT table entry ID/rev fields separate from root qcom,board-id and from properties inside a fragment overlay.
5. Confirm decimal/hex mappings explicitly:
   - entry 2: 8206 decimal = 0x200E;
   - entry 8: 8298 decimal = 0x206A.
6. Do not infer the physical board variant from a model string alone.

Report a mismatch as identity mismatch, not as permission to substitute another file.

## 3. Task B — resolve /rootparam correctly across all nine entries

For all nine dtbo_entry_0.dtbo through dtbo_entry_8.dtbo, distinguish these four concepts:

1. Literal overlay node named /rootparam, if present.
2. Fragment target references:
   - direct target-path = "/rootparam"; or
   - target = <placeholder> plus __fixups__ property naming the base rootparam symbol.
3. The fragment's __overlay__ payload fields and values.
4. DT table entry ID/rev/custom fields (if present in already-existing parser output) — not the overlay-root qcom,board-id property.

For each entry, produce a matrix with:
- entry index;
- DT table ID/rev (or unavailable);
- overlay-root qcom,board-id;
- fragment count;
- rootparam literal node present? (yes/no);
- rootparam target reference present? (yes/no);
- target resolved against base FDT symbol? (yes/no/unresolved/not checked);
- fragment ID(s) targeting rootparam;
- payload field names;
- payload identity values relevant to variant (qcom,boardid, qcom,board_name, qcom,product_name, hardware_version);
- huawei,modem_id only as same generic sentinel as all entries, different, or unavailable; do not print raw values.

Do not treat the existence of a rootparam symbol on the base FDT as proof that the selected overlay populates it. Do not equate a placeholder phandle with a resolved target.

### Resolve the prior report discrepancy

ROUND7 dtbo_board_rootparam_matrix.csv marks rootparam_present=False for every entry; ROUND8 explicitly proves entry 8 fragment@143 targets /rootparam; ROUND137 says all nine entries contain a rootparam overlay target. Establish whether the ROUND7 column meant a literal overlay node, a fragment target, or whether one of the reports is wrong. Cite the exact parser fields / original records used. Do not silently overwrite the older result.

## 4. Task C — compare entry 2 and entry 8 UFS / PMIC overlays

Compare resolved fragments and overlay payloads for both entries. Focus on:
- UFS Host target /soc/ufshc@1d84000;
- UFS PHY target /soc/ufsphy_mem@1d87000;
- any other fragment changing UFS, QMP UFS PHY, regulator, RPMh/RSC, PMIC, or power-domain nodes;
- vcc-supply, vccq-supply, vccq2-supply, vcc-voltage-level, current limits;
- qcom,vccq-parent-supply and qcom,vddp-ref-clk-supply;
- vdda-phy-supply, vdda-pll-supply, vdda-phy-always-on, max-current fields;
- status/enable properties on relevant nodes;
- UFS clock / reset / power-domain / interconnect references, if modified by either overlay.

Use resolved base-FDT symbol paths, not unverified node-name similarity. Produce a compact delta table:
- present in both and identical;
- present in both but changed;
- present only in entry 2;
- present only in entry 8;
- unresolved / unknown.

Do not assume entry 2 and entry 8 are functionally equivalent because they share the same model string or PMIC compatible.

## 5. Task D — verify existing dtbo_idx property provenance (no device access)

Use only the already-existing E5/E6 device-property capture files:
1. Find the exact existing ro.boot.dtbo_idx line and record the source file / line number.
2. Record the capture date/time and any already-recorded firmware build fingerprint/version fields needed to associate the property with the HOS4.3 capture. Redact serial/MAC/IMEI and all personal/device unique IDs.
3. Check whether ro.boot.flash.locked=0 and ro.boot.verifiedbootstate=orange are in the same capture; record them only as context.
4. Do not claim that the actual device dtbo partition matches the extracted package. The capture contains no partition readback hash unless an already-existing record proves otherwise.
5. Do not run adb, fastboot, shell commands on the device, or retry any denied read.

If the original E5 property file is unavailable, cite ROUND137's report and mark source-file-level provenance as PARTIAL.

## 6. Task E — reconcile live reserved-memory count 39 vs base count 37

Compare:
- ROUND24 base-FDT enumeration: 37 immediate children;
- ROUND137 existing live DT directory listing: 39 child directories.

Use only existing local files and logs. Determine whether E5 contains a previously captured sanitized list of live /reserved-memory child names or per-node metadata. If yes:
- compare names only, without physical unit-address suffixes;
- identify two apparent extra names or report the exact name/count delta;
- do not read property values if unavailable;
- do not infer sizes or physical coordinates.

If only the count is present, report:
STRUCTURAL DELTA CONFIRMED IN REPORTS; NODE IDENTITY / VALUES UNAVAILABLE.

Do not retry /sys/firmware/fdt reads, do not use root, and do not re-query the device.

## 7. Task F — decision and impact statement

Answer separately:
1. Is entry 2 a stronger variant reference for this tablet than entry 8, based on the current dtbo_idx=2 capture? State the exact conditionality.
2. Does entry 2's rootparam payload match the current VG overlay? If not, list the mismatching identity fields, without proposing replacement values that have not been directly read.
3. Does entry 2 change any UFS/PMIC properties relative to entry 8 that would affect the current minimal storage board DTS?
4. Is the 39-vs-37 memory-node count reconcilable from existing evidence?
5. Which previous assumptions must be marked UNKNOWN / stale pending final FDT?
6. What single smallest additional evidence would close the variant/rootparam question without using a forbidden device read?

Do not modify the current R3 patch series or draft DTS/DTBO. Do not create a patched candidate.

## 8. Prohibited actions

- No device connection, ADB, fastboot, recovery, USB or serial.
- No ABL partition pull, no boot.img/ramdisk/dtbo/vbmeta partition read, no attempt to access permission-denied paths.
- No permission bypass, privilege escalation, root, unlock, reboot or bootloader operation.
- No firmware download, unpack, extraction or re-extraction.
- No raw FDT/DTBO/boot/ramdisk/vbmeta/binary upload.
- No source/DTS/DTBO/Kconfig/config/patch/test/manifest changes.
- No compile, build, package, AVB operation, signing or flashing.
- No rerun of ROUND135/R3 Image/Kleaf/host tests.
- Do not treat xbl.img, tz.img or uefisecapp.img as an ABL substitute.

## 9. Output / upload / stop

Create the sanitized report:
firmware-analysis/round138/round138-dtbo-variant-and-live-fdt-delta-audit.md

Record:
- all input identities;
- per-entry rootparam matrix;
- entry2 vs entry8 UFS/PMIC delta;
- device property provenance and conditionality;
- reserved-memory 39 vs 37 reconciliation;
- decision matrix with DIRECT / CONDITIONAL / UNKNOWN / NOT FOUND distinctions;
- exact scope limits and final outcome:
  - PASS — ENTRY2/8 STATIC COMPARISON COMPLETE
  - PARTIAL — COMPARISON COMPLETE WITH INPUT LIMITATIONS
  - BLOCKED — EXISTING ARTIFACTS / RECORDS MISSING

Upload only the sanitized Markdown report (and optional safe text-only metadata log) to firmware-analysis/round138/ on the existing firmware-audit-v1 branch. Read back and verify byte identity. After upload, stop.

No subsequent source patch, package, build, device access or boot test is authorized by this taskbook.
