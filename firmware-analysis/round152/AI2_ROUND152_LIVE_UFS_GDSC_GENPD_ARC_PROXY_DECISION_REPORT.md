# AI2 ROUND152 — Live UFS GDSC / devfreq / GenPD / ARC / proxy architecture decision

- Reviewer: **AI2 independent collaborator**
- Target: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250
- Stock runtime: HOS 4.3.0.196(C00E100), Android 12 / API 31, kernel 4.19.157-perf+
- Fixed ACK: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` (`android17-6.18.33_r00`)
- Candidate content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Inputs: ROUND151 WorkBuddy root read-only report; AI1 ROUND151 review; AI2 ROUND150 and ROUND148; AI1 ROUND146; ROUND139; AI1 ROUND144 and ROUND145; fixed ACK source
- Scope: public GitHub reports and immutable fixed-ACK source only
- Disposition: **KEEP CURRENT CANDIDATE UNCHANGED AND FROZEN; ARCHITECTURE NOT YET ACCEPTED AS HOS-EQUIVALENT**
- First candidate boot: **BLOCKED / NOT AUTHORIZED**
- New compile: **NOT JUSTIFIED**

---

## 0. Executive decision

ROUND151 establishes a materially different stock UFS power contract from the candidate:

- HOS declares `vdd-hba-supply` to `ufs_phy_gdsc`, but its live regulator handle is 0 mV / 0 mV, use-count 0, and the provider reports disabled while UFS is active at HS-G1 ×2.
- HOS UFS host and PHY have no `power-domains` or OPP table. HOS uses `qcom,msm-bus` legacy vectors and a live UFS devfreq device.
- The candidate omits `vdd-hba-supply`; its fixed ACK UFS regulator code consequently leaves the HBA regulator pointer NULL and performs no HBA regulator vote. It instead attaches UFS host/PHY to the GCC UFS PHY GDSC through GenPD, and uses OPP/required-opps to request an MMCX RPMhPD performance state.
- Candidate host/PHY GDSC attachments resolve to the same GenPD object, not two separate GDSC providers. They are separate domain clients, and the generic PM-domain core will not power the domain off while an attached client remains runtime-active. This shared-domain property does not, by itself, prove the candidate's runtime sequencing equivalent to HOS.
- The candidate OPP/GenPD path is a plausible upstream-native replacement for a legacy vendor bus/performance path, but it is not a direct equivalent of HOS's declared or observed UFS behavior. In particular, HOS does not declare UFS as an MMCX ARC/GenPD consumer.
- HOS `mmcxlvl` and fixed-ACK `RPMHPD_MMCX` both resolve `mmcx.lvl`. The RPMh cache is keyed by resource address. Two independent ARC and GenPD aggregators would not form a cross-driver max-vote arbiter. This conflict is conditional because the published candidate DTB inventory reports zero ARC providers.
- Proxy declarations are not proof of proxy consumer registration or release timing. The public ROUND151 report does not publish raw per-proxy runtime handle evidence.

**Decision for this round:** do not edit the candidate, add ARC nodes, remove/alter GenPD nodes, or change the UFS OPP mapping. Keep the current candidate tree unchanged as a frozen comparison baseline. This is not acceptance of the current architecture as HOS-equivalent and is not authorization to boot it.

**Longer-term direction:** if full HOS ARC behavior is required, use one owner/arbitrator for `mmcx.lvl` and preserve ARC child-regulator semantics only after exact HOS driver/CMD-DB evidence is available. Do not instantiate an independent ARC `mmcxlvl` writer alongside RPMHPD MMCX. If a deliberately narrower upstream-native replacement is chosen instead, document that the stock ARC graph and UFS vote behavior are not being reproduced.

---

## 1. Evidence grading

- **PUBLISHED OBSERVATION** — stated in an accessible project report; raw local capture may not be public.
- **PINNED SOURCE FACT** — directly shown by fixed ACK source at the immutable commit above.
- **INFERENCE** — follows from combining report observations and source facts; not a direct device measurement.
- **UNKNOWN / NOT PUBLISHED** — the available public evidence does not establish the proposition.

No content below treats regulator-framework voltage/current values as physical measurements.

---

## 2. HOS UFS `vdd-hba` versus candidate GenPD

### 2.1 Stock HOS facts

**PUBLISHED OBSERVATION — ROUND151**

The live merged HOS FDT has:

- `/soc/ufshc@1d84000`, `status = "ok"`, `compatible = "qcom,ufshc"`;
- `/soc/ufsphy_mem@1d87000`, `status = "ok"`, `compatible = "qcom,ufs-phy-qmp-v4"`;
- host `vdd-hba-supply` resolving to `/soc/qcom,gdsc@177004`, regulator name `ufs_phy_gdsc`;
- empty marker properties `vcc-low-voltage-sup` and `vdd-hba-fixed-regulator`;
- no `power-domains` on either UFS host or PHY;
- no UFS `operating-points-v2` or `required-opps`;
- active host bound to `ufshcd-qcom`, link snapshot HS-G1, two lanes, FAST mode;
- GDSC regulator provider `regulator.55`, state `disabled`, `num_users=0`; `regulator_summary` shows the sole UFS child handle at 0 mV / 0 mV and use-count 0.

ROUND151 also reports zero retained boot-time UFS/RPMh/regulator dmesg lines. Therefore the explanation cannot be recovered from that ring-buffer snapshot.

**Important boundary:** this is a regulator-framework/software state observation. It does not prove that the physical GDSC logic gate is off, that the PHY has no power, or that the provider is harmless. The UFS link is demonstrably active at the capture time.

Sources:
- [ROUND151 live UFS FDT and runtime state, §4.1–4.5](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md#L240-L334)
- [AI1 ROUND151 reconciliation, §3–4](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round151/AI1_ROUND151_INDEPENDENT_REVIEW_AND_ROUND152_PLAN.md#L81-L133)
- [ROUND139 stock HOS UFS declaration and no-OPP/no-GenPD census](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L169-L188)

### 2.2 Fixed ACK UFS HBA regulator call sequence

**PINNED SOURCE FACT**

1. `ufshcd_populate_vreg(dev, "vdd-hba", ..., true)` checks whether the consumer node has `vdd-hba-supply`.
   - If the phandle is absent, it logs that the regulator is assumed enabled and returns with `*out_vreg = NULL`.
   - If the phandle exists, it allocates a `struct ufs_vreg`, stores the name and leaves `max_uA=0` because `skip_current=true`.
   - Source: [`ufshcd-pltfrm.c` L121-L160](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufshcd-pltfrm.c#L121-L160).

2. `ufshcd_init_hba_vreg()` calls `ufshcd_get_vreg()`:
   - if the pointer is NULL, `ufshcd_get_vreg()` returns 0 without calling `devm_regulator_get()`;
   - if populated, it calls `devm_regulator_get(dev, "vdd-hba")`.
   - Source: [`ufshcd.c` L9572-L9611](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L9572-L9611).

3. `ufshcd_hba_init()` always calls `ufshcd_init_hba_vreg()` and then `ufshcd_setup_hba_vreg(hba, true)` before initializing clocks. But the setup function is a wrapper around `ufshcd_toggle_vreg()`, and `ufshcd_enable_vreg()` immediately returns success for a NULL regulator pointer.
   - Source: [`ufshcd.c` L9499-L9567](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L9499-L9567) and [`ufshcd.c` L9777-L9848](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L9777-L9848).

4. If a populated HBA regulator exists, ACK calls `regulator_enable()` during HBA init. Failure unwind calls `ufshcd_setup_hba_vreg(..., false)`. `ufshcd_hba_exit()` also disables it when the HBA was powered.
   - Source: [`ufshcd.c` L9499-L9538](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L9499-L9538), [`ufshcd.c` L9777-L9848](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L9777-L9848).

5. During runtime/system suspend, `ufshcd_suspend()` turns off the HBA regulator only when `ufshcd_is_link_off()` or `ufshcd_can_aggressive_pc()` is true. Resume applies the matching HPM enable condition. Ordinary suspend does not unconditionally toggle this supply.
   - Source: [`ufshcd.c` L10093-L10100](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L10093-L10100) and [`ufshcd.c` L10494-L10586](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L10494-L10586).

**Direct answer — when does ACK request `vdd-hba`?**

- With a valid `vdd-hba-supply`, the generic ACK path obtains the regulator and requests enable at HBA initialization, then disables on applicable unwind/exit and on low-power transitions that meet the link-off/aggressive-collapse condition.
- Without `vdd-hba-supply`, the pointer remains NULL, no regulator handle is obtained, and the enable/disable wrappers are no-ops. This is explicitly supported by the source and is not, by itself, a probe failure.

**Candidate implication:** the candidate's deliberate omission of `vdd-hba-supply` means it does not use the ACK UFS regulator handle for `ufs_phy_gdsc`. Its GDSC behavior comes from the candidate GenPD attachments instead. This is a different power-management contract from stock HOS.

### 2.3 How candidate GenPD attachment works

**PUBLISHED OBSERVATION — ROUND144 candidate patch review**

The candidate host node lists, in order:

1. RPMHPD MMCX;
2. GCC `UFS_PHY_GDSC`.

The candidate patch explicitly calls `devm_pm_domain_attach_list()` before `ufshcd_pltfrm_init()`, using the attached virtual domain devices for the UFS host. It configures the one `required-opps` slot with `required_dev_index = 0`, so the slot maps to the first attached domain device, MMCX. ROUND144 found this ordering compatible with fixed ACK OPP setup.

The UFS PHY node separately lists GCC `UFS_PHY_GDSC` as its single domain.

Source and report:
- [ROUND144 candidate attachment and OPP mapping, §3](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round144/AI1_ROUND144_UFS_OPP_REQUIRED_DEVICE_AND_PROBE_ORDER_AUDIT.md#L58-L82)
- [`dev_pm_domain_attach_list()` and `PD_FLAG_REQUIRED_OPP` behavior, fixed ACK `common.c` L193-L300](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/base/power/common.c#L193-L300)
- [Candidate stock-vs-ACK DT distinction, ROUND139 §2.4](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L183-L188)

The generic platform-bus attach path is not enough for a device with two domains: `genpd_dev_pm_attach()` returns without attaching when the node has anything other than exactly one `power-domains` entry. The candidate's explicit `devm_pm_domain_attach_list()` is therefore important, not cosmetic.
- [`platform_probe()` calls `dev_pm_domain_attach()`, fixed ACK `platform.c` L1409-L1417](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/base/platform.c#L1409-L1417)
- [`genpd_dev_pm_attach()` single-domain guard, fixed ACK `pmdomain/core.c` L3270-L3280](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/core.c#L3270-L3280)
- [`genpd_dev_pm_attach_by_id()` creates a virtual device per domain, fixed ACK `pmdomain/core.c` L3282-L3338](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/core.c#L3282-L3338)

### 2.4 Does attaching the same GDSC to host and PHY duplicate power domains?

**PINNED SOURCE FACT**

No second GDSC provider object is created. Both phandles resolve to the same `ufs_phy_gdsc` `generic_pm_domain` instance exported by the GCC driver. `genpd_add_device()` appends each attached device to that domain's device list and increments the same `device_count`.
- [GCC SM8250 `ufs_phy_gdsc` descriptor, fixed ACK `gcc-sm8250.c` L3250-L3264](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/clk/qcom/gcc-sm8250.c#L3250-L3264)
- [`genpd_add_device()` increments the shared domain membership, fixed ACK `pmdomain/core.c` L1917-L1945](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/core.c#L1917-L1945)
- [`genpd_power_off()` checks every attached member's runtime-suspended state, fixed ACK `pmdomain/core.c` L945-L1015](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/core.c#L945-L1015)

Therefore this is best described as **one shared GenPD with multiple device clients**, not two independent GDSC writers. The domain is powered on once and may only be powered off when the GenPD core's membership/runtime conditions allow it.

**Lifecycle caution:** the UFS QMP PHY platform driver does not define a platform `.pm` callback in its driver structure; the host's `ufs_qcom_setup_clocks()` explicitly calls `phy_power_off()` / `phy_power_on()` as part of UFS clock sequencing. The generic PHY core only obtains runtime PM on the PHY class device when that PHY device has runtime PM enabled. This makes the host's explicit domain device-link/runtime-PM sequencing important; a shared domain reference alone does not prove that every PHY on/off transition is tracked as an independent GenPD client.
- [QMP UFS PHY platform driver, fixed ACK `phy-qcom-qmp-ufs.c` L2127-L2242](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/phy/qualcomm/phy-qcom-qmp-ufs.c#L2127-L2242)
- [PHY runtime-PM gating, fixed ACK `phy-core.c`