# AI1 ROUND136 C 项源码复核补充

Date: 2026-11-26
Device: Huawei MatePad 11 (2021) DBY-W09 / KONA / SM8250 v2.1
Pinned ACK: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
Scope: read-only static source recheck; no source or patch modifications.

## 1. UFS required OPP requests

The pinned `arch/arm64/boot/dts/qcom/sm8250.dtsi` UFS OPP table defines:
- `opp-37500000` -> `rpmhpd_opp_low_svs` -> RPMh logical level 64.
- `opp-300000000` -> `rpmhpd_opp_nom` -> RPMh logical level 256.

The provider table defines `opp3 = LOW_SVS` and `opp6 = NOM`. These are logical RPMh level requests, not measured rail voltages and not proof of the target Command DB's hardware corner mapping.

Source:
- [SM8250 UFS OPP table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi#L2507-L2577)
- [SM8250 RPMHPD provider OPP table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/boot/dts/qcom/sm8250.dtsi#L6193-L6224)
- [RPMh logical level constants](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/dt-bindings/power/qcom%2Crpmhpd.h#L28-L55)

## 2. Runtime Command DB mapping is a separate requirement

In `drivers/pmdomain/qcom/rpmhpd.c`:
- `rpmhpd_update_level_mapping()` calls `cmd_db_read_aux_data(rpmhpd->res_name, ...)`.
- AUX entries are consumed as 16-bit values; the implementation allows at most 16 ARC levels and trims zero-padding.
- `rpmhpd_set_performance_state()` compares the requested logical level against the runtime-loaded `pd->level[]` mapping to select the ARC corner.
- `rpmhpd_probe()` resolves the resource address, verifies the CMD DB slave ID is `CMD_DB_HW_ARC`, then loads the AUX mapping.

Therefore static DTS values 64/256 do not disclose the DBY-W09 HOS4.3 Command DB AUX arrays or establish the physical/electrical rail corner. The existing HOS4.3 AUX/runtime-vote evidence gap remains real.

Source:
- [RPMHPD runtime AUX mapping and probe](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L927-L1067)

## 3. SM8250 MMCX does not have an MX parent in this ACK

The pinned ACK declares:
- `mmcx`: peer `mmcx_ao`, resource `mmcx.lvl`, no `.parent`.
- `mmcx_ao`: peer `mmcx`, resource `mmcx.lvl`, no `.parent`.
- `cx_w_mx_parent` and `cx_ao_w_mx_parent` do have MX/MX_AO parents.
- `sm8250_rpmhpds[]` maps RPMHPD_MMCX / RPMHPD_MMCX_AO to plain `mmcx` / `mmcx_ao`, while CX is mapped to the parented descriptor.
- The probe loop calls `pm_genpd_add_subdomain()` only when a descriptor's `.parent` is non-NULL.

Thus the current SM8250 MMCX GenPD does not automatically propagate its performance request to MX. This is a precise source-level behavior statement; it is not by itself proof that HOS4.3 UFS requires or does not require such a parent vote.

Source:
- [RPMHPD descriptors and SM8250 mapping](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L75-L130)
- [SM8250 descriptor table and parent registration](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L440-L480)
- [GenPD parent registration loop](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c#L1055-L1067)

## 4. Decision

- No patch change is justified by this static recheck.
- Do not add an MX parent to the shared SM8250 MMCX descriptor based only on HOS ARC property names.
- Do not implement a new full ARC provider before proving the UFS-specific required corner and parent-vote behavior.
- Keep C marked `BLOCKED` for first safe UFS boot until target-local HOS4.3 Command DB AUX mapping and relevant active/sleep votes, or equivalent authoritative evidence, establish the required behavior.

This supplement narrows the static source boundary only. It does not authorize device connection, boot packaging, AVB changes, fastboot/recovery, partition writes, or boot testing.
