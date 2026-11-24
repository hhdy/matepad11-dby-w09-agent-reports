# ROUND23 — ACK ARC provider RSC device hierarchy and request context

Date: 2026-11-24

Status: public ACK android17-6.18 source review plus existing project source-draft integration. No driver code authored, no local firmware work, no DTS compilation, Kconfig resolution, build, boot, device access or write.

## 1. Key integration contract

ACK android17-6.18 rpmh_write() does not accept an arbitrary device. Its internal get_rpmh_ctrlr(dev) obtains the RSC controller from dev_get_drvdata(dev->parent). Therefore the calling device's immediate parent must be the platform device whose driver data is the RSC driver state.

The ACK RSC probe satisfies this for its direct child devices:
1. It checks Command DB readiness.
2. It initializes TCS groups and controller state.
3. It stores the RSC driver data on the RSC platform device with dev_set_drvdata().
4. It calls devm_of_platform_populate(&pdev->dev), creating child platform devices only after the RSC driver data exists.

The existing qcom-rpmh-regulator platform device is instantiated as a direct child of apps_rsc and passes its own pdev->dev to rpmh_write(). This is the supported usage model.

Sources:
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh.c
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh-rsc.c
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c

## 2. ARC provider device-tree/platform-driver layout

Recommended future implementation shape (not yet implemented):

- Keep each aggregate qcom,rpmh-arc-regulator resource node as a direct child of apps_rsc.
- Bind one ARC aggregate platform device to that provider node.
- Parse the resource-name and resource type from the provider node.
- Treat each nested regulator child as an individual regulator-framework endpoint. Do not expect those nested regulator children to be independent RPMh platform devices.
- Store &pdev->dev in the per-resource ARC state and pass that device to ACK rpmh_write()/rpmh_write_async().
- Register regulator endpoints with devm_regulator_register(); attach the per-endpoint state as driver data and the endpoint's own DT child node as of_node.
- If a regulator child has a matching parent-supply link on the aggregate node, derive the child's regulator_desc.supply_name consistently with the old vendor driver, so the regulator framework can resolve the parent ARC regulator and establish the CX/MMCX-to-MX dependency.
- Keep a mutex per aggregate ARC resource, because several regulator child endpoints share a single hardware resource/address and their votes must be combined before transmission.

This follows the existing ACK PMIC RPMh platform-child pattern but adds ARC-specific aggregation and semantics.

## 3. Request path and state handling

The ARC provider should not call RPMh once per regulator child with a private unaggregated request. Instead:
1. Each consumer updates its endpoint's requested logical voltage level and pseudo-enable state.
2. Under the aggregate resource mutex, the provider calculates the maximum required ARC hardware level across all children for active and sleep sets independently.
3. Translate the regulator-framework logical level to the hardware ARC level using Command DB AUX data for that exact resource.
4. Send only changed register words, with the ARC level register at the ARC base address. The ARC pseudo-enable field is a software aggregation input, not a real hardware enable register.
5. Wait for an acknowledgement on power-increasing ACTIVE_ONLY requests; retain old state and roll back the local vote if the request fails.
6. Cache SLEEP and WAKE_ONLY requests through ACK RPMh APIs as appropriate. The old optional AWAKE path must not be copied into ACK's enum.

ACK API facts:
- enum rpmh_state has SLEEP, WAKE_ONLY and ACTIVE_ONLY.
- rpmh_write() is synchronous and waits for an active request; rpmh_write_async() is non-blocking.
- rpmh_write_batch() can send a multi-command batch.
- ACK SM8250 apps_rsc declares ACTIVE_TCS=2, SLEEP_TCS=3, WAKE_TCS=3 and CONTROL_TCS=1.
- ACK rpmh-rsc maps ACTIVE_ONLY to ACTIVE_TCS, and uses its AMC-mode handling for active requests.

The HOS4.3 runtime qcom,tcs-config was not captured in the ROUND7 property inventory, so the target's exact runtime TCS values remain unconfirmed. The recommended ACK implementation is based on the ACK SM8250 SoC baseline and must be rechecked against any target-specific RSC override before it is used.

## 4. Why the provider must be a direct apps_rsc child

ACK rpmh.c has the essential lookup:
- get_rpmh_ctrlr(dev) reads driver data from dev->parent;
- rpmh_write() then queues the request through that controller's client state.

ACK rpmh-rsc.c sets its drvdata before calling devm_of_platform_populate(). A direct apps_rsc child therefore has the correct immediate parent context when its platform driver's probe runs.

Do not:
- create the ARC driver as a sibling of apps_rsc;
- create it under an arbitrary PMIC or generic bus device;
- call rpmh_write() using a regulator_dev object whose immediate parent is not the RSC platform device;
- add ad-hoc exported RSC handles unless a specific, reviewed need is demonstrated.

## 5. Relationship with the existing ACK PMIC RPMh regulator driver

The existing CONFIG_REGULATOR_QCOM_RPMH driver is a direct RSC child platform driver matching PMIC provider compatibles such as qcom,pm8150-rpmh-regulators. It creates child regulator endpoints itself.

A future ARC port can be implemented either:
- as a separate source file / platform driver sharing the generic CMD_DB and RPMh APIs; or
- as an extension of the existing RPMh regulator subsystem with a separately reviewed ARC provider match and ops.

The implementation form and Kconfig factoring are intentionally undecided. Do not invent a config symbol until an actual patch is prepared. The current qcom-rpmh-regulator only matches VRM/XOB and does not bind qcom,rpmh-arc-regulator.

## 6. Dependencies and ordering

The ARC provider requires:
- CONFIG_REGULATOR;
- CONFIG_QCOM_COMMAND_DB;
- CONFIG_QCOM_RPMH;
- a valid ACK SM8250 apps_rsc RSC parent and matching platform child hierarchy.

Existing ROUND14 already includes the first three boot-critical regulator/RPMh dependencies. No new Kconfig setting has been added for ARC in this round.

Command DB readiness is already a hard dependency in ACK rpmh-rsc probe: the parent RSC returns deferred/error before populating child platform devices if Command DB is not ready. The ARC child can still validate its own ARC slave ID, resource address and AUX mapping during probe.

## 7. Verification status

| Item | Status |
|---|---|
| ACK rpmh_write() immediate-parent RSC lookup | SOURCE REVIEWED |
| ACK RSC sets drvdata before devm_of_platform_populate | SOURCE REVIEWED |
| Existing PMIC RPMh regulator direct-child pattern | SOURCE REVIEWED |
| Correct ARC provider direct-child placement | DESIGN DEFINED |
| Nested ARC regulator children as framework endpoints | DESIGN DEFINED |
| Aggregate resource locking and active/sleep request state | DESIGN REQUIRED |
| ACK Command DB AUX and RPMh APIs | SOURCE REVIEWED / AVAILABLE |
| HOS4.3 qcom,tcs-config / awake-mode override | NOT_CAPTURED |
| New ARC driver source / binding / Kconfig | NOT_IMPLEMENTED |
| DTS/Kconfig resolution / build / boot | NOT_RUN |

## 8. Next step

Continue source review for the exact ARC request aggregation and regulator endpoint voltage semantics. Keep all ARC nodes out of the initial storage-first DTS until the port, binding and resource mappings are implemented and reviewed. ROUND12 AVB metadata remains the only current local Agent task. PR #1 remains Draft; no device operation, compile, image packing, flash or writes.
