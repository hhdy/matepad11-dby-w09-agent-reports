# AI2 ROUND148 — ARC regulator and proxy-consumer portability audit

- Author: 2号 AI（独立 AI 协作者）
- Date: 2026-11-26
- Target: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel: Android 17 ACK android17-6.18.33_r00
- Pinned ACK: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- Candidate source tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Generic Qualcomm reference: OnePlusOSS/android_kernel_oneplus_sm8475, commit `7278ce9a3c8539b4630d6988cc80f90c31c07336`
- Scope: read-only source portability review. No source changes, patch, build, download, device operation or private Agent workspace inspection.

## 1. Executive disposition

**The pinned ACK has the low-level CMD-DB/RPMh and regulator-framework primitives needed to implement an ARC producer, but it does not contain the ARC producer or proxy-consumer facility. The generic Qualcomm ARC implementation is therefore a plausible porting reference, not a drop-in driver. A faithful HOS4.3 model requires both ARC child-regulator semantics and a separately audited proxy-vote/lifecycle implementation.**

The most important architectural risk is the proposed **GenPD UFS OPP + ARC hybrid**:

- HOS4.3's `mmcxlvl` ARC provider uses CMD-DB resource `mmcx.lvl`.
- The pinned SM8250 RPMhPD `RPMHPD_MMCX` descriptor also uses `mmcx.lvl`.
- Both implementations send commands to the same CMD-DB resource address through the same RPMh controller.
- The ARC driver aggregates child regulator requests internally; RPMHPD aggregates its own domain/peer requests internally. The pinned RPMh cache is keyed by command address, not by regulator-vs-GenPD owner. It does not provide a cross-driver max aggregation layer.

Therefore, if both ARC and GenPD instances are active for `mmcx.lvl`, **the design has a shared-address vote ownership collision**. It must not be assumed that Linux will combine their independent votes safely. A single owner must arbitrate the resource, or one implementation must not issue votes for that resource. Whether the candidate compiled DTB actually instantiates the HOS `mmcxlvl` provider remains unpublished/unverified; the collision is conditional on both providers being present and active.

**Recommendation:** do not select ARC-only, ARC+proxy, or hybrid implementation by resource-name resemblance alone. First settle resource ownership for `mmcx.lvl`, inventory the exact candidate DTB ARC nodes, and obtain authoritative HOS4.3 ARC driver / CMD-DB evidence. GenPD-only is the narrowest possible UFS performance replacement, but it is not equivalent to the full HOS ARC child-regulator graph.

## 2. Source facts established

### 2.1 HOS4.3 ARC and proxy inventory (ROUND139)

ROUND139 reports seven HOS4.3 provider groups with compatible `qcom,rpmh-arc-regulator`:

- `mxlvl` → `mx.lvl`
- `cxlvl` → `cx.lvl`
- `mmcxlvl` → `mmcx.lvl`
- `lmx.lvl`, `lcx.lvl`, `gfx.lvl`, `ebi.lvl`

It also resolves exactly five ARC child `*-parent-supply` edges:

| Child provider / child regulator | Parent provider / child regulator | Relationship |
|---|---|---|
| cxlvl / `regulator-pm8150a-s3-level` | mxlvl / `regulator-pm8150a-s3-level` | CX ALL → MX ALL |
| cxlvl / `regulator-pm8150a-s3-level-ao` | mxlvl / `regulator-pm8150a-s3-level-ao` | CX AO → MX AO |
| mmcxlvl / `regulator-pm8150a-s4-level` | mxlvl / `regulator-pm8150a-s3-mmcx-sup-level` | MMCX ALL → MX MMCX-supply ALL |
| mmcxlvl / `regulator-pm8150a-s4-level-ao` | mxlvl / `regulator-pm8150a-s3-level-ao` | MMCX AO → MX AO |
| mxlvl / `regulator-pm8150a-s3-mmcx-sup-level` | cxlvl / `regulator-pm8150-s3-mmcx-sup-level` | MX MMCX-supply → CX MMCX-supply |

These are **regulator-framework ARC child supply edges**, not physical PMIC VIN parents and not simply GenPD parent pointers.

ROUND139 separately reports eight `proxy-supply` occurrences, each pointing into its own child set; `qcom,proxy-consumer-enable` on those eight sites plus one GDSC and one refgen provider; and `qcom,proxy-consumer-current` on four child regulator nodes. The reported HOS inventory does not establish occurrences of `qcom,proxy-consumer-voltage` or `qcom,proxy-consumer-name`; do not assume either property is present or absent without a dedicated census.

Important naming distinction: `regulator-pm8150a-s4-level` is the ARC resource `mmcx.lvl`, not the PM8150 S4 VRM rail (`smpa4`). Likewise, `proxy-supply` is a boot-time consumer supply edge, not an ARC parent-supply edge and not a physical input rail.

Evidence:
- [ROUND139 ARC child edges and proxy sites](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L137-L167)
- [ROUND139 seven ARC groups and pinned-ACK coverage census](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L177-L200)

### 2.2 Pinned ACK ARC driver coverage

Pinned `drivers/regulator/qcom-rpmh-regulator.c` declares only `VRM` and `XOB` in its RPMh regulator type enum. Its OF match table handles per-PMIC groups such as `qcom,pm8150-rpmh-regulators` and `qcom,pm8150l-rpmh-regulators`; it has no `qcom,rpmh-arc-regulator` match and no ARC selector / per-child aggregation implementation.

This is a separate gap from the generic RPMhPD GenPD implementation. The existing `REGULATOR_QCOM_RPMH` Kconfig option builds the VRM/XOB driver; it does not silently supply the legacy aggregate ARC regulator driver.

Evidence:
- [Pinned ACK RPMh regulator types](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/qcom-rpmh-regulator.c#L20-L34)
- [Pinned ACK RPMh regulator OF match and probe](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/qcom-rpmh-regulator.c#L1640-L1752)
- [Pinned ACK Kconfig option](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/Kconfig#L1124-L1134)
- [Pinned ACK regulator Makefile](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/Makefile)

### 2.3 Generic Qualcomm reference is not HOS source

The OnePlus SM8475 reference at the pinned reference commit implements a generic Qualcomm RPMh ARC producer and proxy-consumer facility. It is useful for understanding the API and design, but it is **not proven to be the exact Huawei HOS4.3 source or binary**. It cannot establish HOS-specific CMD-DB AUX contents, child defaults, resource votes or vendor lifecycle choices.

Reference:
- [Reference ARC types / data structures](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L20-L130)

## 3. Pinned ACK API compatibility matrix

Status definitions: PRESENT = declared/implemented in pinned ACK with compatible source-level interface; DIFFERENT = exists but requires semantic or signature adaptation; ABSENT = the facility is not present; UNKNOWN = evidence insufficient.

| Reference dependency | Pinned ACK evidence | Status | Porting interpretation |
|---|---|---|---|
| `cmd_db_read_addr(const char *)` | `include/soc/qcom/cmd-db.h` | **PRESENT** | Same function and resource-name lookup model |
| `cmd_db_read_slave_id(const char *)` | same header; returns `enum cmd_db_hw_type` | **PRESENT** | ARC type `CMD_DB_HW_ARC` exists; integer assignment/comparison is straightforward |
| `cmd_db_read_aux_data(const char *, size_t *)` | same header; returns `const void *` | **PRESENT** | Reference consumes bytes as a u16 array; a port must preserve length validation, endian handling and zero-padding rules |
| `rpmh_write_async()` / `rpmh_write()` | `include/soc/qcom/rpmh.h`, `drivers/soc/qcom/rpmh.c` | **PRESENT** | Signatures match the generic reference |
| `enum rpmh_state` | `include/soc/qcom/tcs.h` | **PRESENT** | `RPMH_SLEEP_STATE`, `RPMH_WAKE_ONLY_STATE`, `RPMH_ACTIVE_ONLY_STATE` exist |
| `struct tcs_cmd` | same header | **PRESENT** | `addr`, `data`, `wait` fields exist |
| `CMD_DB_HW_ARC` | `include/soc/qcom/cmd-db.h` | **PRESENT** | The hardware type constant exists; this does not itself implement ARC |
| ARC `regulator_ops` callbacks | `include/linux/regulator/driver.h` | **PRESENT** | `set_voltage_sel`, `get_voltage_sel`, `list_voltage`, enable/disable callbacks are supported by the framework |
| `regulator_desc.supply_name` | same header | **PRESENT** | Child parent supply can be expressed through normal regulator core |
| `devm_regulator_register()` | pinned regulator driver API and existing ACK drivers | **PRESENT** | Child regulators can be registered by a new provider |
| `regulator_set_voltage()`, `regulator_set_load()`, `regulator_enable()/disable()` | `include/linux/regulator/consumer.h` | **PRESENT** | Required primitives for proxy requests exist |
| `of_platform_populate()` | generic OF platform API | **PRESENT** | Can populate compatible child devices; it does not itself create the child regulator devices |
| Recursive child-regulator lookup | `drivers/regulator/of_regulator.c`, `core.c` | **PRESENT** | Nested provider-child `*-supply` lookup and recursive supply resolution already exist |
| Proxy consumer header/source | `include/linux/regulator/proxy-consumer.h`, `drivers/regulator/proxy-consumer.c` | **ABSENT** | Both paths are absent at pinned ACK |
| `CONFIG_REGULATOR_PROXY_CONSUMER` and Makefile object | pinned regulator Kconfig / Makefile | **ABSENT** | Reference proxy API cannot be included or linked unchanged |
| `regulator_proxy_consumer_register/unregister`, `devm_*`, `regulator_proxy_consumer_sync_state()` | no pinned declarations/implementation | **ABSENT** | Must port the facility or design a separately reviewed replacement |
| Generic device `.sync_state` callback hook | platform driver core | **PRESENT** | Callback infrastructure is distinct from the missing proxy library function |

Exact pinned interfaces:
- [CMD-DB public header](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/include/soc/qcom/cmd-db.h#L1-L50)
- [RPMh public header](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/include/soc/qcom/rpmh.h#L1-L45)
- [RPMh TCS state and command structures](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/include/soc/qcom/tcs.h#L1-L65)
- [Nested child regulator lookup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/of_regulator.c#L571-L640)
- [Regulator supply resolution / recursive parent lookup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L1975-L2140)
- [Regulator recursive enable/disable supply handling](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L2898-L3060)
- [Reference proxy API header](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/include/linux/regulator/proxy-consumer.h#L1-L39)

**Key conclusion:** the lower-level CMD-DB, RPMh transport, selector operations and regulator framework are reusable. The missing pieces are the ARC-specific provider/child driver logic and the entire proxy-consumer facility, not a missing `rpmh_write` primitive.

## 4. ARC producer behavior in the generic Qualcomm reference

### 4.1 Provider probe and resource identity

The reference provider:
1. Matches `qcom,rpmh-arc-regulator`.
2. Reads `qcom,resource-name`.
3. Resolves the CMD-DB address and slave ID.
4. Verifies that the slave ID is `CMD_DB_HW_ARC`.
5. Reads resource-specific AUX data.
6. Enumerates child nodes without their own `compatible`, reads each `regulator-name`, and registers each child as a separate regulator.
7. Calls `of_platform_populate()` for other compatible children.

The per-child regulator devices are created by the provider's explicit `devm_regulator_register()` calls, not by `of_platform_populate()`.

References:
- [Reference ARC resource probe and CMD-DB checks](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L1835-L1990)
- [Reference child enumeration and regulator registration](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L1645-L1830)

### 4.2 Resource-specific CMD-DB AUX level map

The reference reads AUX data separately for each ARC resource. It treats each entry as a 16-bit consumer voltage level, with up to 16 hardware ARC levels (0–15). The selector is the hardware level index; `list_voltage(selector)` returns the corresponding AUX consumer-level value. The implementation validates:
- nonzero AUX length;
- length no larger than 16 × 2 bytes;
- length divisible by two;
- trailing zero padding ignored after the first valid level.

Do not invent or transfer numerical maps between `mmcx.lvl`, `mx.lvl`, `cx.lvl` or other resources. The actual HOS4.3 CMD-DB AUX bytes are not included in the reviewed report and remain **UNKNOWN**.

Reference:
- [ARC selector operations and AUX level-map loader](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L1153-L1316)

### 4.3 Child aggregation and ACTIVE / SLEEP / WAKE_ONLY

Each child regulator keeps its own request values and `qcom,set` flags. The provider aggregates child requests separately for active and sleep sets, using a **maximum value per request register** across children selected for that set.

The reference then:
- sends changed sleep-set values with `RPMH_SLEEP_STATE`;
- when active and sleep sets differ, sends the active aggregate as `RPMH_WAKE_ONLY_STATE` so the active request is restored on wake;
- sends the current active aggregate with `RPMH_ACTIVE_ONLY_STATE`;
- waits for an ACK when a requested level increases (or when configured to always wait).

WAKE_ONLY is therefore a state-restoration request used in the active/sleep transition protocol, not a third independent regulator consumer policy.

The provider's max aggregation is **within one ARC provider resource and its child regulators**. It does not automatically aggregate votes issued by a separate GenPD driver.

Reference:
- [ARC child max aggregation and active/sleep/wake request construction](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L600-L900)

### 4.4 ARC enable / disable

ARC has no independent hardware enable register in this model. The generic reference uses a pseudo-enable request. If AUX level 0 is the OFF level, disabling a child masks its requested ARC level to zero; enabling unmasks it. If level 0 is not OFF, the reference removes enable/disable/is_enabled operations for that regulator. A port must preserve this conditional behavior; it must not assume every ARC resource supports OFF.

Reference:
- [ARC pseudo-enable and aggregate handling](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L600-L700)
- [ARC regulator operations](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L1153-L1316)

### 4.5 Parent-supply versus physical VIN

For each child, the reference checks for a property named `<regulator-name>-parent-supply` on the provider or child node. If found, it sets `regulator_desc.supply_name` to `<regulator-name>-parent`, allowing regulator core's nested child lookup to resolve the referenced parent ARC child regulator.

Separately, if the child has `vin-supply`, the reference sets `supply_name = "vin"`. These are different relationships:
- `*-parent-supply`: ARC provider-child dependency in the regulator framework;
- `vin-supply`: physical/electrical input rail relationship;
- `proxy-supply`: separate proxy consumer request supply.

The five HOS ARC child edges therefore cannot be replaced merely by a GenPD parent pointer or by inventing PMIC VIN relationships.

Reference:
- [Reference ARC child supply-name setup and regulator registration](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L1645-L1830)

## 5. Proxy-consumer semantics and portability gap

### 5.1 Reference behavior

The public Qualcomm proxy library checks for:
- `qcom,proxy-consumer-enable`;
- `qcom,proxy-consumer-voltage` (min/max pair);
- `qcom,proxy-consumer-current`.

If none are present, no proxy consumer is created. The optional `qcom,proxy-consumer-name` selects the regulator supply ID; the default is `proxy`. A `regulator_get(dev, "proxy")` then resolves the consumer's `proxy-supply` phandle through the ordinary regulator OF lookup path.

For a configured proxy request, the library may:
- call `regulator_set_voltage(min_uV, max_uV)`;
- call `regulator_set_load(current_uA)`;
- call `regulator_enable()`.

On removal it reverses the request: disable if enabled, set load to zero, reset voltage range to `0..INT_MAX`, then `regulator_put()`.

Thus, `proxy-supply` is not parsed as a standalone ARC property. It is consumed through normal regulator supply lookup after the proxy library selects a supply name.

References:
- [Proxy request property parsing and voting](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/proxy-consumer.c#L41-L147)
- [Proxy consumer public API](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/include/linux/regulator/proxy-consumer.h#L1-L39)

### 5.2 Lifecycle semantics

The reference provides normal and devm registration/unregistration. The devm release path checks whether a proxy request was already removed before removing it again, preventing double cleanup.

Two lifetime policies are supported:
- **Default per-device sync_state:** the provider driver's `.sync_state` callback calls `regulator_proxy_consumer_sync_state(dev)`, which removes that provider's proxy requests after its consumers have probed and established their own requests.
- **Legacy global cleanup:** with `CONFIG_REGULATOR_PROXY_CONSUMER_LEGACY`, the per-device sync_state callback is a no-op and all proxy votes are removed at `late_initcall_sync()`, assuming device probing has completed.

This timing is functionally important. A naive port that removes proxy votes at provider probe completion, or never removes them, changes the boot-time power contract. The provider's devm cleanup is also distinct from sync_state unvoting: devm handles device detach; sync_state / legacy late-init removes temporary boot votes.

References:
- [Proxy unregister and devm lifetime](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/proxy-consumer.c#L149-L330)
- [Proxy sync_state and legacy late_initcall_sync](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/proxy-consumer.c#L330-L400)
- [Reference proxy Kconfig policy](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/Kconfig#L45-L85)
- [Reference regulator Makefile](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/Makefile)

### 5.3 HOS4.3 vs pinned ACK

ROUND139 reports the HOS proxy-supply and enable/current sites, but the pinned ACK has no proxy-consumer header, source, Kconfig option, Makefile object or proxy-specific symbols. The generic regulator APIs used by the proxy library do exist; the missing feature is the wrapper and its lifetime manager.

Consequences:
- HOS `proxy-supply` declarations are inert in the pinned ACK unless some other consumer explicitly requests the matching supply.
- HOS `qcom,proxy-consumer-enable/current` are not interpreted by the pinned ARC/VRM drivers.
- A port of ARC producer code that calls `devm_regulator_proxy_consumer_register()` unchanged will not compile until the proxy facility is also ported or replaced.
- Do not assume that importing proxy support automatically proves the HOS4.3 boot sequence. Its property inventory, provider dependencies and unvote timing must be validated.

## 6. GenPD UFS OPP and ARC mmcx.lvl ownership collision

This is the main risk for the hybrid option.

### 6.1 Same resource identity

ROUND139 establishes HOS4.3 `mmcxlvl` as an ARC provider with `qcom,resource-name = "mmcx.lvl"`.

Pinned ACK `rpmhpd.c` defines the `mmcx` GenPD descriptor with `.res_name = "mmcx.lvl"`, and the SM8250 descriptor maps `RPMHPD_MMCX` to that `mmcx` object. The GenPD driver resolves the CMD-DB address for that same resource name and sends level commands to that address.

References:
- [Pinned RPMHPD mmcx descriptor and resource name](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L115-L145)
- [Pinned SM8250 RPMHPD mapping](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L445-L485)
- [RPMHPD CMD-DB address lookup and send-corner path](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L800-L860)
- [ROUND139 HOS ARC resource inventory](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L177-L200)

### 6.2 RPMh cache is keyed by address, not by driver consumer

Pinned ACK `rpmh.c` finds an existing cached request by command address. `cache_rpm_request()` updates the stored sleep or wake value for that address. The cache is associated with the RPMh controller, not namespaced by the calling regulator or GenPD driver.

The ARC provider maintains its own child-level max aggregation before sending to RPMh. RPMHPD separately maintains its own domain/peer aggregation before sending to RPMh. Neither aggregator sees the other driver's child/domain request set.

Therefore, if both paths issue requests to the same `mmcx.lvl` CMD-DB address, their requests are not automatically combined by a shared Linux max-vote manager. The shared RPMh cache slot can be overwritten by later writes from either driver; the resulting active/sleep/wake values may reflect the last writer rather than the maximum of ARC and GenPD demands.

This is a source-level ownership conflict, not proof of a specific runtime failure. Actual behavior still depends on which providers are present and probed in the compiled candidate DTB and on the real resource address resolution.

References:
- [Pinned RPMh cache lookup/update keyed by address](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/soc/qcom/rpmh.c#L45-L125)
- [Reference ARC child aggregation is local to one aggregate provider](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8475/blob/7278ce9a3c8539b4630d6988cc80f90c31c07336/drivers/regulator/rpmh-regulator.c#L600-L900)
- [Pinned RPMHPD active/sleep/wake aggregation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L820-L900)

### 6.3 Ownership rule required before hybrid design

Do not allow both independent implementations to own `mmcx.lvl` unless a single shared arbitration layer is designed and verified. Acceptable architectural directions would be:
1. one provider owns the CMD-DB resource and exposes a single API to both GenPD and regulator consumers;
2. GenPD owns `mmcx.lvl` and ARC provider does not independently write that same resource, with explicit proof that all required ARC child semantics are represented elsewhere; or
3. ARC provider owns `mmcx.lvl` and the UFS OPP path is routed through that same owner rather than issuing a second RPMh vote.

Simply instantiating both providers and expecting RPMh to max-aggregate Linux clients is not acceptable.

Also note that the exact compiled candidate DTB ARC-node inventory has not been published in the reviewed artifacts. Whether `mmcxlvl` will actually coexist with the GenPD UFS OPP provider remains **UNKNOWN** and requires a read-only census of the already-built candidate DTB by its owner.

## 7. Porting options

| Option | Benefits | Missing proof / risks | Assessment |
|---|---|---|---|
| **1. Port ARC producer only** | Recreates HOS ARC compatible, CMD-DB AUX mapping, per-child regulator devices, child max aggregation, active/sleep votes and regulator-core parent supplies | Does not implement HOS proxy-consumer boot votes or their unvote lifecycle; proxy properties remain inert. Requires adaptation to pinned regulator API and exact HOS CMD-DB maps | **Incomplete HOS behavior** |
| **2. Port ARC + proxy-consumer facility** | Closest generic source-level match to HOS ARC + proxy declarations; preserves temporary enable/voltage/current votes and sync_state/legacy cleanup model | Adds a new generic subsystem; must inventory each proxy site, resolve all supplies, choose correct lifecycle policy, verify error unwinding and ensure no duplicate resource ownership. OnePlus implementation is not exact HOS code | **Best fidelity candidate only after source and board evidence** |
| **3. GenPD UFS OPP only, with missing ARC pieces handled separately** | Keeps upstream ACK's existing GenPD/OPP architecture for the narrow UFS performance consumer | Does not reproduce five ARC child parent-supply edges or other ARC consumers. If `RPMHPD_MMCX` and ARC `mmcxlvl` both issue votes, address-cache collision. Need a single owner / arbitration plan and proof UFS-only sufficiency | **Potential narrow UFS substitute, not full HOS port** |
| **4. Custom GenPD-only reimplementation** | Avoids adding regulator ARC producer | GenPD parent hierarchy alone does not create child regulator devices, proxy consumers, per-child requests, or regulator-core supply dependencies; may flatten distinct ARC resources/children | **Not recommended without strong behavioral equivalence evidence** |

## 8. Facts, inferences and unknowns

### Source facts
- Pinned ACK RPMh regulator driver supports VRM/XOB only; ARC compatible is absent.
- Pinned ACK CMD-DB exposes address, slave-ID and AUX-data APIs; ARC hardware type exists.
- Pinned ACK RPMh exposes the same ACTIVE/SLEEP/WAKE_ONLY state enum and write APIs used by the reference.
- Pinned ACK regulator core supports nested child regulator supply lookup and recursive parent enable/disable.
- Pinned ACK has no proxy-consumer header/source/Kconfig/Makefile implementation.
- HOS4.3 ROUND139 has seven ARC provider groups, five ARC child parent-supply edges, eight proxy-supply sites and ten proxy-enable sites.
- Both HOS `mmcxlvl` and pinned SM8250 RPMHPD MMCX use resource name `mmcx.lvl`.

### Inferences
- A carefully adapted generic Qualcomm ARC provider can likely be built on the pinned ACK primitives without rewriting CMD-DB or RPMh transport.
- A faithful HOS-style port requires more than ARC selector callbacks: it must preserve child aggregation, state-set handling, nested supply semantics and proxy-vote lifecycle.
- If GenPD and ARC independently write the same `mmcx.lvl` address, the pinned ACK RPMh cache design creates a vote-ownership collision.

### Unknown / not established
- Exact HOS4.3 ARC regulator driver source revision and any Huawei-specific modifications.
- Actual HOS4.3 CMD-DB AUX bytes / per-resource level maps for all seven resources.
- Whether HOS uses the exact OnePlus reference's `qcom,set`, `qcom,send-defaults`, default-request, ACK and proxy cleanup behavior.
- Occurrence census for HOS `qcom,proxy-consumer-voltage` and `qcom,proxy-consumer-name`.
- Whether the already-built candidate DTB contains the seven HOS ARC provider groups, particularly `mmcxlvl`, at all.
- Actual candidate runtime probe order, active/sleep votes, and whether both GenPD and ARC would be active for `mmcx.lvl`.
- Physical PMIC VIN topology. ARC parent-supply and proxy-supply declarations do not prove physical electrical parents.

## 9. Recommended next evidence, in priority order

1. **Read-only candidate DTB census:** enumerate every `qcom,rpmh-arc-regulator` node, `qcom,resource-name`, child `regulator-name`, `*-parent-supply`, `proxy-supply` and proxy-consumer property in the exact compiled candidate DTB. Do not rebuild or inspect another Agent's private workspace.
2. **Resource ownership map:** for each CMD-DB resource, compare the ARC provider and GenPD descriptor resource names and resolved addresses. Explicitly mark a single Linux owner for `mmcx.lvl`.
3. **Authoritative HOS driver provenance:** if an already-accessible HOS4.3 source or extracted firmware source exists, compare ARC AUX parsing, child aggregation, `qcom,set`, defaults, proxy parsing and cleanup against the generic reference. Do not present OnePlus as Huawei source.
4. **CMD-DB AUX evidence:** obtain the actual resource-specific AUX bytes from an authorized existing artifact; decode as little-endian u16 only after verifying the format/version. Do not invent voltage/corner values.
5. **Proxy property matrix:** map each of the eight `proxy-supply` sites and ten `qcom,proxy-consumer-enable` sites to the actual target child regulator and identify current/voltage/name properties and expected sync_state or legacy unvote point.
6. **Only then** decide whether to port ARC alone, ARC plus proxy, or retain GenPD as the single owner of the UFS MMCX performance vote.

## 10. Final status

| Question | Result |
|---|---|
| Pinned ACK `qcom,rpmh-arc-regulator` producer | **ABSENT — source-confirmed** |
| Pinned ACK CMD-DB ARC type and lookup APIs | **PRESENT** |
| Pinned ACK RPMh write/state/TCS interfaces | **PRESENT / compatible** |
| Pinned ACK regulator selector and nested supply framework | **PRESENT** |
| Pinned ACK proxy-consumer facility | **ABSENT — source-confirmed** |
| Generic Qualcomm ARC + proxy reference | **FOUND — generic reference only, not HOS proof** |
| HOS4.3 ARC provider-child graph | **PRESENT — ROUND139 static evidence** |
| Exact HOS CMD-DB AUX mappings | **UNKNOWN** |
| Candidate compiled DTB ARC provider census | **NOT PUBLISHED / UNKNOWN** |
| GenPD MMCX + ARC MMCX independent ownership safe | **NO — source-level conflict risk; single owner required** |
| Complete safe porting design | **NOT ESTABLISHED** |
| First device boot | **BLOCKED / NOT AUTHORIZED** |

No source, DTS, configuration or patch was changed. No build, test, download, device connection or device operation was performed.
