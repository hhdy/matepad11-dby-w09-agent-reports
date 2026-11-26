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
- [PHY runtime-PM gating, fixed ACK `phy-core.c`` L157-L215](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/phy/phy-core.c#L157-L215)
- [PHY power-on/off calls runtime-PM helpers, fixed ACK `phy-core.c` L305-L380](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/phy/phy-core.c#L305-L380)
- [UFS-QCOM clock sequencing controls PHY power, fixed ACK `ufs-qcom.c` L1360-L1435](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufs-qcom.c#L1360-L1435)

**INFERENCE:** the host's attached GDSC virtual device and its device link are expected to provide the active UFS client reference while the host is running; the PHY's `phy_power_on/off` is sequenced by the host. This may be a workable ACK design, but the HOS snapshot does not prove that this GenPD policy is required or equivalent. The candidate runtime state and first boot remain unverified.

### 2.5 How could HOS be active while its `vdd-hba` handle is disabled?

**KNOWN**
- HOS has the `vdd-hba-supply` declaration and a registered GDSC regulator provider.
- The regulator summary reports no active UFS enable request.
- UFS is active at the snapshot.
- HOS has no UFS GenPD attachment.

**POSSIBLE, NOT PROVEN**
- The Huawei 4.19 UFS variant may not acquire or enable this optional HBA regulator on this board/build, despite the overlay property.
- The vendor may treat the empty `vdd-hba-fixed-regulator` marker specially.
- The GDSC may be in a retained/firmware-controlled or otherwise non-voted state while the framework reports no active consumer.
- The regulator's software status may not describe the physical state in the simple way assumed by the candidate.

No one of these explanations is established by the public report. The exact HOS UFS variant source, vendor regulator parsing and GDSC register/status semantics are needed.

### 2.6 Is candidate GDSC GenPD required for first boot?

**UNKNOWN.** Fixed ACK's UFS core can initialize with no `vdd-hba` supply; the source does not make the HBA regulator mandatory. The candidate's GenPD attachment is an architectural/power-management choice, not a generic ACK UFS probe requirement demonstrated by the source alone. However, the target-specific hardware may require a GDSC state for reliable UFS PHY operation. The HOS runtime snapshot is not enough to remove or retain the candidate GenPD safely.

Minimum evidence to decide retain/remove/alter:
1. Exact HOS `ufshcd-qcom` / platform glue source matching `4.19.157-perf+`, including handling of `vdd-hba-fixed-regulator`, `vdd-hba-supply`, and runtime/system PM.
2. Exact HOS GDSC node and provider implementation for `0x177004`: `pwrsts`, `always-on`/retention flags, status check, enable/disable sequence, boot-on state and any firmware ownership.
3. Candidate source/DT attachment call order and device-link flags, plus actual GenPD runtime status for the host virtual clients and PHY provider.
4. A sanctioned, read-only runtime trace or existing boot log showing GDSC state transitions during UFS probe, active operation, runtime suspend and resume. No new device operation is authorized by this round.

---

## 3. HOS legacy devfreq/msm-bus versus candidate OPP/ICC/RPMhPD

### 3.1 Stock HOS

**PUBLISHED OBSERVATION**
- HOS UFS host has legacy `qcom,msm-bus,name = "ufshc_mem"`, `num-cases = 26`, `num-paths = 2`, `vectors-KBps`, and `bus-vector-names`.
- It has no `interconnects`, `operating-points-v2`, or `required-opps`.
- ROUND151 live UFS devfreq: `simple_ondemand`, current 37.5 MHz, maximum 300 MHz; current `active_icc_level = 0x0F`.
- The UFS host is active at HS-G1 ×2 in that snapshot.
- The report also records a `qcom/bus_speed_mode` runtime view. This is consistent with the vendor legacy path, but does not disclose every bus vote or prove its numeric equivalence to ACK ICC.

Sources:
- [ROUND139 HOS `msm-bus` / no OPP or interconnect declarations, §2.4](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L169-L188)
- [ROUND151 live devfreq and UFS state, §4.6](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md#L336-L365)
- [AI1 ROUND151 comparison, §3–5](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round151/AI1_ROUND151_INDEPENDENT_REVIEW_AND_ROUND152_PLAN.md#L81-L133)

### 3.2 Fixed ACK UFS scaling and ICC

**PINNED SOURCE FACT**
- If the UFS host has `operating-points-v2`, `ufshcd_parse_operating_points()` sets up OPP clock configuration, parses the OPP table and sets `hba->use_pm_opp = true`; otherwise the generic driver can use the legacy `freq-table-hz` path.
- During devfreq scaling, the OPP-enabled path calls `dev_pm_opp_set_opp()` for the selected frequency. The OPP core applies the clock configuration and required performance-state request(s).
- The UFS-QCOM variant obtains two ICC paths (`ufs-ddr` and `cpu-ufs`) and applies bandwidth votes. It requests maximum bandwidth before controller/device initialization, then updates bandwidth based on negotiated gear/lane and during clock transitions.
- Thus the candidate's published two ICC paths are not merely decorative DT properties: fixed ACK UFS-QCOM source contains the corresponding ICC consumer path.

Sources:
- [`ufshcd_parse_operating_points()`, fixed ACK `ufshcd-pltfrm.c` L414-L487](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufshcd-pltfrm.c#L414-L487)
- [UFS OPP clock set and scaling, fixed ACK `ufshcd.c` L1135-L1228](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L1135-L1228)
- [UFS devfreq target uses OPP when enabled, fixed ACK `ufshcd.c` L1585-L1665](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/core/ufshcd.c#L1585-L1665)
- [UFS-QCOM ICC path setup and initial max vote, fixed ACK `ufs-qcom.c` L1466-L1491](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufs-qcom.c#L1466-L1491)
- [UFS-QCOM ICC path votes and mode table selection, fixed ACK `ufs-qcom.c` L848-L901](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufs-qcom.c#L848-L901)
- [UFS-QCOM ICC updates during clock transitions, fixed ACK `ufs-qcom.c` L1360-L1435](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/ufs/host/ufs-qcom.c#L1360-L1435)

### 3.3 Candidate OPP / required-opps / RPMhPD mapping

**PUBLISHED OBSERVATION — ROUND139 / ROUND144 / ROUND151**
- Candidate UFS host has `operating-points-v2`, two OPP entries, `required-opps` to the RPMhPD table, and two ICC paths.
- The candidate has two UFS OPP entries, with `required-opps` pointing to RPMhPD table entries `opp3` and `opp6`. The 37.5 MHz current / 300 MHz maximum values cited above are the HOS live devfreq snapshot, not independently asserted here as candidate OPP frequencies.
- ROUND144 confirms the candidate patch attaches domain devices in the order MMCX then UFS PHY GDSC, and the single UFS `required-opps` slot maps to the first attached device with `required_dev_index=0`.
- The selected SM8250 `RPMHPD_MMCX` descriptor is the plain MMCX object with `res_name = "mmcx.lvl"` and no parent pointer. A similarly named MMCX-with-CX-parent descriptor exists but is not selected by the SM8250 array.
- The ACK UFS PHY GDSC descriptor has no `.parent` relationship to MMCX.

Sources:
- [ROUND144 OPP mapping and attachment order, §3–4](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round144/AI1_ROUND144_UFS_OPP_REQUIRED_DEVICE_AND_PROBE_ORDER_AUDIT.md#L58-L109)
- [ROUND145 descriptor object identity and SM8250 selection, §1–2](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round145/AI1_ROUND145_RPMHPD_ARC_PARENT_DESCRIPTOR_COMPATIBILITY_AUDIT.md#L14-L68)
- [RPMHPD MMCX descriptors and `mmcx.lvl`, fixed ACK `rpmhpd.c` L126-L153](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L126-L153)
- [SM8250 RPMhPD array selects plain MMCX and CX-with-MX-parent, fixed ACK `rpmhpd.c` L465-L477](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L465-L477)
- [RPMHPD probe reads CMD-DB resource address/AUX and registers domains, fixed ACK `rpmhpd.c` L1001-L1068](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L1001-L1068)
- [RPMHPD corner requests, fixed ACK `rpmhpd.c` L806-L970](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L806-L970)

### 3.4 Classification

The candidate is **not** a direct equivalent of HOS UFS scaling.

It is a **plausible upstream-native replacement** for some vendor-specific performance/bus-vote functions:
- UFS clock frequency is represented by OPP;
- MMCX performance state is represented by RPMhPD;
- DDR/CPU bandwidth is represented by ICC;
- UFS devfreq continues to provide a scaling policy.

But it is **not proven equivalent**:
- HOS does not declare UFS as an MMCX ARC or RPMhPD consumer;
- HOS's 26-case/two-path `qcom,msm-bus` vectors have not been numerically mapped to candidate ICC votes;
- HOS current `active_icc_level=0x0F` is not shown to be the same unit or state as candidate OPP level / RPMhPD corner;
- HOS live 37.5 MHz is one snapshot, not proof that its complete performance policy has only two levels;
- candidate adds a UFS-to-MMCX RPMhPD request that is not present in the stock UFS FDT.

The candidate does contain ICC paths and the fixed ACK UFS-QCOM consumer code uses them, so it is **not correct to say that candidate ICC is wholly missing**. What remains unknown is whether the path topology, bandwidth table, average/peak units and requested values reproduce the vendor msm-bus vectors.

**Risk classification:** option 2 in the taskbook — a plausible upstream-native replacement — with an additional **potentially excessive/unverified MMCX performance vote**. It is not yet a justified HOS behavior replacement.

---

## 4. `mmcx.lvl` single-owner rule: ARC MMCX versus RPMHPD MMCX

### 4.1 Shared resource identity

**PUBLISHED OBSERVATION / PINNED SOURCE FACT**
- HOS has ARC provider group `mmcxlvl`, resource name `mmcx.lvl`.
- Fixed ACK SM8250 `RPMHPD_MMCX` also uses `mmcx.lvl`.
- ROUND151 / ROUND147 reports the currently published candidate DTB has zero `qcom,rpmh-arc-regulator` providers. Thus the candidate currently does not demonstrate an active two-writer collision.
- If an ARC `mmcxlvl` provider is later added while retaining RPMHPD MMCX, both paths resolve the same CMD-DB resource address.

Sources:
- [ROUND139 seven ARC groups and five child links, §2.4](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L147-L179)
- [ROUND148 shared-resource collision analysis, §1–2](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round148-arc-regulator-portability-review/firmware-analysis/round148/AI2_ROUND148_ARC_REGULATOR_AND_PROXY_CONSUMER_PORTABILITY_AUDIT.md#L1-L25)
- [AI1 ROUND151 confirms conditional conflict and candidate zero-ARC status, §5.1](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round151/AI1_ROUND151_INDEPENDENT_REVIEW_AND_ROUND152_PLAN.md#L135-L151)

### 4.2 Why RPMh does not arbitrate the two drivers

The fixed ACK RPMh cache lookup is by `cmd->addr`: `__find_req()` finds one cache entry for a resource address, and `cache_rpm_request()` updates that same entry's sleep/wake value. `__rpmh_write()` then sends ACTIVE_ONLY requests directly to the controller. This is transport/cache behavior, not a cross-driver max-vote service.

- [RPMh cache keyed by command address, fixed ACK `rpmh.c` L48-L150](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/soc/qcom/rpmh.c#L48-L150)
- [RPMh cache update and write path, fixed ACK `rpmh.c` L130-L250](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/soc/qcom/rpmh.c#L130-L250)
- [RPMHPD aggregates only its own domain/peer objects, fixed ACK `rpmhpd.c` L852-L927](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/pmdomain/qcom/rpmhpd.c#L852-L927)
- [Generic Qualcomm ARC reference aggregates its own child requests; ROUND148 §4.3](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round148-arc-regulator-portability-review/firmware-analysis/round148/AI2_ROUND148_ARC_REGULATOR_AND_PROXY_CONSUMER_PORTABILITY_AUDIT.md#L74-L106)

**Rule:** do not instantiate two independent writers for `mmcx.lvl`. Two separate aggregators do not become a max-vote arbiter merely because they use the same RPMh transport or resource name.

### 4.3 Acceptable ownership models

**Model A — GenPD owns `mmcx.lvl`**
- Keep RPMHPD MMCX as the sole writer.
- Do not register an ARC `mmcxlvl` provider that also writes `mmcx.lvl`.
- Consequence: the HOS ARC MMCX child-regulator API and its five-edge graph are not preserved by this choice. The 11 HOS GDSC consumers of MMCX ALL cannot simply retain their old regulator `parent-supply` references unless they are deliberately remapped to a GenPD-compatible design.
- UFS MMCX OPP vote remains a candidate-specific replacement, not a stock HOS direct consumer relationship.

**Model B — ARC owns `mmcx.lvl`**
- Port/register the HOS-compatible ARC `mmcxlvl` resource and its child regulators as the sole writer.
- Remove, disable or redesign the RPMHPD MMCX path so it cannot write the same address.
- UFS OPP must no longer issue an independent RPMHPD MMCX request; if UFS performance needs a vote, route it through the single ARC owner with a verified child/level mapping.
- This is closer to the HOS regulator-child graph but requires exact HOS CMD-DB AUX and ARC request semantics.

**Model C — one shared arbitration provider owns `mmcx.lvl`**
- Create one resource owner that accepts both GenPD-style performance-state requests and regulator-child requests, computes a single state across all clients, and emits one coherent ACTIVE/SLEEP/WAKE vote set.
- The adapter APIs must not write directly to RPMh; only the common owner may write.
- This is the only model that can potentially preserve both APIs without independent writers. It is a new design requiring explicit lock, aggregation, suspend/wake, error and teardown semantics.

**Model D — GenPD for UFS plus non-overlapping ARC groups**
- Potentially retain the UFS GenPD OPP path and port only ARC resource groups that do not collide with RPMHPD resources.
- This still does not reproduce HOS's MMCX child-supply graph or the 11 GDSC-to-MMCX consumers. Those GDSC consumers must be explicitly remapped or intentionally omitted with a documented functional gap. A coarse GenPD parent link is not a drop-in substitute for child regulator supply dependencies.

**No model is selected for implementation in ROUND152.** The exact HOS AUX tables, active/sleep/wake vote values and complete GDSC consumer requirements are not yet available.

---

## 5. Proxy-consumer lifecycle evidence boundary

### 5.1 HOS declarations

ROUND139/ROUND151 report:
- eight `proxy-supply` declarations, self-referential at the provider/child level;
- ten `qcom,proxy-consumer-enable` declarations;
- four `qcom,proxy-consumer-current` declarations;
- ROUND151 additionally identifies a `qcom,proxy-consumer-voltage` property on the MX MMCX-supply child;
- L5 and L9, the two UFS PHY rails, are among the proxy-bearing resources.

These are DT declarations, not proof of actual runtime proxy handles.

Sources:
- [ROUND139 proxy census and property sites, §2.3](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md#L135-L167)
- [ROUND151 proxy declaration table, §5.4](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md#L435-L447)

### 5.2 What pinned ACK lacks

ROUND148's pinned-source census finds no proxy-consumer header/source, no `CONFIG_REGULATOR_PROXY_CONSUMER`, no Makefile object and no proxy register/unregister/sync-state lifecycle helpers in the fixed ACK. Generic device `.sync_state` infrastructure exists, but it is not the missing proxy library.

The fixed ACK RPMh regulator driver itself declares only `VRM` and `XOB` types and its OF match table is a PMIC-regulator table; it has no ARC provider type or `qcom,rpmh-arc-regulator` match. The regulator core does, however, provide nested child-supply lookup and recursive parent enable/disable. This confirms the split: generic regulator plumbing exists, while the target-specific ARC producer and proxy consumer implementation are missing.

- [ACK RPMh regulator type enum, `qcom-rpmh-regulator.c` L20-L36](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/qcom-rpmh-regulator.c#L20-L36)
- [ACK RPMh regulator OF match table, `qcom-rpmh-regulator.c` L1640-L1755](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/qcom-rpmh-regulator.c#L1640-L1755)
- [ACK nested child lookup, `of_regulator.c` L571-L640](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/of_regulator.c#L571-L640)
- [ACK recursive supply resolution, `regulator/core.c` L1975-L2140](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L1975-L2140)
- [ACK recursive enable/disable, `regulator/core.c` L2898-L3060](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/core.c#L2898-L3060)

- [ROUND148 pinned ACK proxy API gap, §3](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round148-arc-regulator-portability-review/firmware-analysis/round148/AI2_ROUND148_ARC_REGULATOR_AND_PROXY_CONSUMER_PORTABILITY_AUDIT.md#L28-L73)
- [AI1 ROUND151 proxy conclusion, §5.2](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round151/AI1_ROUND151_INDEPENDENT_REVIEW_AND_ROUND152_PLAN.md#L153-L157)

### 5.3 What ROUND151 runtime summary does and does not prove

ROUND151 says the full `regulator/regulator_summary` debugfs read was 25,966 bytes and was inspected locally. The public report publishes selected user counts, consumer nesting and proxy declaration sites, but it does **not** publish the complete raw summary or a per-proxy handle list that identifies proxy registration, enable state, request values and release time.

No explicit proxy-named runtime consumer lifecycle is established by the public report. Normal rail user counts cannot be assigned to proxy handles merely by subtracting known UFS/BT/CNSS consumers.

Therefore:
- proxy supply graph declarations: **PRESENT**;
- exact runtime proxy handle creation: **UNKNOWN**;
- whether each proxy is enabled at the captured time: **UNKNOWN**;
- sync_state/late-init release timing on Huawei's 4.19 kernel: **UNKNOWN**;
- whether proxy votes are required for L5/L9 or MMCX child defaults: **UNKNOWN**.

Do not use the OnePlus SM8475 implementation as proof of Huawei HOS cleanup semantics. ROUND148 explicitly classifies it as a generic Qualcomm reference from a different target/kernel, not exact HOS source.

---

## 6. Architecture options and decision matrix

| Option | Preserves | Does not preserve / hazards | Assessment |
|---|---|---|---|
| **1. Keep candidate GenPD-only UFS OPP, no ARC** | Current ACK-supported UFS OPP, RPMHPD MMCX request, GCC UFS PHY GDSC GenPD, two ICC paths | Does not reproduce seven HOS ARC providers, five ARC child edges, 13 GDSC-to-ARC supply links or proxy lifecycle; UFS-to-MMCX vote is not declared by HOS | **Best frozen baseline only; not HOS-equivalent** |
| **2. ARC provider plus single-owner/arbitrated MMCX** | Closest route to HOS ARC child-regulator graph and GDSC supply relationships | Must resolve `mmcx.lvl` owner; cannot retain independent RPMHPD MMCX writer; exact CMD-DB AUX and HOS vote semantics missing | **Potential full-fidelity direction, not ready** |
| **3. ARC + proxy + redesigned UFS performance control** | Could preserve ARC child supplies, proxy requests and an independently redesigned UFS scaling path | Proxy library absent in ACK; HOS lifecycle unknown; largest API/boot risk; still requires one MMCX owner | **Most complete in theory, least supportable now** |
| **4. GenPD-only UFS plus non-overlapping ARC groups and remapped GDSC users** | Keeps candidate UFS performance design while allowing some independent ARC resources | MMCX ARC children and 11 GDSC consumers need explicit remapping; GenPD hierarchy does not recreate nested regulator handles | **Possible staged compromise, but remapping is not designed** |
| **5. Unified MMCX resource owner exposing both client models** | Could expose ARC regulator-child and GenPD performance-state APIs while issuing one RPMh vote stream | Requires new common aggregation design and rigorous ACTIVE/SLEEP/WAKE, locking, error, probe and teardown semantics | **Best theoretical single-writer architecture if both APIs are truly required; no implementation authorized** |

### Recommendation

1. **Immediate:** Option 1 remains the unmodified candidate baseline only. Keep it frozen; do not add ARC nodes or alter the UFS domains/OPPs in this round.
2. **If full HOS fidelity is required:** evaluate Option 5 or a rigorously exclusive Option 2. The common resource owner must be settled before any `mmcxlvl` provider is introduced.
3. **If a smaller upstream-native port is acceptable:** Option 1 or Option 4 may be selected only after explicitly accepting that the stock ARC regulator-child/proxy graph is not reproduced and after remapping or excluding every affected GDSC consumer.
4. Do not choose based on `mmcx.lvl`, `ufs_phy_gdsc`, `LOW_SVS`, `NOM`, or other matching labels alone. The resource AUX map and consumer semantics determine the hardware request.

---

## 7. Minimal next evidence/source steps (dependency order)

These are future evidence tasks, not actions performed or authorized in this round.

1. **Obtain exact HOS source provenance** matching HOS 4.3.0.196 / kernel 4.19.157-perf+: UFS platform glue, `ufshcd-qcom` variant, GDSC driver, RPMh VRM/ARC provider and proxy-consumer library. Do not substitute the OnePlus SM8475 reference.
2. **Resolve HBA GDSC semantics** from that exact source and the exact HOS merged FDT: optional/fixed `vdd-hba` handling, GDSC enable/disable conditions, retain/always-on flags, status reporting and firmware ownership.
3. **Reconcile candidate GenPD lifecycle** from the already-published candidate patch/report: attach-list flags, device links, required OPP binding, PHY provider attachment, host runtime suspend ordering and domain state ownership. Do not inspect private workspaces.
4. **Map stock bus performance requests**: HOS 26-case/two-path msm-bus vectors versus candidate `ufs-ddr` / `cpu-ufs` ICC paths, including units, average/peak values, gear/lane tables and the `active_icc_level` interpretation.
5. **Establish resource identity and mapping** for every ARC resource: CMD-DB address, slave ID, AUX bytes, level map, child defaults, active/sleep/wake request values and all GDSC consumers.
6. **Choose exactly one `mmcx.lvl` writer** and specify how the 11 GDSC-to-MMCX consumers and the MMCX→MX-MMCX-supply→CX-MMCX-supply chain are represented.
7. **Prove proxy lifecycle separately**: runtime handle names/requests, enable timing, sync_state or late-init release and teardown/error unwind.
8. Only after the above design is reviewed should a separate taskbook authorize DTS/source changes, static checks and a new compile. First boot requires its own explicit gate and authorization.

---

## 8. First-boot implications and stop boundary

The candidate changes more than names:
- HOS has a `vdd-hba` regulator declaration with no active runtime user; candidate removes that consumer and uses GenPD.
- Candidate adds host-side MMCX performance-state voting through OPP/required-opps; HOS UFS has no corresponding declared domain/OPP consumer.
- Candidate relies on ACK ICC paths and RPMhPD mappings; equivalence to the HOS legacy msm-bus vectors is unproven.
- Candidate currently avoids the conditional ARC/RPMHPD `mmcx.lvl` collision by having zero published ARC providers. Adding ARC without an owner decision would introduce the conflict.
- Candidate does not reproduce HOS proxy lifecycle because ACK lacks the proxy-consumer library.

These are **design and first-boot risk factors**, not a prediction that the candidate will or will not boot. The evidence does not justify removing GDSC GenPD, retaining it unchanged as a proven HOS equivalent, or adding ARC/proxy code.

**Independent boot gate from ROUND143 remains open:** the candidate `/memory@80000000` zero-size `reg` tuple is skipped by the fixed ACK ordinary FDT memory scanner; EFI memory-map recovery is conditional on the EFI stub/configuration and complete `/chosen` metadata, none of which is proven for the target boot path. The candidate's 18 reserved-memory children versus HOS's 37 is not, by itself, a proven defect. This separate ARM64/FDT gate is unaffected by the UFS power decision and independently prevents first-boot authorization.
- [ROUND143 FDT zero-size tuple and EFI handoff boundary, §2–3](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round143-arm64-fdt-memory-handoff-audit/firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md#L16-L25)
- [ROUND143 zero-size memory scanner result, §2.2–2.3](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round143-arm64-fdt-memory-handoff-audit/firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md#L49-L70)

**First boot remains BLOCKED / NOT AUTHORIZED.** No device access, source/DTS/DTBO/config edits, patch generation, build, test, flash or boot was performed.

---

## 9. Compliance and final status

- Read only the supplied public taskbook/start prompt, public ROUND139/143/146/148/150/151 reports, ROUND144/145 reports, and fixed ACK source at commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`.
- No tablet, ADB, root, fastboot, recovery, UART, partition or private Agent workspace access.
- No WorkBuddy or 2号 Agent local captures accessed.
- No source, DTS, DTBO, config, patch or candidate artifact edited.
- No build, test, compile, boot or flash.
- No new compile is justified: no safe source/DTS delta has been established, and this taskbook explicitly limits the work to static review.

**Final disposition: PARTIAL — SOURCE TRACE COMPLETE FOR ACK UFS HBA / GENPD / OPP / RPMHPD PATHS; HOS GDSC BEHAVIOR, EXACT MSM-BUS EQUIVALENCE, ARC AUX/VOTES, AND PROXY LIFECYCLE REMAIN UNKNOWN.**

— END OF AI2 ROUND152 REPORT —
