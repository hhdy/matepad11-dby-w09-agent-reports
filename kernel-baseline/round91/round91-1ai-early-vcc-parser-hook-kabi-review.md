# ROUND91 — 1号 AI review: choose an early UFS VCC parse location without casually extending variant-ops ABI

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, with a separate `AGENT_TEST_TASK.md`  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related records:** ROUND82, ROUND84, ROUND88, ROUND90

## 1. Executive result

ROUND88 established that VCC voltage metadata must be parsed before `ufshcd_init()`, because the first generic UFS regulator enable happens before the Qualcomm variant's `.init` callback.

A new review of the fixed ACK interfaces adds an ABI caution:

- `ufshcd_pltfrm_init()` is exported and accepts a caller-supplied `struct ufs_hba_variant_ops *`.
- `struct ufs_hba_variant_ops` has no trailing `ANDROID_KABI_RESERVE()` slots in the pinned header.
- Adding a new callback field is therefore not just a private implementation detail: it changes the layout/size of a structure passed across the exported platform-driver interface. Any such change needs explicit GKI KMI compatibility review and a complete rebuild/review of all consumers.

**Preferred design candidate for 2号 AI:** keep the existing `ufs_hba_variant_ops` layout unchanged. Parse the optional `vcc-voltage-level` inside the already-existing generic `ufshcd_parse_regulator_info()`, immediately after the ordinary `vcc` descriptor is populated and before `ufshcd_pltfrm_init()` enters `ufshcd_init()`.

This keeps the property handling out of the exported `ufshcd_populate_vreg()` helper, preserves the MediaTek dynamic-name helper contract, and satisfies the first-enable ordering gate. The driver and binding must both be implemented and tested; this is not a patch.

## 2. Fixed ACK call path and available hook

Source: [`drivers/ufs/host/ufshcd-pltfrm.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.c).

Pinned `ufshcd_pltfrm_init()` does:
1. `hba->vops = vops`;
2. `ufshcd_parse_clock_info(hba)`;
3. `ufshcd_parse_regulator_info(hba)`;
4. parse additional host properties/OPPs;
5. call `ufshcd_init(hba, ...)`.

Inside `ufshcd_parse_regulator_info()`, the ordinary VCC descriptor is populated by `ufshcd_populate_vreg(dev, "vcc", &info->vcc, false)` before VCCQ and VCCQ2 are parsed. At this time the VCC descriptor exists, but regulator handles have not yet been acquired and no rail has been enabled.

The generic UFS core's later `ufshcd_hba_init()` obtains the handles and calls `ufshcd_setup_vreg(hba, true)` before it calls `ufshcd_variant_hba_init()`. Therefore the VCC voltage range must be prepared at the earlier platform-parse stage.

## 3. Why not immediately append a callback to `ufs_hba_variant_ops`

Pinned source: [`include/ufs/ufshcd.h`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/ufs/ufshcd.h).

The structure contains platform callbacks such as `.init`, `.exit`, clock/power callbacks and later feature callbacks. The fixed pinned definition ends after `.tx_eqtr_notify`; it has no Android KABI reserve slots at the end.

The exported platform init API is declared as:
```c
int ufshcd_pltfrm_init(struct platform_device *pdev,
                       const struct ufs_hba_variant_ops *vops);
```

Both Qualcomm and MediaTek in-tree drivers pass their statically initialized `ufs_hba_variant_ops` objects to this exported function. Appending a callback field could be made source-compatible for drivers rebuilt against the changed header, but it changes the size and layout contract of an object supplied by a platform driver. Do not treat this as ABI-free. Before choosing this design, 2号 AI would need to check the relevant Android GKI KMI policy/symbol/type status and rebuild all in-tree consumers.

No such ABI check was run in this report, so the report does not declare adding a callback forbidden; it marks it as an unnecessary risk when an existing generic parse hook already exists.

## 4. Preferred parser placement

A narrow helper can be called from the existing `ufshcd_parse_regulator_info()` after `info->vcc` has been populated and before the function returns. Its behavior should be:

1. If `vcc-voltage-level` is absent, return success and preserve all existing platform behavior.
2. If the property is present, require exactly two u32 cells.
3. Require `min_uV > 0` and `min_uV <= max_uV`; reject malformed values rather than falling back to broad generic limits.
4. Require `info->vcc` / `vcc-supply` to exist. If the voltage range is present without a VCC supply descriptor, fail early rather than claiming the request will be enforced.
5. Store min/max in a clearly named VCC descriptor field/structure to be applied by the existing generic VCC regulator lifecycle before the first `regulator_enable()`.
6. Do not parse it inside `ufs_qcom_init()`, and do not add the property handling to exported `ufshcd_populate_vreg()`.

This is an optional-property parser in the common platform regulator-info path. It does not require a new callback field in `ufs_hba_variant_ops`. Because the property is named `vcc-voltage-level` and its meaning is a VCC consumer voltage range, its binding scope should match the platforms allowed to use the property. The schema can remain scoped to Qualcomm UFS host nodes even if the common parser is tolerant of the optional property.

### 4.1 Data-storage and KMI note

The current `struct ufs_vreg` in [`include/ufs/ufs.h`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/ufs/ufs.h) stores the regulator handle, name, always-on/enabled state and `max_uA`; no VCC voltage fields exist.

A natural implementation is to store min/max and request-state alongside the VCC descriptor. However, `struct ufs_vreg` is shared through exported helper APIs too, so any size/layout change should also be checked against the GKI KMI policy. Existing in-tree callers receive objects allocated by `ufshcd_populate_vreg()`, but that alone does not prove there are no out-of-tree consumers.

Prefer a representation that keeps the change localized, and explicitly verify the ABI/KMI impact rather than assuming that appending fields is invisible.

## 5. Alternatives and trade-offs

- **Variant-specific parser callback:** clean abstraction, but changes `ufs_hba_variant_ops` layout and requires KMI review.
- **Hard-coded `vops->name == "qcom"` branch in generic glue:** avoids struct layout change but couples common platform initialization to a Qualcomm string and is less extensible.
- **Parsing in exported `ufshcd_populate_vreg()`:** avoids new hook but changes behavior of an exported shared helper also used by MediaTek dynamic supply names; avoid unless the helper is explicitly extended in a way that preserves all callers and the property semantics are validated.
- **Parsing only in `ufs_qcom_init()`:** wrong ordering; generic core already enabled the rails.
- **Parse optional VCC range in existing generic `ufshcd_parse_regulator_info()`:** the preferred minimal option because it is already the pre-enable stage and does not alter variant-ops ABI.

## 6. Required validation for 2号 AI

1. Confirm optional property parsing occurs before `ufshcd_init()`.
2. Confirm malformed/present-without-supply values fail before any regulator handle is enabled.
3. Confirm absent-property behavior is byte-for-byte/semantically unchanged for existing platforms.
4. Verify MediaTek's dynamic `vcc-ufsX` / `vcc-optX` path remains unchanged.
5. Audit `struct ufs_vreg` layout impact and relevant GKI KMI policy if adding fields.
6. Ensure the first VCC on-state voltage interval and DRMS load are applied before the first enable.
7. Re-run source integration, dt_binding_check, DT/schema validation and full Kleaf build only after 2号 AI completes its implementation.
8. Testing Agent may execute only after a separate `AGENT_TEST_TASK.md` is issued.

## 7. Ownership and boundaries

**This is a [1号 AI read-only interface/design review] for 2号 AI.**
- 1号 AI: source call-order and interface compatibility review.
- 2号 AI: owns the implementation decision and patch.
- Testing Agent: test-only, requires a separate task.
- The user is not being asked to run commands.

No source, DTS, binding, patch, config, 2号 AI branch, protected branch or PR was modified. No KMI tool, patch apply, build, schema test or device operation was run.

**Final status:** use the existing early generic regulator-info parser as the leading integration candidate; avoid adding a new `ufs_hba_variant_ops` field without KMI review. ROUND27 schema remains NOT CLEAN until the driver/binding and separate board/rootparam schema fixes are implemented and tested.
