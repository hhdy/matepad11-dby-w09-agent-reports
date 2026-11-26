# AI2 ROUND152 — Live UFS GDSC / devfreq / GenPD / ARC / proxy architecture decision

- **Assigned executor: 2号 AI (independent AI collaborator).**
- Not assigned to 1号 AI, WorkBuddy Agent (local Agent 1), or 2号 Agent (local Agent 2).
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250.
- Stock runtime: HOS 4.3.0.196(C00E100), Android 12 / API 31, kernel 4.19.157-perf+.
- Fixed ACK: android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.
- Candidate content tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b.
- Base independent report: AI2 ROUND150 live ADB ARC reconciliation.
- Branch: ai2/round152-live-ufs-gdsc-genpd-arc-proxy-decision.

## 1. Purpose

Use the new Root-gated ROUND151 stock runtime evidence to update the ROUND150 architecture decision. Focus on the newly exposed behavioural differences between stock HOS UFS and the candidate ACK UFS path, especially the UFS PHY GDSC, HBA regulator, devfreq/msm-bus versus OPP/GenPD, ARC resource ownership, and proxy-consumer evidence limits.

This is a static report/source review only. No device access, private workspace reads, source edits, patch generation, build, or test.

## 2. Mandatory inputs

1. ROUND151 Root runtime report:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md
2. AI1 ROUND151 independent review:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round151/AI1_ROUND151_INDEPENDENT_REVIEW_AND_ROUND152_PLAN.md
3. AI2 ROUND150 live ARC reconciliation:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round150-live-adb-arc-reconciliation-review/firmware-analysis/round150/AI2_ROUND150_LIVE_ADB_ARC_RECONCILIATION_REPORT.md
4. AI2 ROUND148 ARC/proxy portability:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round148-arc-regulator-portability-review/firmware-analysis/round148/AI2_ROUND148_ARC_REGULATOR_AND_PROXY_CONSUMER_PORTABILITY_AUDIT.md
5. AI1 ROUND146 pinned ACK ARC support gap:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round146/AI1_ROUND146_RPMH_ARC_REGULATOR_SUPPORT_GAP_AND_PORTING_OPTIONS.md
6. ROUND139 stock HOS static PMIC/UFS/ARC inventory:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md
7. ROUND143 ARM64 / FDT / RAM handoff review:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round143-arm64-fdt-memory-handoff-audit/firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md
8. Fixed ACK source at commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a, especially:
   - drivers/ufs/core/ufshcd.c
   - drivers/ufs/host/ufshcd-pltfrm.c
   - drivers/ufs/host/ufs-qcom.c
   - drivers/phy/qualcomm/phy-qcom-qmp-ufs.c
   - drivers/clk/qcom/gdsc.c
   - drivers/clk/qcom/gcc-sm8250.c
   - drivers/pmdomain/qcom/rpmhpd.c
   - drivers/soc/qcom/rpmh.c
   - drivers/regulator/qcom-rpmh-regulator.c
   - drivers/regulator/core.c

## 3. Newly established ROUND151 stock facts

Treat these as published runtime/FDT evidence, not as direct access by AI2:

### 3.1 Live stock UFS FDT

- /soc/ufshc@1d84000: status=ok, compatible=qcom,ufshc.
- /soc/ufsphy_mem@1d87000: status=ok, compatible=qcom,ufs-phy-qmp-v4.
- Host rails:
  - vcc → PM8150 L17;
  - vccq → PM8150 L6;
  - vccq2 → PM8150 S4;
  - qcom,vddp-ref-clk-supply → PM8150 L6;
  - qcom,vccq-parent-supply → PM8150L resource S8 / regulator node name pm8150a_s8;
  - vdd-hba-supply → qcom GDSC ufs_phy_gdsc at 0x177004.
- PHY rails:
  - vdda-phy → PM8150 L5;
  - vdda-pll → PM8150 L9;
  - vdda-phy-always-on present.
- HOS host and PHY both have no power-domains.
- HOS UFS host has no operating-points-v2 or required-opps; it has legacy qcom,msm-bus, freq-table-hz and devfreq registration.

### 3.2 Live runtime snapshot

- UFS driver binding ufshcd-qcom, host runtime status active.
- Current UFS mode: HS-G1, two lanes, FAST mode.
- PA/DL/DME error counters read zero at capture.
- devfreq current 37.5 MHz, maximum 300 MHz; simple_ondemand governor.
- UFS current_power_mode=0x11, active_icc_level=0x0F.
- L5 880mV / enabled / 5 users; UFS PHY is one consumer among several.
- L6 1200mV / enabled / 2 users; UFS host has two handles (vccq and vddp-ref-clk).
- L9 1200mV / enabled / 4 users; UFS PHY is one consumer among several.
- L17 2504mV / enabled / 1 user; active UFS VCC consumer.
- S4 1800mV / enabled / 5 users; UFS host plus other consumers.
- S8 1200mV / enabled / 2 users; critically, UFS qcom,vccq-parent handle is shown at 0mV/0mV and does not contribute an enabled user. The two counted users are BT and CNSS.
- These are regulator-framework reported values, not physical voltage measurements.

### 3.3 HBA GDSC

- Stock live FDT declares vdd-hba-supply to ufs_phy_gdsc at 0x177004.
- Regulator provider is registered.
- regulator state is disabled, num_users=0; regulator_summary UFS consumer handle is 0mV/0mV, use-count zero.
- No live stock UFS power-domains node references this GDSC.
- The UFS link is nevertheless active at the snapshot.
- The meaning of this state is UNKNOWN: do not equate software regulator status with a direct physical power-gate measurement.

### 3.4 ARC / proxy

- Seven stock qcom,rpmh-arc-regulator groups are live and bound; five ARC child parent-supply edges and thirteen GDSC-to-ARC edges are confirmed.
- ROUND149 -SUPPLY link interpretation is corrected: supplier directory → consumer link target; the corrected MMCX/MX/CX graph agrees with ROUND139.
- Pinned ACK ARC producer is absent; regulator core nested child-supply plumbing is present.
- Pinned ACK proxy-consumer library is absent; HOS proxy declarations exist but ROUND151 does not prove runtime proxy handle creation/release lifecycle.
- HOS UFS is not shown to consume MMCX ARC directly. Eleven MMCX GDSC consumers are camera/video/display/GPU consumers, not the UFS host.

### 3.5 Candidate differences

- Candidate uses ACK OPP/GenPD:
  - UFS host power-domains include RPMHPD_MMCX and UFS_PHY_GDSC;
  - UFS PHY includes UFS_PHY_GDSC;
  - candidate OPP table / required-opps associate UFS frequencies with MMCX RPMhPD levels;
  - candidate deliberately omits vdd-hba-supply, relying on GenPD for GDSC representation.
- Candidate DTB currently has zero ARC providers according to ROUND147.
- Candidate GenPD MMCX descriptor uses CMD-DB resource name mmcx.lvl. If later adding an independent ARC mmcxlvl provider, the same CMD-DB resource may have two separate owners; ROUND148 identified a conditional shared-address/cache collision.
- Candidate RAM tuple is zero-sized and still requires a justified correction; the new stock live RAM map is available in ROUND151.

## 4. Required analysis

### A. HOS UFS vdd-hba versus candidate GenPD

Trace the exact fixed ACK source call sequence:
- ufshcd_hba_init();
- ufshcd_init_hba_vreg();
- ufshcd_setup_hba_vreg(true);
- ufshcd_enable_vreg() / regulator_enable();
- failure unwind / hba_exit;
- runtime suspend/resume HBA regulator toggling.

Then answer carefully:
1. Under which conditions does fixed ACK actually request vdd-hba?
2. What happens if vdd-hba-supply is absent?
3. How are host and PHY GenPD domains attached and powered in the candidate?
4. Does attaching UFS_PHY_GDSC to both UFS host and PHY create duplicate domain clients, a harmless shared GenPD reference, or a risk? Verify using generic PM domain/device link/runtime PM source, not assumptions.
5. How can the stock HOS state (vdd-hba provider exists but no active user while UFS active) be explained? Separate known facts from possible vendor-driver behaviors.
6. Is candidate GenPD power-on required for first boot or merely upstream architectural preference? Do not overclaim.
7. Specify the minimum source/FDT/runtime evidence required to decide retain/remove/alter GDSC GenPD.

### B. Legacy HOS devfreq / msm-bus versus candidate OPP / ICC / RPMhPD

Trace:
- HOS FDT legacy qcom,msm-bus/freq-table declarations from ROUND139/151;
- live devfreq values and current snapshot from ROUND151;
- ACK UFS-QCOM devfreq scaling / ICC path;
- ACK OPP table and required-opps handling;
- RPMhPD MMCX descriptor and OPP level mapping.

Decide whether the candidate's OPP/GenPD path is:
1. direct equivalent of HOS UFS path;
2. a plausible upstream-native replacement for a vendor msm-bus path;
3. currently unsupported / potentially excessive;
4. incomplete because ICC or platform-specific bus votes are missing.

Identify exact source evidence and unknown hardware requirements.

### C. Resource ownership — ARC MMCX and RPMHPD MMCX

Use ROUND148 resource-ownership conflict analysis and pinned ACK source to define a safe single-owner rule for mmcx.lvl:
- ARC mmcxlvl and RPMHPD MMCX both resolve the same CMD-DB resource address.
- Independent aggregators are not a cross-driver max-vote arbiter.
- Candidate currently has zero ARC providers; conflict is conditional, not observed.
- Propose acceptable design choices: GenPD owns resource; ARC owns resource; or one shared arbitration provider mediates all clients.
- Evaluate consequences for HOS GDSC-to-ARC child relations and UFS OPP.
- Do not add both providers as independent writers.

### D. Proxy lifecycle

Review ROUND148 and ROUND151:
- what HOS declarations exist;
- what runtime evidence could be gleaned from the regulator_summary;
- whether the public report shows any explicit proxy-named consumer;
- whether ROUND151's raw local summary is unpublished, and so runtime lifecycle must remain report-level or UNKNOWN.
Separate proxy consumer registration from proxy-supply graph declarations.
Do not claim exact Huawei vendor cleanup semantics from OnePlus reference.

### E. Final architecture options

Recommend among:
1. retain existing candidate GenPD-only UFS OPP path, no ARC;
2. ARC provider plus a shared owner/arbitration design for MMCX;
3. ARC + proxy plus redesigned UFS performance control;
4. GenPD only for UFS while porting non-overlapping ARC resource groups and remapping GDSC users;
5. other precisely specified architecture.

For each option list:
- what it preserves;
- what it does not preserve;
- shared-resource hazards;
- runtime or boot risk;
- evidence still missing.

Do not decide only from property names or regulator node labels.

## 5. Output requirements

Create a decision report with:
- exact immutable source links and line references;
- clear distinction between report observations, source facts, inference and unknown;
- explicit answer to whether the candidate should be kept unchanged or modified;
- minimal source/DTS steps, ordered by dependency;
- first-boot implications and no-boot boundary;
- whether a new compile is justified now.

## 6. Prohibitions

- No tablet, ADB, root, fastboot, recovery, UART, partition or private Agent workspace access.
- No source/DTS/DTBO/config/patch edits.
- No builds, tests or candidate boots.
- Do not access WorkBuddy or 2号 Agent local captures.
- Do not assume regulator software values are physical voltage.
- Do not claim UFS directly consumes MMCX ARC.
- Do not claim vdd-hba disabled proves physical GDSC off.
- Do not authorize first boot.

## 7. Deliverable and stop condition

Upload report to:
firmware-analysis/round152/AI2_ROUND152_LIVE_UFS_GDSC_GENPD_ARC_PROXY_DECISION_REPORT.md

Do not overwrite the taskbook or start prompt. Read the uploaded report back, verify exact blob and STOP.
