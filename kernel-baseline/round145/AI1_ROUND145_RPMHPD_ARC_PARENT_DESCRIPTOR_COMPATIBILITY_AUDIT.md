# AI1 ROUND145 — SM8250 RPMhPD descriptor identity and ARC parent-chain feasibility audit

- Reviewer / author: **1号 AI (ChatGPT)**
- Date: 2026-11-26
- Target: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel: Android 17 ACK `android17-6.18.33_r00`
- Pinned ACK commit: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Candidate content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Related accepted evidence: ROUND139 HOS4.3 static inventory; ROUND144 UFS OPP/probe-order review
- Scope: source-only feasibility analysis. No edits, build, device access, or runtime assumptions.

## 1. Disposition

**CONFIRMED — a one-line substitution of `RPMHPD_MMCX = &mmcx_w_cx_parent` in the SM8250 descriptor array is not a valid fix.** The existing `mmcx_w_cx_parent` object points specifically to the separate plain `cx.pd` object, but the SM8250 array registers `cx_w_mx_parent` at the CX index. Those are different static `struct rpmhpd` objects, despite both GenPD names being `"cx"`.

**CONFIRMED — the existing SM8250 descriptor graph is CX → MX, but MMCX has no parent.** The HOS4.3 UFS-related ARC child-supply edges show a special MMCX → MX-MMCX-supply → CX-MMCX-supply path. The current ACK descriptor graph does not establish that exact special path.

**POSSIBLE IN PRINCIPLE, NOT PROVEN SAFE — the RPMhPD/GenPD architecture can express parent links and common performance-state propagation.** The kernel source supports adding a subdomain parent pointer, and the SM8250 provider uses a shared OPP table for all RPMhPD indices. That does not establish that the vendor-specific ARC child regulator relationships are equivalent to a simple generic-domain parent chain.

**No DTS/kernel patch is proposed.** Exact ARC resource semantics and hardware ownership remain unproven. Keep the RPMh/MMCX parent-chain gate open.

## 2. Exact SM8250 descriptor-object pairing

Pinned ACK definitions in `drivers/pmdomain/qcom/rpmhpd.c`:

| Descriptor object | `.res_name` | `.parent` |
|---|---|---|
| `mmcx` | `mmcx.lvl` | none |
| `mmcx_w_cx_parent` | `mmcx.lvl` | `&cx.pd` |
| `cx` | `cx.lvl` | none |
| `cx_w_mx_parent` | `cx.lvl` | `&mx.pd` |
| `mx` | `mx.lvl` | none |

SM8250 one-cell array:
- `RPMHPD_MMCX = &mmcx`
- `RPMHPD_CX = &cx_w_mx_parent`
- `RPMHPD_MX = &mx`

Thus, the selected runtime object graph is:
- MMCX: standalone `mmcx.lvl`;
- CX: `cx_w_mx_parent` → MX;
- MX: standalone `mx.lvl`.

The existing alternate descriptor `mmcx_w_cx_parent` does **not** point to `cx_w_mx_parent`. Its parent is the plain `cx.pd` object. That plain `cx` object is not selected in the SM8250 one-cell array; the array selects `cx_w_mx_parent` instead.

The RPMhPD probe initializes only objects present in the selected SoC array, stores those objects into the one-cell provider, and afterward tries to add subdomain links for non-NULL `.parent` fields. A descriptor swap which leaves its parent target out of the selected array would therefore point at a different, unselected GenPD object. It must not be treated as equivalent to wiring MMCX into the currently registered CX domain. The probe's parent-link call also does not check the return value of `pm_genpd_add_subdomain()`, so a proposed object-identity mismatch cannot be waved away as harmless.

Relevant immutable source:
- [Descriptor definitions — plain CX/MMCX and parent variants](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L70-L160)
- [SM8250 and SM8350 arrays](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L465-L505)
- [SM8450 array, which pairs MMCX-with-CX-parent with plain CX](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L500-L530)
- [RPMhPD provider initialization and subdomain registration](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L1000-L1060)

### 2.1 Cross-SoC comparison confirms this is an intentional pairing

SM8450 and SM8550 select:
- `RPMHPD_MMCX = &mmcx_w_cx_parent`
- `RPMHPD_CX = &cx`

That pairing registers the exact `cx.pd` object targeted by `mmcx_w_cx_parent.parent`.

SM8250 instead selects:
- `RPMHPD_MMCX = &mmcx`
- `RPMHPD_CX = &cx_w_mx_parent`

This pairs the selected CX object with an MX parent. The SM8250 array's current choices are explicit, not an accidental omission that can safely be repaired by copying the SM8450 MMCX line alone.

## 3. GenPD performance-state propagation and OPP translation

The source supports the following chain when a valid parent relationship is registered:

1. `rpmhpd_probe()` calls `pm_genpd_init()` for each RPMhPD object selected by that SoC's array.
2. For each selected object with non-NULL `.parent`, it calls `pm_genpd_add_subdomain(parent, child)`.
3. Generic GenPD `_genpd_set_performance_state()` walks `child_links` when the child performance state scales up, converts the state for the parent, and sets the parent's performance state before applying the child request. Scaling down is propagated after the child request.
4. `genpd_xlate_performance_state()` uses `dev_pm_opp_xlate_performance_state(child->opp_table, parent->opp_table, state)` when the parent implements `set_performance_state`.

For SM8250, `of_genpd_add_provider_onecell()` initializes a performance OPP table for each domain index using `dev_pm_opp_of_add_table_indexed()`. The SM8250 provider node has exactly one `operating-points-v2 = <&rpmhpd_opp_table>` phandle. Pinned OPP parser logic explicitly reuses the same single OPP table for every indexed request when only one phandle exists. The table contains `opp-level` entries (RETENTION through TURBO_L1) with no parent `required-opps` mapping. Consequently `dev_pm_opp_xlate_performance_state()` takes its documented one-to-one path and returns the same logical performance state when a valid parent link is present.

Each RPMhPD object then resolves its own `.res_name` to a CMD-DB address and its own auxiliary level table:
- `cmd_db_read_addr(res_name)`
- `cmd_db_read_slave_id(res_name)`, required to be `CMD_DB_HW_ARC`
- `cmd_db_read_aux_data(res_name)`, used to build the hardware-level mapping

This means the driver does not infer hardware values from the names `LOW_SVS` / `NOM` alone; it translates the requested OPP level through the CMD-DB auxiliary mapping for each resource.

Immutable source:
- [SM8250 one shared RPMhPD OPP table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi#L6193-L6240)
- [one-phandle indexed OPP table reuse](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/opp/of.c#L1060-L1090)
- [GenPD provider loads indexed OPP tables](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/core.c#L2780-L2805)
- [GenPD parent-state translation and propagation](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/core.c#L395-L510)
- [RPMhPD CMD-DB address/aux-data setup and parent-link registration](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L960-L1060)

## 4. HOS4.3 ARC graph — what is and is not proven

The accepted ROUND139 report shows these provider-child regulator relationships:

| HOS4.3 ARC relation | Meaning from ROUND139 |
|---|---|
| MMCX ALL → MX MMCX-supply ALL | UFS-related MMCX ARC rail has a parent-supply edge to the MX-group MMCX-supply regulator |
| MX MMCX-supply → CX MMCX-supply | MX-group MMCX-supply regulator itself has a parent-supply edge to the CX-group MMCX-supply regulator |
| CX ALL → MX ALL | separate ordinary CX-to-MX rail relationship |
| MMCX AO → MX AO | MMCX AO relationship |
| CX AO → MX AO | separate ordinary CX AO relationship |

ROUND139 also establishes that:
- the HOS4.3 ARC groups use `compatible = "qcom,rpmh-arc-regulator"`;
- `mmcxlvl`, `mxlvl`, and `cxlvl` have `qcom,resource-name` values `mmcx.lvl`, `mx.lvl`, and `cx.lvl`;
- the vendor FDT's UFS node itself has no `power-domains` or OPP link;
- the six UFS physical PMIC input parents remain UNKNOWN.

The upstream ACK tree uses `qcom,sm8250-rpmhpd` / GenPD for ARC corners and does not bind the HOS `qcom,rpmh-arc-regulator` compatible. The resource names overlap at the coarse group level, but the HOS regulator-child graph has named MMCX-supply variants under the MX and CX groups. The accepted report does not prove that these child regulator instances map to a simple generic GenPD topology with identical timing/enable semantics.

Evidence:
- [ROUND139 ARC parent-edge inventory](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L137-L167)
- [ROUND139 UFS ARC / RPMhPD and ACK comparison](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L169-L213)

## 5. Why the apparent fixes are not ready

### A. Replace MMCX with the existing `mmcx_w_cx_parent`

Rejected as a one-line change. Its parent pointer targets `cx.pd`, but SM8250 selects `cx_w_mx_parent.pd`. A correct object graph would have to change the selected CX object as well, which would remove the currently selected CX→MX relationship unless another compatible descriptor were added.

### B. Copy the SM8450 pair into SM8250

Rejected without hardware evidence. It would select plain CX and MMCX-with-CX-parent, removing SM8250's CX→MX parent link. It may be correct for SM8450, but the HOS4.3 UFS ARC inventory is not proof that SM8250 should copy SM8450's topology.

### C. Add a custom MMCX → MX → CX GenPD chain

Architecturally expressible in principle using additional descriptor objects and parent links, but not yet proven equivalent:
- the HOS UFS-specific parent path uses MMCX-supply child regulators under the MX and CX ARC groups;
- the generic GenPD implementation would vote the coarse RPMhPD resources `mmcx.lvl`, `mx.lvl`, and `cx.lvl`;
- no authoritative mapping yet proves that coarse domain votes are equivalent to the specific vendor child-rail supply behavior, including active/awake votes and AO handling.

A custom descriptor design should not be created until the resource/consumer behavior is established from a trusted vendor driver/source or an equivalent hardware-specific record.

## 6. Gate update

| Item | Current result |
|---|---|
| OPP slot 0 → attached MMCX virtual GenPD device | **PASS — ROUND144** |
| GenPD framework can propagate state across registered parents | **PASS — pinned source** |
| SM8250 selected MMCX descriptor parent | **NONE — confirmed** |
| Existing `mmcx_w_cx_parent` safe one-line replacement | **REJECTED — parent object identity mismatch** |
| HOS4.3 special MMCX-supply chain maps to generic SM8250 GenPD | **UNKNOWN / BLOCKED** |
| Safe custom descriptor hierarchy | **NOT ESTABLISHED** |
| Runtime RPMh CMD-DB votes / physical PMIC behavior | **UNKNOWN / BLOCKED** |

## 7. Next evidence required

1. Independently review the descriptor-object pairing and the potential one-line substitution trap.
2. Identify the actual semantics of the HOS `qcom,rpmh-arc-regulator` child regulators: which exact resource gets requested, how `parent-supply` is enabled, and how AO/active-only corners are handled.
3. Establish whether one generic vote to `mmcx.lvl` plus generic `mx.lvl`/`cx.lvl` votes can reproduce the vendor topology, or whether child regulator-level distinctions are required.
4. Do not alter the SM8250 RPMhPD array until these are answered.

No code or DTS was changed. No build, download, or device operation was performed.
