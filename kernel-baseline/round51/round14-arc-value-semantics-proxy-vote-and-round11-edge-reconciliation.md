# ROUND51 — ROUND14 ARC value semantics, parent-edge reconciliation and S8 policy

Date: 2026-11-24  
Baseline: ACK android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
Status: PUBLIC-SOURCE REVIEW + ROUND14 LOCAL STATIC EVIDENCE; DESIGN ONLY

## 1. Scope and source boundary

ROUND14 is uploaded and complete at firmware-audit-v1:
- firmware-analysis/round14/round14_arc_mmcx_mx_power_properties.txt
- Blob SHA: 2a1cf742ec45b1b17c98c006da241fb7737f6fcd

This report uses ROUND14's existing ROUND3 base-FDT extraction, ROUND11 parent-edge notes and ROUND13 S8 mode/provider evidence. No new local parsing, firmware extraction, DTBO re-scan, runtime regulator or power-domain reads were performed.

Public Qualcomm cross-reference is fixed KONA source commit cad09e061ef6cf689a4a1e54d27562e0f042236a. It is a source-semantics reference, not proof that this exact vendor kernel binary is running on HOS4.3. Fixed ACK references use commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.

## 2. ARC corner values are now symbolically identified

ROUND14 raw values match the public Qualcomm RPMh ARC level definitions:

| Raw value | Symbolic meaning | Local use |
|---:|---|---|
| 16 | RETENTION | MX MMCX-supply child min/init |
| 48 | MIN_SVS | Shared ACK/KONA corner vocabulary |
| 64 | LOW_SVS | MMCX ALL/AO/SO min/init |
| 128 | SVS | Shared ACK/KONA corner vocabulary |
| 192 | SVS_L1 | Shared ACK/KONA corner vocabulary |
| 256 | NOM | Shared ACK/KONA corner vocabulary |
| 320 / 336 | NOM_L1 / NOM_L2 | Shared ACK/KONA corner vocabulary |
| 384 | TURBO | MMCX ALL temporary proxy voltage floor |
| 416 | TURBO_L1 | Shared ACK/KONA corner vocabulary |
| 65535 | MAX | Stored ceiling, not a physical voltage |

The set constants are also established: qcom,set=1 is ACTIVE, 2 is SLEEP, and 3 is ALL (active + sleep). Thus MMCX ALL/AO/SO are intentionally separate request interfaces:
- ALL: set 3; min/init 64; max 65535.
- AO: set 1; min/init 64; max 65535.
- SO: set 2; min/init 64; max 65535.
- MX MMCX-supply ALL target: set 3; min/init 16; max 65535.
- MX AO target: set 1; min/init 16; max 65535.

These are logical ARC corner values. They must not be converted to microvolts or treated as linear physical voltages.

Sources:
- [KONA ARC level and set definitions](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/include/dt-bindings/regulator/qcom%2Crpmh-regulator-levels.h)
- [KONA rpmh-regulator ARC parser and list_voltage](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/rpmh-regulator.c)
- [ACK SM8250 RPMHPD OPP table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi#L6193-L6243)
- [ACK SM8250 selected RPMHPD descriptor map](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L460-L480)
- [ACK RPMHPD performance-state / Command DB level mapping](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L927-L970)

ACK's shared SM8250 RPMHPD OPP table contains the same named numeric performance levels, including RETENTION=16, LOW_SVS=64 and TURBO=384. This establishes common corner vocabulary, not full vendor ARC equivalence: ACK RPMHPD resolves each resource's Command DB level map independently and uses a domain/OPP abstraction, while HOS has multiple logical regulator child interfaces per shared resource.

## 3. qcom,min-dropout-voltage-level = 0xffffffff is NOT a no-dropout sentinel

Fixed KONA source inspection establishes this exact path:

1. The ARC parser reads qcom,min-dropout-voltage-level with of_property_read_u32() and assigns it directly to vreg->rdesc.min_dropout_uV.
2. regulator_desc.min_dropout_uV is an int field, not a u32 field.
3. KONA ARC list_voltage returns the Command DB AUX-derived logical level value for the selected ARC level.
4. regulator core's regulator_set_voltage_unlocked() adds min_dropout_uV directly to the child's mapped/listed value before requesting a parent-supply voltage. There is no 0xffffffff special case, no sentinel translation, and no "ignore this constraint" branch.

On the ARM64 two's-complement target/toolchain, the raw 0xffffffff value is represented as signed -1 when stored in the int field. It therefore acts in this implementation as a -1 offset in the ARC logical level value passed through the regulator core; it is not 4,294,967,295 physical microvolts and is not equivalent to zero/no constraint. A strict language-level caveat is that converting an out-of-range u32 to signed int is implementation-defined in C; the cited target toolchain's two's-complement behavior is the relevant implementation.

This looks counterintuitive beside the binding prose, which describes the property as the minimum level difference the parent must output above the child. The code nevertheless consumes -1 numerically. Do not normalize the local value to 0 or reinterpret it as an absent property. The exact silicon/Command DB intention of a negative one-level delta remains a source-level interpretation; do not claim a measured voltage margin.

ROUND14 confirms that both MMCX ALL and AO carry raw 0xffffffff, matching the public KONA board DTS convention of writing <(-1)> on these two ARC children.

Sources:
- [KONA ARC property parser and supply setup](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/rpmh-regulator.c#L1550-L1595)
- [KONA regulator descriptor field](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/include/linux/regulator/driver.h#L268-L340)
- [KONA regulator parent voltage propagation](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/core.c#L3075-L3110)
- [RPMh regulator binding definition](https://android.googlesource.com/kernel/msm/%2B/c054c528cf8c53a74354cdace8507b9edd559005/Documentation/devicetree/bindings/regulator/rpmh-regulator.txt)

## 4. ROUND11 edge-count correction: five parent-supply properties are now proven

ROUND14's fifth observation is a real regulator parent-supply relation under the public KONA driver contract, not an unrelated property:

- MX provider resource: mx.lvl
- Child regulator-name: pm8150a_s3_mmcx_sup_level
- Provider-level property: pm8150a_s3_mmcx_sup_level-parent-supply = <122>
- Phandle 122 resolves to /soc/rsc@18200000/rpmh-regulator-cxlvl/regulator-pm8150-s3-mmcx-sup-level.

KONA rpmh_regulator_init_vreg_supply() constructs the exact property name from the child regulator's regulator-name and checks for that property on the provider node; when present it registers the matching supply_name. This validates the fifth property as a genuine parent edge for the MX MMCX-supply child.

The reconciled set is therefore **at least five confirmed base-FDT parent-supply edges**:

1. CX ALL child -> MX ordinary ALL child.
2. CX AO child -> MX AO child.
3. MMCX ALL child -> MX MMCX-supply ALL child.
4. MMCX AO child -> MX AO child (the same MX AO child is shared with CX AO).
5. MX MMCX-supply ALL child -> CX MMCX-supply child (newly identified by ROUND14).

ROUND11's four-edge count was incomplete. Replace any statement that ROUND11 completed the parent-edge census with: ROUND11 identified four edges; ROUND14 later confirmed a fifth; the complete total remains unverified. ROUND14 did not rescan the graph, so do not claim exactly five or a complete graph. The six ROUND11 proxy-supply observations remain a separate edge class and must not be counted as parent-supply edges.

The source helper also shows why provider-level nodes can contain several differently named child supplies; a simple one-provider/one-domain graph loses these separate logical interfaces.

Source:
- [KONA regulator supply-name resolution](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/rpmh-regulator.c#L1662-L1698)

## 5. MMCX -> MX numerical similarity is not complete ACK GenPD equivalence

ROUND14 closes the previous missing-input gate for the two MMCX parent targets:
- MMCX ALL: min/init LOW_SVS (64), min-dropout raw -1, parent MX MMCX-supply child min/init RETENTION (16).
- MMCX AO: min/init LOW_SVS (64), min-dropout raw -1, parent MX AO child min/init RETENTION (16).
- MMCX SO is a separate sleep-set interface (set 2) and has no min-dropout or proxy fields in the inspected scope.

ACK's SM8250 RPMHPD OPP table exposes the same canonical numeric corners and the RPMHPD driver maps a requested level to the first available Command DB corner at or above the requested level. This makes the shared corner numbers compatible at the vocabulary level, and it suggests why a -1 child-to-parent offset can round to a neighbouring canonical corner in vendor regulator core.

It still does NOT prove end-to-end equivalent behavior:
- ACK SM8250's selected MMCX and MMCX_AO descriptors have peer semantics but no MX parent pointer. The CX/CX_AO descriptors do have MX parents; that does not automatically add the missing MMCX edge.
- The HOS graph has distinct child regulator nodes under each provider, including a separate MX MMCX-supply child with its own parent edge to a CX MMCX-supply child. A generic GenPD parent pointer between shared MMCX/MX domains does not preserve all these per-child relationships.
- HOS separates ALL, ACTIVE-only and SLEEP-only child interfaces; ACK peer/active-only behavior may approximate some domain behavior but is not proof that the provider child requests and parent votes are identical.
- The local extraction does not contain the complete per-resource Command DB AUX level arrays, full graph census, selected DTBO entry, or runtime RPMh votes.

Decision:
- Do not add a parent pointer to the shared qcom,sm8250-rpmhpd descriptor. It would affect all SM8250 boards and still would not represent the separate MX MMCX-supply -> CX MMCX-supply child relation.
- Do not create a DBY-W09-specific compatible or copy the legacy ARC provider into ACK on the basis of these properties alone.
- Keep the UFS-first ACK GenPD/OPP route as a scoped port design, but leave complete vendor MMCX/MX/CX ARC equivalence as an explicit power-domain validation gate. Do not call it proven or hardware-equivalent.
- A future dedicated ARC-compatible design must model the per-child parent supplies, active/sleep sets, resource aggregation and temporary proxy requests; it is materially more than adding one GenPD parent pointer.

## 6. MMCX ALL has a temporary boot proxy request — not an always-on constraint

ROUND14 shows:
- MMCX provider proxy-supply points to its own ALL child (phandle 105).
- That ALL child has qcom,proxy-consumer-enable (boolean) and qcom,proxy-consumer-voltage = <384 65535>, with no proxy-consumer-current.
- 384 is TURBO; 65535 is MAX.

Public KONA proxy-consumer code registers a temporary consumer request against that child, applies the voltage range and enable request, then removes proxy requests at late_initcall_sync after normal device probing. This is a boot-time hold/request, not a permanent always-on setting and not regulator-system-load. ACK's upstream RPMh regulator stack has no equivalent generic proxy-consumer helper, and ROUND14 finds no qcom,send-defaults on the MMCX provider. This is an additional boot-handoff gap for any attempt to reproduce the vendor ARC graph.

Do not convert this request into regulator-always-on or permanent system-load. A possible ACK implementation could use an explicitly managed temporary MMCX performance-state vote only after driver/lifecycle design proves the target provider is attached and enabled, the Turbo state is valid for the actual Command DB map, and the vote is released at the correct late boot point. No such helper is implemented in this round.

Source:
- [KONA proxy-consumer implementation](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/cad09e061ef6cf689a4a1e54d27562e0f042236a/drivers/regulator/proxy-consumer.c)
- [Pinned ACK SM8250 RPMHPD OPP table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi#L6193-L6243)

## 7. S8 decision: no guessed enable; correct the ACK initial mode to RET

ROUND13 + ROUND14 base-FDT evidence for PM8150L S8 (smpc8, PMIC5 HFSMPS):
- qcom,set=3 (ALL sets).
- qcom,init-voltage=1,200,000 µV; 1.2–1.4 V range.
- qcom,init-mode=1 in the old KONA vendor enum = RET.
- supported modes are RET/AUTO; threshold is 200mA.
- qcom,init-enable, regulator-boot-on and regulator-always-on are NOT_FOUND_IN_INSPECTED_SCOPE on S8; no regulator-state suspend subnodes were found.
- No runtime regulator enable state was read.

The binding defines qcom,set as the target request set(s); qcom,init-enable is a separate VRM enable-state property, and qcom,init-mode is a separate mode property. Therefore set=3 + init-mode=RET does not mean the rail is enabled.

ACK's fixed pmic5_hfsmps510 ops expose enable/disable, voltage and manual mode callbacks, but do not expose get_optimum_mode or set_load. ACK regulator_set_load() only triggers DRMS recalculation when the same consumer handle has a nonzero enable_count. The UFS VCCQ-parent handle in the KONA design is not enabled. Thus:
- a 210mA load-only request is not a reliable enable request;
- on the fixed ACK S8 driver it is a successful no-op because no DRMS callback exists;
- it does not prove that S8 is turned on, changed into AUTO, or has any particular runtime state.

Corrected integration decision:
1. Do not add regulator-boot-on, regulator-always-on, qcom,init-enable, or regulator_enable() for S8 without new evidence. Do not convert qcom,vccq-parent into an enable reference.
2. Do not add a no-op regulator_set_load(210000) call to the initial ACK UFS patch as though it performs mode control. Omit the S8 get/load/enable/disable path from the storage-first companion driver patch. Keep the board's qcom,vccq-parent mapping as source-topology metadata only if the custom binding explicitly permits it; mark it as not consumed by initial ACK code.
3. Set the ACK DTS regulator-initial-mode to RPMH_REGULATOR_MODE_RET, not AUTO, to preserve HOS's only proven initial mode. Keep RET/AUTO as allowed modes for a later evidence-based policy. The previous ROUND48 AUTO fallback was motivated by a 210mA load request that ACK cannot act upon, so that justification is withdrawn.
4. Keep S8 enable/runtime state UNKNOWN and keep its physical vdd-s8 input path unresolved. A future runtime/boot test must establish whether ABL or another RPMh consumer leaves this rail enabled before deciding any explicit enable ownership.

This is deliberately conservative: it avoids inventing an enable reference that could fight another rail consumer or change boot power behavior. It does NOT prove that the UFS device will work without S8; storage bring-up must validate the actual dependency.

Sources:
- [Qualcomm RPMh binding: qcom,set / qcom,init-enable / qcom,init-mode](https://android.googlesource.com/kernel/msm/%2B/c054c528cf8c53a74354cdace8507b9edd559005/Documentation/devicetree/bindings/regulator/rpmh-regulator.txt)
- [Pinned ACK pmic5_hfsmps510 ops](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c#L810-L820)
- [Pinned ACK regulator_set_load behavior](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c#L4950-L4968)
- [ROUND13 S8 raw mode metadata](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt)

## 8. Scope and remaining gates

- ROUND14 is COMPLETE; Local Agent stopped after upload. No further local task is active.
- No ROUND15 task is necessary to make the conservative decisions above. The full parent-edge count remains unverified; a full ARC port would require a separately authorized, narrowly scoped evidence task, not another blind parser run.
- AVB footer/vbmeta descriptors remain BLOCKED (ROUND12); ramdisk and EROFS remain BLOCKED; applicable DTBO entry and effective post-overlay values remain UNKNOWN.
- No full ACK tree patch application, checkpatch, dt-schema, dtc/dtbs_check, Kconfig resolver, Kleaf build, image packaging, device interaction or runtime test has been run.
- Protected ack18-dby-w09-dts-draft branch unchanged; PR #1 remains Draft.
- Stage A ACK 6.18.33 remains the only active milestone. Stage B DerpFest is deferred until actual device boot and UFS/storage/basic-hardware acceptance.
