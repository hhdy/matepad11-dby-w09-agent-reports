# ROUND48 — HOS4.3 PMIC5 regulator mode enum translation and ACK DTS decision

Date: 2026-11-24

## Scope and status

This report combines the sanitized HOS4.3 ROUND13 read-only result with public Qualcomm SM8250 KONA vendor source and the fixed ACK `android17-6.18.33_r00` source. It makes a proposed edit to the review-only `main` branch DTS draft.

No local firmware was read in this round. No device was connected or changed. No source tree was built. No DTB, dt-schema, Kconfig, checkpatch, or boot validation was run. The protected `ack18-dby-w09-dts-draft` branch and PR #1 were not changed; PR #1 remains Draft. All changes described here are on `main` review drafts/reports only.

## 1. ROUND13 local facts

ROUND13 report:
`firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt` on `firmware-audit-v1`.

It scanned 3,281 property-bearing FDT paths plus all nine existing stock DTBO entries, using the already-approved parser and resolution maps.

- Upstream properties `regulator-initial-mode`, `regulator-allowed-modes`, `regulator-allow-set-load`, `regulator-system-load`, and `regulator-state-{standby,mem,disk}` were each `NOT_FOUND_IN_INSPECTED_SCOPE`. This is not a claim of global absence and does not mean the hardware has no mode policy.
- HOS4.3 uses provider-level `qcom,regulator-type`, `qcom,supported-modes`, `qcom,mode-threshold-currents`, plus child-level `qcom,init-mode` and `qcom,set`.
- No `qcom,pmic-id` nodes were found in the examined FDT; identify the local provider by its resource group/path, not by a legacy child label.
- S4: provider `/soc/rsc@18200000/rpmh-regulator-smpa4`, resource `smpa4`; 1.8–1.92 V, init voltage 1.8 V, `qcom,set=<3>`; no regulator type, supported modes, threshold, or init-mode.
- L5: `rpmh-regulator-ldoa5`, `pmic5-ldo`, supported `<2 4>`, threshold `<0 30000>` µA, init-mode `4`; proxy-supply to its child, proxy-consumer-enable, proxy-consumer-current `100000` µA. AO/SO sibling entries have distinct set/init-mode/init-enable values and are not the active ALL child.
- L6: `rpmh-regulator-ldoa6`, `pmic5-ldo`, supported `<2 4>`, threshold `<0 30000>` µA, init-mode `2`; no proxy child.
- L9: `rpmh-regulator-ldoa9`, `pmic5-ldo`, supported `<2 4>`, threshold `<0 30000>` µA, init-mode `4`; proxy-supply to its child, proxy-consumer-enable, proxy-consumer-current `100000` µA.
- L17: `rpmh-regulator-ldoa17`, `pmic5-ldo`, supported `<2 4>`, threshold `<0 10000>` µA, init-mode `2`. HOS4.3 identifies it only as `pmic5-ldo`; its PLDO/NLDO subtype is not established by this FDT.
- S8: provider `rpmh-regulator-smpc8`, type `pmic5-hfsmps`, supported `<1 3>`, threshold `<0 200000>` µA, init-mode `1`; child label `pm8150a` is legacy naming and is not provider identity.
- All nine stock DTBO entries had zero fragment targets inside `/soc/rsc@18200000`, zero RPMh regulator overlays, and zero mode-property overlays. Entry selection is still unresolved (the entries differ by board-id), so the effective post-overlay tree remains UNKNOWN. Do not claim a merged/effective tree or identify a selected entry.

## 2. Auditable vendor mode-number mapping

The public Qualcomm SM8250 KONA vendor source at OnePlusOSS commit `cad09e061ef6cf689a4a1e54d27562e0f042236a` contains the relevant source family:

- Header: [qcom,rpmh-regulator-levels.h](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/include/dt-bindings/regulator/qcom,rpmh-regulator-levels.h)
- Driver: [rpmh-regulator.c](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/rpmh-regulator.c)
- KONA PM8150 rail DTS: [kona-regulators.dtsi](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/arch/arm64/boot/dts/vendor/qcom/kona-regulators.dtsi)

That header defines the old Qualcomm vendor DT enum:
- PASS = 0
- RET = 1
- LPM = 2
- AUTO = 3
- HPM = 4

The driver selects mode interpretation from the provider's `qcom,regulator-type`, then converts generic vendor values to regulator-framework modes and PMIC hardware register modes. For PMIC5:
- LDO vendor mode 2 = LPM; 4 = HPM.
- HFSMPS vendor mode 1 = RET; 3 = AUTO.

The same KONA DTS contains the same resource names and configuration pattern seen by ROUND13:
- S4 / `smpa4`: no explicit mode configuration.
- L5 / `ldoa5`: LDO supported LPM/HPM, 30mA threshold, HPM initial, 100mA proxy consumer.
- L6 / `ldoa6`: LDO supported LPM/HPM, 30mA threshold, LPM initial.
- L9 / `ldoa9`: LDO supported LPM/HPM, 30mA threshold, HPM initial, 100mA proxy consumer.
- L17 / `ldoa17`: LDO supported LPM/HPM, 10mA threshold, LPM initial.
- S8 / `smpc8`: HFSMPS supported RET/AUTO, 200mA threshold, RET initial.

This is unusually close platform/source corroboration for interpreting ROUND13's raw values. It is still a public KONA source cross-reference, not proof of the exact vendor kernel binary version loaded by HOS4.3.

The fixed ACK source is a different interface generation. Its own header at [qcom,rpmh-regulator.h](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/dt-bindings/regulator/qcom,rpmh-regulator.h) defines RET=0, LPM=1, AUTO=2, HPM=3. The fixed ACK RPMh driver has per-hardware `of_map_mode` mappings for `regulator-initial-mode` and `regulator-allowed-modes`; therefore the DTS must use the fixed ACK symbolic constants, not copy the older vendor raw integers. In particular, vendor HPM integer 4 is not a valid ACK HPM integer.

## 3. ACK DRMS capability intersection

ROUND47's fixed ACK review remains authoritative for driver callback capability:
- L5/L6/L9 are PMIC5 NLDO with `get_optimum_mode + set_mode`; ACK HPM threshold 30mA.
- L17 is PMIC5 PLDO with `get_optimum_mode + set_mode`; ACK HPM threshold 10mA. This subtype comes from the ACK PM8150 regulator table, not from the HOS FDT.
- S4 and PM8150L S8 are PMIC5 HFSMPS510 with manual mode set/get but no DRMS `get_optimum_mode` or `set_load`; setting `regulator-allow-set-load` would not provide real dynamic mode switching.

## 4. Proposed DTS decisions

The review-only main-branch draft `dts/dby-w09-ack18-board.dts.draft` has been updated as follows.

| Rail | HOS4.3 interpretation | ACK DTS decision |
|---|---|---|
| S4 | No type/mode/threshold/init-mode fields in inspected scope. | Remove the previous HPM initial-mode. Do not invent allowed-modes or DRMS. Leave mode untouched. |
| L5 | PMIC5 LDO; init HPM; LPM/HPM supported; 30mA threshold; 100mA proxy consumer. | ACK HPM initial; ACK LPM/HPM allowed modes; enable set-load DRMS; set `regulator-system-load=<100000>` as an explicit approximation of the persistent 100mA proxy vote. |
| L6 | PMIC5 LDO; init LPM; LPM/HPM supported; 30mA threshold; no proxy consumer. | ACK LPM initial; ACK LPM/HPM allowed modes; enable set-load DRMS. |
| L9 | PMIC5 LDO; init HPM; LPM/HPM supported; 30mA threshold; 100mA proxy consumer. | Same translation as L5, including 100mA `regulator-system-load` approximation. |
| L17 | PMIC5 LDO; init LPM; LPM/HPM supported; 10mA threshold. | ACK LPM initial; ACK LPM/HPM allowed modes; enable set-load DRMS. Do not claim HOS established its PLDO subtype. |
| S8 | PMIC5 HFSMPS; init RET; RET/AUTO supported; 200mA threshold. | ACK RET/AUTO allowed modes, but set initial AUTO instead of RET. ACK HFSMPS510 lacks load-based DRMS callbacks and the UFS parent advertises up to 210mA; fixed RET would not be dynamically promoted. AUTO uses the hardware's autonomous load response and is the safer static fallback. Do not add allow-set-load. |

### Proxy-load caveat for L5/L9

ACK has no matching vendor `proxy-supply` / `proxy-consumer-enable` lifecycle helper. The draft maps only the measured 100mA proxy current into standard `regulator-system-load`, allowing ACK's existing LDO DRMS aggregation to keep the mode at HPM while that rail is enabled. This is a static-load approximation; it does not recreate the vendor proxy consumer's exact enable/disable timing. The self-referential vendor `proxy-supply` phandle is not copied into the upstream regulator input-supply graph.

### S8 deviation caveat

HOS4.3's initial RET and 200mA RET→AUTO threshold are direct local metadata, but the fixed ACK HFSMPS510 operations cannot perform that load-triggered policy. The draft uses hardware AUTO to avoid forcing a high-current UFS parent supply into fixed RET. This is an intentional compatibility fallback, not a claim that ACK reproduces HOS policy or threshold behavior. Runtime rail behavior remains untested.

## 5. Remaining boundaries

- HOS4.3 effective post-overlay state remains UNKNOWN because the selected stock DTBO entry was not resolved, even though the nine inspected entries do not overlay the target RSC rail subtree.
- The S4/LDO/S8 mode recommendations are static DTS proposals only.
- No full-tree apply, dtc, dt-schema, Kconfig resolution, build, boot, regulator trace, runtime mode/current reading, or hardware test has been run.
- S4/S8 physical PMIC input supply paths remain unresolved; do not infer missing parent connections or add guessed `vdd-s*` / `vph_pwr` properties.
- ROUND12 AVB remains BLOCKED by the trusted local tool gate; EROFS and ramdisk remain BLOCKED. These facts do not change.
- Stage A ACK 6.18.33 remains the only active kernel-port milestone; Stage B DerpFest stays deferred until Stage A boot, UFS storage and baseline hardware checks pass.
