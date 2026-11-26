# ROUND158 — Independent Rootparam / Fastboot-Boot Gate Review

- Reviewer: 2号 AI（独立审查）
- Target: Huawei MatePad 11 DBY-W09 / SM8250
- Review date: 2026-11-27
- Scope: correct ROUND157 source coverage; integrate ROUND157 build results; compare public same-model rootparam/DTBO and fastboot-boot reports against exact HOS4.3 target evidence.
- Method: GitHub report/source read only. No local build, source edit, DTB/DTBO/boot image generation, device interaction, ADB, fastboot, recovery, partition read/write, reboot, signing or key operation.
- Final disposition: **offline kernel build PASS; isolated offline rootparam DTBO experiment CONDITIONAL GO; integrated boot-v2 boot.img + DTBO package NO-GO; temporary boot NO-GO; partition write HARD NO-GO.**

## 0. Executive summary

ROUND158 changes one important part of the ROUND157 picture, but it does not authorize booting or flashing:

1. **Correction:** the AI1 ROUND156 integration report exists at the exact branch/path now supplied by the taskbook. ROUND157 AI2's “missing/unavailable” statement was a branch/path lookup miss. The report was fetched and read in this review. The conservative safety conclusions from ROUND157 are not invalidated by this correction.
2. **Kernel build gate:** Window B completed the exact Kleaf target with RC=0 on source tree `c56d93eafa35057d65176db6594d67d5144868a0`. Window A's RC=1 was an independently evidenced host OOM killing `pahole` during BTF generation, not a source compile error. Therefore the **offline source/build gate is now PASS**, with the qualification that Window A did not complete a second full build.
3. **Public rootparam evidence:** the public `svesnav/linux-dby-w09` project explicitly says its ABL requires a DTBO entry to populate `/rootparam`, and documents `fastboot boot` (RAM boot) as refused. Its published `dby-w09-rootparam.dtso` uses `qcom,board-id = <0x206a 0>` and a particular set of Huawei rootparam properties. A separate MatePad Kubuntu deployment guide is explicitly based on HarmonyOS 4.2 and describes a 5.45-GiB/6-GB-class configuration. These are meaningful same-model reports, **not proof of the same HOS4.3 boot contract**.
4. **Target mismatch is material:** our direct target is HOS 4.3.0.196(C00E100), 12-GB-class live RAM (12,185 MiB windows / about 11.7 GiB MemTotal), with live `androidboot.dtbo_idx=2` and selected stock Entry 2 board-id `0x200e`. Entry 8 / `0x206a` was not the selected live entry. Public `0x206a` values must not be transplanted.
5. The exact HOS4.3 ABL has not yet been shown to require the same `/rootparam` values, use the same DTBO table-selection metadata, or reject `fastboot boot`. Those remain unknown. That uncertainty supports a **host-only experiment**, not an integrated boot package or device test.

## 1. Correction to ROUND157: AI1 report exists

The required AI1 report was fetched from the exact taskbook reference:

- Branch: `ai1/round130-stagea-ufs-lifecycle-integration`
- Path: `kernel-baseline/round156/AI1_ROUND156_DELIVERY_REVIEW_AND_ROUND157_PLAN.md`
- Link: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round156/AI1_ROUND156_DELIVERY_REVIEW_AND_ROUND157_PLAN.md

It records the pinned ACK `android17-6.18.33_r00` commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`, the frozen 23-patch tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`, and the RAM-patched candidate tree `c56d93eafa35057d65176db6594d67d5144868a0`. It summarizes the exact ABL selector/overlay findings and Window B's three candidate DTB variants.

**Correction statement:** ROUND157's assertion that the AI1 ROUND156 integration report could not be found was incorrect. It resulted from looking in the wrong branch/path. This review has read the report at the taskbook's exact location. No evidence supports interpreting that earlier lookup miss as an absent AI1 delivery.

## 2. ROUND157 build evidence — source/build gate is passed

All three exact ROUND157 reports were read:

- AI1 ROUND156 integration report (link in §1).
- Window A: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round157-primary-build-abl-final-proof/firmware-analysis/round157/WORKBUDDY_A_ROUND157_PRIMARY_KERNEL_BUILD_AND_ABL_FINAL_PROOF_REPORT.md
- Window B: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round157-independent-build-repro/firmware-analysis/round157/WORKBUDDY_B_ROUND157_INDEPENDENT_KERNEL_BUILD_REPRODUCTION_REPORT.md
- Previous AI2: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round157-integrated-firstboot-go-no-go/firmware-analysis/round157/AI2_ROUND157_INTEGRATED_FIRST_BOOT_GO_NO_GO_REPORT.md

### 2.1 Window A — environmental failure, not source failure

Window A used the prescribed command:

```sh
tools/bazel build //common:dby_w09 --jobs=2
```

It exited RC=1 after 546.545 seconds. The first real failure was during BTF generation: `pahole` was killed, and host `dmesg` recorded the OOM killer selecting `pahole` with approximately 5.26 GB anonymous RSS. No declared full-build outputs (`Image`, `vmlinux`, `System.map`, packaged DTB) were produced by that failed build. Window A did not retry with changed memory/jobs.

Window A independently verified the RAM-patched source tree `c56d93ea…`, patch identity, and a same-source/same-config/same-toolchain DTB rebuild. That DTB was 108,680 bytes and byte-identical to the frozen candidate:
- SHA-256: `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60`.

### 2.2 Window B — full Kleaf build succeeded

Window B independently reconstructed the same RAM/comment patch from the published R154 patch and verified the exact source tree:
- Build input tree: `c56d93eafa35057d65176db6594d67d5144868a0`
- Command: `tools/bazel build //common:dby_w09 --jobs=2`
- **RC=0**, 775 actions, 625.011 seconds.
- Fresh isolated output root; the report records a newly populated action cache and no network fetches during the build.
- `.config` SHA-256: `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`.
- `Image`: 44,820,992 bytes; SHA-256 `f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21`.
- `vmlinux`: 230,259,072 bytes; SHA-256 `d47e9a71d58747afa69468fa5afea3c06775fb32b7b144c0c6df796b7eb543e8`.
- `System.map`: 7,611,571 bytes; SHA-256 `7f01a12037a367466b8d2bad83ce1e0df191e3137ae81c08367fb16102705f44`.

Window B's separately rebuilt board DTB, using the same source and configuration, was also byte-identical to the R156 candidate: 108,680 bytes, SHA-256 `9d0d7600…fed60`; 905 nodes, 239 phandles, three RAM tuples, 18 reserved-memory children, and UFS/PHY dependency closure passed. `/chosen` exists but has zero properties. The Kleaf target does not expose a named board DTB output, so this DTB was built in a separate Kbuild output directory from the same tree/config; the report explicitly records that distinction.

**Build gate decision: PASS.** At least one complete formal Kleaf build has succeeded on the accepted exact source tree, and its DTB was independently validated. Window A's OOM is an environmental failure, not evidence of a source defect. This does not prove two independent full builds succeeded: Window A did not complete.

Qualification: Window B reports `Module.symvers` is zero bytes and its module staging archive contains no loadable modules. Its build-generated signing certificate is also unique to that build. Do not treat that autogenerated certificate as an established device-trusted signing identity or infer that the output is a flash-ready package.

## 3. Public same-model rootparam / DTBO / fastboot evidence

### 3.1 svesnav/linux-dby-w09

Public project:
- Repository: https://github.com/svesnav/linux-dby-w09
- README: https://github.com/svesnav/linux-dby-w09/blob/main/README.md
- Rootparam overlay: https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso
- DTBO packer: https://github.com/svesnav/linux-dby-w09/blob/main/pack_dtbo.py

The README states two bootloader rules for that project:
- The DTBO entry applied by Huawei ABL must fill `/rootparam` like its stock board overlay; otherwise the tablet returns to fastboot.
- `fastboot boot` (RAM boot) is refused, so their tests flash partitions.

The same README describes a mainline Linux 7.0 DBY-W09 project, with a boot flow using a header-v2 `boot` image and a separate `ramdisk` partition. This is useful same-model implementation evidence, but it is not the user's Android 17 / HOS4.3 package.

Its `dby-w09-rootparam.dtso` contains:
- Root properties: `model = "Huawei MatePad 11 (2021) DBY-W09"`, `compatible = "huawei,dby-w09", "qcom,sm8250"`, and `qcom,board-id = <0x206a 0>`.
- A fragment targeting `<&rootparam>` and setting `qcom,boardid = <0x08 0x02 0x09 0x08>`, `qcom,board_name = "DBY_W09_VG"`, `qcom,product_name = "DBY-W09"`, `hardware_version = "SH1DBSLM"`, and `huawei,modem_id = <0xffffffff 0x00>`.

The public packer creates a one-entry Android DT table with zero-valued entry id/rev/custom fields. That is evidence of how that project's own bundle is formed; it does **not** prove that a zero-metadata one-entry table is accepted by the user's HOS4.3 ABL or matches the target's stock DTBO selection contract.

### 3.2 Anglerfish314/matepad11-dby-w09-kubuntu

Public guide:
https://github.com/Anglerfish314/matepad11-dby-w09-kubuntu/blob/main/README.md

The guide explicitly describes a HarmonyOS 4.2-based deployment. It independently documents `qcom,board-id = <0x206a 0x0>` as required in that deployment and lists a 5.45-GiB usable-memory limitation, consistent with a 6-GB-class device. It also documents a different, highly modified installation/recovery path that replaces HarmonyOS. Its observations must not be conflated with the user's HOS4.3.0.196 / 12-GB-class target.

### 3.3 Evidence grade

These projects provide **same-model, other-firmware implementation evidence**:
- Strong enough to justify investigating `/rootparam` as a possible ABL acceptance gate.
- Strong enough to record that at least one public DBY-W09 implementation reports RAM boot refusal.
- Not strong enough to establish the same requirement, values, selector metadata, or fastboot policy for the exact HOS4.3 ABL.

The hierarchy remains: exact HOS4.3 target captures/ABL > same-target independent reports > same-model other-firmware public implementation > general inference.

## 4. Public firmware and hardware values must not be transplanted

| Dimension | Public rootparam/guide context | User's direct target evidence | Consequence |
|---|---|---|---|
| Firmware | Public guide explicitly based on HOS 4.2; 6-GB-class example | HOS 4.3.0.196(C00E100) | ABL policy and DTBO contract may differ |
| RAM | 5.45 GiB usable / 6-GB-class sample | 12,185 MiB live windows; about 11.7 GiB MemTotal | Do not copy public RAM assumptions |
| Board ID | `0x206a 0` in public rootparam DT overlay | Live selected stock Entry 2 board-id `0x200e` | Do not replace target ID with `0x206a` |
| DTBO entry | Public implementation describes a required rootparam overlay | Live `androidboot.dtbo_idx=2`, selected stock Entry 2 | Public Entry metadata/index is not target selection proof |
| Other stock entry | Public project uses `0x206a` | Entry 8 / `0x206a` was not selected in the target live boot | `0x206a` is not a substitute for target Entry 2 |
| ABL identity | Other-firmware public implementation | Exact HOS4.3 ABL payload SHA-256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` | Exact target ABL remains the authoritative object |

The target's `androidboot.dtbo_idx=2` is an observed selector output. Earlier exact-ABL work found that `androidboot.dtbo_idx` is emitted by the selector, not read as a selector input. Therefore setting a command-line value or copying a public DTBO index does not select the target overlay.

## 5. Independent technical assessment

### 5.1 Is `/rootparam` a target requirement?

**Unknown for HOS4.3.** Public reports make it a credible hypothesis. The ROUND157 target reports do not establish:
- whether the exact candidate base DTB contains a `/rootparam` node;
- whether that node has the same properties, address/path, or phandle behavior as the public project's base;
- whether exact HOS4.3 ABL explicitly validates `/rootparam` for every selected DTBO entry;
- whether the requirement is tied to a specific selected entry, board variant, firmware generation, or later Huawei handoff;
- whether the public rootparam values are read from its own stock overlay/base or are specific to a different board/firmware build.

No target-derived rootparam values should be guessed.

### 5.2 Overlay mechanics create an additional compatibility concern

The public DTSO uses `target = <&rootparam>`, which normally requires an external symbol fixup against the base DTB's `__symbols__`. The ROUND155/156 candidate reports say the candidate base has no `__symbols__`, and the stock Entry 2 was observed to contain 166 external fixups that were not bindable against that candidate. Thus the public source file is **not directly transplantable** into the current candidate merely because the model name matches.

A target-path fragment could avoid the external symbol lookup, but only if the exact target candidate really contains the intended `/rootparam` path and the exact ABL accepts that fragment form in this context. Exact ABL support for target-path was found in ROUND156; that does not prove the node exists or that a rootparam overlay passes the complete HOS4.3 selector and acceptance checks.

### 5.3 DTBO selection metadata remains unresolved

The public packer emits a single-entry table whose id/rev/custom fields are zero. Its DTSO separately places `qcom,board-id=<0x206a 0>` in the overlay FDT root. Those are different layers of metadata. The public script is not evidence that the target ABL selects DTBO entries using those same fields or accepts the same one-entry table.

Before any integrated package design, exact target evidence is still needed for:
- the HOS4.3 stock DTBO table header and entry metadata;
- the selector's actual matching fields and chosen entry;
- whether the target expects a particular index/order/count;
- how the candidate base DTB's root tags and selected overlay's rootparam data interact.

### 5.4 Other boot-chain gates remain open

ROUND157's integrated review still applies:
- ABL actively rebuilds `/memory/reg`; the exact setter primitive and final runtime result are not proven.
- UFDT overlay failure is non-fatal in the traced flow, but transactional/atomic rollback is not proven. A later fragment failure could leave partial mutation.
- Candidate `/chosen` is empty; bootargs, initrd boundaries, and other required handoff values/order are not fully specified.
- Boot-v2 permits a single-FDT path, but exact candidate msm-id/board-id/PMIC matching and package header/entry contract are not all demonstrated.
- AOSP AVB flag semantics do not prove Huawei OEM acceptance. Exact Huawei signature/key/rollback ordering, TA/TZ checks and Huawei digest policy remain unresolved. No trusted signing/acceptance path has been demonstrated.

## 6. Separate GO / NO-GO decisions

| Activity | Decision | Independent assessment |
|---|---|---|
| 1. Offline kernel build | **PASS** | Window B completed the full prescribed Kleaf target RC=0 on exact tree `c56d93ea…`; Window A's OOM is environmental. The source/build gate is passed for offline kernel artifact validation. |
| 2. Minimal rootparam DTBO experiment | **CONDITIONAL GO — host-only, isolated** | Useful to test FDT overlay structure, target-path vs symbol-based targeting, property payload, table serialization and negative cases. First obtain target-derived `/rootparam` node/properties and exact HOS4.3 DTBO selection metadata. Do not copy `0x206a` or public rootparam values. No experiment artifact was generated in this review. |
| 3. Integrated boot-v2 boot.img + DTBO package | **NO-GO** | Rootparam content/requirement, selector index and board/PMIC matching, DTBO table contract, runtime RAM rewrite, `/chosen` handoff, overlay mutation behavior, Huawei AVB/TZ/OEM digest acceptance and exact boot-v2 package contract are not closed. Do not assemble or label a package bootable/flashable. |
| 4. Temporary boot | **NO-GO** | Public same-model README says `fastboot boot` is refused, but that is other-firmware evidence. Exact HOS4.3 ABL command handling and acceptance are unresolved. There is no positive exact-target proof that temporary boot is supported; no attempt is authorized. |
| 5. Partition write | **HARD NO-GO** | Device is A-only; four named root-chain targets (`vbmeta_odm`, `eng_vendor`, `eng_system`, `version`) are absent from the 18-image capture list; complete GPT geometry and rollback metadata are missing; no exact-stock restoration route or rehearsal is proven; AVB/OEM acceptance is unresolved. |
| 6. Next delegation | **Narrow offline evidence tasks only** | See §7. No device actions or package construction should be delegated. |

## 7. Smallest next delegation plan

### Window A — 1号 Agent (exact target ABL owner)

Request a narrowly scoped offline ABL supplement using the already captured HOS4.3 ABL:
1. Locate and decode any explicit `/rootparam` validation/copy/use path, including call sites, property names, failure branch and whether it is unconditional or selected-entry-specific.
2. Decode DTBO table selection metadata and the exact relationship among stock Entry 2, board-id `0x200e`, DTBO table fields and the live `dtbo_idx=2` output.
3. Inspect the exact fastboot command dispatcher / RAM-boot path to determine whether `fastboot boot` is rejected, unsupported, or potentially accepted on this HOS4.3 ABL. Report raw instruction/string/xref evidence and confidence; do not issue a command.
4. Close the already-open `/memory/reg` setter and UFDT partial-mutation questions if the same ABL functions cover them.

### Window B — 2号 Agent (separate independent WorkBuddy window)

After Window A supplies target-derived values and the exact table contract, request a **host-only** independent experiment:
1. Verify candidate base `/rootparam` presence and schema.
2. Build only a minimal test overlay/table in an isolated scratch workspace, with no target-device operation and no boot.img packaging.
3. Test both positive and negative structural cases (missing property, wrong value, wrong table metadata, wrong target path) and record hashes/tool versions.
4. Independently review whether the public symbol-targeting DTSO can work against the candidate's symbol-free base, or whether a verified target-path design is required.

Do not ask Window B to guess target values from the public `0x206a` example.

### 2号 AI — independent integration reviewer

After A/B reports are published, retrieve and compare the exact artifacts/reports, update the evidence matrix and separate GO/NO-GO decisions, and verify any final report readback. 2号 AI is the reviewer/integrator; it is not Window B and should not claim to own Window A's private workspace or raw ABL analysis.

## 8. Partition-write blockers retained from ROUND157

ROUND155/157 backup evidence is strong for the 18 captured images but does not form a proven recovery plan:
- `vbmeta_odm`, `eng_vendor`, `eng_system`, `version` are absent from the 18-image capture set.
- Full GPT geometry (start, size, type and mapping), boot-control state and stored rollback-index metadata remain missing.
- A complete exact-stock firmware package/hash manifest and image-to-partition mapping remain missing.
- Device is A-only; there is no demonstrated alternate-slot fallback.
- Recovery/eRecovery images were captured, but capture does not prove entry/reachability or restoration ability.
- No verified stock restoration procedure, complete-set restoration rehearsal, or user-data preservation/data-loss plan is established.
- No verified Huawei AVB/OEM signing or acceptance route exists for the proposed modified package.

These are independent blockers; solving rootparam alone would not make a write safe.

## 9. Final disposition and stop conditions

- **Offline kernel build:** PASS.
- **Offline minimal rootparam DTBO experiment:** CONDITIONAL GO, host-only and only after exact target values/selection contract are established.
- **Integrated boot-v2 boot.img + DTBO package:** NO-GO.
- **Temporary boot:** NO-GO.
- **Partition write:** HARD NO-GO.

No device interaction, ADB, fastboot, recovery, reboot, partition operation, source build, boot.img/DTBO generation, signing, key extraction, AVB modification or flash was performed in this review.

**STOP — ROUND158 independent evidence review only.**
