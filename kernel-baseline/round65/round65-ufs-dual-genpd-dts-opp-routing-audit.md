# ROUND65 — UFS dual-GenPD DTS activation and required-OPP routing audit

**Date:** 2026-11-25  
**Owner:** Primary AI, pinned-source review  
**Baseline:** ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Scope:** review-only source/patch/DTS design analysis; no code, DTS, config or protected-branch changes; no device.

## 1. Executive result

The ROUND18 Image includes the ROUND33 UFS driver patch, but the current main-branch board DTS draft still inherits only the single GCC UFS_PHY_GDSC domain from the base SM8250 DTSI. It does not yet apply the ROUND37 board-level two-domain delta.

This is not merely a cosmetic difference:

- ROUND33 explicitly preserves the generic one-domain path. Its special attachment and OPP routing code runs only when the SM8250 UFS Host has exactly two `power-domains` entries.
- Under the required contract, index 0 is RPMhPD MMCX and index 1 is GCC UFS_PHY_GDSC.
- The patch attaches both GenPDs with `PD_FLAG_DEV_LINK_ON`, then calls `devm_pm_opp_set_config()` with `required_dev = pd_list->pd_devs[0]` and `required_dev_index = 0` before `ufshcd_pltfrm_init()` parses the UFS OPP table.
- Without that mapping, ACK OPP core has a parsed `required-opps` table but its `required_devs[]` entries remain NULL. The core's `_set_required_opps()` skips NULL required devices. Consequently UFS OPP changes do not issue the corresponding MMCX performance-state request.
- UFS Host's pinned SoC OPP table has two available entries, both with one `required-opps` reference to the SM8250 RPMhPD table. The UFS core sets `use_pm_opp = true`, uses `dev_pm_opp_set_opp()` during clock scaling, and starts at the maximum OPP. This makes the missing mapping operationally relevant.

Therefore, before building the device DTB for the ROUND18 patched Image, integrate the ROUND37 DTS delta in the real board DTS source: add `<&rpmhpd RPMHPD_MMCX>` first and `<&gcc UFS_PHY_GDSC>` second. Keep the UFS PHY's own inherited GCC GDSC domain unchanged. This is a source/driver contract recommendation, not a claim that the hardware has been tested.

## 2. What the current board DTS supplies today

Main review draft:
`dts/dby-w09-ack18-board.dts.draft`, blob `c209d519614fb0ff89b042ce274191b20120a09a`.

The current &ufs_mem_hc override adds its rails and `status = "okay"`, but does not override `power-domains`. The pinned `arch/arm64/boot/dts/qcom/sm8250.dtsi` UFS Host therefore retains exactly one domain:
`power-domains = <&gcc UFS_PHY_GDSC>;`

The base SoC DTSI also defines:
- UFS Host compatible first entry `qcom,sm8250-ufshc`;
- two-entry UFS OPP table, each OPP containing a single `required-opps` reference to `rpmhpd_opp_low_svs` or `rpmhpd_opp_nom`;
- UFS PHY own `power-domains = <&gcc UFS_PHY_GDSC>;`.

The nine stock HOS4.3 DTBO entries do not add a UFS Host power-domain array (ROUND21). Their UFS host/PHY supply fragments are byte-identical, but they do not activate the ROUND33 MMCX mapping.

## 3. Exact driver behavior: ROUND33 dual-domain helper

Integrated patch from ROUND18's actual local apply series:
- ROUND33 UFS driver patch was applied to the Image build source copy.
- The second-AI branch's checkpatch-clean corresponding patch blob is `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`.
- The patch's contract is documented in `kernel-baseline/round37/dby-w09-ufs-dual-genpd-board-dts-delta.md` and `kernel-baseline/round45/ack-ufs-dual-genpd-all-opp-validation.md`.

The relevant helper `ufs_qcom_attach_sm8250_domains()`:

1. Returns unchanged for non-SM8250 UFS Host devices.
2. Counts `power-domains`.
3. If count is one (the current DTSI inheritance) or missing, returns 0 and leaves the generic one-domain path untouched.
4. If count is not exactly two, fails closed.
5. For count two, checks:
   - entry 0 is compatible `qcom,sm8250-rpmhpd`, with one cell equal to `RPMHPD_MMCX`;
   - entry 1 is compatible `qcom,gcc-sm8250`, with one cell equal to `UFS_PHY_GDSC`.
6. Validates every available UFS OPP entry: exactly one `required-opps`, target available, target's containing OPP table belongs to `qcom,sm8250-rpmhpd`, and it is the exact same OPP table phandle advertised by the RPMhPD provider.
7. Calls `devm_pm_domain_attach_list()` with `PD_FLAG_DEV_LINK_ON`.
8. Configures OPP `required_dev` slot 0 to the first attached domain, MMCX.
9. Completes this in `ufs_qcom_probe()` before generic `ufshcd_pltfrm_init()` parses the OPP table.

The driver patch does not implement MMCX-to-MX ARC parent propagation. That separate ROUND30 equivalence gate remains unresolved.

## 4. Exact ACK OPP-core behavior

### 4.1 Required-OPP table allocation

Pinned source: `drivers/opp/of.c`:
- `_opp_table_alloc_required_tables()` lines 140–197 counts the first available OPP entry's `required-opps` property, allocates both `required_opp_tables[]` and `required_devs[]` with `kcalloc()`, then discovers the target tables.
- `kcalloc()` zero-initializes the required-device pointer array; before the ROUND33 `dev_pm_opp_set_config()` mapping, each required-device slot remains NULL.

### 4.2 Required-OPP application

Pinned source: `drivers/opp/core.c`:
- `_set_required_opps()` lines 1196–1239 obtains `opp_table->required_devs` and only calls `_set_opp_level()` when the corresponding `devs[index]` is non-NULL.
- `dev_pm_opp_set_opp()` invokes this path during scaling (lines 1322 onward).
- `_opp_set_required_dev()` lines 2438–2495 validates the index and maps the supplied device into that required slot.
- The ROUND33 patch supplies exactly the missing mapping.

Without a `required_dev`, the UFS OPP table can still be parsed and its UFS clocks can still be scaled, but the `required-opps` target does not produce a request to the RPMhPD GenPD device through this OPP core path. Do not label this a proven UFS boot failure; it is a missing required performance-domain vote.

### 4.3 UFS OPP usage is active in the pinned core

Pinned source:
- `drivers/ufs/host/ufshcd-pltfrm.c:L414-L484`: if `operating-points-v2` exists, collects clock names, configures OPP clocks, adds the OPP table, parses min/max frequencies and sets `hba->use_pm_opp = true`.
- `drivers/ufs/core/ufshcd.c:L1138-L1187`: `ufshcd_opp_config_clks()` programs clocks from indexed OPP frequencies; `ufshcd_opp_set_rate()` finds an OPP and calls `dev_pm_opp_set_opp()`.
- `drivers/ufs/core/ufshcd.c:L1191-L1225`: `ufshcd_scale_clks()` uses the OPP path when `use_pm_opp` is true.
- `drivers/ufs/core/ufshcd.c:L9739-L9747`: initial clock setup sets the maximum OPP.
- `drivers/ufs/core/ufshcd.c:L1585-L1606`: devfreq asks OPP framework to choose the recommended OPP.

Therefore the required-device mapping is not unused scaffolding; it affects the runtime performance-state request associated with UFS clock rates.

## 5. ROUND37 board DTS delta matches the required contract

Main-branch report:
`kernel-baseline/round37/dby-w09-ufs-dual-genpd-board-dts-delta.md`.

Proposed exact Host property:
```dts
power-domains = <&rpmhpd RPMHPD_MMCX>,
                <&gcc UFS_PHY_GDSC>;
```

It also adds:
- `#include <dt-bindings/power/qcom,rpmhpd.h>`;
- `#include <dt-bindings/clock/qcom,gcc-sm8250.h>`.

The report records the fixed IDs:
- `RPMHPD_MMCX = 6`;
- `UFS_PHY_GDSC = 4`.

ROUND37 was applied successfully to an exact one-file fixture made from the then-protected board DTS blob, with `git apply --check`, `git apply`, and `git diff --check` PASS. It has not been integrated into the current main draft, is not in the protected branch, and has not been checked by a full source-tree dtc/schema/DTB build.

The exact ROUND37 delta must be reconciled with the current main draft blob before promotion. It is not permission to modify the protected branch.

## 6. Required integration order and validation

For the next device-tree build candidate:
1. Use the exact ACK common commit.
2. Confirm actual integrated UFS binding series accepts one/two SM8250 power-domains and retains one-domain limits for other Qualcomm UFS families.
3. Integrate the ROUND37 Host two-domain property and required binding headers into an actual ACK kernel DTS source path.
4. Keep the second domain order exactly MMCX index 0, GCC UFS_PHY_GDSC index 1.
5. Inspect the compiled DTB's final `ufs_mem_hc/power-domains` cells and provider compatibility.
6. Confirm UFS PHY remains independently attached to GCC UFS_PHY_GDSC.
7. Run dt_binding_check/dtbs_check/dtc and inspect all output diagnostics; do not accept Makefile exit 0 if diagnostics are printed but swallowed.
8. In the final kernel build, verify ROUND33 helper was applied to the same source commit and final config remains valid.

This is still separate from unresolved MMCX-to-MX parent semantics, PM8150 physical input-parent topology, final RAM/reserved-memory handoff, ABL entry/DTB selection, AVB packaging and actual device boot.

## 7. Status boundary

- Pinned ACK source and ROUND18 applied UFS patch contract review: PASS.
- Main board DTS draft currently contains required two-domain property: NO.
- ROUND37 exact single-file patch application: PASS on an isolated fixture only.
- Complete ACK DTB compile and schema validation for the DBY-W09 board DTS: NOT RUN.
- Kernel build with the completed board DTB integrated: NOT RUN.
- Runtime MMCX vote / UFS link / storage enumeration: NOT RUN.
- Device boot: NOT RUN.

No device was accessed. No branch, DTS, config, source code, binary or firmware input was modified during this review.
