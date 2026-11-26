# ROUND157 — WorkBuddy Window A: Primary Kernel Build and Final ABL Proof

- Executor: **WorkBuddy Window A (1号 Agent)**, continuing from its own ROUND154 RAM-patched source tree and ROUND155 local ABL/XBL capture.
- Window B is a separate WorkBuddy chat and was **not accessed**. No `round154-windowB`, `round155-windowB`, `r156-windowB` or other Window-B path was read or used as a build input.
- Task type: **offline primary full kernel build + narrowly scoped offline ABL control-flow supplement**. No device, no ADB, no partition read/write, no boot.img packaging, no flash, no reboot, no fastboot, no recovery, no signing, no vbmeta/flag change, no key extraction.
- Overall verdict: **A = FAIL (environmental OOM, not a source defect); B = PASS (rebuilt DTB byte-identical to R154, structure verified); C = PARTIAL (raw words reported where the hand decoder has gaps); D = PASS (patch archived).** The RAM gate from ROUND156 remains **CONDITIONAL / not waived**.

---

## 0. Evidence grading and honesty notes

| Grade | Meaning |
|---|---|
| A | Directly observed this round: command output, hash, byte comparison, or decoded control-flow branch. |
| B | Implementation-level string/xref evidence in the exact local ABL PE; not a fully decoded instruction path. |
| C | Report-derived (ROUND151/154/156) or inference; explicitly labelled as such. |

Honesty notes, stated up front because they bound every conclusion below:

1. **The formal full build did not complete.** `tools/bazel build //common:dby_w09 --jobs=2` exited **1** at 546.545 s. The first real failure is an **out-of-memory kill of `pahole`** during BTF generation on `vmlinux.unstripped`, confirmed by kernel `dmesg`. Per the taskbook ("If full build fails, classify the first real failure. Do not patch unrelated code or start an unrequested extra build") I did **not** retry with different jobs/memory, did not edit unrelated code, and did not launch any second build. No `Image`, `vmlinux`, `System.map`, `Module.symvers`, module-signing certificate or packaged DTB was produced by the failed full build.
2. Because no packaged DTB exists from the full build, Task B is satisfied via a **deterministic rebuild of the same source with the same .config and the same dtc/clang**, then compared to the R154 identity. This is a build-input/DTB-identity check, **not** a claim that the full Image build succeeded.
3. The AArch64 decoder used for Task C is a hand-written subset (capstone and aarch64-objdump are unavailable in this environment). Instructions it cannot decode are reported as **raw 32-bit words** with their addresses; I do not guess their semantics. Several `MOV` register aliases in the C1 window remain undecoded and are listed verbatim.
4. This report replaces no device-side evidence. The ROUND156 RAM gate stays **CONDITIONAL**: a live `/proc/iomem` readback is still required before any boot-safety claim.

---

## 1. Exact candidate identity (verified before build)

All values below were re-measured this round against Window A's own frozen `r154-windowA` workspace and the pinned ACK candidate repo.

| Item | Expected (taskbook) | Measured this round | Result |
|---|---|---|---|
| ACK source commit | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` | parent chain of `491d0cbf` → `0c5c84b5c` → `8ad08f75d` | MATCH (A) |
| Frozen pre-change 23-patch tree | `afe9517f8062b96bfeb5b4dd5714942861e6a44b` | `git rev-parse 0c5c84b5c^{tree}` = `afe9517f8062b96bfeb5b4dd5714942861e6a44b` | MATCH (A) |
| RAM/comment patched source tree | `c56d93eafa35057d65176db6594d67d5144868a0` | `git -C staging/common rev-parse HEAD^{tree}` = `c56d93ea…` | MATCH (A) |
| RAM patch commit | `491d0cbffb4d16e2840c1788674e6a05b26e88a2` | `git -C staging/common rev-parse HEAD` = `491d0cbf…` | MATCH (A) |
| Base DTB (pre-RAM) true SHA-256 | `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e` | R140 log `stage-b4…log:66` and R147/R153 records (64-hex); unchanged this round | MATCH (C, report-derived) |
| RAM-patched DTB | 108680 B, `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` | rebuilt DTB = 108680 B / `9d0d7600…` (§3) | MATCH (A) |
| 23 patch SHA-256 / size | identity.json (23 entries) | re-hashed all `01.patch`…`23.patch` by `idx`: **TOTAL=23 MISMATCH=0** | MATCH (A) |
| 23-patch replay | rc=0 per patch, resulting tree `afe9517f` | R154 `A0-setup-and-apply.log`: apply rc=0 ×23, `APPLY_TOTAL_RC=0`, tree `afe9517f` | MATCH (A, re-read log) |
| RAM DTS patch hash | `047a0af868fcdfceac0b0bb30360dbc9587530c0cedb38e4e6b940fa923afda1` | `sha256sum` of archived patch = `047a0af8…` (4919 B) | MATCH (A) |

The stale 63-hex-character "expected hash" inherited from earlier rounds is **invalid** and was not used anywhere.

Build-input identity log: `r157-windowA/logs/A0-build-input-identity.txt` (host-only; not published).

---

## 2. Task A — formal primary full kernel build: **FAILED (environmental)**

### 2.1 Setup

| Field | Value |
|---|---|
| Workspace | `r157-windowA/a157build` (fresh, isolated staging) |
| Staging method | `cp -al` hardlink of ACK workspace skeleton (build/, prebuilts/, external/, devices/, tools/, u-boot/, `.repo`), **excluding** `common/`, `out/`, `bazel-*`; then `cp -al` of the RAM-patched `r154-windowA/base` tree into `common/`. Hardlinks guarantee zero mutation of the source workspace. |
| Fresh output | New `output_user_root` = `…/a157build/out/bazel/output_user_root/d2489ecb…` — no ROUND135/140 output root reused. No `bazel-*` symlinks existed before the build. |
| Launcher | `tools/bazel` → symlink `../build/kernel/kleaf/bazel.sh` → prebuilt `bazel-8.7.0-linux-x86_64` via `prebuilts/build-tools/linux_musl-x86/bin/py3-cmd` |
| Command | `tools/bazel build //common:dby_w09 --jobs=2` (exact taskbook-preferred target and job count) |
| `//common:dby_w09` outs (BUILD.bazel:1354-1369) | `.config`, `Image`, `System.map`, `vmlinux`; defconfig `arch/arm64/configs/gki_defconfig`; post-config fragment `arch/arm64/configs/dby_w09_storage_first.fragment` |
| OS / CPU | Linux 6.6.114.1-microsoft-standard-WSL2, Ubuntu 24.04.5 LTS, x86_64, 12 cores |
| Memory / disk | 7515 MB total, ~6.6 GB available at start; 688 GB free on `/home` |
| Proxy | `https_proxy=http://127.0.0.1:7897` (external repos fetched at build time) |
| Toolchain | pinned clang `clang-r584948c` = "Android (15323222…based on r584948c) clang version 22.0.1"; Bazel 8.7.0; dtc 1.7.2-g52f07dcc (DTB rebuild only) |
| `.config` / fragment | fragment `b483395dc497a38e75a9cfeeca620e0ecea936370546ab0b748a4f0eb1a08753`; accepted product `.config` `efb663e9c792840e2cfbbc03e115996bb486aefe964b448c1717828c55bf042f` (= ROUND140 out-dtb/.config, copied verbatim) |

### 2.2 Result

| Field | Value |
|---|---|
| Exit code | **1** (`r157-windowA/logs/A1-build.rc`: `BUILD_END=2026-11-27T01:15:42+08:00 RC=1`) |
| Elapsed | 546.545 s, Critical Path 494.96 s, 775 processes (524 internal, 251 linux-sandbox) |
| Progress at failure | `[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 462s linux-sandbox` |
| Actions before failure | config creation (`[773 / 775] Creating kernel config (dby_w09_storage_first.fragment)`) succeeded; toolchain/host tools built; no stale-DTB shortcut — the log shows the build action executed for ~462 s |
| Files produced by the full build | **none of the declared outs**. `bazel-bin/common/dby_w09/` contains only `include/`; no `Image`, `vmlinux`, `System.map`, `.config` output, module artifacts or signing certificate. |

### 2.3 First real failure — classified

Verbatim from the untrimmed log (`A1-primary-build.log`):

```
ERROR: .../common/BUILD.bazel:1354:13: Building kernel (...) //common:dby_w09 failed: (Exit 2): bash failed: error executing KernelBuild command ...
Killed
FAILED: load BTF from vmlinux.unstripped: Invalid argument
make[3]: *** .../scripts/Makefile.vmlinux:72: vmlinux.unstripped] Error 255
make[3]: *** Deleting file 'vmlinux.unstripped'
make[2]: *** .../common/Makefile:1286: vmlinux] Error 2
```

Kernel `dmesg` (host, read-only) confirms the mechanism:

```
llvm-nm invoked oom-killer: ... oom_score_adj=0
oom-kill: constraint=CONSTRAINT_NONE, ..., task=pahole, pid=28393, uid=1000
Out of memory: Killed process 28393 (pahole) total-vm:5883516kB, anon-rss:5256012kB, ...
```

**Classification:** environmental OOM. `pahole` (BTF/DWARF processing) peaked at ~5.26 GB anonymous RSS on a 7.5 GB host with concurrent link tools; the OOM killer selected `pahole`, so `vmlinux.unstripped` BTF generation failed and make deleted the target. This is **not** a compile error in the RAM DTS patch — the DTS change is a `reg` property override plus comments and cannot affect BTF/DWARF generation. No source defect was found and none was patched. No retry build was launched, per the taskbook's explicit instruction. (Grade A for the log/dmesg; the "not a source defect" attribution is Grade A inference from the failure site being `pahole`/BTF, downstream of and orthogonal to DTS compilation.)

The full untrimmed build log remains on the host at `r157-windowA/logs/A1-primary-build.log` and is **not** published (taskbook: keep raw logs on the host).

---

## 3. Task B — verify the final DTB: **PASS (identity + structure)**

### 3.1 Why this is a rebuild, not a full-build extraction

The failed full build produced no packaged DTB (§2.2). To still verify the RAM-patched DTB identity deterministically, I rebuilt the DTB from the **same staging source** (`staging/common`, tree `c56d93ea`, board DTS sha `df0fc83c2ab8a294aa78601f4deaa21bf992eb2999484e26e608a8eac6436521`) using the **same accepted product `.config`** (`efb663e9…`) and the **same toolchain** (clang r584948c preprocessor + kernel dtc 1.7.2-g52f07dcc), via the kernel's own `make … ARCH=arm64 O=… LLVM=1 qcom/huawei-dby-w09.dtb`. Log: `r157-windowA/logs/B1-dtb-rebuild.log` (host-only).

| Field | Value |
|---|---|
| Rebuilt DTB | 108680 B / `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` |
| R154 RAM-patched DTB | 108680 B / `9d0d7600…` |
| Byte-for-byte comparison | **BYTE_IDENTICAL = True** (both files compared locally) |
| Compiler/flags identical to R154? | Yes — same clang r584948c, same dtc 1.7.2-g52f07dcc, same .config, same board DTS blob sha. Therefore the SHA comparison is valid per the taskbook's condition. |

### 3.2 Structural verification of that DTB

| Check | Result | Grade |
|---|---|---|
| FDT header | magic `d00dfeed`, `totalsize`=108680 = file size, version 17, self-consistent | A |
| Exactly one `device_type="memory"` node | **1**: `/memory@80000000` | A |
| Its `reg` | 12 cells = `<0 0x80000000 0 0x39900000> <0 0xc0000000 0 0xc0000000> <2 0 2 0>` — the three source tuples **are preserved** (ac=2/sc=2). No second memory node created. | A |
| `/reserved-memory` children | **18**, every one `no-map`; sum = union = `0xfe9c000` = **254.609375 MiB**; no overlaps. Full list below. | A |
| UFS host | `/soc@0/ufshc@1d84000` `status=okay`, compatible `qcom,sm8250-ufshc`/`qcom,ufshc`/`jedec,ufs-2.0` | A |
| UFS PHY | `/soc@0/phy@1d87000` `status=okay`, compatible `qcom,sm8250-qmp-ufs-phy` | A |
| UFS supply closure | HOST: `vcc-supply`→`regulators-0/ldo17`, `vccq-supply`→`ldo6`, `vccq2-supply`→`smps4`; PHY: `vdda-phy-supply`→`ldo5`, `vdda-pll-supply`→`ldo9`. `vdd-hba-supply` is a phandle-array to the GCC UFS_PHY_GDSC (not a single-cell regulator), consistent with R152's "same gate, two expressions" finding. | A |
| clocks / resets / power-domains / OPP / interconnect | HOST has `clocks`+`clock-names`, `resets`, `power-domains`=`u32[52,6,48,4]`, `interconnects`+names, `operating-points-v2`=`u32[92]`; PHY has `clocks`, `resets`, `power-domains`=`u32[48,4]`. All present. | A |
| `/chosen` | **0 properties** — intentionally empty; bootargs/initrd must be injected by bootloader. | A |
| Node/phandle counts | 905 nodes, 239 phandles (unchanged from R154/R155) | A |

18 reserved-memory carve-outs (size in MiB): `memory@80000000` 6.000, `@80700000` 1.375, `@80860000` 0.125, `@80900000` 2.000, `@80b00000` 83.000, `@86200000` 5.000, `@86700000` 1.000, `@86800000` 0.0625, `@86810000` 0.0391, `@8681a000` 0.0078, `@86900000` 5.000, `@86e00000` 5.000, `@87300000` 5.000, `@87800000` 20.000, `@88c00000` 21.000, `@8a100000` 29.000, `@8be00000` 1.000, `@8bf00000` (cdsp_secure_heap) 70.000. These match the R154/R156 baseline exactly (verified by the byte-identical DTB).

**Task B conclusion:** the RAM-patched source compiles deterministically to the R154 DTB `9d0d7600…`, whose memory/reserved/UFS structure is intact. This does **not** waive the ROUND156 RAM gate: ABL actively rebuilds `/memory/reg` from DDR config (R156 §D), so the DTB's tuple *values* are a skeleton, not the runtime truth. Live `/proc/iomem` readback remains required.

---

## 4. Task C — ABL supplement from the local ROUND155 PE (narrow scope)

Source: Window A's own `r155/evidence/abl/abl-decompressed.bin`, 2,597,064 B, SHA-256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` — re-hashed this round, MATCH. No new device read. Decoder: hand-written AArch64 subset (`_r157/arm64.py`, `func156.py`, `flow156.py`, `strings156.py`); capstone/aarch64-objdump unavailable.

### C1 — `/memory` tuple write primitive, exact routine at `0x3f9a4..0x3f9fc`

**Answer (Grade A/B):** the loop does **not** call a stock libfdt `fdt_setprop` / `fdt_appendprop`. It builds a **new FDT property in place by decrementing a builder pointer 0x20 bytes per cell-group** and then copies 4-byte cells into it. The decisive decoded sequence:

```
0x3f9c4  bl 0x5bc68              ; allocator/builder ctor (EDK2 AllocatePool wrapper)
0x3f9c8  ldr x23, [x0,#0x0]      ; current builder pointer
0x3f9d4  sub x9, x23, #0x20      ; reserve 0x20 bytes (one property slot)
0x3f9dc  str x9, [x0,#0x0]       ; advance builder pointer
0x3f9e8  stp xzr, xzr, [x23,#0x10]
0x3f9ec  stp xzr, xzr, [x23,#0x18]
0x3fa04  movz w2, #0x4
0x3fa08  bl 0xb393c              ; per-cell 4-byte copy primitive
0x3fa1c  b.hi 0x3fa30 ; 0x3fa20 sub w20,w20,#4 ; 0x3fa24 add x21,x21,#4
0x3fa2c  cbnz w20, 0x3f9fc       ; loop over tuple cells
0x3fa4c  stp x2,x3,[x23,#0x18] ; 0x3fa58 stp x4,x5,[x23,#0x10]  ; property payload
0x3fa70  str x23, [x19,#0x0]     ; link property into list
0x3fa88  ret
```

Callee identity: `0x5bc68` is an EDK2 `AllocatePool`-style wrapper — `0x5bcb4 ldr x0,[x8,#0xa0]`, `0x5bcb8 ldr x8,[x8,#0x18]`, `0x5bcbc str x0,[x31,#0]`, `0x5bcc0 blr x8` (UEFI boot-service indirect call, Grade A). `0xb393c` is a 4-byte-count memory-copy helper (`0xb3958 cbz x2`, `0xb3964 bl 0x6105c`, Grade B). A parallel tuple property builder at `0x3faa8..0x3fafc` repeats the same `0x5bc68` + `sub #0x20` pattern and calls `0x5afe8` (a second FDT write primitive) with a negative-bit error test at `0x3faf4 tbnz x0,#31,0x3fc0c`.

**Raw words where the decoder has gaps** (reported verbatim, not interpreted, per the taskbook):
`0x3f9a8 f81b0ffe`, `0x3f9bc 2a0103f4`, `0x3f9c0 aa0003f5`, `0x3f9d0 aa0003f3`, `0x3f9d8 aa1703f9`, `0x3f9e4 f81f8f38`, `0x3f9f4 aa1f03fa`, `0x3f9fc aa1603e0`, `0x3fa00 aa1503e1`, `0x3fa14 f1000b5f`, `0x3fa18 b80046c0`, `0x3fa84 f84507fe`, `0x3faa8 2a0303f5`, `0x3faac 2a0203f7`, `0x3fab0 aa0103f6`, `0x3fab4 aa0003f4`, `0x3fad4 f81f8fbc`, `0x3fae8 aa1403e0`, `0x3fae4 aa1603e1`, `0x3faf8 2a0003f6`. Most are `MOV`/`ADD` register aliases; I do not assert their exact operands.

**Implication:** consistent with R156 — ABL reconstructs/regenerates the `reg` property rather than preserving the DTB-supplied tuple values. The candidate's contribution is the memory node skeleton + 18 carve-outs, not the runtime tuple numbers. This keeps the RAM gate CONDITIONAL. It does **not** prove deletion of an existing reg vs. building a fresh tree from scratch at the whole-FDT level — that distinction is not fully resolved by the decoder and is stated as such.

### C2 — Overlay external-fixup atomicity / failure safety

Wrapper `0x6a8d0` (the `ApplyOverlay` call target from R156's `0x37df8`) call sequence, Grade A:

```
0x6a964 bl 0x6e9c0   ; fixup-stage helper (references "is too small for fixup")
0x6a978 bl 0x6f548 ; 0x6a988 bl 0x6f548      ; overlay load/check passes
0x6a99c bl 0x69f68 ; 0x6a9a8 bl 0x6ee80      ; apply+fixup helpers
loop 0x6a9bc: bl 0x6f548 / 0x6f320 / 0x69f68 / 0x6ee80 ; cbnz x25 back-edge
0x6aa0c bl 0x6f748 ; 0x6aa18 bl 0x6ee80
0x6aa20..0x6aa48: EDK2 DEBUG logging, then normal return
```

Strings/assert xrefs place the **external fixup** phase in `ufdt_overlay_do_fixups` (strings `0xe0e7c`/`0xe0eab`) and the **fragment merge** phase in `failed to apply fragments` (`0xe0e22`), with error-log sites clustered at `0x6a5e8..0x6a8c8` (`failed to perform local fixups` `0xe0dd2`, `failed to perform fixups` `0xe0dfd`, `/__fixups__` `0xe0e5c`, `/__symbols__` `0xe0e4f`, `/__local_fixups__` `0xe0e3d`, `fdt_overlay_do_fixups` `0xe0e7d`). In libfdt/ufdt semantics (Grade C, standard implementation order corroborated by the string layering here), external fixups are resolved **before** fragments are merged into the base.

**Answer (Grade B, with explicit limit):** the error sites and call layering are consistent with "resolve `__fixups__` against base `__symbols__` first; only then merge fragments", and R156 already proved the wrapper's errors funnel to a normal (non-abort) return that its caller merely logs. Therefore the *mechanism* does not force a partial base mutation on a missing external label — but I could **not** fully decode the branch that decides whether any fragment had already been copied into the base tree before a later fixup failure. I do not claim atomicity as proven. The raw-word gaps in `0x6a5cc..0x6a8cc` (mostly EDK2 DEBUG macros) are the reason.

**Practical consequence for the "leave stock DTBO unchanged and let its fixup attempt fail" hypothesis:** it remains **plausible but not proven safe** for the base tree. Note the stock Entry 2 carries 166 external fixups and the candidate has no `__symbols__`, so a real failure is expected (R154: 0/166 bindable; R156: ufdt target-path is supported but symbol resolution is absent). A minimal `target-path` overlay with no `__fixups__` (R155's 199 B overlay) avoids this path entirely and is the cleaner no-fixup option. Neither is endorsed for a device without live verification.

### C3 — AVB: AvbSlotVerify → signature/key/rollback → VERIFICATION_DISABLED → unlocked-continue → Huawei digest

All Grade B unless noted; this is exact-PE string/xref evidence plus decoded branch topology, not a fully traced call graph.

| Stage | Evidence | Finding |
|---|---|---|
| libavb ops contract | `assert fail: ops->read_is_device_unlocked != NULL` (`0xbed80`, xref `0x52b4/0x52bc/0x52e8/0x52f0`); `assert fail: ops->validate_vbmeta_public_key != NULL` (`0xbef64`, xref `0x56b8/0x56c0/0x57a4`) | During `AvbSlotVerify`, ABL must supply both the device-unlocked reader and the vbmeta public-key validator; a NULL is an assert, not a skip. |
| Slot data / partition list | `ERROR: AvbSlotVerify slot data error: num of loaded partitions …` (`0xbe271`, xrefs `0x310c/0x3134/0x3168/0x7c84/0x37158`) | AvbSlotVerify is invoked with a prepared requested-partition set; validation errors are logged in the large state function `[0x1d1c..0x3ecc)`. |
| NO_VBMETA_PARTITION flag | `AVB_SLOT_VERIFY_FLAGS_NO_VBMETA_PARTITION was passed but the value …` (`0xbeee0`, xrefs `0x54c8/0x5538/0x1505c/…/0x58060`) | libavb rejects an inconsistent flag/value combination. This is a flag-validation path, not a descriptor bypass. |
| VERIFICATION_DISABLED | `VERIFICATION_DISABLED bit is set` (`0xbf6f9`, in the libavb code region; see R156 §E) | Present in libavb. Its exact relation to top-level vbmeta signature verification is **UNRESOLVED** with the hand decoder; I do not claim "flags=3 skips signature". |
| Unlocked continuation | `State: Unlocked, AvbSlotVerify returned %a, continue boot` (`0xbe118`, xrefs `0x38b4/0x38d0/0x3904/0x3a88`) and `ERROR: Device State %a,AvbSlotVerify returned %a` (`0xbe153/0xbe1de`) | On an unlocked device, a failed `AvbSlotVerify` causes a **continue-boot** log branch rather than a hard stop. This is the source of "orange state" permissiveness. Whether all descriptor classes are bypassed there is **not** established. |
| Boot state value | `green`/`orange`/`yellow` (`0xbdffe`/`0xbe004`/`0xbe00b`) immediately after `androidboot.verifiedbootstate=` (`0xbdfde`) | The verified-boot-state cmdline value table; orange is the unlocked/verification-error state. |
| Top-level vbmeta digest into cmdline | `androidboot.vbmeta.digest` (`0xbe593`) and `androidboot.huawei_vbmeta.digest` (`0xbe5ad`), xref `0x3190/0x3b3c` | ABL propagates both standard and Huawei-specific vbmeta digests into Android cmdline. |
| Huawei TA digest post-check | `ta_parts is not in vbmeta! ta_digest closed` (`0xbe4a5`), `%s part is not in vbmeta` (`0xbe4fb`); function `[0x3ffc..0x4474)` (8 callers). Decoded: `0x41f8 bl 0x83fc` followed by `placeTaDigest success` (`0xbe528`), then `0x4228 bl 0x89b74` / `0x422c bl 0x469c` and a `123456789abcdef` marker (`0xbe516`). | **Confirmed Huawei-specific OEM post-processing**: TA partition digests are checked/replaced against vbmeta after the main verification flow. `ta_digest closed` is an explicit outcome. This is a separate gate from libavb descriptor skipping (Grade A for the presence and placement of these calls; Grade B for their full semantics). |
| Rollback | libavb rollback ops are implied by the standard `AvbSlotVerify` flow, but no distinct Huawei rollback string/xref was isolated this round. | **UNRESOLVED** — not asserted. |

**C3 conclusion (Grade B/C):** the exact chain is *partially* recovered: ops contract, flag validation, unlocked-continue, boot-state table, vbmeta digest propagation, and a confirmed Huawei TA-digest post-check are present. What remains unresolved is exactly **which operations occur before vs. after descriptor skip**, and whether the top-level vbmeta signature check is short-circuited by `VERIFICATION_DISABLED`/flags=3. I do not declare an unconditional AVB bypass. No flags, keys or vbmeta were modified.

---

## 5. Task D — archived minimal RAM DTS patch: **PASS**

Published artifact: `firmware-analysis/round157/AI1_R157_RAM_DTS_PATCH.patch` (4919 B, SHA-256 `047a0af868fcdfceac0b0bb30360dbc9587530c0cedb38e4e6b940fa923afda1`).

Contents: the single git-format patch `From 491d0cbf…` touching exactly `arch/arm64/boot/dts/qcom/huawei-dby-w09.dts` (32 insertions, 15 deletions). It (a) replaces the inherited zero-size `/memory@80000000` reg with the three live RAM tuples, (b) corrects the stale DTBO-selector/ABL comments (Entry 2 / board-id 0x200e vs. the withdrawn 0x206a/Entry 8 claim), and (c) documents that the 18 reserved-memory children, including cdsp_secure_heap, are untouched. No raw firmware, no build logs, no secret paths, no other source files. Sanitized: no device serials, no absolute private paths, no credentials. Window B can apply this patch to its own base to recreate the same source tree.

---

## 6. Consolidated verdict

| Task | Verdict | One-line basis |
|---|---|---|
| Identity + 23-patch replay | PASS | All hashes/trees/commit MATCH; 23/23 patches verified, replay rc=0. |
| A — full kernel build | **FAIL (environmental)** | OOM-kill of pahole (dmesg) at BTF stage, RC=1; no Image/vmlinux/DTB produced; no retry per taskbook. |
| B — final DTB | PASS | Same-source/same-toolchain rebuild = 108680 B / `9d0d7600…`, byte-identical to R154; one memory node, three tuples preserved, 18 reserved = 254.609 MiB, UFS closure intact, `/chosen` empty. |
| C1 — memory write primitive | PARTIAL (raw words reported) | Custom `AllocatePool` + `sub #0x20` builder + 4-byte copy; no stock libfdt setprop/appendprop; gaps listed verbatim. |
| C2 — overlay fixup atomicity | PARTIAL | Fixup-before-merge layering and non-fatal error return corroborated; exact partial-mutation branch not decoded → no atomicity claim. |
| C3 — AVB chain | PARTIAL | ops contract, flag validation, unlocked-continue, boot-state table, Huawei TA-digest post-check confirmed; descriptor-skip ordering and top-level signature bypass UNRESOLVED. |
| D — patch archive | PASS | Minimal 4919 B DTS patch published and hashed. |
| RAM gate (carried from R156) | **CONDITIONAL — not waived** | ABL rebuilds `/memory/reg` at runtime; live `/proc/iomem` readback still required. |

No device/ADB/root read, no partition operation, no boot.img, no DTBO container, no flash/reboot/fastboot/recovery, no signing/flag edit, no Window-B access. Full raw logs and binaries remain on the host and are not published.

— END —
