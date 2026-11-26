# AI1 ROUND139 Independent Review and ROUND140 Disposition

- Reviewer: AI1 (ChatGPT)
- Date: 2026-11-26
- Reviewed executor: WorkBuddy Agent (not AI2; not ROUND140's 2号 Agent)
- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel: ACK android17-6.18.33_r00, pinned commit \`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a\`
- Candidate tree: \`afe9517f8062b96bfeb5b4dd5714942861e6a44b\`
- Report: \`firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md\`
- Report branch: \`firmware-audit-v1\`
- Report blob: \`6704c0c871d651669c45814d21860f1e83db63c4\`
- Report outcome: \`PARTIAL — STATIC INVENTORY COMPLETE WITH INPUT LIMITATIONS\`

## 1. AI1 disposition

**ACCEPTED WITH CORRECTIONS / QUALIFICATIONS — PARTIAL.**

The report substantially completes the requested offline, read-only static inventory for Workstreams B and D. It preserves the material unknowns rather than inventing PMIC parents, runtime votes, ABL behavior, or a recovery route. Its PARTIAL outcome is appropriate because named prior parser outputs and four AVB/recovery image artifacts were unavailable.

Acceptance is limited to the evidence scope actually inspected. It does not establish final ABL FDT/RAM handoff, electrical PMIC input topology, runtime UFS corner/vote behavior, HOS4.3 boot-package compatibility, or reversible recovery. It does not authorize any device interaction.

## 2. Accepted findings — Workstream B (PMIC / UFS)

### 2.1 UFS consumer-to-provider mapping

Accept the static mapping as DIRECT for the inspected HOS4.3 KONA v2.1 FDT/DTBO corpus:

- UFS PHY: \`vdda-phy-supply → PM8150 L5\`; \`vdda-pll-supply → PM8150 L9\`.
- UFS host: \`vdd-hba-supply → ufs_phy_gdsc\`; \`vcc-supply → PM8150 L17\`; \`vccq-supply → PM8150 L6\`; \`qcom,vddp-ref-clk-supply → PM8150 L6\`; \`vccq2-supply → PM8150 S4\`; \`qcom,vccq-parent-supply → PM8150L S8 provider label\`.
- The eight consumer edges are reported identical across all nine DTBO entries.
- The base FDT's UFS nodes are disabled and contain no supply properties; the supplies are introduced by the overlays.

The S8 provider identity is determined by its PMIC regulator group/resource identity, not merely the legacy child label spelling. L6's two consumer properties refer to the same provider and are not two independent rails.

### 2.2 Physical power inputs remain fully BLOCKED

Accept the per-rail status for L5/L6/L9/L17/S4/S8 as UNKNOWN. The report finds no explicit electrical \`vin-supply\`, \`vph-pwr-supply\`, \`vdd-s*-supply\`, \`input-supply\` or \`vs-supply\` declaration for these providers in the inspected base FDT or nine overlays.

The three other dependency types are correctly kept separate:
1. GDSC → ARC level dependencies;
2. ARC provider-child corner edges;
3. proxy / consumer-side declarations, including \`qcom,vccq-parent-supply\`.

Do not reinterpret those relationships as physical voltage-input topology. Do not add guessed fixed regulators, PMIC parent supplies, voltages, or current limits. The missing authoritative evidence remains a DBY-W09 HOS4.3 board DTS/DTBO or board-specific PMIC power-tree / schematic page.

### 2.3 UFS performance-domain findings

Accept the static comparison:
- The inspected HOS4.3 UFS host and PHY nodes have no \`power-domains\`, \`operating-points-v2\`, or \`required-opps\`; no UFS consumer association to an RPMh power domain is declared there.
- The UFS node has legacy \`qcom,msm-bus\` declarations, not standard \`interconnects\`.
- Pinned ACK SM8250 device tree has UFS PHY GDSC domain references, OPP / required-OPP and ICC declarations.
- ACK's SM8250 MMCX descriptor has no parent pointer; CX has an MX parent, but that does not establish MMCX→MX inheritance.
- ACK UFS platform regulator parsing does not consume the downstream \`qcom,vccq-parent-supply\` or \`qcom,vddp-ref-clk-supply\` properties.

Important scope limit: this is a static declaration and source-consumer comparison, not a runtime vote trace. It does not prove what the R3 candidate DTB actually contains or what the first boot would request. ROUND140 must inspect the actual R3-built DTB and source tree for its UFS properties and phandle references rather than assuming the candidate inherited either the complete HOS overlay or the complete generic ACK configuration.

## 3. Accepted findings — Workstream D (boot / ramdisk / DTBO / AVB / recovery)

### 3.1 Boot-v2 and FDT composition

Accept the byte-derived boot-v2 layout, standalone ramdisk layout, DTBO container metadata, and recovery image's byte-identical \`recovery_dtbo\` section as DIRECT package facts.

Material new finding: the 1,664,243-byte boot/recovery DTB section is a concatenation of three FDT variants followed by a 173-byte vendor MP_DATA FDT-like tail. The prior E7 base candidate is FDT #0 (KONA v2.1), not the entire boot DTB section. ROUND139 did not fully analyze FDT #1 and #2; those remain outside the accepted property census. Keep future statements qualified as applying to FDT #0 / KONA v2.1 unless each alternate FDT is separately inspected.

This finding must not be read as evidence that ABL selects FDT #0, accepts a replacement DTB, or uses any particular DTB-selection rule.

### 3.2 Embedded and standalone ramdisks

Accept that:
- \`boot.img\` has a 519,986-byte embedded stock ramdisk;
- the standalone \`ramdisk.img\` is a distinct 1,322,962-byte object;
- the device exposes a separate \`ramdisk\` partition.

Whether HOS4.3 ABL consumes the independent ramdisk, how it combines it with the embedded ramdisk, or whether one is preserved/replaced remains UNKNOWN. Do not package or test a proposed combination yet.

### 3.3 DTBO identity and ABL behavior

Accept the conditional interpretation:
- Existing boot property \`ro.boot.dtbo_idx=2\` is direct evidence in the old capture.
- Entry 2 maps to VD / board-id 8206 / 0x200E only if the tablet's actual DTBO partition corresponds to the inspected package.
- The actual on-device DTBO partition hash/readback is absent.
- Applying the \`/rootparam\` overlay and actual ABL selection policy are unknown.

ROUND138's accepted corrections remain authoritative: entry 2 is a conditional candidate; entry 8/VG is not the current confirmed variant; the reserved-memory count is 37 (not 39 children). The live node values and final RAM tuples remain unknown.

### 3.4 AVB and vbmeta_cust — accepted with a terminology correction

Accept the following structural findings:
- The package contains root vbmeta chain descriptors covering boot, ramdisk, dtbo and other named partitions.
- The listed standalone vbmeta images and their descriptors are statically parseable by the pre-existing AOSP avbtool 1.4.0.
- \`vbmeta_cust.img\` has an AVB0 header at offset 0 whose fields declare \`SHA256_RSA2048\` and include a hashtree descriptor for \`cust\`; the footer at the end of the 1 MiB file points to an out-of-range vbmeta offset.
- Footer provenance and the reason for the size/offset mismatch remain UNKNOWN.

**Terminology correction:** \`avbtool info_image\` / parsing a byte-range copy establishes that the blob is structurally parseable and declares an algorithm and descriptor. It does not, by itself, prove that the signature cryptographically verifies or that the file is a valid signed image for the device's trust chain. Future records must say **“structurally parseable AVB vbmeta header/blob with a declared SHA256_RSA2048 algorithm and cust hashtree descriptor”**, not “cryptographically valid signed vbmeta,” unless a separate authorized verification actually checks the signature against the correct trusted key. No such verification is required or authorized by ROUND140.

The report's phrase “all seven header blocks” does not reconcile directly with the six standalone vbmeta image rows in its table (root, system, vendor, odm, hw_product, cust). ROUND140 should list the exact files counted for rollback-index / key-metadata observations and correct the count or explain the seventh item. Treat this as a report consistency correction, not evidence of an AVB bypass.

### 3.5 Recovery and reversibility

Accept **BLOCKED**:
- The eleven package images are package artifacts, not dumps/readbacks of the tablet's current partitions.
- Device-side partition sizes and a complete set of device-matched original partition backups are absent.
- The public HOS4.2 same-device project is only a reference; its fastboot-boot refusal is not a verified HOS4.3 behavior.
- No tested HOS4.3 recovery / restore route is in evidence.

Therefore the current data does not establish a reversible first-boot experiment. Do not infer recovery readiness from package image availability or hashes.

## 4. ROUND139 outcome

**ACCEPTED — PARTIAL, STATIC INVENTORY COMPLETE WITH INPUT LIMITATIONS.**

Closed by this report:
1. Static HOS4.3 UFS consumer → regulator-provider relationships for the inspected KONA v2.1 base FDT and all nine overlays.
2. Classification and census of physical-parent-like, ARC/GDSC, proxy and consumer-side dependency declarations in that corpus.
3. Exact static UFS power-domain / OPP / ICC differences against pinned ACK source.
4. Boot-v2, ramdisk, DTBO and AVB package structure for available E1 images, including the three-FDT concatenation and \`recovery_dtbo == dtbo.img\`.
5. The old \`vbmeta_cust\` “empty shell / no cust descriptor” reading is corrected; footer provenance remains UNKNOWN.

Not closed:
- Physical power input parent for all six UFS rails.
- Actual UFS runtime OPP / RPMh / CMD DB votes.
- Final post-ABL FDT, RAM map and handoff route.
- Actual DTBO partition identity, ABL DTB policy, selected entry and \`/rootparam\` application.
- Independent ramdisk partition consumption and embedded ramdisk handling.
- Complete AVB interpretation for absent recovery/erecovery images and \`vbmeta_cust\` footer provenance.
- Device-matched complete backups and a tested HOS4.3 recovery route.
- First real-device boot.

No first-boot readiness is declared or authorized.

## 5. ROUND140 instructions for 2号 Agent

ROUND140 remains assigned to **2号 Agent**, not 2号 AI and not the WorkBuddy Agent that executed ROUND139.

2号 Agent must:
1. Read the full ROUND139 report and this review before beginning Stage C.
2. Independently inspect the R3 candidate source/DTB, not just the HOS4.3 FDT:
   - compare actual candidate UFS host/PHY supply properties with the static HOS4.3 provider map;
   - check whether \`vdda-phy\` / \`vdda-pll\` are consumed by the pinned QMP UFS PHY driver;
   - check whether \`vdd-hba\` / \`vcc\` / \`vccq\` / \`vccq2\` are consumed by pinned UFS host code;
   - identify ignored downstream-only properties and do not treat them as effective dependencies;
   - inspect the candidate DTB's actual \`power-domains\`, OPP / required-OPP and interconnect references for UFS host and PHY, including all referenced phandles.
3. Treat absence of an HOS physical parent as UNKNOWN rather than a licence to create a guessed parent; this task only checks candidate wiring and code support, no source change.
4. Keep runtime regulator state and RPMh vote behavior UNKNOWN without a runtime trace.
5. Reconcile the “seven header blocks” wording against the exact image inventory and keep AVB signature cryptographic validity unclaimed.
6. Carry the remaining device-side, ABL and recovery blockers into the first-boot matrix unchanged.
7. If ROUND140's own independent source/build result differs from ROUND135, preserve logs and report the mismatch; do not patch around it.

All ROUND140 prohibitions remain in force: no device connection, ADB, fastboot, recovery, USB/serial, reboot, bootloader interaction, partition read/write, flashing, packaging, signing, AVB modification, root/privilege escalation, or source/patch/DTS/DTBO/config modification.

## 6. Final disposition

**ROUND139 ACCEPTED — PARTIAL. ROUND140 MAY CONTINUE WITH THE ADDITIONAL CHECKS ABOVE. FIRST DEVICE BOOT REMAINS BLOCKED / NOT AUTHORIZED.**
