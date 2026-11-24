# ROUND61 Phase C — manifest-pinned Kleaf target validation

**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Target:** `//common:dby_w09`  
**Fixed ACK common commit:** `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Status:** IN PROGRESS — manifest/source sync is proven; Bazel target query/cquery remain pending.

## 1. Target design and applied inputs

The branch-local ROUND58 Kleaf patch adds a full custom `kernel_build` target named `dby_w09` to the pinned ACK `common/BUILD.bazel`:

- `srcs = [":kernel_aarch64_sources"]`
- `arch = "arm64"`
- `defconfig = "arch/arm64/configs/gki_defconfig"`
- `post_defconfig_fragments = ["arch/arm64/configs/dby_w09_storage_first.fragment"]`
- `make_goals = ["Image"]`
- declared outputs: `.config`, `Image`, `System.map`, `vmlinux`
- no `base_kernel`, no KMI certification claim, and no DTB/DTBO/boot/ramdisk/flash outputs.

The source patch is stored at `kernel-baseline/round61/patches/round58-kleaf-target.patch`. It is applied only in a disposable manifest-synced source workspace. The pristine ACK checkout remains at the immutable commit.

The ordered workflow also applies the validated UFS GenPD/VDDP series and both ROUND63 QMP UFS PHY driver/binding patches before building, so the target compile includes those source changes.

## 2. Manifest-pinned source evidence

Hosted attempt `45450833773` completed Repo sync successfully and recorded:

- manifest revision: `46a1a5274ff0b40419952c861a8958bba5f28cfc`
- common: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- build/kernel: `2bebe7c443d0e6d5d549fb2a2377dce980d1b15e`
- pinned manifest XML SHA-256: `6449879cd7081345cf0a2e7060a1e40b9edfe1b8b22629263c96f8e2141a1f11`
- manifest-provided JDK: OpenJDK 11.0.15
- manifest Kleaf Bazel wrapper: Bazel 8.7.0

The run successfully initialized the manifest, completed `repo sync`, checked out the exact ACK tag commit and ran `tools/bazel version`.

## 3. Runner ABI failure and correction

Run `45450833773` stopped before target query when the manifest-provided Clang 3289846 was executed:

`clang.real: error while loading shared libraries: libtinfo.so.5: cannot open shared object file`

Exit code was 127. This is a host userspace runtime-library mismatch, not a source compile error and not evidence of a Kleaf target failure.

Corrected `.github/workflows/round61-manifest-kleaf-build.yml` to:
- pin `runs-on: ubuntu-22.04`, matching the older Android Clang runtime ABI;
- install the actual `libtinfo5` compatibility package;
- avoid creating a speculative symlink from libtinfo.so.6 to libtinfo.so.5.

Retry trigger commit: `4a2db7667b14d1fb83477e692b6f38d6e5c126b2`. Hosted run `45452267778` is the active retry.

## 4. Required closure evidence

Phase C remains open until the retry proves all of the following with the manifest-pinned wrapper:

1. `tools/bazel query //common:dby_w09` returns the declared target.
2. `tools/bazel cquery //common:dby_w09 --output=files` resolves the output inventory.
3. The resolved target includes the actual post-defconfig fragment.
4. Kleaf accepts the rule attributes and target graph without compatibility errors.
5. The resulting `.config` output is a real target artifact, not a guessed path.

Do not mark Phase C PASS from patch application, buildifier or Bazel version output alone.


## Second runner attempt — pre-build checkpatch harness mismatch

Run `45452267778` on Ubuntu 22.04 successfully resolved the previous Clang ABI blocker: manifest JDK 11.0.15, Bazel 8.7.0, Clang path and Rust 1.91.1 were located. It applied the full ordered UFS/ROUND63/Kleaf patch set and passed both prior code-patch checks, then stopped in strict checkpatch because the ROUND63 patch references the existing kernel API member `regulator_bulk_data.init_load_uA`, which upstream checkpatch labels CAMELCASE. The independent UFS validation workflow already narrowly ignores only this known CAMELCASE false positive for the same patch; it reports 0 errors / 0 warnings after that ignore.

Aligned the manifest build workflow with the same narrow `--ignore CAMELCASE` handling for ROUND63 only. No other checkpatch category is ignored. Retry trigger commit: `1b833dd74ddb39dd90f7a691f62ce313e0dfe5d2`. Await new run before claiming target query/cquery.


## Watchdog recovery for non-reporting runner

After the narrow CAMELCASE adjustment, run `45453412267` remained API-reported `in_progress` with no `updated_at` movement after `2026-11-24T17:52:57Z`; its job log endpoint returned BlobNotFound and its manifest/build step never advanced. No target-query result can be inferred from that state. Recovery trigger commit `4877a6d2afb643e69e1ac68685983c4495e20936` started run `45455279898`, which is now the active monitored attempt. The previous run is left untouched. Await fresh query/cquery and terminal artifact evidence.
