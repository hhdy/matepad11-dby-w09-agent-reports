# ROUND88 — 1号 AI source review: UFS VCC voltage parsing must precede the first regulator enable

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, after a separate test task is issued  
**Pinned baseline:** ACK `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Related records:** ROUND82, ROUND84, ROUND86, ROUND87

## 1. Executive result

**New sequencing requirement:** the DBY-W09 UFS VCC voltage interval must be parsed and stored before the first `ufshcd_setup_vreg(hba, true)` call.

The fixed ACK initialization order is:

1. `ufshcd_pltfrm_init()` sets `hba->vops`.
2. It calls generic `ufshcd_parse_regulator_info(hba)`, which creates the `vcc` / `vccq` / `vccq2` descriptors.
3. It then calls `ufshcd_init()`.
4. During `ufshcd_hba_init()`, the core obtains regulator handles, then calls `ufshcd_setup_vreg(hba, true)`.
5. Only after the regulator rails have been configured and enabled does `ufshcd_hba_init()` call `ufshcd_variant_hba_init()`, which invokes the Qualcomm variant's `ufs_qcom_init()` callback.

Therefore, parsing and applying `vcc-voltage-level` solely from `ufs_qcom_init()` is too late to guarantee that the initial VCC enable observes the UFS consumer interval. The regulator API can change voltage while enabled, but that does not make the post-enable placement equivalent to the legacy pre-enable request order.

This sequencing issue does not invalidate ROUND86's finding that L17 supports the interval; it affects where/how 2号 AI must wire the parsed request into the UFS lifecycle.

## 2. Exact pinned ACK call order

### 2.1 Generic platform probe

Source: [`drivers/ufs/host/ufshcd-pltfrm.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.c).

In `ufshcd_pltfrm_init()`:
- `hba->vops = vops` is assigned first.
- `ufshcd_parse_clock_info(hba)` runs.
- `ufshcd_parse_regulator_info(hba)` runs and creates the generic supply descriptors.
- OPP information is parsed.
- `ufshcd_init(hba, ...)` is called afterward.

This is an early stage where the platform code already knows the variant ops and has created `hba->vreg_info.vcc`, but the UFS regulator enable sequence has not started yet.

### 2.2 UFS HBA regulator setup

Source: [`drivers/ufs/core/ufshcd.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c).

In `ufshcd_hba_init()`, the relevant sequence is:
- `ufshcd_init_vreg(hba)`: obtains the VCC/VCCQ/VCCQ2 regulator handles.
- `ufshcd_setup_vreg(hba, true)`: configures and enables the UFS device rails.
- `ufshcd_variant_hba_init(hba)`: invokes the variant's init callback.

The generic UFS core therefore enables the supply rails before the Qualcomm variant init callback executes.

### 2.3 Qualcomm variant callback

Source: [`drivers/ufs/host/ufs-qcom.c`](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufs-qcom.c).

- `ufs_hba_qcom_vops.init` is `ufs_qcom_init`.
- `ufs_qcom_probe()` invokes `ufshcd_pltfrm_init(pdev, &ufs_hba_qcom_vops)`.
- The core later invokes this variant init callback only from `ufshcd_variant_hba_init()`, after `ufshcd_setup_vreg(hba, true)`.

A patch that first reads the VCC range inside `ufs_qcom_init()` cannot ensure that the first VCC enable was preceded by the voltage request.

## 3. Why the distinction matters

The regulator API supports `regulator_set_voltage()` while a regulator is enabled or disabled. Therefore, a late call may still update the running L17 voltage request and may not fail simply because the rail is on.

However, the legacy Qualcomm sequence applied its VCC range before enabling VCC. Applying the request only in `ufs_qcom_init()` creates a window where:
- the generic core has already enabled VCC;
- only provider constraints / pre-existing PMIC state govern the initial requested voltage;
- the UFS consumer-specific 2.504–2.950 V range has not yet been applied.

For this board, L17 provider constraints are wider (2.496–3.008 V) than the UFS consumer interval. A late request therefore does not preserve the old pre-enable contract.

## 4. Recommended integration point

2号 AI should keep the exported `ufshcd_populate_vreg()` generic and unchanged. It is used by MediaTek UFS paths for dynamically named `vcc-ufsX` / `vcc-optX` rails.

Instead, add a narrow early-parse mechanism after generic supply descriptor population and before `ufshcd_init()` begins. Options include:

**Preferred separation:** add a small optional variant callback dedicated to regulator-property parsing (or equivalent platform-init hook). The Qualcomm variant registers the callback; `ufshcd_pltfrm_init()` invokes it immediately after `ufshcd_parse_regulator_info()` and before `ufshcd_init()`. The callback can read the Qualcomm VCC property into `hba->vreg_info.vcc` without acquiring or enabling the regulator yet.

**Minimal alternative:** keep the parser in platform glue and gate it explicitly to the Qualcomm variant (whose `vops` is already assigned before generic parsing). This is simpler but couples generic platform glue to the Qualcomm variant name/property.

Do not:
- parse only in `ufs_qcom_init()` and claim it was applied before initial enable;
- modify the exported `ufshcd_populate_vreg()` to parse this Qualcomm-only property for every consumer name;
- move all variant initialization before generic regulator setup, because that would reorder unrelated host initialization and could change other drivers' assumptions.

After the min/max values are stored in the VCC descriptor before `ufshcd_init()`, the existing first `ufshcd_setup_vreg(hba, true)` path can apply the voltage request and DRMS load before calling `regulator_enable()`, preserving the legacy ordering.

## 5. Integration and test requirements

A follow-up patch/test should prove:
1. The optional parser is called for the Qualcomm variant before `ufshcd_init()`.
2. The parsed range is stored before `ufshcd_init_vreg()` / `ufshcd_setup_vreg(hba, true)`.
3. The first VCC regulator operation applies the range before `regulator_enable()`.
4. The VCC voltage request and VCC DRMS load vote are both applied; neither replaces the other.
5. A missing property leaves other platforms' behavior unchanged.
6. MediaTek's dynamic VCC path and any non-Qualcomm platform using `ufshcd_pltfrm_init()` remain unchanged.
7. A malformed present property fails before any VCC regulator is enabled.
8. Rollback and voltage-request release errors remain separately tracked as required by ROUND84/87.

## 6. Ownership and boundaries

**This is a [1号 AI read-only source-order review] for 2号 AI.**
- 1号 AI: source call-graph analysis and design feedback.
- 2号 AI: owns the actual patch and its integration design.
- Testing Agent: test-only; requires a separate `AGENT_TEST_TASK.md` after the patch is ready.
- No command execution is being assigned to the user.

No source, DTS, binding, patch, config, 2号 AI branch, or protected branch was modified. No patch was applied, no build/schema/test command was run, and no device was accessed.

**Final status:** Qualcomm VCC voltage parsing needs an early variant-specific hook before first regulator enable. Parsing only inside `ufs_qcom_init()` would be late. This is a new integration-order requirement for the 2号 AI implementation, not a change to the board DTS values.
