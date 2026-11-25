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
## 11. ROUND74 — ACK MMCX local vote behavior and HOS ARC equivalence boundary

The source-only review [ROUND74 — ACK SM8250 MMCX parent semantics and HOS ARC equivalence gate](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round74/round74-ack-sm8250-mmcx-parent-and-hos-arc-equivalence.md) refines the earlier MMCX concern:

- Pinned ACK SM8250 selects a **parentless plain MMCX** RPMh GenPD descriptor. Its local `rpmhpd` code validates the resource/AUX data, sends local RPMh power-on/corner votes, and handles the MMCX/mmcx_AO peer ACTIVE_ONLY / WAKE_ONLY / SLEEP aggregation. A missing GenPD parent does not itself disable local voting or cause provider probe failure.
- The rev2 UFS dual-domain order (MMCX first, UFS_PHY_GDSC second) still routes the UFS OPP required-device request to the ACK-side MMCX endpoint. Keep that route in the candidate; removing it would lose the ACK UFS OPP vote path.
- But the HOS4.3 legacy ARC graph separately contains MMCX→MX parent-supply relationships. The plain ACK MMCX descriptor does not propagate its request to MX. A simplistic GenPD parent link would pass the same pstate one-to-one unless a specific required-opps translation is implemented; it would not automatically reproduce HOS `min-dropout-voltage-level` semantics.

**Correct classification:** this is an open board power-equivalence / voltage-margin risk, not a proven UFS probe blocker. Whether UFS link startup or high-performance stability depends on the additional HOS ARC parent/dropout behavior remains UNKNOWN until exact HOS4.3 request fields are captured (ROUND25) and ultimately tested safely at runtime. Do not add a DBY-specific MMCX→MX descriptor or port ARC wholesale before that evidence.
## 12. ROUND75 — stock normal ARM64 entry and live-FDT inference

The source/artifact inference is recorded at [ROUND75 — stock HOS4.3 kernel entry-route and live-FDT inference](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/kernel-baseline/round75/round75-stock-hos43-entry-and-live-fdt-inference.md). ROUND20's stock-kernel header inspection shows the decompressed HOS4.3 kernel has ARM64 Image magic but no PE/COFF EFI header; its payload is gzip-compressed. The normal ARM64 boot path receives the FDT pointer in x0 and obtains usable RAM from the FDT. Pinned arm64 source skips a memory node whose size is zero and does not independently discover RAM on this non-EFI entry path.

Since the stock system boots, this implies the final FDT delivered to the stock kernel must have a usable RAM description, either because ABL patches the extracted `/memory/reg=<0 0 0 0>` template or because it selects/constructs another FDT. **This is a source-contract deduction, not direct observation of the ABL action or final tuple values.** The actual actor, final FDT, RAM ranges and reserved-memory map remain BLOCKED because the live FDT capture was denied and the ABL image/log is unavailable.

For the new ACK Image, the safer compatibility-first assumption is to preserve the normal ARM64 entry + final FDT in x0 and retain a gzip payload candidate (the stock loader is proven to decompress gzip). The ACK Image's PE/COFF EFI capability does not prove ABL will invoke its EFI entry. If EFI Stub is used without the appropriate platform DTB configuration table, it could lose vendor FDT data such as `/firmware/android/fstab`; do not force EFI without ABL evidence.
## 13. Current verdict

**PHASE E: BLOCKED.** The draft remains a review artifact. The unresolved facts are real boot-critical inputs, not documentation polish. Keep Phase E open until actual HOS4.3 memory handoff and physical PM8150 supply topology are evidenced and the resulting board source passes the real pinned-kernel DT compilation/schema checks.


## 14. ROUND25 — HOS4.3 MMCX/MX ARC request and dropout semantics (2026-11-25)

Local-Agent report:
[ROUND25 — HOS4.3 MMCX/MX ARC request and dropout semantics](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round25/round25-hos43-mmcx-mx-arc-request-semantics.txt).

The report reuses the already-decompiled HOS4.3 base DTS and sanitized ROUND11/ROUND14 evidence. It is read-only and does not establish runtime regulator state.

**Confirmed ARC topology (not physical PMIC inputs):**
- HOS4.3 has `mmcx.lvl` and `mx.lvl` ARC providers.
- The MMCX ALL and AO children have phandle-confirmed parent edges to MX children. The separate MX→CX raw property is retained as observed topology, not promoted to a proven performance-parent edge.
- MMCX ALL/AO children carry init corner `0x40`; their MX parent-target children carry `0x10`. MMCX ALL/AO `qcom,min-dropout-voltage-level` is stored as `0xffffffff`. Its semantic meaning, AUX corner-name table and parent-state derivation rule remain unknown. Literal ACTIVE/SLEEP bit-name mapping for `qcom,set` is also not captured.
- These are vendor ARC voltage-level relationships. They must not be converted into PM8150 `vin-supply`, `vph-pwr-supply` or `vdd-s*-supply` physical input links.

**UFS participation boundary:**
The inspected base FDT's UFS host and UFS bus nodes do not explicitly reference MMCX/MX ARC rails; the observed MMCX/MX consumers are camera/display/video/GPU-class nodes. Whether UFS participates in ACTIVE or SLEEP requests through another firmware/runtime mechanism remains UNKNOWN. This is not proof that UFS never depends on those rails.

**Pinned ACK compatibility consequence:**
ACK's generic GenPD parent propagation passes the same incoming pstate unless a required-opps translation is explicitly supplied. Therefore a bare MMCX→MX parent descriptor would forward the same state and would not reproduce the observed HOS MMCX `0x40` / MX `0x10` corner relationship. An evidence-backed translation and documented `0xffffffff` dropout encoding would be needed; neither is currently available.

**Decision:** do not add a bare MMCX→MX parent descriptor, invent required-opps corner mappings, or port vendor ARC semantics speculatively. Keep the existing ACK UFS OPP→MMCX route as a distinct ACK-side request path, but do not claim it is HOS ARC-equivalent. ROUND25 classifies this as an unresolved hardware-equivalence / voltage-margin risk, not a demonstrated UFS probe blocker.

ROUND25 does not close either Phase E primary gate: final ABL-to-Linux memory handoff and authoritative DBY-W09 PM8150 physical input-parent topology remain BLOCKED. The board DTS remains review-only; no build/package/device action is authorized by this evidence.


## 15. ROUND26 — inherited ACK SM8250 memory / reserved-memory interval comparison (2026-11-25)

Local-Agent report:
[ROUND26 — ACK SM8250 vs HOS4.3 reserved-memory interval audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round26/round26-sm8250-vs-hos43-reserved-memory-interval-audit.txt).

All physical tuples were parsed and compared locally; only node names, match classes and coarse size classes were published. No coordinates or coordinate hashes were uploaded.

**Reserved-memory comparison:**
- Pinned ACK `sm8250.dtsi` declares 18 immediate fixed-reg `no-map` children. HOS4.3 has 37 direct children: 24 fixed-reg and 13 dynamic/no-fixed-reg.
- 17 ACK fixed intervals are exact matches to HOS4.3 fixed intervals. No ACK-vs-HOS fixed interval was classified as overlap or same-base/different-size.
- The sole unresolved ACK-side interval is `cdsp_secure_heap`: ACK has a fixed interval, while the HOS4.3 same-name node has no fixed `reg`. It is not valid to call these equivalent.
- HOS4.3 has seven fixed nodes without exact ACK counterparts and 13 dynamic/no-fixed-reg nodes, including CMA/shared pools absent from the generic ACK DTSI.
- rev2 includes `sm8250.dtsi`, so its compiled tree inherits the 18 ACK carveouts and six SoC memory-region consumers. A present consumer node does not imply its driver probes.

**Top-level memory placeholder comparison:**
The ACK and HOS4.3 top-level memory nodes are both zero-size single-tuple placeholders, but are not structurally identical. ACK's inherited node has a nonzero base and a unit-address suffix; HOS4.3's base node has a zero base and no unit-address suffix. The rev2 include graph therefore inherits the ACK placeholder, not the HOS placeholder. Neither placeholder provides usable RAM values.

**Decision and remaining gate:**
On interval evidence alone, retaining the 17 exact-match upstream reservations is more defensible than omitting all HOS4.3 reservations. This is not proof that the whole inherited tree is safe: `cdsp_secure_heap` remains fixed-vs-dynamic unresolved, and no comparison to actual usable RAM / ABL / secure-firmware allocations is possible without the final post-ABL FDT. Do not delete, resize or override any node based on this report. Keep the memory map and Phase E BLOCKED pending the actual final ABL-to-Linux FDT/EFI handoff.

ROUND26 is a static local comparison only. It does not close the PM8150 physical input-parent gate, does not establish runtime reservation ownership, and does not authorize a DTS edit, build, package or device operation.
