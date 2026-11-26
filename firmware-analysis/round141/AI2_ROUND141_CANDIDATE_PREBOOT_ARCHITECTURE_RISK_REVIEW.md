# ROUND141 — Candidate pre-boot architecture risk review

- Reviewer: 2号 AI (independent reviewer; not 2号 Agent and not WorkBuddy Agent)
- Date: 2026-11-26
- Device target: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Fixed ACK: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` (`android17-6.18.33_r00`)
- Candidate content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Taskbook blob: `ce40b02a21a0896b8b952ebfd30900733d66b45f`
- Start prompt blob: `f38932c9aeaab194843b4f80bd1fddd8c86cf3d6`
- Review mode: read-only inspection of the fixed ACK source, candidate patch/report evidence and existing sanitized reports.
- Result: **NOT READY — additional offline evidence is required. First device boot remains BLOCKED / NOT AUTHORIZED.**

## 0. Scope and method

This review followed ROUND141's taskbook. It did not connect to or access a tablet; use USB, ADB, fastboot, recovery, serial, bootloader, root or partition access; download firmware or dependencies; build; modify source, patches, DTS, DTBO or configuration; package, sign, change AVB or flash anything. No other Agent's private workspace was accessed. No request was sent to another Agent to repeat ROUND140.

Evidence was separated into:
1. direct fixed-ACK source evidence, with exact paths, line ranges and fetched blob identities;
2. candidate source/DTB facts reported by ROUND135 R3 and ROUND140, with the distinction between raw source inspected here and report-level evidence retained;
3. HOS4.3 static package/FDT/DTBO facts in ROUND138/139;
4. explicit unknowns that cannot be closed by a static build.

The candidate tree SHA is a content-tree identity, not a commit SHA, Image SHA or bootability claim.

## 1. Review A — UFS supply declarations, driver consumers and inert properties

### 1.1 Property → provider → code consumer → verdict

| UFS consumer/property | HOS4.3 provider mapping | Fixed ACK / candidate consumer evidence | Verdict |
|---|---|---|---|
| PHY `vdda-phy-supply` | PM8150 L5 | Fixed ACK QMP UFS PHY has the SM8250 bulk supply name `vdda-phy` and load 89,900 µA; QMP probe obtains the bulk regulators and PHY power-on enables them before clocks. | **DIRECT static link** |
| PHY `vdda-pll-supply` | PM8150 L9 | Same QMP bulk table, `vdda-pll`, 18,800 µA; same bulk get/enable/disable sequence. | **DIRECT static link** |
| Host `vcc-supply` | PM8150 L17 | `ufshcd_parse_regulator_info()` parses `vcc`; UFS core obtains/enables/disables the regulator through its host-vreg path. | **DIRECT static link** |
| Host `vccq-supply` | PM8150 L6 | Parsed by the host platform layer; UFS core obtains it, applies load settings and toggles it. | **DIRECT static link** |
| Host `vccq2-supply` | PM8150 S4 | Parsed by the host platform layer; UFS core obtains it, applies load settings and toggles it. | **DIRECT static link** |
| Candidate `qcom,vddp-ref-clk-supply` | PM8150 L6 (same provider as `vccq-supply`) | ROUND140 §7.1 reports a candidate-only consumer at `drivers/ufs/host/ufs-qcom.c:1525`, `ufs_qcom_init_vddp_ref_clk()` (patch 06). This property is not consumed by the unpatched ACK baseline. The raw candidate source file was not separately published in the reviewed corpus, so this specific line is accepted as ROUND140 report evidence, not claimed as a fresh raw-file read in this review. | **REPORT-CONFIRMED; candidate-source readback still desirable** |
| Candidate `qcom,vccq-parent-supply` | PM8150L S8 provider label | ROUND140 §7.1 reports no consumer anywhere in the candidate; fixed ACK UFS platform parser only reads `vdd-hba`, `vcc`, `vccq`, `vccq2`. No S8 enable owner or sequencing consumer is established. | **PRESENT BUT INERT in reviewed candidate evidence** |
| HOS4.3 `vdd-hba-supply` | GCC `ufs_phy_gdsc` | Candidate deliberately omits the supply property and represents the GDSC through the host `power-domains` list. Fixed ACK's missing-supply path sets no vreg, logs “assuming enabled” and returns success. | **NON-FATAL parser path; hardware equivalence UNKNOWN** |

HOS4.3 provider mappings above are from ROUND139 §2.1, which resolved overlay fixups against the base FDT. The base FDT UFS nodes are disabled and have no supply properties; the nine DTBO entries add the consumer properties. ROUND139 reports the same eight overlay consumer edges in all nine entries. L6 is one provider referenced by both `vccq-supply` and `qcom,vddp-ref-clk-supply`; this is not two separate rails.

### 1.2 Driver lifecycle actually established by fixed ACK source

- `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c:1208-1211` declares the SM8250 QMP UFS PHY regulator bulk list: `vdda-phy` (89,900 µA) and `vdda-pll` (18,800 µA).
- The same file `:2126-2130` calls `devm_regulator_bulk_get_const()` during probe. `:1832-1854` enables the regulator bulk before enabling clocks; if clock enable fails, it disables the regulators. `:1894-1907` disables clocks and then the regulator bulk on power-off.
- `drivers/ufs/host/ufshcd-pltfrm.c:175-195` parses exactly `vdd-hba`, `vcc`, `vccq`, `vccq2`. `:181` is the HBA rail parse; `:185`, `:189`, `:193` are the three device rails.
- `drivers/ufs/core/ufshcd.c:9499-9537` implements regulator enable/disable; `:9540-9562` toggles VCC, VCCQ and VCCQ2; `:9565-9570` handles the HBA regulator; `:9590-9612` obtains the regulators.
- `drivers/ufs/core/ufshcd.c:10027-10045` and `:10054-10084` show UFS low-power / resume rail transitions and a VCC-on delay where the applicable quirk is set.

These code paths establish that the named properties can be consumed by the relevant generic drivers. They do not establish that the six PMIC rails have correct physical inputs, that the HOS4.3 power sequence is identical, or that any regulator was enabled on the target device.

### 1.3 Physical input parents — all six remain BLOCKED

ROUND139 §2.2 reports no `vin-supply`, `vph-pwr-supply`, `vdd-s<N>-supply`, `input-supply` or `vs-supply` declaration for the six rails in the inspected HOS4.3 base FDT and nine overlays. It explicitly classifies the physical parent of each rail as UNKNOWN:

- PM8150 L5 — UNKNOWN
- PM8150 L6 — UNKNOWN
- PM8150 L9 — UNKNOWN
- PM8150 L17 — UNKNOWN
- PM8150 S4 — UNKNOWN
- PM8150L S8 — UNKNOWN

The `parent-supply`-family properties found in the corpus are not interchangeable with board-level electrical input parents: ROUND139 decomposes them into GDSC-to-ARC and ARC provider-child relationships, plus self-proxy relationships. `qcom,vccq-parent-supply` is a consumer-side property pointing to S8, not proof of S8's own physical input. The candidate adds no guessed parent, fixed regulator or voltage.

**Smallest missing evidence:** an authoritative DBY-W09 HOS4.3 PMIC power-tree / schematic / board-specific netlist that identifies the actual input net and upstream source for each of L5/L6/L9/L17/S4/S8. Another generic Qualcomm DTS or an ARC edge is not a substitute.

## 2. Review B — MMCX / MX / GDSC and UFS multi-domain attachment

### 2.1 What the candidate wiring establishes

ROUND135 R3 §3.2 and ROUND140 §4.3 / §7.2 report the compiled candidate DTB host power-domain order as:
1. `qcom,sm8250-rpmhpd` / `RPMHPD_MMCX` (index 0);
2. `qcom,gcc-sm8250` / `UFS_PHY_GDSC` (index 1).

The UFS PHY retains the single GCC `UFS_PHY_GDSC` domain. The candidate also retains the host OPP table, both required-OPP references and both ICC paths. ROUND135 R3 reports its source and compiled-DTB assertions passed and that the candidate's UFS dual-domain driver attaches the list before `ufshcd_pltfrm_init()`.

The frozen dual-GenPD driver patch (blob `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`, `kernel-baseline/round61/patches/round33-checkpatch-clean.patch`) implements the following:
- validates the available OPP entries and the exact RPMh provider OPP table;
- calls `devm_pm_domain_attach_list()` with `PD_FLAG_DEV_LINK_ON`;
- requires exactly two attached domains;
- maps the UFS OPP's `required_dev` to `pd_list->pd_devs[0]` (MMCX), index 0.

The fixed ACK generic attach implementation in `drivers/base/power/common.c:193-275` iterates all `power-domains` entries. With `PD_FLAG_DEV_LINK_ON`, it adds `DL_FLAG_RPM_ACTIVE` to the device-link flags (lines 239-240), then creates links to each attached domain supplier (266-275). This proves the software attachment/link mechanism, not successful runtime RPMh transactions.

### 2.2 The selected SM8250 MMCX descriptor has no parent

Direct fixed-ACK source evidence:

- `drivers/pmdomain/qcom/rpmhpd.c:125-137`: the plain `mmcx` / `mmcx_ao` descriptors have no `.parent` member.
- `:139-153`: a separate `mmcx_w_cx_parent` descriptor exists, but its parent is `cx.pd` (and its AO peer points to `cx_ao.pd`).
- `:465-482`: the SM8250 descriptor table maps `RPMHPD_MMCX` to **`&mmcx`**, not `&mmcx_w_cx_parent`; it maps `RPMHPD_CX` to `&cx_w_mx_parent`, which is a separate descriptor with an MX parent.

Therefore, in this exact ACK source version, a vote on the candidate's SM8250 `RPMHPD_MMCX` does **not** acquire an MX parent vote through the selected MMCX descriptor. The existence of another MMCX descriptor variant, or matching numeric corner labels, does not alter the SM8250 mapping. The candidate's second GCC UFS PHY GDSC domain is a separate domain and does not supply the missing MMCX→MX parent edge.

### 2.3 What remains runtime-only

The candidate establishes a static two-domain attachment and associates its UFS required-OPP device with MMCX index 0. It does not establish:
- that the UFS OPP is actually selected or changed at runtime;
- that CMD-DB and RPMh requests complete;
- that MMCX transitions to the expected physical corner;
- that an MX vote is generated by the HOS4.3 ARC graph;
- that HOS4.3 ARC set/corner/dropout/proxy semantics are equivalent to the fixed ACK descriptor;
- that UFS PHY GDSC and MMCX transitions occur in the required order on hardware.

**Verdict:** candidate dual-domain source/DTB wiring is statically established; MMCX→MX runtime equivalence is **BLOCKED**.

**Smallest missing evidence:** an authoritative complete HOS4.3 ARC graph / descriptor map for the relevant resources, together with a device-matched runtime vote trace showing UFS OPP, MMCX and MX requests and their acknowledged transitions. No such trace is available in this review, and none was collected.

## 3. Review C — RAM placeholder, scan behavior and reserved-memory ownership

### 3.1 Zero-size `/memory` tuple

ROUND140 §4.3 reports the compiled candidate node as:

`/memory@80000000 reg = <0x0 0x80000000 0x0 0x0>`

This is a bootloader-filled placeholder, not a usable RAM range. Direct fixed-ACK source evidence in `drivers/of/fdt.c`:

- `:1034-1072`: `early_init_dt_scan_memory()` walks root subnodes, selects nodes with `device_type = "memory"`, reads `linux,usable-memory` or falls back to `reg`, decodes each address/size tuple, and executes `if (size == 0) continue;` at lines 1069-1072.
- `:1246-1263`: `early_init_dt_scan_nodes()` calls `early_init_dt_scan_memory()` before `early_init_dt_check_for_usable_mem_range()` and the KHO handover check.
- `:1265-1274`: `early_init_dt_scan()` verifies the FDT and then invokes `early_init_dt_scan_nodes()`.

Thus the candidate's zero-size tuple is skipped by this fixed ACK early memory scanner. It does not add usable RAM through that tuple. The candidate DTB alone is not a valid final RAM map. This finding does not prove what a final ABL-supplied FDT or another supported handoff route will contain.

### 3.2 Candidate 18 vs vendor FDT 37 reserved-memory children

ROUND140 §4.3 reports 18 direct children under the candidate `/reserved-memory`. ROUND138 §5 reports 37 direct children in the HOS4.3 vendor base FDT #0 and confirms the earlier live-directory count correction: `st_nlink=39` means 37 child directories, not 39. ROUND138 also reports that the nine overlays add no `/reserved-memory` node or `memory-region` property.

These are different FDT artifacts. **18 vs 37 is a reconciliation requirement, not proof that the candidate is defective.** Nor is it permission to copy all 37 vendor nodes blindly. The reviewed reports do not provide a complete candidate-vs-vendor per-node address/size/consumer ownership comparison. ROUND138's appendix lists vendor child names only and explicitly says per-child identity/values were unavailable from its existing live listing. Therefore no range-by-range equivalence is claimed here.

**Smallest missing evidence:** the actual final post-ABL FDT that is handed to Linux, including all `/memory/reg` tuples and every relevant `/reserved-memory/*/reg`, `no-map`, `reusable`, `memory-region` and consumer relationship. The capture must identify the FDT at the Linux entry point and the ABL/EFI/classic handoff route. Without this, RAM availability and reservation ownership stay BLOCKED.

## 4. Review D — ROUND140 Image hash attribution and dependency-fetch compliance

### 4.1 Image hash: certificate attribution is supported; BTF generalization is not closed

ROUND140 §3.3-3.4 reports:
- both Images are 44,820,992 bytes, but their SHA-256 differs;
- `.config` is byte-identical;
- the independently rebuilt board DTB is byte-identical to the R3 artifact, corrected SHA-256 `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e`;
- 1,072 bytes in `.init.data` differ at the generated module-signing certificate region;
- `.BTF` differs by 149 bytes (+136 type bytes, +13 string bytes), with downstream changes in `.BTF_ids`, `__stop_BTF`-derived offsets, two small code constants and the build-id note.

AI1's ROUND140 review §3.3 accepts the per-build generated X.509 module-signing certificate as a sound explanation for a per-build Image difference. It explicitly does **not** accept the stronger claim that BTF output is inherently nondeterministic or impossible to reproduce: the report lacks independently auditable pahole/BTFGen binary hash/version and the exact BTF-generation command. The reported BTF byte diff is a useful attribution hypothesis, not a fully proven toolchain-independent property.

The R3 explanation that the Image hash was staging-path-specific is not supported by ROUND140's reported byte comparison; `.debug_info` is byte-identical across the two staging roots. Do not carry forward the path-string explanation as established.

**Disposition:** do not use full Image SHA equality as the sole cross-root acceptance gate while the signing certificate is independently generated. Keep the exact R3 and R140 artifact hashes recorded. Keep the BTF sub-attribution **PARTIAL / UNRESOLVED** until existing provenance logs provide the pahole/BTFGen versions, binary identities and exact command line. No rebuild is authorized by this review.

**Smallest missing evidence:** the existing, sanitized ROUND135 and ROUND140 BTF generation provenance (tool version/hash, command line, environment inputs) and certificate-generation configuration/log. If those logs do not exist, mark the BTF explanation unresolved rather than recreating them with a new build.

### 4.2 External Kleaf dependency fetch: UNRESOLVED, not silently compliant

ROUND140 report §1 records: `external Kleaf repositories fetched at build time (mirror.bazel.build 200, github.com 200)`. AI1 ROUND140 review §3.4 notes that the ROUND140 taskbook had required stopping if the local dependency cache was insufficient.

The report does not identify:
- repository names or URLs beyond the two hosts;
- fetched byte counts;
- cache-hit / cache-miss status;
- whether HTTP 200 was metadata-only or actual dependency payload;
- which fetches, if any, were avoidable with the existing cache.

Therefore the evidence cannot distinguish COMPLIANT cache use / metadata access from a DEVIATION involving new dependency payload fetches. The correct classification is **UNRESOLVED**. This review did not access the Agent's private workspace or logs and did not retry any fetch.

**Smallest missing evidence:** an already-existing sanitized Bazel repository-fetch/cache log from ROUND140 showing repository identity, cache hit/miss, response type and bytes transferred. If that existing log is unavailable, the compliance question remains unresolved; do not rebuild or fetch again to investigate.

## 5. Other carried pre-boot blockers

- **DTBO variant:** ROUND138 maps entry 2 to VD / board-id 8206 / 0x200E and entry 8 to VG / 8298 / 0x206A. The old `ro.boot.dtbo_idx=2` capture is evidence of that boot's property only. The actual device DTBO partition hash/readback and ABL selection linkage are absent, so entry 2 remains CONDITIONAL.
- **Boot-v2 / FDT / ramdisk:** ROUND139 identifies a boot-v2 image with an embedded ramdisk, a separate `ramdisk` partition and a boot/recovery DTB section containing three FDTs plus a vendor MP_DATA tail. ABL's selected FDT, DTBO application policy and handling of the independent ramdisk remain UNKNOWN.
- **AVB:** ROUND139 reports structurally parseable vbmeta headers/descriptors, including a `vbmeta_cust` hashtree descriptor, but the `vbmeta_cust` footer points to an out-of-range vbmeta offset. Structural parsing is not cryptographic signature verification. `recovery_vbmeta` and `erecovery*` images were not among the eleven copied E1 images. Complete trusted-chain verification and footer provenance remain BLOCKED.
- **Recovery:** package images are not device partition backups. Complete device-matched original backups, partition-size reconciliation and a tested HOS4.3 restore route are absent. HOS4.2 reference material does not prove an HOS4.3 recovery route.

## 6. First-boot gate matrix

| # | Gate | Verdict | Evidence / reason | Smallest missing artifact to close |
|---:|---|---|---|---|
| 1 | 23-patch candidate identity | **PASS** | ROUND135 R3 and ROUND140 report exact candidate tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`; R3 reports 23/23 identities and tree match. | None for content-tree identity; retain the pinned manifest and logs. |
| 2 | Independent build and artifact identity | **CONDITIONAL** | ROUND140 build RC=0; .config and board DTB byte-identical; Image SHA differs. Certificate difference is supported; BTF toolchain attribution is incomplete. | Existing BTFGen/pahole version/hash and exact command logs; existing certificate-generation provenance. |
| 3 | UFS consumer/provider/driver links | **CONDITIONAL** | Host/PHY standard supplies resolve to providers and fixed ACK consumers. Candidate `vddp-ref-clk` consumer is report-confirmed; `vccq-parent` has no consumer. | Raw candidate `ufs-qcom.c` / patch blob for independent readback of the reported line 1525; no new code change. |
| 4 | Physical inputs for L5/L6/L9/L17/S4/S8 | **BLOCKED** | No authoritative physical input parent in HOS4.3 FDT/DTBO evidence; all six UNKNOWN. | DBY-W09 HOS4.3 PMIC power-tree / schematic / netlist. |
| 5 | S8 effective consumer and power sequencing | **BLOCKED** | `qcom,vccq-parent-supply` is present but inert in reviewed candidate evidence; no S8 consumer or effective enable owner/sequence established. | Actual candidate source consumer if one exists, plus authoritative S8 enable/sequence evidence; otherwise a device-matched runtime trace under separate authorization. |
| 6 | MMCX/MX runtime votes | **BLOCKED** | SM8250 maps MMCX to descriptor without parent; candidate OPP maps required_dev to MMCX; no HOS4.3 ARC/runtime equivalence trace. | Complete HOS4.3 ARC graph and device-matched CMD-DB/RPMh MMCX/MX vote trace. |
| 7 | Final post-ABL FDT and usable RAM tuples | **BLOCKED** | Candidate `/memory` size is zero and ACK skips zero-size tuples; no final ABL FDT or proven alternate handoff. | Exact final FDT handed to Linux plus boot handoff route and usable RAM tuples. |
| 8 | Reserved-memory ranges and ownership | **BLOCKED** | Candidate count 18 vs vendor base FDT count 37; counts alone do not prove defect; per-node range/consumer reconciliation missing. | Same final post-ABL FDT with every reservation range/flag and consumer ownership. |
| 9 | Device DTBO identity and selected entry | **CONDITIONAL** | `ro.boot.dtbo_idx=2` captured; entry 2 maps VD only if inspected package equals device DTBO partition. | Device-matched DTBO partition identity/hash and ABL selection evidence, only under separate authorization. |
| 10 | ABL boot-v2 DTB / independent ramdisk handling | **BLOCKED** | Boot-v2 layout and embedded/separate ramdisk facts exist; ABL selection/combination behavior unknown. | ABL source/spec or existing boot trace that identifies selected FDT, overlay and ramdisk handling. |
| 11 | AVB trusted verification and footer provenance | **BLOCKED** | Descriptor structure is not cryptographic verification; `vbmeta_cust` footer out of range; recovery/erecovery vbmeta artifacts absent. | Complete device-matched AVB image set, correct trusted-key chain and verified footer provenance. |
| 12 | Complete device-matched backups and tested HOS4.3 recovery route | **BLOCKED** | No complete current-partition backups or tested HOS4.3 restore route. | Complete device-matched original partition backup set and separately reviewed/reversible HOS4.3 recovery procedure. |
| 13 | First device boot authorization | **NOT AUTHORIZED** | Multiple hard gates remain BLOCKED/CONDITIONAL; this review has no authorization to touch or boot the device. | All hard gates closed, complete recovery/reversibility evidence, and a separate explicit user authorization. |

## 7. Final recommendation

**NOT READY — more offline evidence is needed.**

The candidate has a reproducible 23-patch content identity, an independently successful build, and a byte-identical board DTB. The UFS supply/driver relationships and dual-domain attachment are substantially understood at the static level. Those results do not close the physical PMIC inputs, S8 effective sequencing, MMCX/MX runtime behavior, final ABL RAM/FDT handoff, reservation ownership, boot-v2/DTBO/ramdisk selection, AVB trust/footer provenance or recovery gates.

The immediate offline follow-up should be limited to obtaining existing sanitized provenance logs for ROUND140 BTF generation and dependency-cache/fetch activity, plus authoritative board power-tree and complete boot/AVB/recovery artifacts if they already exist. Do not rebuild, fetch dependencies, access another Agent's private workspace or interact with the device as part of this review.

**No source-level defect is asserted solely from the current static evidence. No first boot is recommended or authorized.**

## 8. Evidence index and exact source identities

### Fixed ACK source (all fetched at commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`)

| Path | Relevant lines | Git blob SHA |
|---|---:|---|
| `drivers/of/fdt.c` | 1034-1072; 1246-1274 | `a931cd4beaaa6e3becc3692e3b4b8a0e42d6a691` |
| `drivers/ufs/host/ufshcd-pltfrm.c` | 175-195 | `5ac7afe759346debfc2910fb219d8e491ba08b64` |
| `drivers/ufs/core/ufshcd.c` | 9499-9612; 10027-10084 | `2cf7aa8e0a9472f9024d4251ac2f9d7da830e219` |
| `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c` | 1208-1211; 1832-1854; 1894-1907; 2126-2130 | `8af777f7ddd0385a6bb9d9b9563f0e6329699cd3` |
| `drivers/pmdomain/qcom/rpmhpd.c` | 125-153; 465-482 | `4c3cbf3abc7504cce3b8211c339b7ada03d65e38` |
| `drivers/base/power/common.c` | 193-275 | `6ecf9ce4a4e62bbc4861d5341971eec518b5c58b` |
| `include/linux/pm_domain.h` | 20-48; 548-550 | `f67a2cb7d7814859fd0657d44144a30d595bd6ed` |

### Candidate patch/report evidence

| Evidence | Branch/path | Blob SHA |
|---|---|---|
| Frozen dual-GenPD driver patch | `ai-parallel/stagea-port-until-boot:kernel-baseline/round61/patches/round33-checkpatch-clean.patch` | `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622` |
| ROUND135 23-patch manifest | `ai1/round130-stagea-ufs-lifecycle-integration:kernel-baseline/round135/ROUND135_23_PATCH_SERIES_MANIFEST.md` | `9188de2022f88c374bfcaa367c505428812608d9` |
| ROUND135 R3 final report | `firmware-audit-v1:firmware-analysis/round135/r3-validation/ROUND135_R3_FINAL_REPORT.txt` | `7b8dc971d752bbffc1bab08a185c2aa43b05d8f0` |
| ROUND138 DTBO/FDT audit | `firmware-audit-v1:firmware-analysis/round138/round138-dtbo-variant-and-live-fdt-delta-audit.md` | `2d712e01f96b724058122118122de2b9c10557dd` |
| ROUND139 HOS4.3 audit | `firmware-audit-v1:firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md` | `6704c0c871d651669c45814d21860f1e83db63c4` |
| AI1 ROUND139 review | `ai1/round130-stagea-ufs-lifecycle-integration:kernel-baseline/round139/AI1_ROUND139_INDEPENDENT_REVIEW_AND_ROUND140_SUPPLEMENT.md` | `ea18e2f4b419ff1593d5153822ff05c09ec9de05` |
| ROUND140 Agent report | `agent2/round140-independent-preboot-tests:firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md` | `719c5dafc0ae56a7eab1a5b588ee362c27e0ffc5` |
| AI1 ROUND140 review | `ai1/round130-stagea-ufs-lifecycle-integration:kernel-baseline/round140/AI1_ROUND140_INDEPENDENT_REVIEW_AND_ROUND141_DISPOSITION.md` | `2b2457bca761a29aa7dd170cb57d32918beebc49` |

The report intentionally does not reproduce device-unique values, memory addresses, secrets, firmware binaries or private Agent logs.

— END OF ROUND141 REVIEW —
