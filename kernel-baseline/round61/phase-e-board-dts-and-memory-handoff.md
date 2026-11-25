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

The local HOS4.3 ROUND7/ROUND19 inventory reports that the inspected stock base boot FDT has no root `/memory` node and no `device_type = "memory"` property. It has 34 `/reserved-memory` child nodes covering several classes, including firmware/secure/DSP/reusable/crash records. The public inventory redacts the physical addresses.

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

## 7. Current verdict

**PHASE E: BLOCKED.** The draft remains a review artifact. The unresolved facts are real boot-critical inputs, not documentation polish. Keep Phase E open until actual HOS4.3 memory handoff and physical PM8150 supply topology are evidenced and the resulting board source passes the real pinned-kernel DT compilation/schema checks.
