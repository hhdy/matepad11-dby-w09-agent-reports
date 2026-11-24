# ROUND22 — ACK RPMh ARC and proxy-consumer port feasibility

Date: 2026-11-24

Status: public source comparison only, using the completed ROUND11 base-FDT report and the existing ROUND7 sanitized property inventory. No local re-extraction, no new parser, no DTS compilation, Kconfig resolution, build, boot, device access or write. No driver code is authored in this round.

## 1. Main finding

The HOS4.3 qcom,rpmh-arc-regulator provider graph is a distinct Qualcomm RPMh ARC accelerator model, not an alternative spelling of the upstream PMIC VRM regulator and not fully replaceable by the SoC rpmhpd OPP domain.

The old Qualcomm downstream RPMh regulator implementation supports three accelerator classes:
- VRM: physical PMIC voltage / enable / mode / headroom requests;
- ARC: CPR-managed voltage-level requests for PMIC LDO/SMPS resources;
- XOB: PMIC peripheral enable requests.

The HOS4.3 CX/MMCX/MX regulator groups are ARC resources. Their parent-supply links are interpreted by the old driver as regulator-framework parent relationships. They must not be converted to PM8150 VRM vdd-* input-supply links.

Sources:
- Legacy Qualcomm RPMh regulator driver (fixed source commit): https://android.googlesource.com/kernel/msm.git/+/c584d6401f3ffeb16eabe28959dd2f8b0a184388/drivers/regulator/rpmh-regulator.c
- Legacy proxy-consumer helper: https://android.googlesource.com/kernel/msm.git/+/c584d6401f3ffeb16eabe28959dd2f8b0a184388/drivers/regulator/proxy-consumer.c
- ACK android17-6.18 driver: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c

## 2. What the old ARC driver actually does

### 2.1 Command DB AUX voltage map

For each ARC resource, the old driver reads the resource's Command DB AUX data. It expects a u16 array with 1–16 entries, maps shared regulator-framework logical voltage-level identifiers (roughly 1–513) to ARC hardware operating levels (0–15), and ignores zero-padding entries added for alignment. The regulator binding intentionally reuses regulator-min/max-microvolt for these logical corner identifiers; they are not physical microvolt values. The ARC regulator list_voltage callback returns the AUX-mapped logical level, and set_voltage_sel submits the selector as the hardware ARC level. ROUND24 records the binding and local HOS4.3 examples.

It verifies:
- the qcom,resource-name exists;
- Command DB has a resource address;
- the Command DB slave ID matches ARC;
- AUX map length is non-zero, no larger than 16 levels and divisible by the 2-byte level size.

This is important: a port must read the runtime Command DB AUX data, not hardcode voltage-level mappings or assume that regulator-min/max-microvolt alone expresses the ARC mapping.

### 2.2 Request aggregation and enable semantics

The old driver groups multiple regulator children sharing one ARC resource and independently aggregates maximum register requests for active and sleep sets. It sends only changed request registers, uses sleep/wake-only sets when needed, waits for acknowledgement when increasing power, and restores the previous local request on failure.

ARC has no distinct hardware enable register. The old implementation uses a pseudo-enable field in software: where ARC level zero represents OFF, disabling masks the level to zero; otherwise an invalid enable leaves the voltage level invalid rather than sending an unrelated enable command.

These behaviors are essential parts of the protocol. A minimal port that only writes ARC_LEVEL for one child without shared-resource aggregation, active/sleep separation, error rollback or pseudo-enable rules is not equivalent.

### 2.3 Parent supply relationship

The legacy driver dynamically creates a parent supply name from each child regulator's regulator-name. If the aggregate provider node contains regulator-name-parent-supply, it sets the child's regulator descriptor supply name to regulator-name-parent.

That is the intended framework meaning of the four ROUND11 HOS4.3 parent-supply links. They describe virtual ARC level dependency edges (CX/MMCX to MX), not physical PMIC input rails.

Source locations in the legacy implementation:
- ARC level map: rpmh_regulator_load_arc_level_mapping()
- request aggregation: rpmh_regulator_send_aggregate_requests()
- ARC ops / pseudo enable: rpmh_regulator_arc_ops, rpmh_regulator_handle_arc_enable()
- parent supply mapping: rpmh_regulator_init_vreg_supply()
- probe and ARC Command DB slave-ID check: rpmh_regulator_probe()

## 3. ACK android17-6.18 API compatibility

### 3.1 Reusable interfaces

ACK still exposes the required low-level facilities:
- CMD_DB_HW_ARC remains in include/soc/qcom/cmd-db.h;
- cmd_db_read_slave_id() can verify the ARC accelerator class;
- cmd_db_read_addr() resolves the ARC resource address;
- cmd_db_read_aux_data(resource, &len) supplies AUX data and length in one call;
- rpmh_write(), rpmh_write_async() and rpmh_write_batch() accept a device pointer, state and TCS commands.

The Command DB path is therefore substantially reusable. The old two-step cmd_db_get_aux_data_len() / cmd_db_get_aux_data() can be adapted to the ACK pointer-plus-length API.

Sources:
- ACK Command DB API: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/soc/qcom/cmd-db.h
- ACK RPMh API: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/soc/qcom/rpmh.h
- ACK TCS state definitions: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/soc/qcom/tcs.h
- ACK SM8250 apps_rsc TCS configuration: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi
- ACK RSC ACTIVE_ONLY -> ACTIVE_TCS / AMC handling: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh-rsc.c

### 3.2 Required RPMh adaptation

The old downstream implementation stores a struct rpmh_client pointer, calls rpmh_get_byindex() / rpmh_release(), and submits writes with the client handle. ACK uses the newer device-based RPMh interface (rpmh_write(struct device *, ...)) and does not expose those old client-handle functions in its public header.

The old driver also has an optional RPMH_AWAKE_STATE path for controllers without an AMC. ACK enum rpmh_state exposes SLEEP, WAKE_ONLY and ACTIVE_ONLY; it does not expose that AWAKE enumerant. However, the ACK SM8250 apps_rsc SoC node declares ACTIVE_TCS=2, SLEEP_TCS=3, WAKE_TCS=3 and CONTROL_TCS=1. ACK's rpmh-rsc driver maps ACTIVE_ONLY requests to ACTIVE_TCS and triggers the AMC path. For an ACK SM8250 board based on this SoC DTSI, the initial ARC implementation should therefore use ACTIVE_ONLY / SLEEP / WAKE_ONLY; it should not blindly copy the old optional AWAKE branch. The actual HOS4.3 base-FDT property inventory did not capture qcom,tcs-config, so the runtime vendor RSC configuration is still not independently established.

The ARC port must therefore:
- use the correct ACK resource-controller device context;
- adapt the old client lifetime to the current device-based API;
- use the ACK ACTIVE_ONLY/SLEEP/WAKE_ONLY flow for the upstream SM8250 RSC layout, then verify no HOS-specific RSC override is needed;
- retain request aggregation, acknowledgement, rollback and error handling.

No safe one-line API rename is sufficient.

## 4. Proxy-supply is a separate feature

The legacy proxy-consumer.c is not the ARC provider. It implements temporary boot-time regulator votes:
- it checks a regulator child node for qcom,proxy-consumer-enable, qcom,proxy-consumer-voltage and/or qcom,proxy-consumer-current;
- it requests the regulator through regulator_get(reg_dev, "proxy"), resolving the child's proxy-supply;
- it sets voltage/current and optionally enables the rail;
- it removes all temporary proxy votes in late_initcall_sync, on the assumption that actual device consumers have probed and installed their own requests.

The helper was tied into the downstream regulator core's registration/unregistration path and exposed through CONFIG_REGULATOR_PROXY_CONSUMER.

The ACK android17-6.18 source currently has:
- no drivers/regulator/proxy-consumer.c;
- no CONFIG_REGULATOR_PROXY_CONSUMER symbol in drivers/regulator/Kconfig;
- no proxy-consumer build entry in drivers/regulator/Makefile;
- no regulator_proxy_consumer_register() core hook in the current regulator core.

Therefore a DT proxy-supply phandle alone does not create a boot-time vote on ACK. If the HOS4.3 proxy requests are required, the helper and its regulator-core lifecycle integration must be ported as a distinct feature.

### 4.1 What ROUND11 does and does not establish

ROUND11 resolves six proxy-supply phandles and their targets. It does not establish whether the source regulator children carry qcom,proxy-consumer-enable, qcom,proxy-consumer-voltage, or qcom,proxy-consumer-current, because those flags were outside that task's requested property filter.

The partial ROUND7 public property inventory also does not contain those custom property names; that is not proof they are absent from the raw FDT.

So:
- the six proxy-supply edges are FOUND / RESOLVED;
- whether those edges are paired with active proxy consumer votes is UNKNOWN;
- whether UFS first-stage actually depends on any of those temporary proxy votes is UNKNOWN.

Do not add the old proxy helper or claim it is required until the request flags and lifecycle purpose are established.

Sources:
- Legacy proxy helper: https://android.googlesource.com/kernel/msm.git/+/c584d6401f3ffeb16eabe28959dd2f8b0a184388/drivers/regulator/proxy-consumer.c
- Legacy Kconfig option: https://android.googlesource.com/kernel/msm/%2B/299339a73b9bff8dcc510eadb88a20e023343b62/drivers/regulator/Kconfig
- Legacy proxy header: https://android.googlesource.com/kernel/msm/%2B/android-wear-6.0.1_r0.2/include/linux/regulator/proxy-consumer.h

## 4.2 ACK RPMh write API: resource aggregation must stay in the ARC provider

ROUND23 source review adds an important API detail. ACK drivers/soc/qcom/rpmh.c stores one cached wake_val and one sleep_val per command address. RPMH_ACTIVE_ONLY_STATE and RPMH_WAKE_ONLY_STATE replace the cached wake value with the new command data; RPMH_SLEEP_STATE replaces the sleep value. Active-only requests are sent immediately, while sleep/wake requests are buffered for controller flush. These cache entries are not a collection of independent Linux regulator-client votes and the RPMh API does not compute a maximum across multiple child regulator requests that share one ARC resource.

The legacy ARC provider explicitly owns that layer: one aggregate object per RPMh ARC resource; multiple regulator framework children attached to the shared resource; per-child active/sleep request state and qcom,set membership; independent max aggregation across child requests; ARC pseudo-enable handling after aggregation; and only changed aggregate values submitted to RPMh.

Therefore an ACK ARC port must not have each child regulator callback call rpmh_write() directly with its own selector. The last callback to write the same address would replace the AP-side cached value and could lower the requested corner while another child still requires a higher level.

The ACK device hierarchy supports a clean implementation: rpmh-rsc calls devm_of_platform_populate() on the RSC device, creating apps_rsc children as direct child platform devices. rpmh_write() finds the controller through dev->parent. An ARC provider as a direct child of apps_rsc can pass its own pdev->dev without modifying the RSC core.

Proposed provider structure (design only):
- One shared arc_resource object per top-level ARC provider node, holding the direct-child device, resource name/address, validated AUX level map, mutex, child regulator array, previous active/sleep aggregates and validity masks.
- One child arc_vreg request record per regulator subnode, holding regulator_dev, regulator-name, selector, active/sleep participation, pseudo-enable state and parent/dropout configuration.
- On each regulator callback: lock the shared resource; snapshot and update the child request; recompute active and sleep max aggregation across all children; apply the level-zero OFF rule; send changed aggregate requests using the current ACK state API; roll back the child request if an acknowledged write fails; unlock.

Sources:
- ACK RPMh cache implementation: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh.c
- ACK direct-child population and parent controller lookup: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh-rsc.c
- ACK RPMh API and TCS states: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/soc/qcom/rpmh.h and https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/soc/qcom/tcs.h
- Legacy ARC max aggregation: https://android.googlesource.com/kernel/msm/%2B/28f2b66a16e50693a0796b323d652ed1669115b1/drivers/regulator/rpmh-regulator.c

## 4.2 ARC regulator voltage-selector semantics (ROUND24)

The legacy RPMh regulator binding states that regulator-min-microvolt and regulator-max-microvolt on ARC children carry RPMH_REGULATOR_LEVEL_* identifiers, unlike physical VRM regulator outputs. qcom,set is required and selects active, sleep or both request sets. qcom,init-voltage-level is an optional initial ARC corner; qcom,min-dropout-voltage-level is an optional parent/child level delta used only when a parent-supply link exists. These values and properties must be preserved as corner semantics, not converted to physical microvolts.

ROUND7's selected HOS4.3 property inventory shows ARC child minima such as 16, 48 and 64, with a 65535 maximum sentinel. The same inventory shows VRM outputs such as PM8150 L5 at 880000 and L9 at 1200000, which are physical microvolt constraints. The two meanings must remain separate. Resource names, qcom,set, init-level, dropout and send-default flags were not included in the selected ROUND7 rows, so their HOS4.3 values remain UNKNOWN, not absent.

See ROUND24 for exact local examples and the required future local-property scope.

## 5. Recommended port sequence

1. Do not change the current storage-first DTB yet. Keep its PM8150 VRM outputs and consumer supply links; do not add vendor ARC groups or guessed PMIC input rails.
2. Prototype/review an ARC-capable provider against the ACK regulator framework and current cmd_db_read_aux_data() / device-based RPMh API. The provider must be one direct child device of apps_rsc per ARC group and must retain its own max aggregation across sibling regulator children; ACK RPMh cache is last-value-per-address, not an ARC client vote aggregator. Preserve active/sleep state separation, AUX-level translation, pseudo-enable and parent-supply dependency behavior.
3. Add a Devicetree binding for the ARC provider and validate it against the exact ACK schema. Keep it separate from the existing PM8150 VRM binding.
4. Verify which HOS4.3 qcom,proxy-consumer-* flags exist and whether they matter before deciding whether to port the optional proxy helper and regulator-core hooks.
5. The current ROUND7/ROUND11 reports do not establish all required ARC group properties such as qcom,resource-name, qcom,set, qcom,send-defaults, qcom,init-voltage-level, or qcom,min-dropout-voltage-level. A future targeted local scan should collect only those properties from the three existing ARC provider nodes and their children; do not repeat the ROUND11 supply graph or scan unrelated hardware.
6. Only after source and schema review decide whether the ARC provider belongs in the first storage milestone or can be deferred to the first consumer that needs CX/MMCX/MX performance votes.

This is a source feasibility plan, not an implemented driver. No code or DTS ARC nodes have been added.

## 6. Verification status

| Item | Status |
|---|---|
| Legacy Qualcomm RPMh ARC implementation | SOURCE REVIEWED |
| ARC AUX map format (u16, 1–16 entries) | SOURCE REVIEWED |
| ARC active/sleep aggregation and pseudo-enable semantics | SOURCE REVIEWED |
| Legacy ARC parent-supply property mapping | SOURCE REVIEWED |
| ACK Command DB ARC ID / AUX data interfaces | SOURCE REVIEWED / AVAILABLE |
| ACK device-based RPMh write interfaces | SOURCE REVIEWED / AVAILABLE |
| ACK RPMh controller lookup via direct device parent | SOURCE REVIEWED; supports an apps_rsc direct-child provider |
| ACK RPMh per-address cache aggregation | LAST-VALUE cache only; ARC provider must aggregate sibling votes itself |
| Old rpmh_client API | ADAPTATION REQUIRED |
| Old RPMH_AWAKE_STATE branch | NOT IN ACK enum; upstream SM8250 apps_rsc has ACTIVE_TCS=2 and AMC path, so use ACTIVE_ONLY unless HOS-specific RSC evidence differs |
| ACK upstream PMIC regulator has ARC match/provider | NO |
| Legacy boot proxy-consumer helper | SOURCE REVIEWED |
| ACK proxy-consumer source/Kconfig/core hook | ABSENT IN ACK SOURCE REVIEW |
| ROUND11 six proxy-supply phandles | COMPLETE / RESOLVED |
| HOS4.3 qcom,tcs-config / RSC awake-mode override | NOT_CAPTURED in ROUND7 partial property inventory |
| HOS4.3 ARC group resource-name / set / init / default / dropout properties | NOT_ESTABLISHED from existing partial inventory |
| HOS4.3 qcom,proxy-consumer-* request flags | UNKNOWN (not in ROUND11 scope) |
| Whether UFS depends on a boot proxy vote | UNKNOWN |
| ARC driver port / new DT binding / Kconfig / schema | NOT_IMPLEMENTED |
| DTS/Kconfig resolution / build / boot | NOT_RUN |

## 7. Next step

ROUND23 has established the direct-child provider layout and shared aggregation requirement. Continue source-side driver design. After the current ROUND12 AVB task is complete, a targeted local property scan may be needed for the three existing ARC groups' qcom,resource-name, qcom,set, init/default/dropout flags and proxy-consumer request flags; do not reparse the ARC parent/proxy phandle graph. ROUND12 AVB metadata remains the only current Agent task. Keep PR #1 Draft; no device operation, image writes, compile or flash.


## 3.3 The required ACK RSC device hierarchy (ROUND23)

ACK rpmh_write() obtains its controller handle with get_rpmh_ctrlr(dev), which reads driver data from dev->parent. The RSC platform driver sets its own driver data and only then calls devm_of_platform_populate(&pdev->dev), which creates child platform devices for the RSC's direct compatible children. The existing qcom-rpmh-regulator platform device is one of these direct children and passes its own pdev->dev to rpmh_write().

A new ARC provider must follow the same hierarchy: one ARC aggregate/provider node as a direct child of apps_rsc, with the per-regulator nodes as children consumed by the ARC driver. The provider should store &pdev->dev as its RPMh context and pass that device to rpmh_write()/rpmh_write_async(). Do not pass the regulator_dev device or put the provider under an unrelated platform parent: ACK's get_rpmh_ctrlr() assumes the immediate parent carries struct rsc_drv driver data. Because RSC populates after setting drvdata, the direct-child probe order satisfies this contract.

The existing ACK PMIC regulator driver confirms the pattern: qcom,pm8150-rpmh-regulators is matched as a platform child node; its children are registered as regulator devices by that driver. A separate ARC driver can follow the same platform-driver shape without modifying the generic RPMh RSC layer.

Sources:
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh.c
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh-rsc.c
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c


## 3.3 The required ACK RSC device hierarchy (ROUND23)

ACK rpmh_write() obtains its controller handle with get_rpmh_ctrlr(dev), which reads driver data from dev->parent. The RSC platform driver sets its own driver data and only then calls devm_of_platform_populate(&pdev->dev), which creates child platform devices for the RSC's direct compatible children. The existing qcom-rpmh-regulator platform device is one of these direct children and passes its own pdev->dev to rpmh_write().

A new ARC provider must follow the same hierarchy: one ARC aggregate/provider node as a direct child of apps_rsc, with the per-regulator nodes as children consumed by the ARC driver. The provider should store &pdev->dev as its RPMh context and pass that device to rpmh_write()/rpmh_write_async(). Do not pass the regulator_dev device or put the provider under an unrelated platform parent: ACK's get_rpmh_ctrlr() assumes the immediate parent carries struct rsc_drv driver data. Because RSC populates after setting drvdata, the direct-child probe order satisfies this contract.

The existing ACK PMIC regulator driver confirms the pattern: qcom,pm8150-rpmh-regulators is matched as a platform child node; its children are registered as regulator devices by that driver. A separate ARC driver can follow the same platform-driver shape without modifying the generic RPMh RSC layer.

Sources:
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh.c
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh-rsc.c
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c
