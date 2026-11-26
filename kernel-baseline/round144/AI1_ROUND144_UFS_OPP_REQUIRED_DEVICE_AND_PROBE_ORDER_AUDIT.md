# AI1 ROUND144 — UFS OPP required-device mapping, probe order, and RPMh parent-propagation audit

- Reviewer / author: **1号 AI (ChatGPT)**
- Date: 2026-11-26
- Target: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel: Android 17 ACK `android17-6.18.33_r00`
- Pinned ACK commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- Candidate content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Reviewed candidate patch artifacts:
  - ROUND33 / dual-GenPD and UFS OPP mapping: `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`
  - ROUND52 patch 06 / VDDP REF_CLK: `7e5df841b756dfef803edec486d9a5e3e753f47b`
- Scope: static source semantics and accepted report reconciliation only. No source modifications, build, network dependency fetch, or device access.

## 1. Disposition

**PASS — the candidate's single required-OPP slot is correctly bound to the first attached power-domain device (MMCX), and the attachment/configuration order is compatible with the pinned ACK OPP core.**

**NOT CLOSED — this does not prove that an MMCX performance vote propagates through the HOS4.3 MMCX → MX-MMCX-supply → CX-MMCX-supply ARC hierarchy.** The selected SM8250 RPMhPD descriptor for MMCX has no parent. The candidate therefore cannot claim a complete parent-corner vote chain based only on the dual-domain attachment and OPP mapping.

The source audit finds no basis for changing `required_dev_index=0` to 1. That would bind the single UFS `required-opps` slot to the second attached domain (GCC UFS_PHY_GDSC), not repair MMCX parent propagation.

First boot remains **BLOCKED / NOT AUTHORIZED** because this review does not close physical PMIC inputs, the ARC topology equivalence, runtime RPMh/CMD-DB votes, final post-ABL memory/FDT, AVB and recovery.

## 2. Pinned-source basis

All kernel implementation claims below refer only to the exact pinned ACK commit. The source blob identities read during this audit are:

| File | Blob SHA |
|---|---|
| `drivers/base/power/common.c` | `6ecf9ce4a4e62bbc4861d5341971eec518b5c58b` |
| `drivers/opp/core.c` | `157c84b689feba9ae2c446083e42de63e94a38a6` |
| `drivers/opp/of.c` | `505d79821584e28f454dae673cf85078762b2ec7` |
| `include/linux/pm_opp.h` | `789406d95e69f8b0545f1ed329fdc6629e864570` |
| `drivers/pmdomain/qcom/rpmhpd.c` | `4c3cbf3abc7504cce3b8211c339b7ada03d65e38` |
| `drivers/pmdomain/core.c` | `8adc78d62d05f1f7432a154c7d71ce0ade3f406a` |
| `drivers/ufs/host/ufs-qcom.c` | `a80c6998406dbc88c25dbd9977699ba481207efe` |
| `drivers/ufs/host/ufshcd-pltfrm.c` | `5ac7afe759346debfc2910fb219d8e491ba08b64` |
| `drivers/ufs/core/ufshcd.c` | `2cf7aa8e0a9472f9024d4251ac2f9d7da830e219` |
| `drivers/phy/phy-core.c` | `04a5a34e7a950ae94fae915673c25d476fc071c1` |
| `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c` | `8af777f7ddd0385a6bb9d9b9563f0e6329699cd3` |
| `drivers/interconnect/core.c` | `6cc979b26151e76fbc3ad480a871df89161b8778` |

Immutable source links:
- [GenPD list attachment](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/base/power/common.c#L193-L275)
- [OPP required-device mapping and index validation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/opp/core.c#L1198-L1230)
- [OPP required-device setup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/opp/core.c#L2443-L2499)
- [OPP config must precede OPP initialization](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/opp/core.c#L2542-L2643)
- [RPMhPD descriptors and SM8250 mapping](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L125-L153)
- [SM8250 RPMhPD table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L465-L482)
- [RPMhPD performance-state aggregation and parent registration](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L844-L960)
- [Generic GenPD parent-state propagation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/core.c#L412-L510)
- [UFS platform probe order](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufshcd-pltfrm.c#L644-L696)
- [UFS rail initialization sequence](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L9777-L9826)
- [Qualcomm UFS variant initialization and ICC setup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufs-qcom.c#L1460-L1598)
- [Qualcomm UFS PHY power-up sequence](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufs-qcom.c#L487-L545)
- [QMP UFS PHY regulator enable path](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/phy/qualcomm/phy-qcom-qmp-ufs.c#L1832-L1854)

## 3. ROUND33 OPP slot mapping — confirmed correct

The candidate ROUND33 patch performs the following, before calling `ufshcd_pltfrm_init()`:

1. Verifies that the SM8250 UFS node declares exactly two power domains.
2. Verifies domain index 0 is `qcom,sm8250-rpmhpd` / `RPMHPD_MMCX`.
3. Verifies domain index 1 is `qcom,gcc-sm8250` / `UFS_PHY_GDSC`.
4. Validates that each available UFS OPP contains exactly one `required-opps` entry, and that the referenced OPP belongs to the exact RPMhPD provider table.
5. Calls `devm_pm_domain_attach_list()` with `PD_FLAG_DEV_LINK_ON`.
6. Requires exactly two attached domains, then sets:
   - `required_dev = pd_list->pd_devs[0]`
   - `required_dev_index = 0`
7. Calls `devm_pm_opp_set_config()` before the platform probe parses/initializes the UFS OPP table.

Pinned ACK semantics validate that arrangement:

- `dev_pm_domain_attach_list()` walks the `power-domains` phandles by ID in order and stores each attached provider device in `pd_devs[i]`. With `PD_FLAG_DEV_LINK_ON`, the supplier device link includes `DL_FLAG_RPM_ACTIVE`.
- `struct dev_pm_opp_config.required_dev_index` identifies the index in the consumer OPP table's `required-opps` vector. It is not the power-domain index.
- `_opp_set_required_dev()` validates the index against `required_opp_count`, resolves the required OPP table, and records the supplied device at that exact index.
- `_set_required_opps()` later uses `required_devs[index]` alongside `opp->required_opps[index]` when the UFS OPP changes.
- `dev_pm_opp_set_config()` explicitly expects to be called before OPPs are initialized. The candidate patch places it before `ufshcd_pltfrm_init()`, whose code later calls `ufshcd_parse_operating_points()`.

Because the candidate OPP has one `required-opps` slot, index 0 is the only valid slot and maps that slot to the first attached domain, MMCX. Index 1 would be invalid for a one-entry required-OPP array or would fail the patch's intended table/index contract; it is not a solution for parent-corner propagation.

**Conclusion:** no correction to ROUND33's `required_dev_index=0` is justified by the fixed ACK OPP API. This validates the software mapping only; it does not prove actual CMD-DB votes or board power equivalence.

## 4. Critical distinction — attached MMCX is not automatically propagated to MX/CX

The fixed ACK source has multiple RPMhPD descriptor objects:

- Plain `mmcx`: peer `mmcx_ao`, resource name `mmcx.lvl`, **no `.parent`**.
- `mmcx_w_cx_parent`: resource name `mmcx.lvl`, with `.parent = &cx.pd`.
- `cx_w_mx_parent`: resource name `cx.lvl`, with `.parent = &mx.pd`.

However, the SM8250 descriptor table explicitly selects:
- `RPMHPD_MMCX = &mmcx` (plain, no parent);
- `RPMHPD_CX = &cx_w_mx_parent`.

The existence of `mmcx_w_cx_parent` elsewhere in the file does not make it active for SM8250.

The RPMhPD probe only calls `pm_genpd_add_subdomain(parent, child)` for descriptor objects whose `.parent` is non-NULL. Generic GenPD performance-state propagation then traverses the registered child links, translates the requested child state to the parent table, and applies the parent state. With the currently selected plain SM8250 MMCX descriptor, this parent link is absent, so an MMCX state request cannot travel through that descriptor to CX via GenPD's parent-state mechanism.

### 4.1 HOS4.3 comparison — different ARC resources, not physical input rails

ROUND139's accepted HOS4.3 static report establishes five ARC provider-child links, including a vendor-specific MMCX-related sequence:
- MMCX ALL → MX MMCX-supply ALL;
- MX MMCX-supply → CX MMCX-supply;
- matching MMCX AO / MX AO relation.

The report also distinguishes these ARC corner-resource edges from the UFS's physical PMIC regulator supply providers. They are not `vin-supply` edges, and they do not disclose the physical input parent of L5/L6/L9/L17/S4/S8.

This matters because a normal direct GenPD parent link `MMCX → CX` is not automatically equivalent to the vendor's two-stage resource-name chain `MMCX → MX MMCX-supply → CX MMCX-supply`. Similar labels or corner values are not proof that the resources and mappings are identical.

### 4.2 Why no patch is proposed here

Do **not**:
- change required-dev index 0 to 1;
- add `mmcx_w_cx_parent` to the SM8250 table merely because it exists;
- infer that the vendor MMCX ARC resource maps to a plain ACK `mmcx.lvl` state solely by matching names or numeric levels;
- fabricate a CMD-DB resource or parent rail;
- patch ARC parent propagation without a pinned mapping from the HOS4.3 resource graph to the ACK provider implementation.

A separate evidence-backed design is required if the HOS ARC chain must be represented. That design must show the exact resource names, provider ownership, CMD-DB auxiliary tables and the correct parent relationships. ROUND139 already says the numerical corner labels alone are not runtime equivalence.

## 5. UFS regulator and PHY startup order

Pinned ACK `ufshcd_hba_init()` separates controller power from UFS device rails and performs this order:

1. Parse/acquire and enable `vdd-hba` (when declared).
2. Initialize and enable controller clocks.
3. Parse/acquire and enable generic UFS rails `vcc`, `vccq`, `vccq2`.
4. Call Qualcomm variant initialization `ufs_qcom_init()`.

In the candidate, ROUND52 patch 06 adds the separate `qcom,vddp-ref-clk` consumer in `ufs_qcom_init()`. It:
- applies only to the intended SM8250 UFS compatible and only when the property is present;
- requires a non-zero `qcom,vddp-ref-clk-max-microamp`;
- obtains the managed regulator handle;
- sets the configured load;
- enables that regulator;
- registers a cleanup action to disable the rail and clear the load during unbind.

The accepted HOS4.3 overlay maps both host `vccq` and `qcom,vddp-ref-clk` to PM8150 L6. The patch therefore intentionally obtains a second consumer handle for the same regulator. This is consistent with a separate REF_CLK load/enable request, but the actual physical L6 input and effective voltage remain unknown. It is also important that the patch does **not** consume `qcom,vccq-parent-supply` → PM8150L S8; that property remains inert candidate metadata without a driver consumer.

The QMP UFS PHY's bulk regulator table consumes `vdda-phy` and `vdda-pll`, which the accepted HOS overlay maps to L5 and L9. Its power-on handler enables the bulk regulators before enabling PHY clocks. This is an actual driver consumer relationship, not proof of physical rail input.

The Qualcomm HCE PRE_CHANGE path resets the host/PHY, calls `phy_init()`, sets PHY mode, calls `phy_power_on()`, then calibrates the PHY. That path propagates errors. The generic PHY API documents `phy_init()` must precede `phy_power_on()`.

One existing sequencing caveat is retained, not patched here: `ufs_qcom_init()` makes an early `ufs_qcom_setup_clocks(..., POST_CHANGE)` call whose return value is not checked; that callback calls `phy_power_on()` before the later HCE PRE_CHANGE path performs the full reset/init/mode/power-on/calibration sequence. The later HCE path does propagate its failures. This is worth retaining in a future runtime/error-path audit, but the source review alone does not prove that it breaks the later startup path or justify a behavioral change.

## 6. ICC (interconnect) dependency

The Qualcomm UFS variant obtains two named paths:
- `ufs-ddr`
- `cpu-ufs`

It requests maximum bandwidth on those paths during variant initialization, before UFS controller/device initialization. The generic interconnect core aggregates path requests and applies provider constraints; Qualcomm RPMh interconnect providers commit their BCM votes through the RPMh voter.

ROUND140's candidate DTB structural review found two ICC paths. That proves the DTB contains the declarations, not that every provider, BCM, CMD-DB address and runtime vote is available on the target device. This remains a probe/runtime dependency to verify from the final FDT and real probe logs.

## 7. Updated gate matrix

| Item | Disposition |
|---|---|
| ROUND33 OPP single-slot mapping to attached MMCX | **PASS — fixed ACK API semantics match** |
| OPP config timing before OPP parsing | **PASS — source order matches** |
| Both MMCX and UFS_PHY_GDSC attachment | **PASS — static patch semantics** |
| Supplier device links with runtime-active flag | **PASS — static GenPD attach semantics** |
| MMCX → CX/MX parent propagation in selected SM8250 table | **BLOCKED — selected MMCX descriptor has no parent** |
| HOS4.3 ARC MMCX → MX-MMCX → CX-MMCX equivalence | **BLOCKED — no proven resource/table mapping to ACK** |
| VCC/VCCQ/VCCQ2 generic rail consumer sequence | **PASS — source semantics; board inputs unknown** |
| QMP L5/L9 supply consumer and bulk enable | **PASS — source semantics; board inputs unknown** |
| VDDP REF_CLK L6 consumer (candidate patch 06) | **CONDITIONAL — candidate patch confirmed; physical/runtime rail unknown** |
| S8 qcom,vccq-parent consumer | **BLOCKED — no candidate consumer identified** |
| ICC provider and runtime BCM votes | **BLOCKED — DT declarations only; runtime unknown** |
| Physical PMIC input parents | **BLOCKED** |
| First device boot | **NOT AUTHORIZED** |

## 8. Recommended next work

1. Keep ROUND33 `required_dev_index=0`; do not change it without contradictory source evidence.
2. Have the next source investigation focus on the HOS4.3 ARC resource chain and the actual ACK RPMhPD/CMD-DB table model, not another generic OPP review.
3. Resolve the physical rail input question only through authoritative board-level evidence or explicitly authorized read-only device evidence. Do not guess fixed inputs.
4. Verify ICC provider availability, RPMh voter/BCM and CMD-DB runtime outcomes only after a safe evidence-capture plan exists.
5. Keep the final ABL FDT/RAM, reservations, selected DTBO, boot-v2/ramdisk, AVB and tested recovery gates open.

No code or DTS was changed in this round. No build or device action was performed.
