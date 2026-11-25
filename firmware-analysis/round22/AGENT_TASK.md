# ROUND22 — DBY-W09 board-DTS compile readiness and UFS regulator/driver contract audit

**Owner:** local WorkBuddy Agent; local offline audit  
**Device:** Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250  
**Kernel:** ACK android17-6.18.33_r00, common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Purpose:** prepare the existing storage-first board DTS draft for a safe first DTB compile decision without editing project sources or building the kernel.

## 0. Inputs already available

Reuse only existing work copies:
- ROUND18 pinned ACK source tree, final .config and built Image (do not rebuild);
- ROUND19 already-decompiled HOS4.3 base DTB and nine DTBO DTS texts;
- ROUND20/ROUND21 reports;
- main-branch draft dts/dby-w09-ack18-board.dts.draft;
- existing storage-first fragment and any locally available UFS patch-series files.

Do not re-extract firmware, redeploy WSL or sync source.

## 1. Strict boundaries

- Do not edit any source, Kconfig, .config, fragment, DTS/DTBO, firmware or existing report.
- Do not run olddefconfig, menuconfig, Kleaf/Bazel or a kernel build.
- Do not create a boot image, package, sign, alter AVB, or deploy anything.
- Do not connect to the tablet or use ADB/fastboot/recovery, reboot, unlock, root, flash or write partitions.
- Do not change main source files, ack18-dby-w09-dts-draft, ai-parallel/stagea-port-until-boot, PR #1 or any protected ref.
- A temporary DTB or DTBO may be generated under the ROUND22 temp directory solely for syntax/label validation, only from byte-identical unmodified source copies. Never upload the binaries. If dtc prerequisites are absent, mark BLOCKED rather than install/download tools.
- Do not infer the selected runtime DTBO from board-id candidates.

## 2. Work package A — reconcile HOS base /memory documentation

There is a contradiction:
- Existing main board-DTS draft comment states the HOS4.3 base FDT has no /memory node.
- ROUND19 and ROUND20 reports state /memory exists, but reg is an all-zero placeholder.
Read the existing ROUND19 decompiled base_2.dts and prior report source, without re-extracting. Determine:
- exact node path, device_type, reg, address/size cells and whether there are aliases or multiple memory nodes;
- whether the node is missing versus present-but-empty;
- whether any prior source or same-device DTS supports ABL rewriting it (label as inference only).
Report the exact correction needed in the draft comment. Do not change the draft and do not invent RAM sizes, addresses or reserved-memory regions.

## 3. Work package B — board DTS syntax / label / include readiness

Use the existing dts/dby-w09-ack18-board.dts.draft unchanged and the pinned ACK DTS include tree:
- resolve the exact sm8250.dtsi include path and all included headers;
- confirm every label used by the draft exists in the pinned source (apps_rsc, ufs_mem_hc, ufs_mem_phy, and any other labels);
- identify any duplicate node/property or malformed fragment visible statically;
- if the pre-installed dtc 1.7.0 and include paths are available, copy the draft byte-identically to a temporary source file and run dtc with required include paths, writing output only under ROUND22 temp. Capture the exact command, exit code and warnings. This validates syntax only, not schema or runtime hardware.
- If a separate rootparam overlay draft exists in existing local work copies, inspect it and compile it independently with dtc -@; do not guess a path, do not merge it into the base DTS and do not fail the base check merely because that separate draft is missing.
- Do not edit includes or source to make compilation pass. Any required edits are recommendations only.

## 4. Work package C — UFS host/PHY Device Tree contract against actual patched ACK source

Use the exact source workspace used by ROUND18, not only memory or old drafts. Verify:
- base SoC ufs_mem_hc and ufs_mem_phy compatibles, clocks, resets, interconnects, power-domains and required-opps;
- board-DTS status, UFS voltage/current ranges, vcc/vccq/vccq2, vdda-phy/vdda-pll, qcom,vddp-ref-clk and qcom,vccq-parent-supply properties;
- whether vdd-hba-supply is consumed by the exact compiled QCOM UFS driver or if the GDSC power-domains property is sufficient; do not assume comments in the draft are correct;
- whether the ROUND18 patch series actually contains the implementation required for each vendor property (identify exact source file/function), especially parent VCCQ rail handling, VDDP ref-clock rail handling, PHY always-on semantics, dual GenPD/required-opps;
- check the pinned binding schemas for those properties and exact compatible strings; note any schema gaps/patches used in ROUND18;
- verify whether the board DTS compatible override is needed for the compiled driver to bind the host and PHY.
Provide a property-to-consumer matrix: property, provider node, consumer function, patch/schema dependency, status.

## 5. Work package D — PM8150 VRM input parents and electrical assumption

The board draft currently creates PM8150/PM8150L RPMh rail provider nodes used by UFS but omits physical input parent supplies because ROUND11/14 did not find them in the HOS4.3 base DTB.

Inspect the pinned ACK:
- regulator binding definitions for PM8150 VRM supply names (vdd-s4, grouped LDO input supplies, vdd-s8, etc.);
- drivers/regulator/qcom-rpmh-regulator.c / PMIC-specific descriptors and regulator-core optional/dummy-supply behavior;
- the exact sm8250.dtsi regulator tree and any other existing same-SoC upstream board DTS usage, but do not copy another device's actual rail values unless it is only used to establish software semantics.
Answer separately:
1. Does the binding require these input parent properties for schema validity?
2. Does the regulator driver require a resolved parent supply to register/operate?
3. Does regulator core silently provide a dummy parent when omitted?
4. If a dummy parent is allowed, what physical/electrical assumption does that leave unresolved?
5. Can existing HOS4.3 data establish a safe physical rail mapping? If not, keep it UNKNOWN and identify the exact data needed.
Do not create fake fixed regulators, vph_pwr, vdd-s* supplies or invented voltages.

## 6. Work package E — build-readiness decision and minimal recommendations

Provide a matrix:
- board DTS syntax and label resolution: PASS / PARTIAL / BLOCKED;
- UFS host and PHY driver binding: PASS / PARTIAL / BLOCKED;
- every vendor UFS supply property's exact consumer implementation: PASS / PARTIAL / BLOCKED;
- PM8150 regulator-parent electrical path: resolved / unresolved;
- memory node handoff: resolved / unresolved;
- rootparam DTBO readiness: PASS / PARTIAL / BLOCKED;
- whether it is safe to proceed to DTB-only compilation, DTBO compilation, or still only static design review.

Separate:
- source/syntax items that can be fixed in a draft without any guessed hardware data;
- software contract gaps that require a driver/schema patch;
- electrical/ABL/runtime facts that must remain unknown.
No code or DTS edits during this round.

## 7. Deliverable

Upload exactly one sanitized UTF-8 report:
firmware-analysis/round22/round22_board_dts_compile_and_ufs_regulator_contract_audit.txt
to branch firmware-audit-v1.

Include exact source paths/line ranges, tools and versions, temporary dtc commands and results if run, property-to-consumer matrix, /memory correction, PM8150 parent-supply findings, and explicit boundaries.

Do not upload DTB/DTBO binaries, source files, firmware, parser scripts or sensitive paths/keys.

## 8. Stop rule

After the one report is uploaded, stop. Do not start another round, edit a DTS, change Kconfig, build kernel, package/sign, or contact the device.