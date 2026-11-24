# ROUND23 — ACK ARC provider device topology and request aggregation design

Date: 2026-11-24

Status: public ACK and legacy Qualcomm source review, informed by existing ROUND7 and completed ROUND11 reports. No local extraction, no new parser, no driver source authored, no binding written, no Kconfig resolution, no compile, no DTB/boot packaging or device operation.

## 1. Device hierarchy: an ARC provider can be an apps_rsc direct child

The ACK rpmh-rsc platform driver:
1. probes the apps_rsc RSC node and stores struct rsc_drv as the RSC device's driver data;
2. calls devm_of_platform_populate() on the RSC device to create available children as platform devices.

The ACK RPMh client helper obtains the controller with dev_get_drvdata(dev->parent).

Consequently, a new ARC provider platform device must be a direct child of the apps_rsc RSC device. Its pdev->dev then has the RSC device as dev->parent, so the current rpmh_write() API can find the controller. A provider created one device level lower would not satisfy this API's current parent lookup unless a separate supported RSC client device context were introduced.

This permits an isolated ARC driver port under drivers/regulator/ without changing rpmh-rsc.c itself.

Sources:
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh-rsc.c
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh.c
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/soc/qcom/rpmh.h

## 2. Do not rely on RPMh API to aggregate ARC child votes

The ACK RPMh cache is keyed by resource address. For a given address:
- RPMH_ACTIVE_ONLY_STATE and RPMH_WAKE_ONLY_STATE replace the cached wake_val with the new command data;
- RPMH_SLEEP_STATE replaces the cached sleep_val;
- active-only requests are sent immediately;
- sleep/wake requests are buffered for controller flush.

This API is a transport/cache layer, not a collection of independent Linux regulator-client votes. It does not compute a maximum across multiple child regulator requests that map to the same ARC resource.

The old Qualcomm ARC driver explicitly owns that layer:
- one aggregate object per RPMh ARC resource;
- multiple regulator framework children attached to the shared resource;
- each child stores its own active/sleep request and qcom,set membership;
- aggregate logic independently takes the maximum register request across all requesting children for ACTIVE and SLEEP;
- pseudo-enable rules are applied after aggregation;
- only the changed aggregate is sent to RPMh.

Without this shared aggregation, the last callback that writes the same ARC address can overwrite the previously requested level and lower the resource while another child still needs a higher corner.

Sources:
- ACK cache implementation: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/rpmh.c
- Legacy max aggregation: https://android.googlesource.com/kernel/msm/%2B/28f2b66a16e50693a0796b323d652ed1669115b1/drivers/regulator/rpmh-regulator.c

## 3. Proposed internal data model (design only)

One arc_resource per top-level ARC provider node:
- struct device pointer: the provider platform device, a direct child of apps_rsc;
- resource name and command database address;
- u16 voltage-level table with up to 16 validated entries from Command DB AUX data;
- mutex;
- child regulator array/list;
- previous aggregate active/sleep request values and validity masks;
- optional policy flags such as always-wait-for-ack.

One child arc_vreg record per regulator subnode:
- regulator descriptor and regulator_dev;
- regulator-name;
- framework min/max level range mapped onto the resource AUX table;
- selected active/sleep participation from qcom,set;
- active and sleep request state;
- pseudo-enable state;
- initial level and optional parent-dropout constraints;
- generated supply_name = regulator-name-parent when the parent provider node supplies regulator-name-parent-supply.

On a regulator callback:
1. lock the shared arc_resource;
2. snapshot the child's previous request;
3. update one child's active/sleep state;
4. recompute aggregate max for active and sleep across every child, respecting set membership;
5. apply ARC level-zero OFF / pseudo-enable semantics;
6. submit changed aggregate command using the current ACK RPMh device API;
7. if a synchronous/ACKed write fails, restore the child's previous state and preserve the previous aggregate;
8. unlock.

The resource provider should not send one raw RPMh write independently per child regulator.

## 4. Command DB parsing and DT binding requirements

The legacy binding requires a top-level qcom,resource-name, which must match a resource known to bootloader Command DB. Legacy ARC probe verifies that the resource exists and has the ARC slave ID. It then reads a u16 AUX voltage-level map (1–16 entries; zero padding at the end is ignored).

The ACK APIs are available:
- CMD_DB_HW_ARC;
- cmd_db_read_slave_id();
- cmd_db_read_addr();
- cmd_db_read_aux_data(resource, &len);
- current device-based rpmh_write() / rpmh_write_async().

The new ACK binding should explicitly validate:
- correct ARC resource-name and Command DB class;
- AUX data length/endianness/entry count;
- child regulator-name uniqueness and supported level ranges;
- qcom,set state membership;
- qcom,init-voltage-level, qcom,min-dropout-voltage-level, and optional qcom,send-defaults semantics;
- parent supply property name generation;
- unsupported/unknown properties fail clearly rather than silently mapping a wrong voltage level.

The old downstream binding also defines optional qcom,use-awake-state. For the upstream ACK SM8250 RSC configuration, the normal path is ACTIVE_ONLY/SLEEP/WAKE_ONLY; do not copy an AWAKE-only mode into ACK. HOS4.3 runtime TCS override was not established by the existing property inventory.

References:
- Legacy RPMh regulator binding: https://android.googlesource.com/kernel/msm/%2B/1c7b30fefbb5b998e1093335ad27668c5c2dc50c/Documentation/devicetree/bindings/regulator/rpmh-regulator.txt
- Legacy probe/resource validation: https://android.googlesource.com/kernel/msm/%2B/3e85c600521948b1e7dde991979c700d3d465a6a/drivers/regulator/rpmh-regulator.c
- ACK Command DB API: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/soc/qcom/cmd-db.h
- ACK TCS states: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/include/soc/qcom/tcs.h

## 5. What is still missing from the local HOS4.3 evidence

ROUND11 completed the supply/phandle graph, but not the complete ARC initialization contract. Existing ROUND7 CSV is a selected/partial property inventory and cannot prove that unlisted properties are absent.

The existing reports do not yet establish:
- top-level qcom,resource-name for mxlvl, cxlvl and mmcxlvl;
- top-level qcom,send-defaults, qcom,always-wait-for-ack, or qcom,use-awake-state;
- child qcom,set, qcom,init-voltage-level, and qcom,min-dropout-voltage-level;
- exact AUX map contents (these are runtime Command DB data rather than just a normal DT property);
- qcom,proxy-consumer-enable, qcom,proxy-consumer-voltage, qcom,proxy-consumer-current flags associated with proxy-supply.

The likely standard resource names for Qualcomm SM8250-family ARC groups are mx.lvl, cx.lvl and mmcx.lvl (as shown in public Qualcomm Kona regulator sources), but these remain candidates until verified against this exact HOS4.3 FDT and Command DB resource namespace.

The next required local property check, once the current ROUND12 AVB task is complete, should be narrowly scoped to these three existing ARC provider nodes and their regulator children. It should report property names and non-sensitive string/enum values only; do not export AUX data, physical addresses, binaries, or the rest of the FDT. Do not repeat the ROUND11 parent/proxy phandle extraction.

## 6. Proxy-consumer remains separate

The old proxy helper temporarily votes supplies with proxy-supply and qcom,proxy-consumer request flags, then releases them at late_initcall_sync. ACK does not currently have this helper or regulator-core registration hook.

The six ROUND11 proxy-supply phandles are known, but whether their owners carry request flags and whether UFS first-stage requires a proxy vote remain UNKNOWN. Do not fold proxy support into the ARC provider or assume it is required.

## 7. Porting recommendation

1. Keep the storage-first board DTS unchanged for now: no ARC compatible nodes or proxy consumer flags.
2. Design the ARC provider as a separate direct child of apps_rsc, one shared aggregator per ARC resource.
3. Keep the PMIC VRM provider and its unresolved physical input parents a separate issue (ROUND21); do not try to solve those with ARC child-parent links.
4. After the targeted HOS4.3 ARC properties are confirmed, draft the binding and driver implementation plan and only then add corresponding ARC nodes in a separate DT overlay/revision.
5. Port proxy-consumer only if source flags prove it is used by the device and first-stage boot depends on it.

This round is an implementation blueprint, not a driver implementation. No source file, binding, Kconfig symbol or ARC DTS node has been added.

## 8. Verification status

| Item | Status |
|---|---|
| ACK RSC devm_of_platform_populate child topology | SOURCE REVIEWED |
| RPMh API dev->parent controller lookup | SOURCE REVIEWED |
| ACK RPMh per-address cache semantics | SOURCE REVIEWED |
| Legacy ARC shared-resource max aggregation | SOURCE REVIEWED |
| Proposed direct-child ARC provider architecture | DESIGN COMPLETE |
| HOS4.3 ARC qcom,resource-name values | UNKNOWN / NOT IN CURRENT REPORT |
| HOS4.3 child qcom,set / initial / dropout flags | UNKNOWN |
| HOS4.3 Command DB AUX level data | NOT_READ |
| HOS4.3 proxy request flags | UNKNOWN |
| ARC driver / schema / Kconfig implementation | NOT_IMPLEMENTED |
| Kconfig resolution / compilation / DTB build / boot | NOT_RUN |

## 9. Next step

Continue source-side review of ACK RPMh/Command DB interactions and the proposed ARC driver. The next local check is limited to existing HOS4.3 ARC group properties after ROUND12 finishes; do not ask the Agent to repeat ROUND11 supply graph work. Keep PR #1 Draft; no device operation, image writes, compile or flash.
