# AI1 ROUND151 — Independent review of Root ADB capture and ROUND152 disposition

- Reviewer: **1号 AI (ChatGPT)**
- Executor: WorkBuddy Agent (local Agent 1)
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250
- Stock system: HOS 4.3.0.196(C00E100), Android 12 / API 31, kernel 4.19.157-perf+
- Fixed ACK: android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Candidate tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- Primary input: [ROUND151 Root read-only runtime report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md)
- ROUND151 current report blob: 5e4d6ef48c1a34599d8c5afe157c2db199ba6f0c (public serial redacted; raw FDT/logs stay local).
- Related independent review: [AI2 ROUND150 live ADB ARC reconciliation](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round150-live-adb-arc-reconciliation-review/firmware-analysis/round150/AI2_ROUND150_LIVE_ADB_ARC_RECONCILIATION_REPORT.md)
- Disposition: **ACCEPTED WITH CORRECTIONS — major live evidence acquired; candidate integration remains BLOCKED / NOT AUTHORIZED.**

## 0. Executive disposition

ROUND151 is the most substantial target-device evidence round so far. KernelSU root access was already available to the ADB shell; no bypass or SELinux change was used. The running stock FDT was captured byte-exactly and verified against a device-side SHA-256. Its root cell values, physical RAM tuples, all 37 reserved-memory child nodes/ranges, full live UFS host/PHY supply declarations, seven ARC provider groups and five ARC parent-supply edges are now known.

The key updates:

1. **Stock physical memory map known:** three regions totalling 12,185 MiB, corroborated by /proc/iomem. ROUND149's cell-size ambiguity is closed. The candidate's zero-size /memory@80000000 tuple remains a candidate-side blocker.
2. **Stock UFS graph known:** ufshc and QMP UFS PHY are status=ok; the live merged tree resolves all UFS/PHY supply properties and confirms dtbo_idx=2.
3. **Stock UFS uses no declared power-domains or operating-points-v2:** it exposes legacy qcom,msm-bus, devfreq and a UFS host devfreq device. This is not the same design as the candidate ACK OPP/GenPD model.
4. **Stock ufs_phy_gdsc is registered but has zero enabled users and reports disabled while UFS is active.** This is a high-priority difference to resolve before deciding whether the candidate should attach UFS to UFS_PHY_GDSC through GenPD.
5. **The complete stock ARC graph is confirmed in the live FDT:** seven providers, five child-supply edges, thirteen GDSC-to-ARC links. Corrected runtime direction agrees with ROUND139 and AI2 ROUND150.
6. **S8 nuance:** the S8 rail is globally enabled by other consumers, but the UFS S8 consumer handle is shown at 0 mV / 0 mV. Do not claim UFS actively votes or enables S8.
7. Proxy property declarations are visible, but actual proxy-consumer lifecycle and release timing remain unproven.

No source, DTS, patch or candidate artifact was modified; no build or candidate boot was performed. **No new compile is justified from ROUND151 alone.**

## 1. Root gate and evidence integrity

ROUND151 identifies the same DBY-W09 / HWDBY / KONA / SM8250 device and HOS 4.3 build seen in ROUND149. The one su -c id gate reports uid=0(root) under u:r:ksu:s0; no prompt appeared because the existing KernelSU configuration had already granted the shell session. The agent did not use adb root, an exploit, an alternate privilege path or a SELinux change.

The FDT was captured as binary through a byte pipe. The report gives 800,316 bytes, magic 0xd00dfeed, totalsize=800316, and equal host/device SHA-256:

fefeaa049f64a9cc79f0aa7558883f7a31ba98cf0ad73f541834c0ec2d46b700

The FDT and raw dmesg remain local, not public. The public report's serial was redacted and the ROUND151 branch was repointed to the pre-report commit before publishing the sanitized report. This review relies on the published technical values and the agent's integrity report; AI1 did not download or re-hash the local binary.

One user-side setting change did occur before root capture: the user re-enabled USB debugging after the host initially exposed only MTP/WPD and ADB had no device. No other device change is reported.

## 2. Physical RAM map — ROUND149 D-2 closed

The live FDT root values are:

- #address-cells = 2
- #size-cells = 2
- model = Huawei Technologies, Inc. DBY-W09
- compatible = qcom,kona-qrd, qcom,kona, qcom,qrd
- board-id = <0x200e 0x0>

The live /memory reg consists of twelve 32-bit cells, decoded as three 2-address-cell / 2-size-cell tuples:

| Region | Base | Size | MiB |
|---|---:|---:|---:|
| 0 | 0x80000000 | 0x39900000 | 921 |
| 1 | 0x200000000 | 0x200000000 | 8,192 |
| 2 | 0xc0000000 | 0xc0000000 | 3,072 |
| **Total** | | | **12,185 MiB** |

The report says these windows are corroborated by /proc/iomem. Therefore the earlier ROUND149 concern that 4-byte root cell properties might mean a 1/1 tuple format was incorrect: a 4-byte property length says one cell is stored; only the captured binary reveals its numeric value. The live root is 2/2, and the twelve cells divide exactly into three tuples. ROUND149 D-2 is closed.

### 2.1 MemTotal arithmetic clarification

ROUND151 reports MemTotal = 11,984,584 kB, which is 11,703.695 MiB (approximately 11.43 GiB), or 481.305 MiB less than the sum of the three declared RAM regions.

The 23 non-zero static reserved-memory reg entries sum to approximately **232.689 MiB** when counted as entries. One 8 MiB display-ramdump region is fully nested inside the 35 MiB continuous-splash range, so the union of unique statically covered address intervals is approximately **224.689 MiB**. The remaining difference between declared RAM and MemTotal is not explained by the unique static reg ranges alone. Dynamic reserved pools, CMA treatment, other memblock reservations, kernel allocations and page accounting can contribute, but this capture does not provide a complete exact accounting equation.

Do not repeat a simplified claim that the whole 481.3 MiB difference equals the 232.7 MiB static ranges. Preserve the distinction between sum-of-entry sizes, unique physical interval union, dynamic reservation requests and MemTotal.

### 2.2 Reserved-memory inventory

The live FDT has 37 /reserved-memory children: 23 with non-zero reg, one zero-sized kerneldump placeholder and 13 dynamic size/alignment/alloc-ranges nodes. The report resolves 23 statically placed entries, one intentional nested overlap (8 MiB disp_rdump_region within cont_splash_region), and says every static range falls inside one of the three RAM windows.

This is now board-specific evidence, not merely the ROUND149 directory count. It does **not** automatically authorize copying all 37 HOS nodes into the candidate: candidate reserved-memory must be compared by name, address, size, flags, phandles and actual consumer requirements before selecting which declarations must be carried into Android 17.

## 3. Live UFS/PHY topology and state

The captured live merged FDT reports:

- /soc/ufshc@1d84000: status=ok, compatible=qcom,ufshc.
- /soc/ufsphy_mem@1d87000: status=ok, compatible=qcom,ufs-phy-qmp-v4.
- Host supplies: vcc → PM8150 L17; vccq → PM8150 L6; vccq2 → PM8150 S4; qcom,vddp-ref-clk-supply → PM8150 L6; qcom,vccq-parent-supply → PM8150L S8 / child name pm8150a_s8; vdd-hba-supply → GDSC ufs_phy_gdsc at 0x177004.
- PHY supplies: vdda-phy → PM8150 L5; vdda-pll → PM8150 L9; vdda-phy-always-on is present.
- Both stock nodes have no power-domains; the host has no operating-points-v2 or required-opps. The UFS host instead has a legacy qcom,msm-bus declaration and runtime devfreq registration.

The boot args contain androidboot.dtbo_idx=2; ROUND138 maps entry 2 to the VD / board-id 8206 variant. This confirms the running stock boot reports index 2. It does not hash the physical DTBO partition or prove the final FDT binary is byte-identical to package overlay output.

### 3.1 Software regulator values — separate UFS use from global rail state

ROUND151 reads software regulator state under root. The reported values are:

| Rail | Live target µV | State | num_users | UFS-specific use |
|---|---:|---|---:|---|
| L5 | 880,000 | enabled | 5 | UFS PHY is one consumer; other devices also consume it |
| L6 | 1,200,000 | enabled | 2 | UFS host has two distinct handles: VCCQ and vddp-ref-clk |
| L9 | 1,200,000 | enabled | 4 | UFS PHY is one consumer; other devices also consume it |
| L17 | 2,504,000 | enabled | 1 | one active UFS host VCC consumer |
| S4 | 1,800,000 | enabled | 5 | UFS host plus other consumers |
| S8 | 1,200,000 | enabled | 2 | **not a proven enabled UFS vote**; UFS qcom,vccq-parent handle is shown at 0 mV / 0 mV; two counted enabled users are BT and CNSS |

These are regulator-framework reported targets/constraints and user counts, not physical voltage measurements. In particular, S8 is present as a provider and the UFS DT property resolves to it, but the report's own regulator_summary says the UFS child handle is 0 mV / 0 mV and does not contribute an enabled user. Rewrite ROUND151 G7's broad label "all six UFS rails enabled at runtime" as: **all six provider resources exist; L5/L6/L9/L17/S4 are enabled with UFS-related active consumers; S8 is globally enabled by other devices but no enabled UFS S8 vote is shown.**

### 3.2 UFS health is a time-bounded snapshot

The host is bound to ufshcd-qcom, runtime status active, and reports a momentary UFS mode of HS-G1, two lanes, FAST mode. PA/DL/DME error counters read zero. devfreq is registered with a 37.5 MHz current value and 300 MHz maximum; the current ICC-level attribute is 0x0F.

This confirms the original stock UFS link was running at capture time. It is not a stress test, sustained-load qualification or boot-probe log. The kernel ring buffer contains only the last 234 seconds of a much longer-running system and has no retained UFS probe messages.

## 4. New high-priority UFS GDSC behavioural delta

The stock FDT declares vdd-hba-supply to ufs_phy_gdsc, and the provider is registered. However, ROUND151 reports:
- regulator.55 maps to 177004.qcom,gdsc;
- state=disabled;
- num_users=0;
- regulator summary has the UFS host child handle at 0 mV / 0 mV and use-count 0;
- no node in the live FDT references it through power-domains;
- the stock UFS link is active.

This is a real runtime fact, but its explanation is unknown. Do not say that the physical GDSC power gate is certainly off or that it is harmless: the provider's exposed regulator state and the fact UFS is operating create a behaviour that needs to be reconciled against the vendor 4.19 driver and GDSC implementation.

### 4.1 Fixed ACK 6.18.33 path is materially different

Pinned ACK UFS core source:
- drivers/ufs/core/ufshcd.c:9499-9516 — ufshcd_enable_vreg() calls regulator_enable() for a populated regulator.
- :9565-9570 — ufshcd_setup_hba_vreg() toggles the vdd_hba regulator.
- :9607-9612 — ufshcd_init_hba_vreg() obtains the HBA regulator.
- :9777-9800 — ufshcd_hba_init() obtains and enables the HBA regulator before initializing clocks.
- :9835-9848 — HBA exit disables the HBA regulator.

The candidate deliberately omits vdd-hba-supply and represents GCC UFS PHY GDSC through GenPD power-domains. It also adds the MMCX OPP/required-opps path. That is not the same contract as the stock HOS device tree. Before boot, establish exactly what the candidate's attached GenPD devices will power, when runtime PM will turn them on/off, whether both UFS host and PHY attach the same GDSC, and how this differs from the stock vdd-hba regulator handle that has zero active users.

Do not infer that the candidate must remove its GDSC domain or must enable it based on the ROUND151 snapshot alone. This is a specific source/DT/runtime reconciliation task, not a reason to add or delete a patch blindly.

## 5. ARC topology — confirmed, but vote values and proxy lifecycle remain open

ROUND151's live FDT contains seven qcom,rpmh-arc-regulator providers and 40 VRM providers, with all 47 bound under the vendor RPMh driver. It resolves all five ARC provider-child parent-supply edges and 13 GDSC-to-ARC supply links. AI2 ROUND150 independently establishes Linux v4.19 -SUPPLY sysfs link direction: the link is inside the supplier's directory and points to the dependent consumer.

The MMCX/MX/CX ALL chain is:
CX MMCX-supply child → supplies MX MMCX-supply child → supplies MMCX ALL child.
For regulator-core dependency wording, MMCX ALL depends on MX MMCX-supply, and MX MMCX-supply depends on CX MMCX-supply. The other ALL/AO pair edges match ROUND139 exactly. ROUND149 D-9 is closed in favour of ROUND139; ROUND149's interpretation was inverted.

This proves provider and framework topology, not ARC level values, CMD-DB AUX maps, active/sleep/wake vote values or measured voltages. ARC regulator microvolts values are level encodings, not literal microvolts.

### 5.1 Candidate resource ownership conflict

AI2 ROUND148 confirms the pinned SM8250 RPMHPD MMCX descriptor and HOS ARC mmcxlvl both use CMD-DB resource mmcx.lvl. Separate ARC-provider and GenPD aggregators do not automatically max-aggregate across drivers; the RPMh cache is address-keyed. Therefore, if both issue requests to the same mmcx.lvl address, there is a conditional shared-resource ownership conflict.

ROUND147 reports the current candidate DTB has zero ARC providers, so the current candidate does not establish an active dual-owner collision. But adding stock ARC groups while retaining candidate UFS RPMHPD MMCX would make ownership a mandatory design decision. Do not instantiate both independently and assume RPMh will combine them.

The candidate's GenPD-only model is not equivalent to the complete HOS ARC provider-child graph. At most it is a candidate-specific implementation of a narrow performance-state request; even that needs comparison against stock HOS devfreq/legacy msm-bus behavior because stock UFS has no declared OPP/GenPD relationship.

### 5.2 Proxy-consumer remains separate

ROUND139 and ROUND151 expose proxy-related properties, including proxy-supply, qcom,proxy-consumer-enable and current/voltage settings. ROUND148 establishes pinned ACK lacks the generic proxy-consumer library/lifecycle helpers. However, current reports do not prove exactly which proxy handles are live, their enabled state, or their sync_state/late-init unvote timing on the Huawei kernel.

Do not infer proxy runtime lifecycle solely from declarations or rail num_users. A narrow analysis of the existing ROUND151 regulator-summary output may identify explicit proxy handles, but if it does not, proxy lifecycle remains UNKNOWN until an authorized data source or source provenance is available.

## 6. Corrections to ROUND151 report claims

1. **Referenced reports were not missing.** ROUND151 V-8 says ROUND143 / ROUND146 / ROUND148 do not exist in any repository branch. That is a search-scope error: all three are retrievable from their known branches:
   - [ROUND143 AI2 FDT/RAM/EFI handoff review](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round143-arm64-fdt-memory-handoff-audit/firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md)
   - [ROUND146 AI1 ARC support-gap report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round146/AI1_ROUND146_RPMH_ARC_PARENT_DESCRIPTOR_COMPATIBILITY_AUDIT.md)
   - [ROUND148 AI2 ARC/proxy portability audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round148-arc-regulator-portability-review/firmware-analysis/round148/AI2_ROUND148_ARC_REGULATOR_AND_PROXY_CONSUMER_PORTABILITY_AUDIT.md)
2. **MemTotal arithmetic:** 12,185 MiB declared RAM minus 11,703.695 MiB MemTotal is 481.305 MiB. The 232.689 MiB sum of non-zero static reservation entries is not the whole delta; the 8 MiB nested overlap means unique static interval coverage is 224.689 MiB. Remaining page/allocator/dynamic reservation accounting is not resolved.
3. **S8 UFS user count:** S8 is globally enabled, but the UFS qcom,vccq-parent-supply handle is reported at 0 mV / 0 mV and does not contribute an enabled UFS user. Do not list S8 as an active UFS voltage vote.
4. **GDSC interpretation:** ufs_phy_gdsc reports disabled with zero users while UFS is operating. This is confirmed as a software-reported regulator state, but the physical gate interpretation remains open.
5. **Candidate-vs-stock handoff:** absence of standard EFI memory properties in stock /chosen is proven. It does not prove every detail of the ABL entry implementation.

## 7. Updated gate matrix

| Gate | Status after ROUND151 | Note |
|---|---|---|
| KernelSU root available through existing su | **PASS** | One su -c id, uid 0; no bypass |
| Live stock FDT binary integrity | **PASS** | Device and host SHA-256 equal, valid FDT header |
| Live root cells / memory tuples | **PASS** | 2/2 cells, three regions, /proc/iomem corroboration |
| Stock reserved-memory layout | **PASS for inventory** | 37 child nodes and values; candidate mapping still required |
| Stock /chosen UEFI metadata | **ABSENT in this live DT path** | Overall ABL path remains a narrower question |
| Stock UFS host / PHY / six supply mapping | **PASS for live declaration** | S8 active UFS vote caveat above |
| UFS regulator state | **PASS for software readout** | Not physical voltage measurement |
| UFS link state | **PASS for one snapshot** | HS-G1 x2, zero reported error counters |
| UFS GDSC behavior | **OPEN / HIGH PRIORITY** | disabled, zero use while UFS active |
| Seven ARC providers / binding / child graph | **PASS for structure and binding** | Vote/AUX values unknown |
| Five ARC child-supply relationships | **PASS** | ROUND139 + ROUND151 + AI2 ROUND150 |
| Thirteen GDSC-to-ARC links | **PASS for structure** | Vote values unknown |
| Proxy-consumer lifecycle | **UNKNOWN** | Declarations do not prove live proxy requests or cleanup |
| Physical PMIC VIN input parents | **BLOCKED** | Needs authoritative DBY-W09 schematic/netlist |
| Candidate RAM map | **BLOCKED** | Zero-size tuple must be replaced with justified values |
| Candidate reserved-memory parity | **UNKNOWN** | Requires exact compiled candidate DTB comparison |
| Candidate resource ownership (ARC vs RPMHPD) | **BLOCKED FOR DESIGN** | Single owner/arbitration required if both use mmcx.lvl |
| AVB / partition backup / tested recovery | **BLOCKED** | Partition names/sizes are not backup/recovery proof |
| First candidate boot | **NOT READY / NOT AUTHORIZED** | No build/boot/flash gate closed by this report |

## 8. ROUND152 plan

### 8.1 2号 Agent — existing candidate DTB memory/reserved/UFS-domain comparison

Use only the existing ROUND140 candidate artifacts in 2号 Agent's own workspace. Do not build. Produce an exact report comparing the candidate DTB against the new stock live FDT facts:
- root #address-cells/#size-cells;
- every candidate /memory node reg tuple and whether any size is zero;
- every candidate /reserved-memory node, reg/size/alignment/alloc-ranges/no-map/reusable properties and phandle references;
- differences against the 37 stock nodes, grouped into exact match / candidate-only / stock-only / same name but different values;
- UFS Host/PHY power-domains, OPP, vdd-hba, GDSC and supply properties;
- candidate RPMHPD mmcx.lvl ownership and ARC node count (ROUND147 reported zero ARC groups).
Do not access WorkBuddy Agent's local folder or raw FDT. Use this report's published decoded stock values only.

### 8.2 2号 AI — focused architecture review

Update the ROUND150 conclusion with ROUND151 evidence. Priorities:
- UFS vdd-hba GDSC disabled/zero-user observation versus pinned ACK ufshcd_hba_init() early HBA-regulator enable path;
- stock legacy UFS devfreq/msm-bus versus candidate UFS OPP/GenPD;
- whether a narrow UFS performance vote is needed and who owns mmcx.lvl;
- proxy-consumer evidence boundary;
- consequences for a minimal first-boot candidate versus full stock ARC fidelity.
No patch or build.

### 8.3 1号 AI integration work

After candidate DTB comparison and AI2 review:
1. Prepare one candidate FDT/DTS memory-map and reservation plan; do not blindly copy all stock nodes without consumer/resource review.
2. Resolve whether candidate UFS GDSC GenPD attachment should be retained, altered or removed using source evidence and a clear probe/PM-runtime explanation.
3. Decide the single owner of mmcx.lvl if ARC is introduced; do not permit independent ARC and RPMHPD writers.
4. Decide which proxy behavior is essential for first boot versus later fidelity.
5. Only after these choices are settled, consolidate code changes into one patch group and one main compile plus one independent reproduction.

**No new compile is justified now.** ROUND151 changes our understanding and supplies data, but does not itself change a source file or establish a safe code delta.

## 9. First boot and device safety

ROUND151 is a stock read-only evidence capture. It does not validate the candidate image. We still lack a full, verified partition backup and a tested recovery route. No candidate boot, temporary boot, fastboot, flash, partition write or reboot is authorized by this review.

**Final disposition: accept ROUND151's successful live capture, apply the corrections above, keep the 23-patch candidate frozen, and proceed with candidate-DTB comparison plus UFS/ARC ownership design.**
