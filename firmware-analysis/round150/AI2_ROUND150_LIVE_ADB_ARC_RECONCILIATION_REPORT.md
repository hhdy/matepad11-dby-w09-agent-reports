# AI2 ROUND150 — Live ADB ARC regulator graph reconciliation report

- Reviewer: **2号 AI (independent reviewer)**
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250
- Stock runtime reported: HOS 4.3.0.196(C00E100), Android 12, kernel 4.19.157-perf+
- Fixed ACK: `android17-6.18.33_r00`, `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Candidate content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Report branch: `ai2/round150-live-adb-arc-reconciliation-review`
- Disposition: **PARTIAL — ARC graph topology reconciled; live vote values, proxy lifecycle, final memory map and implementation ownership remain unresolved.**
- First candidate boot: **BLOCKED / NOT AUTHORIZED**

## 0. Executive decision

ROUND149's runtime evidence is a substantial structural confirmation, but its D-9 interpretation of regulator `-SUPPLY` links is backwards. Linux v4.19 regulator-core source shows that the link is created **inside the supplying regulator's device directory and points to the dependent consumer regulator device**. Applying that rule to the reported link-directory and target pairs yields the same five ARC child-supply edges previously extracted from the HOS4.3 FDT in ROUND139.

The corrected runtime direction is:

- CX `regulator.6` supplies MX `regulator.3`;
- MX `regulator.3` supplies MMCX `regulator.32`;
- MX ALL `regulator.1` supplies CX ALL `regulator.4`;
- MX AO `regulator.2` supplies both CX AO `regulator.5` and MMCX AO `regulator.33`.

The runtime report also identifies eleven GDSCs supplied by MMCX ALL, one GDSC supplied by CX ALL, and one GDSC supplied by GFX level: **13 GDSC-to-ARC relationships**, consistent with ROUND139's static census.

This proves the stock HOS regulator-framework topology exists at runtime, subject to the evidence limitation that ROUND149's raw `s9_01/s9_02` symlink captures were not published. The class-entry/provider mapping and symlink observations are therefore report-derived, not independently re-read raw evidence in this review.

It does **not** prove runtime votes, active/sleep corner values, physical voltage, or proxy-consumer lifecycle. It also does not show UFS directly consuming MMCX ARC. ROUND139 reports no HOS UFS `power-domains` or OPP relationship; ROUND149's live UFS devfreq and `qcom/bus_speed_mode` are consistent with its legacy scaling path. The eleven MMCX GDSC consumers must not be misidentified as UFS consumers.

**Architecture decision:** the current candidate's GenPD-only model is not demonstrated equivalent to the stock HOS ARC provider-child graph. Keep the existing 23-patch candidate unchanged and frozen while the design and ownership questions are resolved. No new compile is justified now: this round authorizes no source/DTS changes, and no specific safe code delta has been established.

## 1. Evidence set, scope and confidence

### 1.1 Inputs reviewed

1. [ROUND149 WorkBuddy live ADB report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round149-adb-runtime-readonly-audit/firmware-analysis/round149/WORKBUDDY_ROUND149_ADB_RUNTIME_READONLY_AUDIT.md)
2. [AI1 ROUND149 independent review and ROUND150 disposition](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round149/AI1_ROUND149_INDEPENDENT_REVIEW_AND_ROUND150_DISPOSITION.md)
3. [ROUND139 HOS4.3 PMIC/UFS/ARC static inventory](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md)
4. [ROUND146 pinned-ACK ARC/proxy support-gap analysis](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round146/AI1_ROUND146_RPMH_ARC_REGULATOR_SUPPORT_GAP_AND_PORTING_OPTIONS.md)
5. [ROUND143 ARM64/FDT/memory handoff audit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round143-arm64-fdt-memory-handoff-audit/firmware-analysis/round143/AI2_ROUND143_ARM64_BOOT_HANDOFF_FDT_MEMORY_AUDIT.md)
6. Linux v4.19 regulator core: [drivers/regulator/core.c](https://github.com/torvalds/linux/blob/v4.19/drivers/regulator/core.c)
7. Fixed ACK source at commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, including [RPMh regulator driver](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/qcom-rpmh-regulator.c), [RPMh power-domain driver](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/pmdomain/qcom/rpmhpd.c), and [regulator core](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c).

### 1.2 Evidence labels

- **SOURCE FACT** — directly supported by cited source code.
- **PUBLISHED REPORT OBSERVATION** — reported by an already published round; not independently re-captured here.
- **INFERENCE** — follows from source semantics plus report observations.
- **UNKNOWN** — values or artifacts are unavailable; no default/zero value is assumed.

No private Agent workspace, local raw capture, tablet, ADB, fastboot, partition, or build environment was accessed in ROUND150.

## 2. Linux v4.19 `-SUPPLY` sysfs semantics and D-9 correction

### 2.1 Source trace

In Linux v4.19 `drivers/regulator/core.c`:

- `set_supply(rdev, supply_rdev)` creates the consumer handle by calling `create_regulator(supply_rdev, &rdev->dev, "SUPPLY")`. Here `rdev` is the dependent regulator and `supply_rdev` is its supplier.
- `create_regulator()` receives the supplier regulator as its first argument and the dependent regulator's `struct device` as its second argument.
- It calls `sysfs_create_link_nowarn(&rdev->dev.kobj, &dev->kobj, buf)`: the first argument is the **supplier's kobject directory**; the second is the **consumer device target**.

Immutable source references:
- [Linux v4.19 set_supply() and supply handle creation](https://github.com/torvalds/linux/blob/v4.19/drivers/regulator/core.c#L1228-L1248)
- [Linux v4.19 create_regulator() and sysfs link creation](https://github.com/torvalds/linux/blob/v4.19/drivers/regulator/core.c#L1380-L1415)

Therefore a link named `<consumer-device>-SUPPLY` located **inside supplier regulator S's directory**, with target C, means **S supplies C**. The link target alone does not identify the dependency direction unless its containing directory is also known.

### 2.2 Corrected runtime graph

ROUND149 §6.3.1 provides the class-entry-to-provider/DT-node mapping and the reported directory/target pairs. Read according to the source rule above:

| Link directory (supplier) | Link name → target (consumer) | Correct relationship | ROUND139 static edge |
|---|---|---|---|
| CX `regulator.6` / `cxlvl` / `pm8150-s3-mmcx-sup-level` | `regulator.3-SUPPLY` → MX `regulator.3` | CX MMCX-supply child → supplies MX MMCX-supply child | MX MMCX-supply child depends on CX MMCX-supply child |
| MX `regulator.3` / `mxlvl` / `pm8150a-s3-mmcx-sup-level` | `regulator.32-SUPPLY` → MMCX `regulator.32` | MX MMCX-supply child → supplies MMCX ALL child | MMCX ALL child depends on MX MMCX-supply child |
| MX `regulator.1` / `mxlvl` / `pm8150a-s3-level` | `regulator.4-SUPPLY` → CX `regulator.4` | MX ALL child → supplies CX ALL child | CX ALL child depends on MX ALL child |
| MX `regulator.2` / `mxlvl` / `pm8150a-s3-level-ao` | `regulator.5-SUPPLY` → CX `regulator.5` | MX AO child → supplies CX AO child | CX AO child depends on MX AO child |
| MX `regulator.2` / `mxlvl` / `pm8150a-s3-level-ao` | `regulator.33-SUPPLY` → MMCX `regulator.33` | MX AO child → supplies MMCX AO child | MMCX AO child depends on MX AO child |

The ALL chain can be written from upstream supplier to dependent consumer as:

`CX MMCX-supply → MX MMCX-supply → MMCX ALL`

The static DT parent-supply wording describes the same chain from child to parent:

`MMCX ALL parent=CX/MX chain: MMCX ALL depends on MX MMCX-supply, which depends on CX MMCX-supply`.

For the other paired resources, CX ALL depends on MX ALL; CX AO and MMCX AO each depend on MX AO.

**D-9 verdict: AI1's correction is right.** ROUND149's statement that the live links reverse ROUND139 is an interpretation error caused by treating the link target as supplier without accounting for the directory in which the link resides. The corrected runtime topology matches all five ROUND139 ARC provider-child edges.

### 2.3 Evidence limitation

The ROUND149 report says the raw `s9_01/s9_02` captures remain local and were not uploaded. This reviewer therefore cannot independently verify the literal path of every symlink from the raw command output. The semantic correction is directly established by Linux v4.19 source; the exact regulator class IDs, provider mapping and link observations are **PUBLISHED REPORT OBSERVATIONS**. A narrow redacted listing containing each link's full containing directory, link name and resolved target would remove this remaining report-level dependency. No private capture was accessed to obtain it.

## 3. Reconcile all five ARC child edges and 13 GDSC links

### 3.1 Five ARC provider-child edges

ROUND139 §2.3 reports exactly five `*-parent-supply` edges among ARC child regulators. ROUND149's link-directory/target mapping, interpreted correctly, independently corroborates the five:

1. CX ALL child depends on MX ALL child.
2. CX AO child depends on MX AO child.
3. MMCX ALL child depends on MX MMCX-supply ALL child.
4. MMCX AO child depends on MX AO child.
5. MX MMCX-supply child depends on CX MMCX-supply child.

The fifth edge is important: the MMCX ALL path is not a simple MMCX→MX→CX domain-name hierarchy. It passes through specifically named child regulators, including the separately named `mmcx-sup` child resources. The child identity and regulator-core supply relationship are part of the topology.

### 3.2 Thirteen GDSC-to-ARC supply links

ROUND139's static census contains 13 GDSC nodes with `parent-supply` links to ARC children:

| ARC supplier child | GDSC consumers | Count |
|---|---|---:|
| MMCX ALL (`mmcxlvl` / `regulator-pm8150a-s4-level`) | `ad07004`, `ad0a004`, `ad0b004`, `ad08004`, `ad09004`, `ad0c144`, `af03000`, `abf0d18`, `abf0bf8`, `abf0d98`, `abf0c98` | 11 |
| CX ALL (`cxlvl` / `regulator-pm8150-s3-level`) | `3d9106c` | 1 |
| GFX level (`gfxlvl` / `regulator-pm8150a-s1-level`) | `3d9100c` | 1 |
| **Total** | | **13** |

ROUND149 §6.3.1 explicitly lists the eleven MMCX consumers. It also records the link under CX ALL `regulator.4` to GDSC `3d9106c`, and the link under the GFX-level regulator `regulator.31` to GDSC `3d9100c`. Under v4.19 semantics these are supplier-directory links, so all three groups point in the same supplier→consumer direction as ROUND139.

This reconciles the five ARC-child edges and 13 GDSC edges: **18 supply links in total** in the relevant published runtime census. It does not establish vote state or requested corner.

## 4. What live provider presence and binding prove

ROUND149 reports 47 `rpmh-regulator-*` platform devices under `18200000.rsc`, bound to the `qcom,rpmh-regulator` platform driver; seven level-style groups named `mmcxlvl`, `mxlvl`, `cxlvl`, `lmxlvl`, `lcxlvl`, `gfxlvl` and `ebilvl`; and three regulator-class entries each under MMCX, MX and CX.

Keep these proof levels separate:

| Level | Evidence | Verdict |
|---|---|---|
| Provider/device presence | 47 provider platform-device directories and seven `*lvl` names are reported live | **CONFIRMED — report-level runtime observation** |
| Driver binding/probe | Provider devices appear under the bound `qcom,rpmh-regulator` driver; child regulator class devices are registered | **CONFIRMED — runtime registration/binding evidence** |
| ARC identity | ROUND139's static FDT identifies the same seven groups as `qcom,rpmh-arc-regulator`; ROUND149 cannot read the live `of_node/compatible` values | **CONFIRMED by static+runtime correlation; not a new live compatible read** |
| Child regulator/supply graph | Three MMCX, three MX and three CX class entries, plus corrected live nested links | **CONFIRMED structurally, with raw symlink listing not published** |
| Runtime enable/voltage/current/vote values | Regulator attributes and debugfs are denied; RPMh vote/corner values not captured | **UNKNOWN** |
| Physical rail voltage | No physical measurement; software regulator values are also denied | **UNKNOWN / NOT MEASURED** |

The fact that the seven level-style devices bind under the vendor `qcom,rpmh-regulator` driver is strong evidence that the stock HOS kernel implements an ARC-capable producer path. It does not imply the pinned ACK implementation supports it. Nor does binding prove which level is currently voted or whether a resource is physically at a particular voltage.

The pinned ACK's `drivers/regulator/qcom-rpmh-regulator.c` enum contains only VRM and XOB and has no `qcom,rpmh-arc-regulator` match entry. The ACK has generic nested regulator lookup and supply recursion, but no ARC producer registering these child regulators. See [ACK RPMh regulator enum](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/qcom-rpmh-regulator.c#L20-L34), [match table](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/qcom-rpmh-regulator.c#L1640-L1752), and [nested child lookup](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/drivers/regulator/of_regulator.c#L571-L640).

## 5. UFS relationship: no proven direct MMCX ARC consumer

### 5.1 HOS4.3 evidence

ROUND139's static FDT inventory reports:

- HOS `ufshc@1d84000` and `ufsphy_mem@1d87000` have no `power-domains` property;
- neither has `operating-points-v2` / `required-opps`;
- no UFS OPP table is referenced;
- UFS instead declares the legacy `qcom,msm-bus` path (`ufshc_mem`, two paths, 26 cases);
- UFS PHY GDSC `gdsc@177004` has no `parent-supply`;
- the whole-FDT `power-domains` consumer census contains no UFS consumer.

ROUND149 adds live observations that the host at `1d84000.ufshc` is bound to `ufshcd-qcom`, has a registered `devfreq/1d84000.ufshc` directory and a `qcom/bus_speed_mode` attribute. The host's `soc/` DT subtree and attribute values were denied, so this is consistent with, but does not independently re-read, the HOS legacy devfreq/msm-bus declaration.

The eleven GDSCs supplied by MMCX are camera/video/display/GPU consumers listed in ROUND149. They are not the UFS host. The UFS PHY GDSC at `0x177004` is a separate GDSC and ROUND139 reports no ARC parent supply on it.

**Conclusion:** no evidence in the reviewed HOS reports establishes that UFS directly consumes MMCX ARC. Do not infer a UFS→MMCX ARC edge from the existence of the MMCX ARC provider or from the eleven unrelated GDSC consumers.

### 5.2 Candidate ACK model

The candidate uses ACK UFS OPP/GenPD wiring, including an MMCX RPMhPD performance-state association and UFS PHY GDSC. That is a candidate-specific architecture. It is not a direct transcription of the HOS UFS graph, which has no UFS `power-domains` or OPP declaration in ROUND139.

The candidate may still need a deliberate UFS performance vote for the target ACK architecture, but it must be described as a porting design choice and justified against the actual UFS devfreq/ICC requirements—not labelled as proven HOS ARC equivalence.

## 6. ARC, proxy and GenPD architecture decision

### 6.1 Why GenPD-only is not equivalent on current evidence

ARC provider-child and GenPD are different framework contracts:

- HOS ARC registers individual child regulator devices, with regulator-core supplier-consumer relationships and resource-specific ARC votes.
- The generic regulator core recursively resolves/enables a child's parent supply. This is not created merely by setting a GenPD parent pointer.
- GenPD/RPMhPD propagates performance states through power-domain descriptors and required-OPP mappings. It does not automatically register the HOS ARC child regulator names, reproduce their five nested supply edges, or reproduce the 13 GDSC regulator supply relationships.
- The pinned ACK SM8250 descriptor mapping selects a plain MMCX domain without the same parent chain; the CX descriptor's selected parent identity is a separate object. ROUND145 already showed why a one-line descriptor substitution is unsafe.

Therefore a GenPD-only model is **not demonstrated equivalent to the full stock HOS ARC graph**. It may implement a selected performance-vote function for a specific candidate consumer, but that narrower equivalence requires a consumer-by-consumer proof and cannot be generalized to the HOS regulator topology.

### 6.2 Proxy-consumer is a separate, still-unproven runtime facility

ROUND139 statically identifies:
- eight `proxy-supply` sites (L5, L9, L14, L11, CX MMCX-supply child, MMCX ALL child, GDSC `af03000`, and refgen);
- `qcom,proxy-consumer-enable` on those eight plus the GDSC/refgen sites (ten sites total);
- four `qcom,proxy-consumer-current` sites (L5, L9, L14 and PM8150A L11).

ROUND146 confirms the pinned ACK lacks the proxy-consumer header, implementation, Kconfig/Makefile integration and proxy-specific registration/lifecycle helpers. A generic Qualcomm reference implementation exists in a different kernel tree, but is not proof of Huawei HOS source behavior.

ROUND149's runtime regulator links do **not** expose whether proxy consumers were instantiated, what requests they hold, or when their requests are released. The live graph therefore does not close the proxy lifecycle question. It would be incorrect to claim that adding only ARC producer logic automatically preserves the vendor proxy behavior.

Proxy consumer support must be treated as a distinct feature with its own property parsing, regulator acquisition, enable/voltage/current request policy, naming, cleanup and synchronization semantics. In particular, evaluate the vendor's `sync_state` versus legacy late-init release behavior and the lifetime of boot-time proxy requests before porting.

### 6.3 Design option comparison

| Design | What it can represent | Main gap/risk | Disposition |
|---|---|---|---|
| ARC provider support | HOS child regulator devices, five nested child-supply edges, ARC active/sleep resource votes | Requires correct CMD-DB resource/AUX mapping and request aggregation; does not by itself add proxy lifecycle | **Closest base model for HOS graph** |
| ARC + proxy-consumer support | ARC model plus vendor boot-time proxy enable/voltage/current requests | More lifecycle/API work; must audit all proxy sites and avoid hidden votes | **Potentially most faithful, pending evidence** |
| Hybrid ARC + GenPD | ARC graph for HOS regulator/GDSC relationships plus GenPD for selected candidate performance-state consumers | Duplicate/conflicting votes if both paths write same resource; ownership and synchronization must be explicit | **Possible only with a single-owner/shared-arbitration design** |
| GenPD-only | Coarse performance states for selected consumers such as candidate UFS OPP mapping | Does not reproduce ARC child regulators, parent-supply graph, or GDSC links; HOS UFS itself has no declared GenPD/OPP consumer | **Not proven equivalent; not the default porting choice** |

### 6.4 Shared-resource ownership and duplicate-vote risk

The resource name `mmcx.lvl` is particularly sensitive. HOS ARC provider logic and the pinned ACK RPMhPD path can both address the same CMD-DB resource. Separate driver-local aggregators do not automatically create a single cross-driver max-vote arbiter. If an ARC provider and RPMhPD independently issue commands to the same resource, one path may overwrite or otherwise conflict with the other depending on the RPMh command/cache implementation and call ordering.

This is a **conditional architectural risk**, not a claim that ROUND149 observed a live collision. The candidate's actual compiled DTB ARC-node census is not published in the reviewed inputs; whether both providers would be active in the candidate remains unknown.

Before hybrid implementation, establish exactly one owner for each resource/set, or implement a common arbitration layer that combines all clients' requests before issuing RPMh commands. Do not rely on two independently maintained software maxima.

## 7. Required ARC implementation semantics before code

Do not blindly copy the SM8475 reference driver. It is useful as an API/algorithm reference only, not as exact HOS4.3 provenance.

The smallest technical specification needed before writing an ACK ARC producer is:

1. **Provider/resource identity:** for each of the seven HOS level groups, exact `qcom,resource-name`, CMD-DB address, slave ID, hardware resource type and valid CMD-DB entry.
2. **AUX mapping:** exact per-resource ARC hardware-level→consumer-level maps, entry count, ordering, valid values and behavior when AUX data is absent or malformed. These values are currently unknown.
3. **Child descriptors:** every child name, regulator ID, supported level range, initial mode/level, constraints and parent-supply relationship. Preserve all five ARC edges and the 13 GDSC edges.
4. **Aggregation:** per-child request tracking and aggregation across consumers; determine whether the HOS implementation takes the maximum requested level per ACTIVE and SLEEP set and verify how that maps to the target CMD-DB AUX values.
5. **State semantics:** define ACTIVE, SLEEP and WAKE_ONLY precisely. WAKE_ONLY must not be invented as a third independent consumer vote; the public reference describes it as a wake/restore path for the active state. Verify exact HOS behavior before adopting this interpretation.
6. **RPMh interaction:** exact command address/data layout, request completion/error handling, cache behavior, TCS/set selection, ordering and removal/release semantics.
7. **Ownership:** enumerate every other ACK consumer that can vote `mmcx.lvl`, `mx.lvl`, `cx.lvl` and the other four level resources. Decide whether RPMHPD, ARC or a shared arbiter owns each.
8. **Proxy lifecycle:** separately map all ten enable sites, eight proxy-supply sites and four current sites to actual runtime registration and release behavior.

The public Qualcomm reference describes active/sleep vote aggregation and per-resource AUX mapping, but these details must be checked against HOS-specific evidence rather than assumed to match.

## 8. FDT, memory and DTBO reconciliation

### 8.1 Live `/chosen` and EFI metadata

ROUND149 reports that the complete live `/chosen` property listing contains only `bootargs`, `kaslr-seed`, `linux,initrd-start`, `linux,initrd-end` and `name`. It contains no `linux,uefi-mmap-*`, no `linux,usable-memory-range`, and no `linux,efi-*` property.

This proves only that **the current running HOS boot's live, unflattened FDT does not expose those standard EFI/usable-memory metadata properties in `/chosen`**. It does not prove that ABL never used any EFI-related code path, that no EFI-like services existed earlier, or that there was no vendor-specific memory handoff path. Do not infer the entire ABL implementation from this one live property list.

ROUND143's pinned-source trace explains why the standard properties matter to the ACK EFI FDT-parameter path, but the target's actual entry route remains unknown.

### 8.2 Root cell values and `/memory/reg`

ROUND149 reports:
- root `#address-cells` property length: 4 bytes;
- root `#size-cells` property length: 4 bytes;
- live `/memory/reg` length: 48 bytes, i.e. twelve 32-bit cells;
- `MemTotal = 11,984,584 kB`.

A 4-byte property length proves one 32-bit cell is present; it does **not** reveal that cell's numeric value. Since the root cell values were denied, the twelve `/memory/reg` cells cannot be safely grouped into base/size tuples from the published data. Their addresses, sizes, tuple count and high-memory layout remain UNKNOWN. `MemTotal` is a kernel-reported aggregate and cannot substitute for the physical memory map or reserved-range evidence.

### 8.3 Reserved memory and candidate RAM node

The live stock FDT has 37 `/reserved-memory` children. Their names/property shapes are reported, but all per-node values needed to resolve static `reg` ranges, dynamic `size` / `alignment` / `alloc-ranges`, flags and phandle ownership remain denied. The number 37 confirms structure only; it does not prove every reservation is valid or calculate the available RAM.

The candidate's `/memory@80000000` zero-size tuple remains a real candidate-side issue. Pinned ACK's ordinary FDT memory scanner skips a tuple whose decoded size is zero. ROUND149's stock `/memory/reg` being 48 bytes does not provide the candidate's missing memory ranges, nor does it justify copying stock values. A non-zero candidate RAM map must be based on authoritative board/boot evidence.

### 8.4 DTBO

`ro.boot.dtbo_idx=2` is a live runtime property observation. ROUND138 maps entry 2 to the VD / board-id 8206 variant, so it is a useful corroboration of that mapping. It is not a hash of the physical DTBO partition, does not reveal the partition bytes, and does not by itself prove the exact final overlay bytes passed to Linux. Keep physical DTBO partition identity/hash and final post-ABL FDT identity UNKNOWN.

## 9. Gate table

| Gate / claim | Status | Reason |
|---|---|---|
| Correct interpretation of Linux v4.19 `-SUPPLY` links | **CONFIRMED** | Source semantics directly establish supplier-directory → consumer-target direction |
| Five HOS ARC child-supply edges | **CONFIRMED** | ROUND139 static edges agree with corrected ROUND149 reported runtime links; raw captures remain unpublished |
| Thirteen GDSC-to-ARC supply links | **CONFIRMED** | ROUND139's 11 MMCX + 1 CX + 1 GFX links agree with ROUND149's reported runtime targets |
| Seven HOS ARC provider identities | **PARTIAL** | ROUND139 reads compatible values; ROUND149 confirms matching live level-style devices/binding but live compatible values are denied |
| ARC runtime enable/vote/corner values | **UNKNOWN** | Regulator values and debugfs/RPMh votes unavailable |
| Physical rail voltages | **UNKNOWN** | No measurement or readable physical-voltage evidence |
| Pinned ACK ARC producer support | **CONFIRMED ABSENT** | Pinned driver supports VRM/XOB, not ARC |
| Pinned ACK nested regulator core plumbing | **CONFIRMED PRESENT** | Child lookup and recursive supply handling exist |
| Pinned ACK proxy-consumer support | **CONFIRMED ABSENT** | Header/source/Kconfig/Makefile/lifecycle facility absent at pinned commit |
| HOS proxy runtime lifecycle | **UNKNOWN** | Runtime evidence does not show proxy requests or release behavior |
| UFS directly consumes MMCX ARC on HOS | **NOT DEMONSTRATED / UNKNOWN** | HOS UFS has no declared power-domain/OPP edge; 11 MMCX GDSCs are other consumers |
| Candidate GenPD-only equivalent to full HOS ARC graph | **BLOCKED** | Framework semantics and dependency graph differ; no equivalence proof |
| Candidate compiled-DTB ARC/proxy inventory | **UNKNOWN** | No published candidate census in reviewed evidence |
| Live `/chosen` standard EFI map metadata | **ABSENT THROUGH THIS LIVE DT PATH** | Complete live property listing contains none; does not identify entire ABL route |
| Live stock root cell numeric values / RAM tuple decoding | **UNKNOWN** | Property lengths known, values denied |
| Live stock reserved-memory ranges/owners | **UNKNOWN** | 37 children known; values denied |
| Candidate zero-size RAM tuple | **BLOCKED** | Pinned ACK scanner skips zero-size tuple; justified candidate memory map absent |
| DTBO index | **CONFIRMED** | Runtime reports index 2; entry mapping is corroborative only |
| Physical DTBO bytes/hash and final post-ABL FDT identity | **UNKNOWN** | No partition read/hash or final FDT artifact |
| First candidate boot | **BLOCKED / NOT AUTHORIZED** | Memory, ARC/proxy, ownership, boot image, AVB and recovery gates remain open |

## 10. Minimal next work plan and ownership

### Priority 0 — preserve current candidate

- Keep the 23-patch candidate unchanged.
- Do not edit DTS, driver source, Kconfig, Makefile, RPMhPD descriptors or UFS OPP mappings during this evidence round.
- Do not compile: there is no approved code change to validate, and a build cannot resolve the missing HOS semantics or ownership questions.

### Priority 1 — AI1: close narrow evidence gaps from existing public artifacts

1. Publish a redacted, narrow excerpt of ROUND149's already-existing `s9_01/s9_02` link listings (directory path, link name, resolved target only), if available and authorized. Do not upload serials, unrelated logcat or private app content.
2. Publish an inventory of ARC/proxy nodes and child edges in the already-existing compiled candidate DTB artifact owned by its creator. No rebuild and no access by another agent to a private workspace.
3. Produce a resource ownership matrix for each ARC CMD-DB resource, especially `mmcx.lvl`, against candidate RPMHPD/GenPD/OPP consumers. Explicitly identify any second writer and the arbitration strategy.
4. Search only already-accessible, authorized HOS4.3 source/firmware evidence for the exact ARC and proxy implementation revision. If none exists, state that provenance is unavailable; do not infer Huawei's implementation from SM8475.
5. Confirm the precise ROUND138 DTBO entry-2/VD board-id 8206 mapping against the already-published package table, while keeping physical partition hash/bytes open.

### Priority 2 — AI2: independent design review after Priority 1 evidence

- Compare any exact HOS ARC implementation evidence against pinned ACK regulator, RPMh and GenPD APIs.
- Review CMD-DB AUX data and active/sleep aggregation, including WAKE_ONLY semantics.
- Review proxy property parsing and synchronization/release semantics as a separate patch series.
- Re-evaluate ARC-only versus ARC+proxy versus hybrid only after resource ownership and candidate-DTB ARC presence are known.

### Local Agent requirement

**No new local Agent action is presently required.** ROUND149 already reached the ordinary ADB permission boundary; repeating denied reads is not justified. A future privileged capture, device action or private-workspace operation would require separate explicit authorization and a narrowly scoped task. This ROUND150 task does not authorize it.

## 11. Compile/build decision

**No new compile is justified now.**

Reason:
- No source or DTS edit is authorized in this round.
- The current candidate's ARC/proxy compiled-DTB inventory and resource ownership are not yet established.
- The exact HOS ARC AUX maps and proxy lifecycle are unknown.
- A compile of unchanged source would not answer any of these architecture questions and would add no meaningful evidence.

Revisit compilation only after a reviewed, minimal patch is selected from the evidence above, with explicit ownership of every shared RPMh resource and a defined validation target. No build or test was run for this report.

## 12. Compliance and final disposition

- Only published GitHub reports and public source at immutable references were reviewed.
- No tablet, ADB, fastboot, root, recovery, UART, partition or private Agent workspace was accessed.
- No source/DTS/DTBO/config edits, patch creation, build, boot test or device operation was performed.
- ROUND149 raw local captures were not accessed.
- No claim is made about denied runtime vote values, physical voltage, actual EFI entry route, memory tuple contents, reserved ranges or physical DTBO bytes.

**Final: PARTIAL — corrected live ARC graph matches ROUND139's five child dependencies and 13 GDSC links; pinned ACK ARC/proxy support gaps remain; UFS direct MMCX dependency is not shown; GenPD-only equivalence is not established. Keep the candidate frozen, perform the narrow evidence/ownership work above, and do not compile or boot yet.**

— END OF ROUND150 AI2 REPORT —
