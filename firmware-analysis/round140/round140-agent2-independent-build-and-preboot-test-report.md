# ROUND140 — 2号 Agent independent build reproduction and pre-boot test report

- **Executor:** 2号 Agent (second local execution agent). **Not** 2号 AI. **Not** the WorkBuddy Agent that executed ROUND139.
- **Dispatched by:** AI1 (ChatGPT); taskbook `firmware-analysis/round140/AGENT_TASKBOOK_AGENT2_INDEPENDENT_BUILD_AND_PREBOOT_TESTS.md` (blob `31b021efd41a`) plus supplement `ROUND140_SUPPLEMENT_AFTER_ROUND139.md`.
- **Device:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1 — **not connected, not accessed in any way.**
- **Kernel:** ACK `android17-6.18.33_r00`, pinned `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, root tree `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7`.
- **Candidate:** 23-patch series → content tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- **Mode:** offline, isolated, read-only with respect to sources. Build executed in a disposable staging owned by this round.
- **Date:** 2026-11-26 (local, GMT+8).

## 0. Result

| Field | Value |
|---|---|
| Stage A — source/patch identity | **PASS** — 23/23 patches applied in manifest order at their declared blob identities; tree17 `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`, tree23 `afe9517f8062b96bfeb5b4dd5714942861e6a44b` |
| Stage B — independent Kbuild DTB | **PASS (byte-identical)** — `108648` B, sha256 `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e`, `cmp` identical to the accepted R3 artifact |
| Stage B — independent Kleaf Image | **PARTIAL (attributed)** — build RC=0, `.config` byte-identical, System.map identical except the derived `__stop_BTF`; Image size identical, Image sha256 differs, every differing byte attributed to BTF emission + the per-build signing certificate |
| Stage C — ROUND138 cross-check | **PASS** — all five carried facts independently confirmed against the ROUND138 text |
| Stage C — ROUND139 cross-check | **PASS WITH TWO CORRECTIONS** — one consumer-path statement needs narrowing; the “seven header blocks” count does not reconcile with the inventory |
| Supplement — candidate UFS wiring vs ACK consumers | **PASS (static only)** — 7 of 8 HOS consumer edges reproduced in the candidate; `vdd-hba-supply` deliberately absent; `qcom,vccq-parent-supply` present but inert |
| **Overall** | **PARTIAL — SOURCE REPRODUCED, DTB REPRODUCED BYTE-EXACT, IMAGE HASH NOT REPRODUCIBLE BY CONSTRUCTION** |

This verdict is a build-reproduction statement only. It says nothing about device bootability, PMIC physical inputs, ABL behaviour, AVB validity or recovery readiness.

---

## 1. Execution identity and isolation

```
executor_role       = 2号 Agent (independent local build agent)
not_this_agent      = 2号 AI (independent reviewer) / WorkBuddy Agent (ROUND139 executor)
host                = WSL2 Linux 6.6.114.1-microsoft-standard-WSL2 x86_64 / Ubuntu 24.04.5 LTS
cpu                 = 12 threads, 7.8 GiB RAM, 2 GiB swap
disk                = 696 GiB free at build start
git                 = 2.43.0
kleaf_bazel         = prebuilts/kernel-build-tools/bazel/linux-x86_64/bazel -> bazel-8.7.0 (pre-existing, not installed)
toolchain           = prebuilts/clang/host/linux-x86/clang-r584948c — Android (15323222, +pgo, +bolt, +lto, +mlgo, based on r584948c) clang 22.0.1
jdk                 = prebuilts/jdk (used by Kleaf; no system java)
network             = external Kleaf repositories fetched at build time (mirror.bazel.build 200, github.com 200)
tools_installed     = none      tools_upgraded = none      firmware_downloaded = none
device_connected    = false     adb/fastboot/usb/serial/recovery/bootloader = untouched
source_modified     = false     23 patches / DTS / DTBO / config / Kconfig = unchanged
```

Round-private directories (nothing shared with ROUND135 or ROUND139):

| Purpose | Path |
|---|---|
| Independent tree | `/home/kerneldev/work/matepad11/round140-agent2/tree` |
| Patch input copy | `/home/kerneldev/work/matepad11/round140-agent2/patches` |
| Build staging | `/home/kerneldev/work/matepad11/round140-agent2/a30build` |
| Kleaf output root | `…/round140-agent2/a30build/out/bazel/output_user_root` (Kleaf default **inside this staging**) |
| Independent `O=` DTB build | `/home/kerneldev/work/matepad11/round140-agent2/out-dtb` |
| Logs | `/home/kerneldev/work/matepad11/round140-agent2/logs/` |

Disclosure: the default WSL distribution `Ubuntu` on this host is unusable (`Wsl/Service/CreateInstance/MountDisk/HCS/ERROR_PATH_NOT_FOUND`; its `ext4.vhdx` is absent). All work ran in `Ubuntu-24.04` (`D:\WSL\Ubuntu-24.04`), which is the distribution ROUND135 R3 also used. No repository, patch or report from any other agent was read from a private working directory.

---

## 2. Stage A — independent source / patch identity

### 2.1 Source object store and tree creation

```
source_object_store = /home/kerneldev/work/matepad11/ack-6.18.33-a30/.repo/projects/common.git
objects_symlink     = YES -> ../../project-objects/kernel/common.git/objects
src_HEAD            = 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a   (match = YES)
ack_root_tree       = 790a68ae6d4f4ac51ab2d88977b6fd5c031473b7   (match = YES)
method              = git init + git fetch --depth=1 file://<src> HEAD + git checkout --detach FETCH_HEAD
```

Rationale for the method (same constraint ROUND135 R2 documented): `git clone --local` refuses a symlinked `objects` directory, `--shared`/`--reference` would create an alternates file (violating the isolation rule), and a full-history transport clone of the 17 GB object store exceeds the round budget. The result is nevertheless an independent repository:

```
git_common_dir          = …/round140-agent2/tree/.git      (absolute; own repository)
alternates_file         = absent
is_shallow              = true                             (disclosed: history depth only)
in-pack objects         = 97291
initial status lines    = 0
submodules              = 0
initial branch          = detached HEAD at the pinned commit
```

### 2.2 The 23 patch inputs (identity re-verified before use)

Each patch was copied byte-for-byte from the ROUND135 R2 input set (`cp -a`, `copy_hash_mismatches=0`) and re-hashed. `IDENT_MATCH` compares `git hash-object` against the manifest blob.

| # | Patch (manifest path, basename) | git blob | sha256 (first 12) | bytes | check RC | apply RC |
|---:|---|---|---|---:|---:|---:|
| 01 | round36/0001-dt-bindings-ufs-allow-sm8250-dual-power-domains.patch.draft | `dad87ef8dfef` | `9bd87c76939d` | 1575 | 0 | 0 |
| 02 | round61/round52-0001-context-corrected.patch | `e47219d4a944` | `74ef372913a1` | 5093 | 0 | 0 |
| 03 | round61/round36-corrected-power-domain-range.patch | `79b00af90445` | `5b3dbd2f7624` | 1006 | 0 | 0 |
| 04 | round61/round32-corrected-sc7180-clock-names.patch | `2a038774ffac` | `f1fe33f0fb8f` | 1151 | 0 | 0 |
| 05 | round61/round33-checkpatch-clean.patch | `f1d54e5e0379` | `e95e2ee727ad` | 8481 | 0 | 0 |
| 06 | round61/round52-0002-checkpatch-clean.patch | `7e5df841b756` | `d3f9bc5294a4` | 4773 | 0 | 0 |
| 07 | round61/round63-0002-qmp-ufs-phy-binding.patch | `a6668eebe293` | `534412c3dba8` | 1152 | 0 | 0 |
| 08 | round61/round63-0001-phy-qcom-qmp-ufs-always-on.patch | `99fffb10603b` | `d33e1d405cc6` | 7402 | 0 | 0 |
| 09 | round61/round58-kleaf-target.patch | `dc8f4b5932f6` | `bd9f124ab9ac` | 8513 | 0 | 0 |
| 10 | round61/round31-0001-regulator-add-proxy-consumer.patch | `c7438eb8772c` | `38f8daf2cf24` | 14865 | 0 | 0 |
| 11 | round61/round31-0002-regulator-proxy-consumer-binding.patch | `d810e771bc16` | `1f89f0b7c1a5` | 2657 | 0 | 0 |
| 12 | round61/round31-0003-dby-w09-enable-proxy-consumer.patch | `2a486d066b8e` | `c55529184c29` | 1230 | 0 | 0 |
| 13 | round61/round32-0001-regulator-child-scoped-proxy-consumer.patch | `6b4f6d9969dd` | `9b47f5bf1259` | 14265 | 0 | 0 |
| 14 | round61/round32-0002-regulator-child-scoped-proxy-binding.patch | `ae349d95b011` | `30a1ee712348` | 2945 | 0 | 0 |
| 15 | round61/round32-0003-dby-w09-child-scoped-proxy-review-dts.patch | `14f0219736c0` | `3f524acc4bac` | 2625 | 0 | 0 |
| 16 | round61/round33-0001-regulator-proxy-self-target-only.patch | `3899e2b7ce7f` | `7b4858f5bf8f` | 3375 | 0 | 0 |
| 17 | round61/round33-0002-regulator-proxy-self-target-binding.patch | `d2e818296118` | `d19fb3b6ddf4` | 2848 | 0 | 0 |
| 18 | round135/series/18-round120-ufs-per-hba-async-join.patch | `f604c8672fcb` | `12efbe8a14d8` | 3242 | 0 | 0 |
| 19 | round135/series/19-round122-ufs-regulator-load-first.patch | `64dd2ad90222` | `2f335f513fd1` | 2339 | 0 | 0 |
| 20 | round135/series/20-round128-qmp-ufs-dual-rail-v2.patch | `22ccec1cabf2` | `53ef42bb997a` | 11114 | 0 | 0 |
| 21 | round135/series/21-round126-proxy-consumer-load-first.patch | `c180dbf45840` | `eae21b96d34e` | 2252 | 0 | 0 |
| 22 | round135/series/22-round135-huawei-dby-w09-real-dts.patch | `ab0108364c83` | `c88d4fdb4a14` | 15986 | 0 | 0 |
| 23 | round135/series/23-round135-huawei-dby-w09-dtb-makefile.patch | `ceb72ed206d9` | `cf9536d807ff` | 542 | 0 | 0 |

`23/23 IDENT_MATCH=YES`, `46/46` applier invocations returned 0, `23/23` `git diff --check` returned 0. No fuzz flag, no reject file, no fallback applier, no manual edit.

### 2.3 Content-tree gates

```
patch 17 applied → TREE17 = 77e2b2b1515b3813f7538aedffe4c5a4e90edb57   TREE17_MATCH = YES
patch 23 applied → TREE23 = afe9517f8062b96bfeb5b4dd5714942861e6a44b   TREE23_MATCH = YES
board DTS blob   = 58293f7a62a50f8109886c92ce4b9cd14d7980e2  (15437 B)  MATCH = YES
Makefile entry   = 282:dtb-$(CONFIG_ARCH_QCOM)<TAB>+= huawei-dby-w09.dtb
changed_paths    = 20   diff --check RC = 0   HEAD after apply = 8ad08f75…
```

The 20 changed paths are the expected overlay: `BUILD.bazel`, 4 binding YAMLs, the qcom `Makefile`, `dby-w09-proxy-review.dts`, `huawei-dby-w09.dts`, the config fragment, 5 driver sources (`phy-qcom-qmp-ufs.c`, `regulator/{core,proxy-consumer}.c`, `ufshcd.c`, `ufs-qcom.c`), 2 headers, plus `drivers/regulator/{Kconfig,Makefile}` and `ufshcd-priv.h`/`ufs-qcom.h`.

### 2.4 Controlled offsets reproduced exactly

| Patch | Hunk | Result | Offset |
|---|---|---|---|
| 16 (regulator proxy self-target) | #1 / #2 / #3 | succeeded at 187 / 244 / 274 | **−25 / −2 / +2** |
| 17 (proxy self-target binding) | #1 / #2 | succeeded at 119 / 149 | **+1 / −2** |
| 20 (QMP UFS dual-rail v2) | #3 | succeeded at 2310 | **−19** |
| all other 20 patches | — | primary applier emitted no offset line | 0 |

Identical to the ROUND135 accepted-offset record. Offsets are recorded, not “zero”: `git apply` reports block displacement when the surrounding context has moved; no hunk needed fuzz (content matched exactly at the shifted position).

---

## 3. Stage B — independent Kleaf build

### 3.1 Staging construction and build-input proof

Kleaf needs the whole ACK workspace skeleton (`build/`, `prebuilts/` 21 GB, `external/`, `devices/`, `tools/`). The staging is therefore a **hardlink** copy of the pinned workspace top level excluding `common/`, `out*/` and its `bazel-*` symlinks, plus a hardlink copy of **this round's** tree into `common/`:

```
staging_common HEAD        = 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
staging_common HEAD^{tree} = 790a68ae6d4f4ac51ab2d88977b6fd5c031473b7
staging_common .git        = …/round140-agent2/a30build/common/.git   (this round's repository)
build_input_tree23         = afe9517f8062b96bfeb5b4dd5714942861e6a44b
BUILD_INPUT_TREE_MATCH     = YES
```

The last line is the proof that the build consumed the independently reproduced tree and not a copied artifact. No ROUND135 output root, action cache or artifact was used as an input; the staging owns its own `out/`.

### 3.2 Build

```
command   : tools/bazel build //common:dby_w09 --jobs=2
BUILD_RC  = 0
elapsed   : bazel 415.014 s (critical path 380.73 s); wall 419 s
actions   : 775 total (523 internal, 252 linux-sandbox)
targets   : bazel-bin/common/dby_w09/{.config,Image,System.map,vmlinux}
```

### 3.3 Artifact comparison against the ROUND135 R3 baseline

| Artifact | This round (bytes / sha256) | ROUND135 R3 record | Verdict |
|---|---|---|---|
| `.config` | 238410 / `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15` | same | **IDENTICAL** — `cmp` against the R3 copy exits 0 |
| `Image` | 44820992 / `a0f39ee8c992d554824af86c5abbf3f22bb32f324578fc78bde761f8ee7b969c` | 44820992 / `ee94c4fa0364018244d4aa467dcc4318a816b53363a25b3b717acb6a002e82c6` | **size identical, hash differs** — fully attributed in §3.4 |
| `System.map` | 7611571 / `a952852a7f29b29bb6079386c7c60ee643e8e7c2c04a636c1be3a30ad3079900` | 7611571 / `a7a597bef4228c018b3f465949c8bc1327254ff8f9e06058fccf71d63e90ee2c` | **3 bytes differ**, one range: the `__stop_BTF` symbol value |
| `vmlinux` | 230259072 / `c0e9329744ced3609d71a3a11ba89c783ac6d946844f1ab3391422ab99287faa` | 230259072 / `efac6aed109aa1b97bfbed47962092ffa1399fe72d2c8dfd88cce3c3d2b169d8` | **8 of 60 ELF sections differ** — see §3.4 |

### 3.4 Image hash difference — byte-level attribution

The ROUND135 R3 report explained the Image hash as “staging-path-specific (embedded path strings)”. **My measurements do not support that explanation**, and the corrected attribution matters because it decides whether the Image hash can ever be a reproducibility gate.

Per-section SHA-256 comparison of the two `vmlinux` files (60 sections each, identical section set):

| Section | Size (B) | Differing bytes | Where | Reading |
|---|---:|---:|---|---|
| `.text` | 20 414 464 | **2** | `0xffffffc080336e31..32` = `btf_parse_vmlinux+0x49` | one instruction immediate trailing the BTF change |
| `.init.text` | 462 356 | **3** | `0xffffffc082392728..2b` = `btf_vmlinux_init+0x10` | same class |
| `.rodata` | 8 308 763 | **2** | `0xffffffc081921cdc..dd` inside `kallsyms_offsets` | the kallsyms relative-offset entry for `__stop_BTF` (0x2359ce5 vs 0x2359d7a) |
| `.init.data` | 184 872 | **1072** | starting `__module_cert_start+0xf` | the **build-time auto-generated kernel signing certificate** (`CN = Build time autogenerated kernel key`) |
| `.BTF_ids` | 4 616 | **2280** (836 × 2-byte cells) | entire table | BTF type-ID numbering |
| `.notes` | 84 | **20** | `_note_41` (build-id) | derived hash of the differing content |
| `.symtab` | 10 852 632 | **2** | one entry | `__stop_BTF` |
| `.BTF` | 7 404 773 vs 7 404 922 | n/a | whole section | +136 type bytes, +13 string bytes |
| **all other 52 sections** | — | **0** | — | includes `.data`, `__ksymtab`, `__ksymtab_strings`, and **`.debug_info` (132 333 875 B, byte-identical)** |

Chain of causation, established from the data rather than assumed:

1. `.debug_info` is byte-identical across two different staging roots. Absolute paths are therefore **not** embedded (Kleaf normalises them), and source, flags and toolchain are identical. The “embedded path strings” explanation is refuted.
2. `.BTF` still differs: `type_len` +136, `str_len` +13; the only string-set difference is that the R3 build carries one extra name, `ro_image_end` (a parameter name of the arm64 BPF JIT trampoline helper), absent from mine. Consequence: `__stop_BTF` moves by exactly +149 (`0x95`), which equals the BTF size delta.
3. That single move propagates into the kallsyms offset entry (2 B), the symtab entry (2 B), the `.BTF_ids` table (2280 B), two BTF-related code constants (2 B + 3 B) and the derived build-id note (20 B).
4. Independently of BTF, `.init.data` carries a **per-build generated X.509 certificate** for module signing, which differs on every build by construction (1072 B).

**Conclusion:** the Image/`vmlinux` digest is not a valid cross-root reproducibility oracle for this target — it cannot be satisfied by any independent rebuild of the identical tree, because (a) the signing certificate is generated per build and (b) BTF type emission is not byte-stable across build roots. The meaningful, path- and build-independent oracles are: `.config` identity, `System.map` symbol identity, DTB byte identity, and per-section identity of everything except `.BTF*`, `.init.data` cert region, `.notes` and the two derived offsets. All four hold.

No `--fuzz`, no patching, no workaround was applied to make hashes agree, and nothing was substituted for the missing digest match.

---

## 4. Stage B4 — independent board DTB build and structural inspection

### 4.1 Build

```
src_tree        = this round's tree (content tree afe9517f…)
config_source   = this round's Kleaf product bazel-bin/common/dby_w09/.config
O=              = …/round140-agent2/out-dtb        (independent, created by this script)
command         = make -C <tree> O=<out-dtb> ARCH=arm64 LLVM=1 qcom/huawei-dby-w09.dtb
pinned clang    = prebuilts/clang/host/linux-x86/clang-r584948c
DTB_BUILD_RC    = 0   (3 s; host dtc built from scripts/dtc)
olddefconfig RC = 0
```

### 4.2 Identity — and a documentation defect in the accepted baseline

```
dtb_size        = 108648                     expected 108648              MATCH
dtb_sha256      = cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e
taskbook/R3 record = cab82fe3901dbb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e
```

The two strings differ **only** by a transposition at positions 11–12 (`bd` ↔ `db`). This round resolved which is correct by hashing the accepted artifacts themselves:

```
ROUND135 R3 out-dtbA/…/huawei-dby-w09.dtb      cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e
ROUND135 R3 out-dtbs-fullA/…/huawei-dby-w09.dtb cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e
this round  out-dtb/…/huawei-dby-w09.dtb        cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e
cmp (R3 artifact, this artifact)               IDENTICAL
```

**Finding D-1 (documentation, not a build defect):** the digest published in ROUND135 R3 §4 and copied into the ROUND140 taskbook §1 is a two-character transcription error. The accepted artifact and this round's independent rebuild are **byte-identical** at `cab82fe3901bdb4…`. Because both R3 copies and my build agree, the product is not in doubt; only the recorded string is. AI1 should re-issue the value; this report does not edit the taskbook.

### 4.3 Structural checks on this round's DTB (independent checker, stdlib only)

Header / limits:

```
magic               = 0xd00dfeed          totalsize = 108648 = file size (no padding)
totalsize <= 2 MiB  = OK (Documentation/arch/arm64/booting.rst:53-54)
off_dt_struct       = 56      %4 = 0
off_dt_strings      = 105524  %4 = 0
off_mem_rsvmap      = 40      %8 = 0
version             = 17      last_comp_version = 16
nodes               = 905     phandles = 239
duplicate node path = none    duplicate phandle value = none
unresolved phandle / 0xffffffff placeholder in typed phandle properties = none
FDT_END reached, node stack balanced at depth 0
```

Storage-node assertions (all from the compiled DTB, not from source text):

| Assertion | Result |
|---|---|
| exactly one `ufshc@1d84000`, `compatible = qcom,sm8250-ufshc`, `status = okay` | PASS |
| host `power-domains` = 2 entries: (`0x34`,`0x06`) → `qcom,sm8250-rpmhpd` **RPMHPD_MMCX**; (`0x30`,`0x04`) → `qcom,gcc-sm8250` **UFS_PHY_GDSC** | PASS |
| the two domain providers are distinct nodes | PASS |
| exactly one UFS PHY `phy@1d87000`, `compatible = qcom,sm8250-qmp-ufs-phy`, `status = okay` | PASS |
| PHY `power-domains` = 1 entry → `qcom,gcc-sm8250` **UFS_PHY_GDSC** | PASS |
| host `operating-points-v2` → `/soc@0/ufshc@1d84000/opp-table` | PASS |
| OPP table has 2 available entries; `opp-37500000 → required-opps` → rpmhpd `opp3`, `opp-level 0x40`; `opp-300000000 → required-opps` → rpmhpd `opp6`, `opp-level 0x100` | PASS |
| both `required-opps` targets are children of the provider's own OPP table | PASS |
| host `interconnects` = 2 paths: `aggre1_noc(MASTER_UFS_MEM,0) → mc_virt(SLAVE_EBI_CH0,0)`; `gem_noc(MASTER_AMPSS_M0,0) → config_noc(SLAVE_UFS_MEM_CFG,0)`; names `ufs-ddr`, `cpu-ufs` | PASS |
| `dtc -I dtb -O dts` decompile | RC 0, **6159 lines** (R3 recorded 6159) |
| dtc warnings | 32 pre-existing base-tree diagnostics (30 × `unique_unit_address`, 2 × `avoid_unnecessary_addr_size`) — recorded verbatim, not “fixed” |

Two observations that must be carried into the matrix, not treated as defects:

- `/memory@80000000` `reg = <0x0 0x80000000 0x0 0x0>` — **size zero**. The candidate DTB carries a bootloader-filled placeholder, exactly as the manifest warned. Nothing in this round may be read as a RAM map.
- the candidate DTB has **18** `/reserved-memory` direct children, whereas the vendor base FDT (ROUND138) has **37**. These are different artifacts (ACK-built tree vs HOS4.3 vendor FDT); no equivalence is claimed and the difference is left as an open item for the memory gate.

---

## 5. Stage C1 — ROUND138 carried facts, independently checked

Each fact the taskbook ordered to be adopted was re-read in the ROUND138 text and checked for internal support.

| Carried fact | ROUND138 location | Independent verdict |
|---|---|---|
| entry 2 = VD / board-id 8206 / 0x200E | §1.4 row 2, §1.2, §2.2, §3.1 | supported (decimal/hex/payload cross-consistent) |
| entry 8 = VG / board-id 8298 / 0x206A | §1.4 row 8, §1.2, §2.2 | supported |
| `ro.boot.dtbo_idx=2` makes entry 2 a *conditional* stronger reference; DTBO partition hash absent | §4, §7 F1 | supported; the report explicitly withholds confirmation |
| nine overlays reach `/rootparam` through `__fixups__`; no literal node | §2.1 items 1–2, §2.3 | supported (0 literal nodes; one fixup each, all resolved) |
| entry 2 and entry 8 identical for UFS/PMIC/regulator/RPMh/power-domain payload | §3, §3.3 | supported (142 identical fragments; differences limited to `/rootparam` identity and the Wi-Fi pubfile) |
| 39 is `st_nlink` → 37 children; base FDT also 37 | §5.1–§5.3 | supported; AI1's kernfs rule (`fs/kernfs/inode.c`, `subdirs + 2`) is consistent with this pinned tree |

No ROUND138 statement was found overstated within its own scope. One boundary worth restating: ROUND138's 37 applies to the **vendor base FDT**; the candidate DTB built here has 18 reserved-memory children (§4.3). The two numbers describe different files and must never be compared as a delta.

---

## 6. Stage C2 — ROUND139 cross-check (report now delivered)

ROUND139 report: `firmware-audit-v1:firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md`, 53 055 B, blob `6704c0c871d6`; AI1 review blob per its own header. Both were read in full before Stage C. ROUND139's PARTIAL verdict and its input limitations are adopted as given; no firmware was re-scanned and no device was touched.

### 6.1 Items that hold up under independent logic review

- The six UFS rails resolve to L5 / L6 / L9 / L17 / S4 / S8 across all nine entries, and the base FDT contributes no supply property at all (§2.1 of ROUND139). The distinction between the ARC level regulators and the VRM rails (§2.3 “naming traps”) is essential and correctly drawn — `regulator-pm8150a-s4-level` is not `regulator-pm8150-s4`.
- Physical input parents: zero `vin-supply` / `vph-pwr-supply` / `vdd-s*-supply`; the 31 parent-like occurrences decompose exactly into 26 GDSC-form + 5 ARC provider-child edges (§2.2, §2.3). No guessed parent is introduced anywhere.
- The three-FDT + 173-byte `MP_DATA` composition of the boot DTB section, and the consequence that E7's base candidate is FDT #0 only (§3.1 D1-a), is a genuine scope correction and is stated with the right caveat.
- `vbmeta_cust`: the offset-0 blob is structurally parseable and declares `SHA256_RSA2048` with a `cust` hashtree descriptor; the footer points out of range; provenance UNKNOWN (§3.2). The report does **not** claim signature verification — consistent with AI1's terminology rule.

### 6.2 Correction 1 — “no code path reads `qcom,vddp-ref-clk-supply`” is true only of *stock* ACK

ROUND139 §2.4 states: “No code path in the pinned tree reads `qcom,vccq-parent-supply` or `qcom,vddp-ref-clk-supply`.” That is correct for the unpatched pinned tree, but it is not the whole picture for the candidate this round reproduces:

- The **candidate** tree (23 patches) contains a real consumer: `drivers/ufs/host/ufs-qcom.c:1525` (`ufs_qcom_init_vddp_ref_clk()`, property guard at `:1531-1534`), guarded by `of_device_is_compatible(dev->of_node, "qcom,sm8250-ufshc")` **and** `of_find_property(dev->of_node, "qcom,vddp-ref-clk-supply")`, reading `qcom,vddp-ref-clk-max-microamp` and doing `devm_regulator_get(dev, "qcom,vddp-ref-clk")`.
- That code arrives with frozen patch **06** (`round52-0002-checkpatch-clean.patch`, 20 hits on `vddp_ref_clk`), not with stock ACK.
- `qcom,vccq-parent-supply` remains without any consumer — the only occurrences in the whole tree are comments in the board DTS. ROUND139's statement is accurate **for this property**.

So the precise statement is: stock ACK consumes neither; the candidate consumes `qcom,vddp-ref-clk-supply` and not `qcom,vccq-parent-supply`. ROUND139's sentence should be scoped to “pinned ACK source (unpatched)” so that a later reader does not conclude the candidate's L6 REF_CLK link is inert.

### 6.3 Correction 2 — “all seven header blocks” does not reconcile with the inventory

ROUND139 §3.2 reports rollback-index/key-metadata observations for “all seven header blocks”, while its own table lists **six** standalone vbmeta images. The exact E1 inventory (ROUND139 Appendix B, 11 files) decomposes as:

| Class | Count | Files |
|---|---:|---|
| standalone vbmeta (AVB0 + footer, own partition) | **6** | `vbmeta.img`, `vbmeta_system.img`, `vbmeta_vendor.img`, `vbmeta_odm.img`, `vbmeta_hw_product.img`, `vbmeta_cust.img` |
| AVB hash-descriptor images (vbmeta header block derived from the footer) | **5** | `boot.img`, `ramdisk.img`, `dtbo.img`, `recovery.img`, `recovery_ramdisk.img` |
| total E1 images | **11** | — |

Neither 6 nor 11 equals 7. The only self-consistent readings are “six standalone vbmeta header blocks” or “eleven images carrying AVB structures”; “seven” is not derivable from the report's own table, and this round cannot invent a seventh file. **Finding D-2 (report consistency):** the count should be corrected to the explicit list above. This is a wording/count defect only — it has no bearing on any descriptor, and nothing here suggests an AVB bypass.

### 6.4 Items adopted unchanged

Physical input parents (all six rails) stay UNKNOWN; runtime OPP/RPMh/CMD-DB votes stay UNKNOWN; ABL DTB acceptance, ramdisk consumption and `/rootparam` application stay UNKNOWN; selected DTBO entry stays CONDITIONAL (entry 2); AVB coverage for absent `recovery_vbmeta`/`erecovery*` images stays NOT FOUND; HOS4.3 recovery stays BLOCKED. No “package image available” was promoted to “recovery route exists”.

---

## 7. Supplement — candidate DTB / DTS UFS wiring vs pinned ACK consumers

Scope: the exact independent tree of §2 and the DTB of §4. Static declarations and source-level consumers only. No runtime inference.

### 7.1 What the candidate actually declares (compiled DTB, host `ufshc@1d84000`, `status = okay`)

| Property | Present | Resolved provider (candidate DTB) | Provider `status` | ACK consumer? |
|---|---|---|---|---|
| `vcc-supply` | yes | `/soc@0/rsc@18200000/regulators-0/ldo17` (`regulator-name = pm8150_l17`) | absent → enabled | **yes** — `ufshcd-pltfrm.c:185` |
| `vccq-supply` | yes | `…/regulators-0/ldo6` (`pm8150_l6`) | absent → enabled | **yes** — `ufshcd-pltfrm.c:189` |
| `vccq2-supply` | yes | `…/regulators-0/smps4` (`pm8150_s4`) | absent → enabled | **yes** — `ufshcd-pltfrm.c:193` |
| `vdd-hba-supply` | **absent** | — | — | conditioned — `ufshcd-pltfrm.c:181` (see §7.4) |
| `qcom,vddp-ref-clk-supply` | yes | `…/regulators-0/ldo6` (`pm8150_l6`, same node as `vccq`) | absent → enabled | **yes, in the candidate** — `ufs-qcom.c:1525` (patch 06) |
| `qcom,vccq-parent-supply` | yes | `…/regulators-1/smps8` (`pm8150l_s8`, group `qcom,pm8150l-rpmh-regulators`) | absent → enabled | **no consumer anywhere** |
| `vcc-voltage-level`, `*-max-microamp` | yes | — | — | read by `ufshcd-pltfrm.c` (`max_uA`), values 800000 / 210000 / 100 |

PHY `phy@1d87000`, `status = okay`:

| Property | Present | Resolved provider | ACK consumer? |
|---|---|---|---|
| `vdda-phy-supply` | yes | `…/regulators-0/ldo5` (`pm8150_l5`) | **yes** — `phy-qcom-qmp-ufs.c:1212-1215` (`sm8250_ufsphy_vreg_l`: `vdda-phy` 89900 µA) |
| `vdda-pll-supply` | yes | `…/regulators-0/ldo9` (`pm8150_l9`) | **yes** — same table (`vdda-pll`, 18800 µA) |
| `vdda-phy-always-on` | yes | — | **yes** — `phy-qcom-qmp-ufs.c:1137` flag, patch 08 |

Both regulators are children of ACK-style per-PMIC groups (`qcom,pm8150-rpmh-regulators`, `qcom,pm8150l-rpmh-regulators`), i.e. the candidate expresses the HOS rail topology in the upstream provider model.

### 7.2 Performance-domain / OPP / ICC (candidate) vs pinned ACK baseline

| Element | Candidate DTB | Pinned ACK `sm8250.dtsi` baseline | Delta |
|---|---|---|---|
| host `power-domains` | 2: rpmhpd **MMCX** (0x6), gcc **UFS_PHY_GDSC** (0x4) | 1: gcc **UFS_PHY_GDSC** (`:2519`) | **+MMCX, ordered index 0** — introduced by board DTS (patch 22) |
| PHY `power-domains` | 1: gcc **UFS_PHY_GDSC** | 1: gcc **UFS_PHY_GDSC** (`:2593`) | none |
| host OPP | `operating-points-v2` → own `opp-table`, 2 entries | same shape (`:2542-2577`) | inherited, untouched by the board overlay |
| `required-opps` | 37.5 MHz → rpmhpd `opp3` level `0x40`; 300 MHz → `opp6` level `0x100` | `rpmhpd_opp_low_svs` / `rpmhpd_opp_nom` | inherited; symbol↔level identity confirmed in the compiled DTB |
| ICC | 2 paths (aggre1_noc→mc_virt; gem_noc→config_noc), names `ufs-ddr`, `cpu-ufs` | identical (`:2544-2547`) | none |
| legacy `qcom,msm-bus` | absent | absent | — |

Every phandle in these properties resolves to an existing node (§4.3); no placeholder or dangling reference exists. The **only** structural delta against the ACK baseline is the added MMCX domain entry, which is precisely the candidate's design intent.

### 7.3 What this does not prove

A static DTB cannot show that MMCX is voted, that the corner actually transitions 37.5 → 300 MHz, that CMD-DB/RPMh handshakes complete, that any regulator is enabled at runtime, or that the UFS link starts. Nothing in this section may be cited as such evidence.

### 7.4 The `vdd-hba-supply` decision, stated precisely

HOS4.3 resolves `vdd-hba-supply` to `ufs_phy_gdsc`. The candidate **deliberately omits** it, with an in-source rationale at `huawei-dby-w09.dts:252-253`: the same GDSC is now expressed as a `power-domains` entry, and it “is not a regulator”. Consequence at the code level:

- If `vdd-hba-supply` is present, `ufshcd_parse_regulator_info()` (`ufshcd-pltfrm.c:181`) would obtain it as a fixed regulator.
- If absent, `ufshcd_populate_vreg()` (`:121-155`) logs “Unable to find vdd-hba-supply regulator, assuming enabled”, sets no regulator and **returns 0** — probe does not fail.

So the omission is coherent and non-fatal in the pinned code, and the GDSC dependency is re-expressed through the domain API. It is still a **deliberate deviation from the HOS4.3 board contract**, and whether the resulting domain transition satisfies the hardware is a runtime question that remains open.

---

## 8. First-boot gate matrix

| Gate | Question | Verdict | Basis |
|---|---|---|---|
| Candidate source identity | 23 patches replayed to the exact tree SHA? | **PASS** | tree17 `77e2b2b1…`, tree23 `afe9517f…`, 46/46 RC=0 |
| Image / DTB reproduction | independently built and identified? | **PARTIAL** | DTB byte-identical; `.config` identical; Image hash differs by construction (§3.4) — attribution complete, cross-root byte reproducibility not achievable |
| Final FDT / RAM | post-ABL FDT bytes, `/memory` reg tuples, reserved-memory identity/values, handoff route? | **BLOCKED** | candidate `/memory` size = 0 placeholder; 18 vs 37 reserved-memory children; no post-ABL capture; ROUND139 §2/§3 unchanged |
| DTBO variant | device DTBO partition readback + actual selection? | **CONDITIONAL** | `ro.boot.dtbo_idx=2` only; no partition hash; entry 2 = VD / 8206 conditional |
| PMIC physical inputs | authoritative physical input parent per UFS rail? | **BLOCKED** | zero `vin`/`vph-pwr`/`vdd-s*` in the corpus; six rails UNKNOWN; the candidate adds none |
| UFS performance domain | MMCX/MX, CMD DB, RPMh request and actual runtime vote? | **BLOCKED** | candidate wiring verified (MMCX + GDSC, OPP/required-OPP, ICC) but static only; ACK MMCX descriptor has no parent |
| Boot-v2 / ramdisk / DTBO | real ABL consumption rules, embedded stock ramdisk handling, DTBO selection? | **BLOCKED** | ROUND139 §3.3: all UNKNOWN |
| AVB | complete, unambiguous descriptor/chain interpretation and a legal boot path? | **BLOCKED** | 11 images only; `recovery_vbmeta`/`erecovery*` absent; `vbmeta_cust` footer out of range; signature validity unverified |
| Recovery | tested HOS4.3 recovery route and complete device-matched backups? | **BLOCKED** | package images ≠ device dumps; no tested route |
| First device boot | all hard gates closed **and** explicit user authorization? | **NOT AUTHORIZED** | device never touched by this round |

No missing item was upgraded with “should”, “usually” or “same model”. Every UNKNOWN stays UNKNOWN.

---

## 9. Failures, not-run items and limitations

| # | Item | Status |
|---|---|---|
| L-1 | Default WSL distro `Ubuntu` unusable (`ext4.vhdx` missing, `ERROR_PATH_NOT_FOUND`); work done in `Ubuntu-24.04` | disclosed, no impact |
| L-2 | Patches copied from the ROUND135 R2 input set rather than re-downloaded from GitHub | hashes re-verified against the manifest, 0 mismatches |
| L-3 | Tree is a `--depth=1` fetch (shallow) | history depth irrelevant to content-tree identity; disclosed |
| L-4 | `dtbs_check` **NOT RUN** — python `dtschema` is not installed and installing tools is forbidden | recorded as NOT RUN, not PASS |
| L-5 | `checkpatch` / SPDX / host regression / object compiles | out of this round's scope (not requested by ROUND140 §3–§5) |
| L-6 | dtc emits 32 base-tree warnings on decompile | pre-existing, RC 0, recorded verbatim |
| L-7 | Image / `vmlinux` SHA mismatch vs R3 | attributed, not “fixed” (§3.4) |
| L-8 | Published DTB digest contains a transposition (D-1) | artifact verified byte-identical; record needs AI1 correction |
| L-9 | ROUND139 “seven header blocks” (D-2) | cannot be reconciled with 6 standalone vbmeta / 11 images |
| L-10 | ROUND139 “no code path reads `vddp-ref-clk`” | true of stock ACK only; the candidate consumes it via patch 06 (§6.2) |

---

## 10. What this round closes, and what it does not

**Closed by this round**

1. Independent reproduction of the 23-patch source identity, including the intermediate tree17 gate and all controlled offsets.
2. Independent Kleaf build of `//common:dby_w09` from that tree, proven by the build-input tree digest, with a byte-identical `.config`.
3. **Byte-identical reproduction of the accepted board DTB**, and correction of the digest recorded for it.
4. Full attribution of the Image/`vmlinux` digest difference, which retires that digest as a reproducibility gate and replaces it with four gates that do hold.
5. Static verification of the candidate's UFS wiring — supplies, providers, power domains, OPP/required-OPP, ICC — with every phandle resolved, plus a source-level consumer verdict for each property.
6. Two corrections to ROUND139's record, neither of which changes any descriptor, rail or gate.

**Still open (unchanged)**

UFS runtime votes and corner transitions; physical input parents for L5/L6/L9/L17/S4/S8; ABL DTB/DTBO/ramdisk behaviour; post-ABL FDT and RAM map; AVB cryptographic validity and `vbmeta_cust` footer provenance; device-matched backups and a tested HOS4.3 recovery route; **first boot — NOT AUTHORIZED**.

**No first-boot readiness is declared.** Build success is not bootability, and this report says so explicitly.

---

## 11. Deliverable and readback

- Report: `firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md`
- Branch: `agent2/round140-independent-preboot-tests`
- Only this sanitised Markdown is uploaded. No binary, image, DTB, key, certificate, signature or firmware is included.
- Upload method: GitHub Contents API on the existing branch; commit SHA, blob SHA and a byte-for-byte raw readback are recorded in §12 after the upload.

## 12. Upload record

(to be filled from the upload response and the raw readback)

— END OF REPORT —
