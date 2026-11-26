# ROUND158 — WorkBuddy Window B: Independent rootparam overlay variant and DTBO-container audit

- Executor: **WorkBuddy Window B (2号 Agent)**.
- Task type: **offline candidate-design experiment only**. No device, no ADB/root/fastboot, no partition read/write, no boot.img/vbmeta package, no flash/reboot/temporary boot, no signing/key extraction/AVB bypass, no source-tree or config modification.
- Window A's private workspace, logs and raw ABL were **not accessed**. All offline inputs came from Window B's own `r157-windowB` reconstruction plus the public repositories named in the taskbook.
- Overall verdict: **candidate `/rootparam` = PRESENT/EMPTY/NO-PHANDLE; P = PASS (host merge clean); Q = FAIL on candidate base / PASS only on an isolated one-symbol scratch base; DTBO container = internally self-consistent but not page-padded; module archive = packaging/build-graph gap, not `CONFIG_MODULES=n`.** No overlay in this report is asserted to be boot-ready or accepted by ABL.

---

## 0. Evidence grading

| Grade | Meaning |
|---|---|
| A | Directly measured this round: file hash, parsed FDT field, compiler/host-tool exit code, or config/rule text. |
| B | Public-repository evidence fetched verbatim this round; behaviour attributed to that external port, not to the user's HOS4.3 device. |
| C | Inference from A/B evidence; explicitly bounded. |

Honesty notes:

1. The two board IDs are kept as **separate labelled variants**. `0x200e` and `0x206a` are not merged into a single "chosen" overlay. The taskbook's HOS4.3 live Entry2 `0x200e` and Entry8 `0x206a` observations are identity candidates only; the ABL selector contract remains Window A's scope and is **UNRESOLVED** here.
2. Every value copied from `svesnav/linux-dby-w09` is marked **HOS4.2 reference evidence only**. That port reports a 6 GB HOS4.2.0.213 sample; the user's captured HOS4.3 target has 12 GB-class RAM windows, so neither the public values nor the public board ID are treated as correct for this target.
3. Host `fdtoverlay` results characterize **libfdt/dtc host behaviour only**. They do not prove ABL fragment ordering, fixup atomicity, or boot acceptance.

---

## 1. Candidate source-tree and compiled-DTB identity

All paths below are Window B's own artifacts; no Window A path was read.

| Item | Measured value | Grade |
|---|---|---|
| Candidate source tree (`git rev-parse HEAD^{tree}`) | `c56d93eafa35057d65176db6594d67d5144868a0` | A |
| Candidate HEAD | `bfbe3a32702575affe82768932dfcc1cf71ba346` | A |
| Board DTS tree blob | `patched-dts.blob` = candidate board DTS identity from ROUND157 | A (reused) |
| Compiled DTB | `r157-windowB/out-dtb/arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb` | A |
| DTB size / SHA-256 | 108,680 B / `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` | A |
| Kleaf build `.config` | SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`, 238,410 B | A |
| Kbuild DTB `.config` after `olddefconfig` | SHA-256 `efb663e9c792840e2cfbbc03e115996bb486aefe964b448c1717828c55bf042f` | A |
| FDT header | magic `0xd00dfeed`, totalsize 108,680 = file size, version 17, struct 105,500 B, strings 3,124 B | A |
| Tree counts | 905 nodes, 239 phandle properties | A |

The compiled DTB was not rebuilt in ROUND158; the ROUND157 file above was re-hashed and re-parsed in place.

---

## 2. Candidate `/rootparam` inspection

### 2.1 Compiled DTB

| Check | Result | Grade |
|---|---|---|
| `/rootparam` exists | **YES** | A |
| Property count | **0** — node is empty, not pre-populated | A |
| Children | 0 | A |
| `phandle` / `linux,phandle` on `/rootparam` | **NONE** | A |
| Any phandle whose target is `/rootparam` | **NONE** | A |
| `/__symbols__` | **absent** | A |
| `/__fixups__` | **absent** | A |
| `/__local_fixups__` | **absent** | A |

Root properties relevant to the public comparison:

| Property | Candidate compiled value |
|---|---|
| `model` | `"Huawei MatePad 11 (2021) DBY-W09"` |
| `compatible` | `"huawei,dby-w09", "qcom,sm8250"` |
| `qcom,msm-id` | `<356 0x20001>` |
| `qcom,board-id` | `<0 0>` |

### 2.2 Source lines

`arch/arm64/boot/dts/qcom/huawei-dby-w09.dts` in tree `c56d93ea`:

```
36	 * Local ROUND3 identity: MSM-ID [356, 131073] = SM8250 v2.1.
37	 * Keep the SoC DTB board-id at zero. The captured stock boot used DTBO
38	 * Entry 2 (dtbo_idx=2, board-id 0x200e); the earlier 0x206a/Entry 8
39	 * selection claim is withdrawn and the selection mechanism is UNKNOWN.
41	 qcom,msm-id = <QCOM_ID_SM8250 0x20001>;
42	 qcom,board-id = <0 0>;
56	 /*
57	  * The label is required by dby-w09-ack18-rootparam.dtso.draft.
58	  * Board identity values are populated by the matching DTBO. ...
62	  rootparam: rootparam {
63	  };
```

The DTS label `rootparam:` exists at line 62, but the compiled base contains no `__symbols__/rootparam`; therefore the label is **not externally bindable** in this base DTB. That is the root cause of the Q-form failure in §4.

---

## 3. Public HOS4.2 reference comparison

Source: `svesnav/linux-dby-w09` main branch at commit `116cb1fe06110543ce03217e8bd8f35c12ca89c3` (committer date `2026-11-02T17:39:36Z`).

| Fetched file | Bytes | SHA-256 |
|---|---:|---|
| `dby-w09-rootparam.dtso` | 841 | `755343e505f3d3971f90db341a03dc9d3d7ad90ee5b49296b88fd5fbffd3c584` |
| `pack_dtbo.py` | 1,032 | `383472692c966b14cb9f5856e3cf2ba0dbbebdaa5a6215658874df185c7b46a9` |
| `sm8250-huawei-dby-w09.dts` | 24,502 | `d2ee4d92e241ceddae237c84f93b4c73193194380252c0006e415770ff419e75` |

### 3.1 Public overlay, verbatim fields (all HOS4.2 reference evidence only)

| Location | Field | Public value | Notes |
|---|---|---|---|
| root | `model` | `"Huawei MatePad 11 (2021) DBY-W09"` | Identical to candidate root. HOS4.2 reference only. |
| root | `compatible` | `"huawei,dby-w09", "qcom,sm8250"` | Identical to candidate root. HOS4.2 reference only. |
| root | `qcom,board-id` | `<0x206a 0>` | Public HOS4.2 board selection. **Not adopted** for user's HOS4.3 target. |
| `fragment@0` | target | `<&rootparam>` | External phandle/label form. |
| `__overlay__` | `qcom,boardid` | `<0x08 0x02 0x09 0x08>` | Decimal digits 8298 = `0x206a`, per public comment. HOS4.2 reference only. |
| `__overlay__` | `qcom,board_name` | `"DBY_W09_VG"` | HOS4.2 reference only. |
| `__overlay__` | `qcom,product_name` | `"DBY-W09"` | HOS4.2 reference only. |
| `__overlay__` | `hardware_version` | `"SH1DBSLM"` | HOS4.2 reference only. |
| `__overlay__` | `huawei,modem_id` | `<0xffffffff 0x00>` | HOS4.2 reference only; candidate source comment says all nine stock entries use the same sentinel. |

The public base DTS (lines 30–51) pre-populates `/rootparam` with the same five fragment fields and uses `qcom,board-id = <0 0>`. This differs from the candidate base, which declares the empty labelled node and expects the DTBO to populate it.

### 3.2 Variant metadata derivation

For the labelled comparison variants:

| Variant | Root `qcom,board-id` | Fragment `qcom,boardid` | Basis |
|---|---|---|---|
| `0x200e` | `<0x200e 0>` | `<0x08 0x01 0x09 0x00>` | `0x200e` = decimal 8190 → digits 8/1/9/0, applying the public decimal-digit encoding. Grade C; selector contract unresolved. |
| `0x206a` | `<0x206a 0>` | `<0x08 0x02 0x09 0x08>` | Exact public HOS4.2 reference value. Grade B; not adopted as target truth. |

---

## 4. Offline overlay prototypes P and Q

All overlays were compiled with the ROUND157 Window B host `dtc` (`DTC 1.7.2-g52f07dcc`) and applied with the matching host `fdtoverlay`. No source tree or `.config` was changed.

### 4.1 Prototype P — `target-path = "/rootparam"`, no symbols/fixups

| Variant | DTS SHA-256 | DTBO bytes | DTBO SHA-256 | Header | Fragments | `__fixups__` | `__local_fixups__` |
|---|---|---:|---|---|---|---|---|
| `0x200e` | `8b7c94958972366d871f5d99ef9359f9351060ceb48e70a1ebe608740d2df02b` | 483 | `7c6f179a49ff3042642f050468e5a9ec76e21a552837d0e7fa3a50e155c64824` | magic `d00dfeed`, v17, totalsize=483 | 1 | absent (0 props) | absent |
| `0x206a` | `2f774a0c4ce6fb6d9e606b5acd9f1e93ba41793517140094bc2d00dd524d6727` | 483 | `03855c4447106f38020fc00c31a1fbd4ba52486dee5ba26584b59f4d618508ef` | magic `d00dfeed`, v17, totalsize=483 | 1 | absent (0 props) | absent |

Both fragments contain exactly one `target-path = "/rootparam"` and one `__overlay__` with the five public-reference rootparam fields. The `0x200e` file uses `qcom,boardid = <8 1 9 0>`; the `0x206a` file uses `<8 2 9 8>`. They are separate files.

#### Host merge against the candidate DTB

| Variant | `fdtoverlay` rc | Merged DTB size / SHA-256 | Changed properties | Unrelated changes |
|---|---:|---|---:|---:|
| `0x200e` | 0 | 108,876 / `4d833410dd4ccd59912e97f0f8da5e354d451fa6557b639f0b9146ab72d622ca` | 5, all under `/rootparam` | **0** |
| `0x206a` | 0 | 108,876 / `4c8394c1fb3bbe68fafc74bbe594c4a08a9e6f095a6f7a2178000806d0d531bc` | 5, all under `/rootparam` | **0** |

No nodes were added or removed. The only property changes are the five new `/rootparam` properties. Confirmed merged values:

```
0x200e: qcom,boardid = <8 1 9 0>; huawei,modem_id = <0xffffffff 0>;
        qcom,board_name = "DBY_W09_VG"; qcom,product_name = "DBY-W09";
        hardware_version = "SH1DBSLM"
0x206a: qcom,boardid = <8 2 9 8>;  (other four fields identical)
```

Important host-tool observation: the overlay root properties `model`, `compatible` and `qcom,board-id` are present in the DTBO FDT, but host `fdtoverlay` did **not** write them into the base root; the merged root still has `qcom,board-id = <0 0>`. The public port's claim that ABL copies these root properties over the base is therefore **not verifiable with this host tool** and is not adopted as an offline result.

### 4.2 Prototype Q — phandle target for comparison

| Variant | DTS SHA-256 | DTBO bytes | DTBO SHA-256 | Header | Fragments | Fixup dependency |
|---|---|---:|---|---|---|---|
| `0x200e` | `2bf452ea489471672a51c16db8570d9da71bf87eef17b32cc012c59721c680e9` | 536 | `ab5d55975f7063a44fa40d39bac344f34396e2754de801aa3a5baa0c23417aaf` | magic `d00dfeed`, v17, totalsize=536, compiled with `-@` | 1 | `/__fixups__/rootparam = "/fragment@0:target:0"` (1 prop) |
| `0x206a` | `81be121663540fb90c1d1f451b902cb5037fa6c51c4e556534a92ad04a4484f0` | 536 | `8005d2bb6402a77751b68842604f58a985f3ac8de09925f46f733121f97c66a2` | magic `d00dfeed`, v17, totalsize=536, compiled with `-@` | 1 | same single external fixup |

Both Q overlays use `target = <&rootparam>` and have `target = <0xffffffff>` placeholder plus one external-fixup entry. Neither has `__local_fixups__` in this minimal single-fragment case.

#### Merge against the candidate base: FAIL

Both variants returned rc=1 with the exact host message:

```
Failed to apply '...Q_rootparam_phandle_*.dtbo': FDT_ERR_BADOFFSET
base blob does not have a '/__symbols__' node, make sure you have compiled the base blob with '-@' option
```

No output DTB was created by these failed host runs. This is a host-tool result; it does **not** establish ABL atomicity or ABL failure semantics.

#### Merge against an isolated scratch base: PASS

A disposable scratch base was created from the ROUND157 decompiled DTS (SHA-256 `e0b6806139ec06eb78350f427f7e69ca314c969d09b13e2b5bc055d436cb641d`) by adding **exactly one** `phandle = <0x7fffffff>;` on `/rootparam` and **exactly one** symbol string `/__symbols__/rootparam = "/rootparam"`. No vendor 166-symbol stubs were added.

| Scratch artifact | Bytes | SHA-256 |
|---|---:|---|
| `scratch-base-symbols.dts` | 146,678 | `5aa104140cede4880578f2978474426f4e06b34b5f4a20f119e79d8457846150` |
| `scratch-base-symbols.dtb` | 108,750 | `7958e4af10c2991c05b690d2461dc10adbd3bdd06ab1178cb839b613761e415b` |

The scratch base has 906 nodes, 240 phandles, one symbol property, and `/rootparam` phandle `2147483647`.

| Variant | `fdtoverlay` rc | Merged DTB size / SHA-256 | Changed properties | Unrelated changes |
|---|---:|---|---:|---:|
| `0x200e` | 0 | 108,946 / `59918b4cdec7c511bf482140ffac969dd581f0eff4d06d61f4d792960c636519` | 5, all under `/rootparam` | **0** |
| `0x206a` | 0 | 108,946 / `1d44da8733f17fd47cc82f5d817924e7f2674465b156aa8830ac439a09e87bea` | 5, all under `/rootparam` | **0** |

Conclusion: Q is technically resolvable, but **only** when the base exports the label. The current candidate base does not. P is the only form that applies directly to the current candidate in host tools.

---

## 5. Android DTBO table container check

The public `pack_dtbo.py` logic was reimplemented for disposable artifacts. Each table contains exactly one overlay FDT.

| Table artifact | Bytes | SHA-256 | Embedded FDT |
|---|---:|---|---|
| `P_rootparam_target_path_200e.img` | 547 | `81c3401af6f02e7072c216c4edbcf27fb0d9f145b4a5c7865ab13ee38107e2b4` | 483 B P/200e DTBO |
| `P_rootparam_target_path_206a.img` | 547 | `828135e2ea0ca52a45c2b9c037bc46188cdb613c33431c25593d60efabf38c0d` | 483 B P/206a DTBO |
| `Q_rootparam_phandle_200e.img` | 600 | `1cc87943f552f01cc35c6fb79c498c29754151ff0778edb610c4ab8606e8018d` | 536 B Q/200e DTBO |
| `Q_rootparam_phandle_206a.img` | 600 | `eaf8e98176e84518cdb9fdd5261f2c7f92155c5f442af5fcf760feaabd1c2a4d` | 536 B Q/206a DTBO |

### 5.1 Parsed header/entry fields

Common header for all four tables:

```
magic = 0xD7B7AB1E
total_size = 64 + overlay_size
header_size = 32
dt_entry_size = 32
dt_entry_count = 1
dt_entries_offset = 32
page_size = 4096
reserved = 0
```

Common `dt_table_entry` (8 × big-endian u32):

```
dt_size = overlay_size (483 or 536)
dt_offset = 64
id = 0, rev = 0
custom[0..3] = 0,0,0,0
```

### 5.2 Check results

| Check | Result |
|---|---|
| Magic `0xD7B7AB1E` | PASS (4/4) |
| 32-byte header / 32-byte entry | PASS (4/4) |
| `entry_count = 1`, `entries_offset = 32` | PASS (4/4) |
| `total_size` equals actual file size | PASS (4/4) |
| Table end = 32 + 1×32 = 64, within `total_size` | PASS (4/4) |
| `dt_offset` equals table end | PASS (4/4) |
| `dt_offset + dt_size` equals file end | PASS (4/4) |
| Embedded FDT byte-identical to source overlay | PASS (4/4) |
| Header and entry re-serialize identically from parsed fields | PASS (4/4) |
| Board metadata consistency: root `qcom,board-id` vs fragment `qcom,boardid` digits | PASS (4/4): `0x200e` ↔ `<8 1 9 0>`, `0x206a` ↔ `<8 2 9 8>` |

Alignment detail, reported rather than treated as acceptance:

| Field | Value |
|---|---|
| `header_size % 4`, `dt_entry_size % 4`, `dt_entries_offset % 4`, `dt_offset % 4` | all 0 |
| `page_size` | 4096, power of two |
| `dt_offset % page_size` | 64 — **not page-aligned** |
| `total_size % page_size` | 547 or 600 — **not page-aligned** |

The reused public packer emits a compact container, not a 4096-padded partition image. The parser verifies internal consistency only. **ABL acceptance and the exact HOS4.3 selector contract are not asserted.** The selector contract is explicitly left to the Window A HOS4.3 ABL audit.

---

## 6. ROUND157 module archive / `Module.symvers` finding

Existing ROUND157 Window B evidence was reused; no full kernel build was rerun and no config/source file was edited.

### 6.1 Measured artifacts

| Artifact | Size | SHA-256 |
|---|---:|---|
| `modules_staging_dir.tar.gz` | 67 B | `2780920e5dbfbe103d03a583ed75345306e572ec5a48cb10361f046767d9f29a` |
| `Module.symvers` | 0 B | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Kleaf `.config` | 238,410 B | `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15` |

`tar -tzvf` shows the 67 B archive contains exactly one entry: `./`. The full `//common:dby_w09` build itself completed RC=0 in 625.011 s with 775 actions.

### 6.2 Root cause

1. The Kleaf build config is **not** `CONFIG_MODULES=n`; it contains `CONFIG_MODULES=y`.
2. It is **not** true that all drivers are built-in: the same config has **108** `=m` entries and **2,224** `=y` entries.
3. The actual cause is a **build-graph / packaging gap**: the `dby_w09` target declares `make_goals = ["Image"]` only.

Exact rule evidence:

```
common/BUILD.bazel:1354-1370
1354 kernel_build(
1355     name = "dby_w09",
...
1365     make_goals = [
1366         "Image",
1367     ],
1369     post_defconfig_fragments = ["arch/arm64/configs/dby_w09_storage_first.fragment"],
```

Kleaf's `kernel_build.bzl` behaves as follows:

```
build/kernel/kleaf/impl/kernel_build.bzl:1674-1683
1678   if grep -q "\bmodules\b" <<< "{make_goals}" ; then
1679       make ... INSTALL_MOD_PATH=... modules_install
1680   else
1681       # Workaround as this file is required, hence just produce a placeholder.
1682       touch {internal_outs_under_out_dir}
1683   fi

build/kernel/kleaf/impl/kernel_build.bzl:1834-1835
1834   # Archive modules_staging_dir
1835   tar czf {modules_staging_archive_self} -C {modules_staging_dir} .

build/kernel/kleaf/impl/kernel_build.bzl:1619-1627
1619   # If Module.symvers is requested in outs, and "modules" is not in make_goals ...
1622   if "modules" not in make_goals and "Module.symvers" in all_output_names_minus_modules:
1625       if [ ! -f ${OUT_DIR}/Module.symvers ]; then
1626           : > ${OUT_DIR}/Module.symvers
1627       fi
```

Because `modules` is absent from `make_goals`, `make modules_install` is skipped, the staging directory stays empty, and the placeholder `Module.symvers` is zero-filled before being archived/exported.

### 6.3 Storage-first drivers verified built-in

All symbols below are `=y` in the ROUND157 Kleaf `.config` (`0850213...`):

| Subsystem | Symbols |
|---|---|
| Core/SoC | `CONFIG_ARM64`, `CONFIG_ARCH_QCOM`, `CONFIG_OF`, `CONFIG_BLOCK`, `CONFIG_SCSI` |
| UFS | `CONFIG_BLK_DEV_SD`, `CONFIG_SCSI_UFSHCD`, `CONFIG_SCSI_UFSHCD_PLATFORM`, `CONFIG_SCSI_UFS_QCOM` |
| QMP PHY | `CONFIG_GENERIC_PHY`, `CONFIG_PHY_QCOM_QMP`, `CONFIG_PHY_QCOM_QMP_UFS` |
| Clocks/reset/PM | `CONFIG_COMMON_CLK`, `CONFIG_COMMON_CLK_QCOM`, `CONFIG_QCOM_CLK_RPMH`, `CONFIG_SM_GCC_8250`, `CONFIG_RESET_CONTROLLER`, `CONFIG_PM` |
| Interconnect | `CONFIG_INTERCONNECT`, `CONFIG_INTERCONNECT_QCOM`, `CONFIG_INTERCONNECT_QCOM_SM8250` |
| Regulators/RPMh | `CONFIG_QCOM_COMMAND_DB`, `CONFIG_QCOM_RPMH`, `CONFIG_QCOM_RPMHPD`, `CONFIG_REGULATOR`, `CONFIG_REGULATOR_QCOM_RPMH`, `CONFIG_REGULATOR_PROXY_CONSUMER` |
| IOMMU | `CONFIG_IOMMU_SUPPORT`, `CONFIG_ARM_SMMU` |
| First-stage mount | `CONFIG_BLK_DEV_DM`, `CONFIG_EROFS_FS`, `CONFIG_DM_VERITY`, `CONFIG_DM_VERITY_FEC` |

This confirms the early-boot dependency chain is built in; the empty module tar is not caused by those drivers being modular. ROUND158 did **not** edit the target, fragment or config to add `modules` to `make_goals`; any such change is a separate design decision.

---

## 7. Limitations and verdict

| Task | Verdict | Basis |
|---|---|---|
| Candidate `/rootparam` audit | PASS | Present, empty, no phandle; no symbols/fixups nodes in compiled DTB. |
| Public HOS4.2 comparison | PASS | Exact public fields fetched and hashed; all values labelled HOS4.2 reference only. |
| P target-path prototype | PASS (host only) | Applies cleanly to candidate DTB; 5 `/rootparam` properties added, 0 unrelated changes. |
| Q phandle prototype | PARTIAL | Compiles with 1 external fixup; fails on candidate base; passes only with isolated one-symbol scratch base. |
| DTBO table container | PASS (internal) | Magic/header/entry/bounds/reparse/metadata consistency all PASS; public packer leaves container non-page-padded. |
| Module archive explanation | PASS | `CONFIG_MODULES=y`, 108 modular entries; empty tar/Module.symvers explained by `make_goals=["Image"]` and Kleaf placeholder path. |
| Flash/boot readiness | **NOT ASSESSED** | No device access, no ABL acceptance proof, no selector contract proof, no boot.img/vbmeta, no signing. |

No overlay, table or container in this report is endorsed for flashing. The correct board-id metadata for the user's HOS4.3 target remains **UNDECIDED**; both `0x200e` and `0x206a` variants are archived as clearly labelled experiments only.

— END —
