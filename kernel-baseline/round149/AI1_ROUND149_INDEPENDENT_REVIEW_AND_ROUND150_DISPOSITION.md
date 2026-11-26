# AI1 ROUND149 — Independent review of live ADB evidence

- Reviewer: **1号 AI (ChatGPT)**
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250
- Live system: HOS 4.3.0.196(C00E100), Android 12 / API 31, kernel 4.19.157-perf+
- Candidate ACK: android17-6.18.33_r00, pinned 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Candidate tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- Input report blob: ef5348bf93b75e3872cf7104aeb73581c027fcd4
- Disposition: **ACCEPTED WITH CORRECTIONS — HIGH-VALUE LIVE STRUCTURAL EVIDENCE; FIRST BOOT STILL BLOCKED / NOT AUTHORIZED.**

## 0. Executive findings

ROUND149 is a meaningful advance. It establishes that the actual running DBY-W09 HOS4.3 system has 47 RPMh regulator provider devices bound under the vendor RPMh regulator driver; seven live level-style providers; registered regulator children for MMCX, MX and CX; resolved nested regulator supplier-consumer relationships; eleven GDSC consumers of the MMCX level rail; a live UFS host at 1d84000.ufshc bound to ufshcd-qcom; a traceable LUN-5 block device; all six candidate UFS rail-provider resources; dtbo_idx=2; 37 live reserved-memory child nodes; and a populated stock /memory/reg property.

The report is correctly marked PARTIAL. Most value-bearing interfaces are denied to uid 2000, so actual RAM ranges, reserved ranges, regulator voltages/use counts, RPMh corner votes, UFS descriptor values and kernel boot logs remain unknown. No partition data was read, no backup was created, and no recovery route was tested.

## 1. Device identity and execution integrity — ACCEPT

The report identifies one connected device as DBY-W09 / HWDBY / KONA / SM8250 and reports HOS 4.3.0.196(C00E100), kernel 4.19.157-perf+, eight AArch64 CPUs, uid=2000(shell), and SELinux Enforcing. It records 252 commands and says no root, writes, remount, debugfs mount, reboot, fastboot, flash or candidate boot occurred.

This is consistent with the agreed read-only boundary. Serial and raw application logs were retained locally rather than uploaded, which is appropriate. The public report does not include the 270 raw evidence files or their manifest, so the hash/manifest claims are accepted as Agent-reported metadata, not independently re-hashed by AI1.

## 2. ARC / regulator graph — important runtime confirmation

### 2.1 Direct runtime evidence

ROUND149 finds 47 rpmh-regulator-* platform devices under 18200000.rsc, bound under qcom,rpmh-regulator; seven level-style providers named mmcxlvl, mxlvl, cxlvl, lmxlvl, lcxlvl, gfxlvl and ebilvl; three regulator-class entries each for MMCX, MX and CX; and live regulator consumer links. Eleven GDSC regulator devices appear as consumers of the MMCX level regulator.

This independently corroborates ROUND139's static provider census and upgrades the evidence from package-only structure to live driver/device registration. The seven nodes' compatible property values were denied, so their identification as qcom,rpmh-arc-regulator is a combined ROUND139-static plus ROUND149-runtime conclusion, not a fresh compatible-string read.

### 2.2 Correction to ROUND149 D-9 — sysfs link direction was interpreted backwards

ROUND149 D-9 says the live -SUPPLY links reverse the direction in ROUND139. That conclusion is not supported by Linux regulator-core sysfs semantics.

In Linux v4.19, set_supply(rdev, supply_rdev) creates the relationship by calling create_regulator(supply_rdev, &rdev->dev, "SUPPLY"). The link is created inside the supplying regulator's device directory and points to the dependent consumer regulator device. The implementation calls sysfs_create_link_nowarn(&rdev->dev.kobj, &dev->kobj, ...), with the supplier as the link directory and consumer as the target:
- https://github.com/torvalds/linux/blob/v4.19/drivers/regulator/core.c#L1228-L1248
- https://github.com/torvalds/linux/blob/v4.19/drivers/regulator/core.c#L1380-L1415

Therefore, if regulator.3 contains regulator.32-SUPPLY -> regulator.32, regulator.3 is the supplier and regulator.32 is its consumer. Likewise, regulator.6 containing regulator.3-SUPPLY -> regulator.3 means regulator.6 supplies regulator.3.

Using ROUND149's own provider mapping:
- CX child regulator.6 supplies MX child regulator.3;
- MX child regulator.3 supplies MMCX child regulator.32;
- eleven GDSCs consume the MMCX level regulator.

This agrees with ROUND139: the MMCX child depends on the MX child, and the MX MMCX-supply child depends on the CX MMCX-supply child. The apparent discrepancy is a sysfs link-location/target interpretation error, not proof of reversed HOS DT dependencies. Correct D-9 after checking the raw s9_01/s9_02 listing against this supplier-to-consumer rule.

### 2.3 Architecture consequence and boundary

ROUND149 now demonstrates that stock HOS has registered ARC-style provider devices and a resolved nested regulator graph. This substantially strengthens ROUND146's conclusion that HOS uses a real regulator-framework ARC provider-child model, not just generic GenPD parent pointers.

It does not disclose active/sleep vote values, RPMh corners, enable state or CMD-DB transactions. It also does not prove that UFS itself directly consumes MMCX: ROUND139 says the stock HOS UFS node has no power-domains or OPP relationship and uses legacy qcom,msm-bus. The eleven MMCX GDSC consumers must not be relabelled as UFS consumers. Candidate GenPD/OPP behavior is a separate candidate-specific design question, and any translation must avoid duplicate votes.

## 3. UFS and PMIC — provider availability confirmed, runtime values unknown

The live host path is /sys/devices/platform/soc/1d84000.ufshc, bound to ufshcd-qcom, with host0, UFS attribute/descriptor directories and devfreq/1d84000.ufshc. The readable block symlink sdf resolves through the UFS host as SCSI LUN 5.

The six relevant rail providers are present:
- L5 → ldoa5
- L6 → ldoa6
- L9 → ldoa9
- L17 → ldoa17
- S4 → smpa4
- S8 → smpc8

The UFS PHY GDSC at address 0x177004 is also registered. These observations confirm host/device/provider existence, not current power mode, voltage, load, use count, physical PMIC input source, UFS geometry or correct sequencing. The devfreq device and qcom/bus_speed_mode attribute are consistent with ROUND139's legacy vendor scaling-path findings, but unreadable soc/ node properties mean ROUND149 does not independently prove absence of OPP or the exact active ICC vote.

All six candidate supply targets resolving to live provider resources is useful compatibility evidence, not proof of electrical equivalence. qcom,vccq-parent-supply consumer ownership remains unknown. Physical input parents of L5/L6/L9/L17/S4/S8 remain unknown and cannot be derived from ordinary ADB regulator listings.

## 4. Memory / FDT — correction to ROUND149 D-2

### 4.1 Established observations

The live stock FDT structure exposes:
- /chosen with exactly five properties: bootargs, kaslr-seed, linux,initrd-start, linux,initrd-end and name;
- no linux,uefi-mmap-*, no linux,usable-memory-range and no linux,efi-* property in that live /chosen;
- /memory/reg exists and is 48 bytes;
- /reserved-memory has 37 children;
- /sys/firmware/fdt is root-only and could not be copied by the shell user.

This shows that the current stock boot's enumerated /chosen does not expose the standard EFI memory-map metadata properties. It narrows the handoff question, but does not prove the entire ABL-to-Linux handoff mechanism or exclude vendor-specific/alternate memory handoff paths. Values remain unreadable.

### 4.2 The reported 1/1 cell concern is not established

A 4-byte #address-cells or #size-cells property file means that the property contains one 32-bit cell. It does **not** mean that the cell's numeric value is 1. The actual value is the property content, which was denied.

Likewise, the 48-byte /memory/reg value contains twelve 32-bit cells. The number of base/size tuples depends on the actual numeric values of root #address-cells and #size-cells, which remain unknown. Therefore D-2's hypothetical “1/1 root cannot express >4 GiB” cannot be applied as an observed contradiction.

Correct conclusion: /memory/reg is present and contains twelve cells, but root cell values, tuple grouping, addresses and sizes are unknown. MemTotal=11,984,584 kB is a useful system-visible total, not a substitute for the physical RAM map or reserved ranges.

### 4.3 Candidate implication

ROUND141/ROUND143's candidate finding remains important: the candidate /memory@80000000 tuple has zero size, and pinned ACK's ordinary FDT scanner skips zero-sized memory tuples. ROUND149 proves that stock HOS has a populated /memory/reg property, but its values are inaccessible. The candidate RAM node therefore still needs a justified non-zero map before candidate boot can be considered.

The absence of standard linux,uefi-mmap-* properties in the live /chosen does not alone prove whether ABL used direct entry, an EFI-related route with metadata removed, or another vendor-specific mechanism. Correlate with ROUND143 source analysis and boot-image evidence.

## 5. DTBO, partitions and AVB

- ro.boot.dtbo_idx=2 is now a live observation. ROUND138 mapped entry 2 to the VD / board-id 8206 variant. This is a strong runtime cross-check of the reported index, but is not a hash of the physical DTBO partition and does not prove the exact bytes delivered to Linux.
- The by-name symlink farm exposes 86 partition names/targets, including boot, dtbo, vbmeta and recovery-related partitions. No partition sizes/data, image hashes, full backup or restore test were obtained.
- Empty slot suffix and lack of A/B names are consistent with an A-only layout; keep that as a layout inference.
- verifiedbootstate=orange and flash.locked=0 are observations only. Do not claim a verified AVB chain or a proven effective bootloader lock state from these properties alone.

## 6. Evidence-quality and process corrections

1. **Taskbook/report path collision (D-1):** the report overwrote the taskbook at the same branch path. The old taskbook blob is reported recoverable from branch history, but future taskbooks, start prompts and reports must use distinct filenames. The current path now contains the report, not the original taskbook.
2. **ROUND143 was not missing:** the ROUND149 search list omitted the known branch ai2/round143-arm64-fdt-memory-handoff-audit. The report exists at https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round143-arm64-fdt-memory-handoff-audit/firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md. Treat this as a search-scope omission, not a missing artifact.
3. **Raw-evidence availability:** local raw captures and a 270-line SHA-256 manifest are claimed but not uploaded. Keep them local for privacy; a future independent check can use a narrow, redacted bundle of symlink listings and property-name/length listings rather than raw logcat.
4. **D-5 / D-6:** denied size-ioctl and /dev/null read probes returned no device data and made no device writes. Record the deviations; they did not alter tablet state.

## 7. Updated gate disposition

| Area | ROUND149 effect | Status |
|---|---|---|
| Device / SoC identity | Confirmed live | CLOSED for identity only |
| HOS RPMh provider presence/binding | 47 providers; seven level groups live | STRUCTURE + BINDING CONFIRMED |
| ARC nested regulator relationships | Runtime consumer links corroborate ROUND139 after correcting sysfs direction | STRUCTURE CONFIRMED; vote values UNKNOWN |
| Proxy-consumer behavior | No conclusive runtime lifecycle evidence | UNKNOWN |
| UFS host and rail provider existence | Host, driver, LUN-5 path and all six providers observed | PRESENCE CONFIRMED; state/sequence UNKNOWN |
| UFS OPP / ICC / current bus votes | devfreq path visible; node values denied | PARTIAL / UNKNOWN |
| Stock RAM map | /memory/reg exists, 48 bytes; values denied | UNKNOWN |
| Candidate RAM map | zero-size tuple remains | BLOCKED |
| EFI map via live /chosen DT | standard properties absent on this stock boot | ABSENT THROUGH THIS DT PATH; overall ABL path UNKNOWN |
| Reserved-memory | 37 live nodes/names; values denied | STRUCTURE CONFIRMED; ranges UNKNOWN |
| DTBO | runtime dtbo_idx=2 | INDEX CORROBORATED; partition bytes/hash UNKNOWN |
| AVB / boot chain | partition names and properties only | UNKNOWN |
| Backup / tested recovery | not done | BLOCKED |
| First candidate boot | not attempted or authorized | NOT READY / NOT AUTHORIZED |

## 8. ROUND150 recommendation

Do not rebuild or edit the candidate based on ROUND149 alone. No new code is justified solely by provider presence.

Assign **2号 AI** an independent static/live evidence reconciliation:
1. reproduce Linux v4.19 regulator sysfs link direction and correct D-9 from the raw ROUND149 listing;
2. reconcile the five ROUND139 ARC child-supply edges with the live provider-to-consumer links;
3. independently assess what the seven live level-provider devices prove about missing pinned-ACK ARC producer support;
4. distinguish ARC provider support from proxy-consumer behavior, which remains unproven at runtime;
5. assess whether a GenPD-only UFS OPP implementation represents the stock HOS UFS path, given ROUND139's lack of HOS UFS power-domains/OPP and ROUND149's live devfreq evidence;
6. recommend the smallest source/DTS work plan, without editing code, creating patches, building or touching the tablet.

A separate local Agent round is not presently required. Ordinary ADB has reached the stock build's permission boundary; repeating denied reads without a new authorized access method will not produce the missing values. Any further privileged capture needs a separate, narrowly scoped authorization or should be replaced with legitimate firmware/board evidence.

**No first-boot authorization is granted by this review.**
