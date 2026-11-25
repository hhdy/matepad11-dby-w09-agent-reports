# ROUND61 Phase E — board DTS, final memory handoff and PM8150 input topology

**Owner:** Second AI  
**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1  
**Status:** BLOCKED — do not promote the board DTS draft into a build input or produce a boot candidate.

## 1. Current board source is review-only

The current file is `dts/dby-w09-ack18-board.dts.draft` (branch blob `dd9035083458ea6ccdb5fdd852b7a1860509fbaf`). It contains a minimal board identity, PM8150 RPMh output definitions, UFS Host supply links and QMP UFS PHY supplies. It is explicitly marked DRAFT ONLY: it has not been dtc-compiled, schema-validated or boot-tested, and it is not included by the kernel build target.

The current draft also intentionally does not reconstruct `/memory` or `/reserved-memory`. That omission is deliberate, not an incomplete guess to fill with another board's addresses.

## 2. Final Linux memory handoff is not established

The ROUND64 local-Agent recheck corrects earlier wording that described the root `/memory` node as absent: the inspected stock/pre-ABL base FDT contains a `/memory` `reg` placeholder whose tuple is all zero. This is a template placeholder, not an enabled, usable RAM map. The sanitized Agent report does not publish a complete property dump, so this update does not infer the exact `device_type`, cell counts or any real RAM range from that placeholder. The ROUND24 direct enumeration revises the old count: the stock base FDT has **37** `/reserved-memory` direct children (not 34). Their existence does not establish the physical RAM ranges. The public inventory redacts physical addresses.

The same-device public Linux 7.0 DTS is only a structural comparison and is based on HOS4.2; it has no explicit `/memory` node and a different four-child reserved-memory description. It is not a valid source for HOS4.3 RAM or carveout addresses.

The possibility that Huawei ABL injects the usable-memory node into the final live FDT is documented but unproven for the ACK DTB entry path. The stock base FDT alone is not proof of the FDT actually passed to the kernel. Do not synthesize a RAM map from reserved-memory sizes, infer ranges from other SM8250 tablets, or copy HOS4.2 splash/DFPS carveouts.

### Evidence required to close this gate

One of the following exact handoff paths must be demonstrated for the user's HOS4.3 boot chain:

1. **Classic FDT entry:** a trustworthy capture of the final FDT as passed by ABL to Linux, with enabled RAM node(s), `device_type = "memory"`, and exact `reg` / `linux,usable-memory` values; all required reserved-memory ranges and attributes (`reg`, `no-map`, `reusable`, status and relevant phandles) must be retained and reconciled.
2. **Linux EFI-stub entry:** proof that the actual path enters through EFI stub, including valid `/chosen/linux,uefi-system-table` and the UEFI memory-map handoff/descriptors used by the kernel.

The source must be the HOS4.3 DBY-W09 device's actual final handoff, not a base image approximation or HOS4.2 reference. If the final FDT is not accessible through the currently authorized read-only workflow, mark the memory gate blocked rather than inventing data.

## 3. PM8150 physical input-parent topology is not proven

The draft maps several PM8150 RPMh outputs and UFS consumers from the HOS4.3 inventory. This identifies output rails, not their own physical input sources.

ROUND11/14 found several vendor ARC level-parent relationships and proxy-supply relationships. They represent HOS vendor voltage-level / temporary proxy semantics, not PMIC VRM input rails. The inspected HOS4.3 base-FDT scope did not show `vdd-s1..s10-supply`, `vin-supply`, or `vph-pwr-supply`. The exact physical PM8150 input parent(s) therefore remain unresolved. In particular, UFS consumer links such as `qcom,vccq-parent-supply` and `qcom,vddp-ref-clk-supply` do not establish the input source for the PMIC regulator itself.

ACK's regulator core may use a dummy parent when a physical input supply is absent. That runtime fallback is not electrical evidence and must not be interpreted as a valid board power tree.

### Evidence required to close this gate

Provide a source-backed HOS4.3 DBY-W09 power-tree mapping for every PM8150 VRM output used by the board:
- the PMIC input rail name and its actual upstream source;
- the physical parent / inter-PMIC relationship and the evidence for that mapping;
- any required ABL/firmware handoff or boot-time enable assumption;
- whether a purported parent edge is a VRM input, an ARC level parent, or a temporary proxy consumer.

Acceptable evidence must come from a trusted local HOS4.3 final device tree, authoritative hardware schematic/power-tree material, or an equivalently trustworthy board-specific source. Do not add guessed `vph_pwr = 3.7V`, `vin-supply`, `vdd-s*-supply`, dummy fixed regulators or translated proxy edges just to satisfy schema validation.

## 4. Independent ARC / proxy compatibility gap

The draft documents that ACK's upstream `qcom-rpmh-regulator` supports the SM8250 VRM/XOB regulator model, not the HOS4.3 vendor `qcom,rpmh-arc-regulator` graph. ROUND22/48/51 identify vendor ARC parent relationships and temporary proxy votes that are not implemented by the current ACK port. ACK RPMhPD/GenPD and OPP handling is not a proven one-to-one substitute.

Do not create permanent `regulator-system-load` or always-on votes to emulate temporary proxy consumers. This remains a separate power-handoff compatibility item to assess against the real HOS4.3 final handoff and boot-time requirements.

## 5. No build or boot promotion

Until the two primary gates (final memory handoff and physical PM8150 input topology) are closed:
- keep `dts/dby-w09-ack18-board.dts.draft` review-only;
- do not add a production board DTS/DTB target;
- do not select the stock HOS4.3 DTBO entry 8 for the minimal base: its 145 fragments target Huawei vendor-only nodes not present in this draft;
- do not build a boot/DTBO candidate or perform device operations;
- do not promote Phase E to PASS.

The Image-only ACK kernel build can continue independently, but a successful Image does not close Phase E.

## 6. Narrow request for the local read-only evidence collector

When the authorized local Agent can collect the relevant HOS4.3 information, request only:
1. a sanitized report/capture of the **final ABL-to-Linux FDT** (or proof and capture of the actual EFI memory-map handoff), preserving the complete memory/reserved-memory node structure and exact address/size cells needed to reconcile the map; and
2. a source-backed PM8150 VRM input-parent map for the rails used by UFS, distinguishing physical input rails from ARC/proxy relationships.

Do not request device unlock, reboot, partition writes, flashing, or changes to bootloader policy for this evidence collection. If an approved read-only method cannot acquire those facts, leave the phase blocked.

## 7. ROUND64 local-Agent evidence update (2026-11-25)

The local Agent completed the read-only Phase E taskbook. Full sanitized report (on `firmware-audit-v1`):
[ROUND64 Phase E — HOS4.3 final memory handoff and PM8150 input-parent evidence](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round64/round64-dby-w09-hos43-final-memory-and-pm8150-input-evidence.md).

The result confirms, rather than closes, both primary blockers:

- **Final ABL-to-Linux memory handoff: BLOCKED.** The only candidate `/sys/firmware/fdt` capture was attempted in ROUND2 and failed with `Permission denied`; its sidecar says the live FDT is unavailable. No other already-authorized local artifact is a final post-ABL capture. The stock FDT's all-zero `/memory/reg` placeholder cannot be used as RAM size/range evidence. The actual entry path (classic FDT versus EFI stub), final RAM tuples, chosen EFI metadata and final reserved-memory ranges remain unknown.
- **PM8150 physical input-parent topology: BLOCKED.** Six UFS-consumer outputs are identifiable (PM8150 L5/L6/L9/L17/S4 and PM8150L S8), but the authorized corpus contains no board-specific schematic/power tree and no explicit `vdd-s1..s10-supply`, `vin-supply` or `vph-pwr-supply` parent mapping. Vendor ARC level relationships and proxy-supply edges are not accepted as physical VRM input edges. No voltage, parent rail or fixed regulator was invented.

No new device access or privilege escalation occurred. The Agent identifies the narrow evidence needed to resume: an already-authorized sanitized final post-ABL FDT/EFI handoff capture, and an authoritative DBY-W09 PMIC power-tree/schematic mapping for those outputs.

### Supplemental pinned-ACK UFS HBA supply contract

The separate ROUND64 pinned-source audit [round64-ufs-hba-gdsc-regulator-source-review.md](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round64/round64-ufs-hba-gdsc-regulator-source-review.md) finds that ACK's `vdd-hba-supply` is a real regulator consumer, while the referenced Qualcomm GDSC node is registered as a generic power domain, not as an output regulator. With the HOS-style phandle pointed at that GDSC, regulator lookup may defer; with the optional HBA supply property absent, ACK treats it as already enabled and retains the inherited `UFS_PHY_GDSC` power-domain relationship. Keep `vdd-hba-supply` and `vdd-hba-fixed-regulator` out of the ACK board draft unless a real regulator provider is independently established. This source-level finding does not close the memory or PMIC electrical gates and does not make the draft build-ready.
## 8. ROUND22 prior-draft DTS syntax and UFS supply-contract audit (2026-11-25)

The local Agent's sanitized ROUND22 report is available at:
[ROUND22 — board-DTS compile readiness and UFS/regulator contract audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round22/round22_board_dts_compile_and_ufs_regulator_contract_audit.txt).

**Syntax evidence is limited to the exact older input revision named in that report.** The Agent copied a 14,588-byte pre-rev2 board draft byte-identically into a temporary directory, ran the kernel-style `cpp` preprocessing flow and preinstalled dtc 1.7.0, and obtained a 145,841-byte temporary DTB with exit 0. It recorded 32 warnings, all inherited from pinned `sm8250.dtsi`, and zero warnings attributable to that draft copy. No temporary binary was uploaded. This is syntax/label evidence only; it is not dt-schema, dtbs_check, runtime or boot evidence. It does **not** validate the current Stage-A branch draft blob or the newer main-branch rev2 candidate. ROUND23 was separately tasked to test that rev2 candidate and the rootparam overlay.

**UFS contract findings against the actual ROUND18 compiled ACK source:**
- The inherited `qcom,sm8250-ufshc` + `qcom,ufshc` compatible path binds the QCOM UFS driver; no board compatible override is needed.
- UFS `vcc/vccq/vccq2`, `qcom,vddp-ref-clk-supply`, QMP PHY `vdda-phy/vdda-pll`, and the `vdda-phy-always-on` path have real consumers in the patched ACK source reviewed by ROUND22.
- `qcom,vccq-parent-supply` is declared by schema but has no runtime consumer in the reviewed ACK UFS driver. Treat it as topology metadata only; do not assume a runtime regulator vote or enable.
- The dual-GenPD OPP-to-MMCX mapping is present in the patched source but only activates in the two-domain path. The older draft compiled by ROUND22 had one UFS Host domain, so that OPP mapping was dormant there. The newer rev2 candidate adds MMCX index 0 followed by GCC UFS_PHY_GDSC index 1; ROUND23 must verify those specifiers and order.

**PM8150 input-supply software behavior:**
- The pinned regulator binding makes PM8150/PM8150L input-parent properties optional for schema validity. The RPMh regulator driver provides a supply name to regulator core; on a populated arm64 DT, regulator core can substitute a dummy parent if the supply is unresolved.
- That can allow regulator registration, but it means software assumes an input is externally present/enabled. It does not identify the physical source, prove voltage headroom or establish safe sequencing. Therefore the physical PM8150 topology gate remains BLOCKED exactly as Phase E states.

ROUND22 did not edit the board source, change Kconfig/configuration, run dt-schema/dtbs_check, package a DTBO, or contact the device. Keep the board DTS review-only until the final memory handoff and physical PMIC parent evidence are available.
## 9. ROUND23 — rev2 board DTB and rootparam overlay temporary composite validation

Local-Agent report:
[ROUND23 — rev2 DTS and rootparam overlay composite validation](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round23/round23_rev2_dts_and_rootparam_overlay_composite_validation.txt).

**Temporary syntax/overlay checks: PASS.** Using byte-identical copies of the main-branch rev2 candidate and rootparam overlay, preinstalled cpp/dtc 1.7.0 compiled the base DTB (145,849 bytes) with the same 32 inherited `sm8250.dtsi` warnings as ROUND22 and no new candidate-local warnings. The 536-byte overlay compiled with `dtc -@ -a 4`; its `__fixups__` correctly targets `rootparam`. `fdtoverlay` applied it to the temporary base DTB and produced a 146,045-byte composite.

Composite checks confirmed the five VG rootparam payload values, UFS Host dual-domain order `RPMhPD MMCX(6)` then `GCC UFS_PHY_GDSC(4)`, the UFS PHY retaining only `GCC UFS_PHY_GDSC(4)`, the expected UFS regulator properties, and no `vdd-hba-supply` phandle to GDSC. The overlay's root `qcom,board-id=<0x206a 0>` remains overlay-root metadata; fragment application only merges its `/rootparam` payload into the base. It does not modify base root `qcom,board-id=<0 0>` or define Android DT-table `id/rev`.

**Scope limitation:** this was temporary compile/fixup/composite validation of candidate files on `main`, not a source change or build target on the Stage-A branch. No `dtbs_check`, `dt_binding_check`, Kleaf/Bazel target, DTBO table package, boot image or device action ran. It proves syntax and overlay mechanics, not HOS4.3 ABL selection or boot acceptance.
## 10. ROUND24 — HOS4.3 reserved-memory inventory and consumer map

Local-Agent report:
[ROUND24 — HOS4.3 reserved-memory and consumer map](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round24/round24-hos43-reserved-memory-and-consumer-map.txt).

**Count correction:** the inspected HOS4.3 base FDT has **37** direct `/reserved-memory` children, not the historical 34. 35 have alias entries; `kerneldump` and `linux,cma` do not. The nine DTBO overlays contain no `/reserved-memory` node and no scanned memory-region references.

**Consumer map:** exact phandle-cell matching identifies 31 true reserved-memory references (45 scan hits including firmware-name / SMEM-state strings); 23 reserved nodes are actually consumed by base-tree memory-reference properties. Major classes include firmware/AOP/SMEM handoff, PIL remoteproc carveouts, DSP shared pools, QSEE/secure pools, display/splash, WLAN, crash logging and CMA. The report keeps all physical addresses redacted.

**UFS-specific finding:** the current rev2 candidate's UFS Host/PHY nodes have no `memory-region` or reserved-memory phandle, and the HOS4.3 base/overlays show no UFS reserved-memory consumer. Thus no direct UFS carveout dependency is evidenced for a storage-only path. This does **not** make it safe to drop the firmware-owned early reservations: hyp/XBL-AOP/cmd-db/SMEM/removed-region/XBL log reservations may cover RAM already occupied before Linux. The minimal rev2 candidate is not acceptable for first boot until the final ABL handoff confirms the usable RAM and reserved-memory ownership.

ROUND24 also establishes that the current rev2 candidate inherits generic upstream SM8250 reserved-memory declarations from `sm8250.dtsi`; those are not verified against HOS4.3 physical coordinates. The nine overlays introduce no reservation changes. No addresses were copied, no nodes added, and no build or device action occurred.
## 11. Current verdict

**PHASE E: BLOCKED.** The draft remains a review artifact. The unresolved facts are real boot-critical inputs, not documentation polish. Keep Phase E open until actual HOS4.3 memory handoff and physical PM8150 supply topology are evidenced and the resulting board source passes the real pinned-kernel DT compilation/schema checks.
