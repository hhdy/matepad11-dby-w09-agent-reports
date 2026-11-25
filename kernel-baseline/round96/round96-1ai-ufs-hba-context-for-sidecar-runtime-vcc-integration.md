# ROUND96 — 1号 AI review: thread HBA context through private UFS regulator helpers so sidecar state covers runtime PM

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, with a separate AGENT_TEST_TASK.md  
**Pinned baseline:** ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Related records:** ROUND84–ROUND95

## 1. Executive result

ROUND95 identified the existing `ufs_hba::android_oem_data1` slot as a candidate for an ABI-preserving VCC sidecar. This round confirms how that sidecar can be used by the entire private UFS regulator lifecycle, including runtime PM:

- Every actual call site of the private `ufshcd_toggle_vreg()` macro is inside `drivers/ufs/core/ufshcd.c` and has access to `struct ufs_hba *hba` either directly or through its parent helper.
- `ufshcd_enable_vreg()` and `ufshcd_disable_vreg()` are `static` functions in the same translation unit and are only called through the private toggle macro.
- The higher-level setup, low-power and high-power helpers already receive `hba`.

**Implementation candidate:** change the private toggle/enable/disable helper path to carry `struct ufs_hba *` rather than only `struct device *`, and let those private helpers retrieve the OEM sidecar from `hba->android_oem_data1`. This does not require changing the KMI-visible `ufs_hba_variant_ops`, `ufs_vreg`, `ufshcd_pltfrm_init()` or `ufshcd_populate_vreg()` interfaces.

This is a source-level integration map, not an approved patch. 2号 AI must still verify final config, OEM slot ownership, devres lifetime and Kleaf ABI result before adopting ROUND95's sidecar candidate.

## 2. Exact private helper call graph

Pinned source: [drivers/ufs/core/ufshcd.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c).

### 2.1 Existing private functions

- `ufshcd_enable_vreg(struct device *dev, struct ufs_vreg *vreg)` is static.
- `ufshcd_disable_vreg(struct device *dev, struct ufs_vreg *vreg)` is static.
- `ufshcd_toggle_vreg(_dev, _vreg, _on)` is a file-local macro that dispatches to those static helpers.
- `ufshcd_setup_vreg(struct ufs_hba *hba, bool on)` already has HBA context for VCC, VCCQ and VCCQ2.
- `ufshcd_setup_hba_vreg(struct ufs_hba *hba, bool on)` already has HBA context for VDD-HBA.
- `ufshcd_vreg_set_lpm(struct ufs_hba *hba)` and `ufshcd_vreg_set_hpm(struct ufs_hba *hba)` are runtime power-policy helpers and already have HBA context.

The enable/disable functions are not exported and have no external call sites in this pinned source file; they are reached via the local toggle macro. Their private signatures can therefore be refactored to accept HBA context without modifying an exported function signature.

### 2.2 All actual toggle call-site families

The fixed source contains these call-site families:

1. `ufshcd_setup_vreg()` — VCC, then VCCQ, then VCCQ2; rollback toggles the same three rails off in reverse sequence.
2. `ufshcd_setup_hba_vreg()` — VDD-HBA only; this supply has `skip_current=true` in the generic parser and should not be treated as the DBY VCC interval.
3. `ufshcd_vreg_set_lpm()` — runtime low-power transition can toggle VCC off by itself, or turn all device rails off for a full device/link power-off. It separately changes VCCQ/VCCQ2 DRMS modes through `ufshcd_config_vreg_lpm()`.
4. `ufshcd_vreg_set_hpm()` — runtime high-power transition can toggle VCC back on or turn all supplies on; it separately changes VCCQ/VCCQ2 DRMS modes through `ufshcd_config_vreg_hpm()`.

These helpers are reached from initialization, resume/recovery paths and normal runtime/system power management. If the sidecar is only consulted in the initial probe/setup path, later VCC off/on transitions will not update the consumer voltage range correctly.

## 3. Suggested private-helper refactor shape

One possible internal shape for 2号 AI to evaluate:

    static int ufshcd_enable_vreg(struct ufs_hba *hba,
                                  struct ufs_vreg *vreg);
    static int ufshcd_disable_vreg(struct ufs_hba *hba,
                                   struct ufs_vreg *vreg);

    #define ufshcd_toggle_vreg(_hba, _vreg, _on) ...

Then `ufshcd_setup_vreg()`, `ufshcd_setup_hba_vreg()`, `ufshcd_vreg_set_lpm()` and `ufshcd_vreg_set_hpm()` pass the existing HBA pointer. Private helpers can obtain `hba->dev` for diagnostics and sidecar state from the OEM slot. This is a conceptual interface suggestion; the exact helper factoring belongs to 2号 AI.

Keep the sidecar limited to data not already stored elsewhere:
- parsed VCC min/max request;
- voltage request state (ON interval vs OFF-relaxed interval vs pending cleanup);
- DRMS load state for affected UFS rails if required by ROUND90/93 error handling;
- pending voltage/load cleanup diagnostics.

Do not duplicate `vreg->enabled` blindly. ROUND90/93 show that the regulator consumer enable reference, stored load vote, voltage request and cleanup-pending state are separate facts.

## 4. Runtime transitions that must be preserved

| Path | Existing transition | Sidecar-aware requirement |
|---|---|---|
| Initial HBA setup | `ufshcd_setup_vreg(hba, true)` | Install VCC ON interval and required DRMS load before first VCC enable (ROUND88/89/91). |
| Runtime LPM while device sleeps | `ufshcd_vreg_set_lpm(hba)` may toggle VCC off | Relax VCC to `[0, max_uV]` and handle DRMS/enable ref according to ROUND89/90. |
| Runtime HPM / resume | `ufshcd_vreg_set_hpm(hba)` may toggle VCC on | Restore `[min_uV, max_uV]` before regulator enable; preserve the correct load vote. |
| Full device/link power-off | `ufshcd_setup_vreg(hba, false)` | Apply the same tracked off transition to VCC, VCCQ and VCCQ2; keep the L6 VDDP shared-consumer condition in mind. |
| Resume/recovery | calls setup/enable helpers again | Do not inherit stale state from failed enable or failed vote cleanup. |
| HBA removal | `ufshcd_hba_exit()` calls setup_vreg(false) before devres release | Sidecar must still be alive for final rail cleanup; ROUND95 devres order confirms it can be. |

## 5. KMI and source boundaries

This approach changes only private helpers/macros in `drivers/ufs/core/ufshcd.c` and their in-file call sites. It does not need to:
- append a callback field to `struct ufs_hba_variant_ops`;
- add voltage/state members to `struct ufs_vreg`;
- change the exported `ufshcd_pltfrm_init()` signature;
- change the exported `ufshcd_populate_vreg()` signature or its shared MediaTek behavior.

Any helper exported to other objects or any structure shared across KMI would need separate KMI analysis. Do not convert this private state path into a new exported API merely for convenience.

## 6. Required 2号 AI checks

1. Confirm the final config has `CONFIG_ANDROID_VENDOR_OEM_DATA=y` before referencing `hba->android_oem_data1`.
2. Search the complete integration worktree and OEM extensions for any existing use of this HBA OEM slot.
3. Keep the static helper refactor within `ufshcd.c` unless there is a compelling reason to introduce a new exported interface.
4. Cover initial probe, VCC-only LPM/HPM transitions, full power-off/on, suspend/resume, error recovery, probe failure and remove.
5. Preserve ROUND84/89/90/93/94 state and rollback requirements for voltage request, load vote, enable reference and pending cleanup.
6. Run the exact pinned Kleaf KMI ABI diff after implementation; unchanged type sizes alone are not a substitute for the ABI tool result.
7. Run real patch apply, build and schema checks only in the authorized disposable ACK workspace.

## 7. Ownership and boundaries

**This is a [1号 AI read-only source integration review] for 2号 AI.**
- 1号 AI: call-graph analysis and design feedback.
- 2号 AI: owns implementation and patch changes.
- Testing Agent: test executor only, after a separate AGENT_TEST_TASK.md.
- The user is not asked to run any commands.

No source, DTS, binding, patch, config, 2号 AI branch, protected branch or PR was modified. No patch application, compiler, dt-schema, KMI checker, regulator measurement or device operation was run.

**Final status:** the complete private UFS toggle call graph already carries HBA context at the higher-level call sites. Threading HBA into the private enable/disable helpers is a feasible way to make the ROUND95 sidecar available to initial setup, runtime PM, rollback and removal without growing the KMI-visible UFS structures. This remains a design candidate pending the ROUND95 ownership/config checks and later tests.