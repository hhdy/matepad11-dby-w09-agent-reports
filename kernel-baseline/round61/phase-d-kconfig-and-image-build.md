# ROUND61 Phase D — resolved Kconfig and DBY-W09 Image compilation

**Owner:** Second AI  
**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Target:** `//common:dby_w09`  
**Fixed ACK common commit:** `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Status:** PASS for actual Kconfig resolution and Image compilation on prior hosted runs; archived .config independently passes current 33-symbol validation. A repeat build using the corrected transparent 9-stage workflow is currently in stage 8/9.

## 1. Build target and source integrity

The real Kleaf target applies `arch/arm64/configs/dby_w09_storage_first.fragment` after the pinned ACK GKI defconfig. Target `//common:dby_w09` declares `.config`, `Image`, `System.map`, and `vmlinux` as outputs.

Immutable source:
- ACK `android17-6.18.33_r00`: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`;
- manifest commit: `46a1a5274ff0b40419952c861a8958bba5f28cfc`;
- `build/kernel`: `2bebe7c443d0e6d5d549fb2a2377dce980d1b15e`;
- manifest XML SHA-256: `6449879cd7081345cf0a2e7060a1e40b9edfe1b8b22629263c96f8e2141a1f11`.

## 2. Actual successful Image builds

### Run 45453412267

The independent Agent report established that run `45453412267` completed successfully at `2026-11-24T18:22:49Z` (exit 0). It produced:
- Image: 44,820,992 bytes;
- config: 238,376 bytes;
- artifact: `14951184014`;
- exact ACK and manifest pins above.

The archived `.config` was independently rechecked by Second AI against the current strengthened list described below.

### Run 45455279898

This run was started by the earlier watchdog-recovery push while `45453412267` was still healthy; independent analysis correctly classified it as an accidental duplicate, not recovery from a dead runner. It nevertheless completed successfully at `2026-11-24T18:34:35Z` and produced artifact `14951574600` (210,439,547 bytes).

Its completed build log records:
| Artifact | Size | SHA-256 |
|---|---:|---|
| `dby_w09.config` | 238,376 B | `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7` |
| `Image` | 44,820,992 B | `8a90e4fa5bd77ce266e9c095cc8e451815cf10bf27099c6e408e6b865a8747de` |
| `System.map` | 7,610,772 B | `93ccfa166d83b785880473a294af355f90f54f412fbc24ab169fbdf7b5e2a5c9` |
| `vmlinux` | 230,254,408 B | `9ef6fca88f530291e1c52ef6df0a27c30ea94ab57af07e8fd0bed4408835882e` |

The .config hash exactly matches the archived config from run 45453412267.

## 3. Final config acceptance — PASS, 33/33

The archived 238,376-byte `dby_w09.config` from the successful Image build was checked independently against the current 33 required symbols. Result:
- 33/33 required symbols resolve to `=y`;
- no required symbol is missing;
- no required symbol is `=m` or `=n`;
- no duplicate symbol assignments;
- SHA-256: `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7`.

The strengthened validator explicitly asserts `CONFIG_BLOCK=y` and derived `CONFIG_ARM_SMMU_QCOM=y` in addition to the UFS / PHY / clock / regulator / interconnect / IOMMU / DM / EROFS and other storage-first dependencies. Eleven validator unit tests passed in hosted run `45457083961` and again in stage 6 of run `45529395645`.

## 4. Deterministic manifest-pinned toolchain — PASS on current retry

The earlier nine-stage workflow attempt `45463060672` failed before compiler discovery because it looked for the constants file under the wrong repository directory. The fix now reads `$WORK/common/build.config.constants` from the exact immutable ACK common repository, hashes it, checks:
- Clang `r584948c`;
- Rust `1.91.1.p3`;

and verifies the exact manifest-provided executable paths:
- `prebuilts/clang/host/linux-x86/clang-r584948c/bin/clang`;
- `prebuilts/rust-toolchain/linux-x86/1.91.1.p3/bin/rustc`.

In run `45529395645`, stage 4 passed, real ordered UFS / ROUND63 PHY / Kleaf patch apply passed in stage 5, strict checkpatch/buildifier/11 tests passed in stage 6, and the Bazel target query/cquery passed in stage 7.

## 5. Current transparent repeat build

Run `45529395645`, job `138920645396`, was triggered from `eb37d21224a0878059b0ed5eef72a29cdbd69af9`. At the latest status snapshot:
- stages 1–7 passed, including exact pinned compiler/toolchain discovery and Bazel query/cquery;
- stage 8/9 `Build DBY-W09 Image` is `in_progress`, started at `2026-11-25T02:03:17Z`;
- stage 9/9 final .config validation and artifact hashing is pending;
- no failed step is reported.

This repeat run is to validate the newly split workflow and make the true compiler versions visible and reproducible. Do not mistake the previous accidental first-on-disk `clang-3289846`/Rust p2 report for the pinned Kleaf compiler. Do not mark this repeat run complete until stages 8 and 9 pass and the new artifact is inspected.

## 6. Build scope and safety boundary

A successful Image build is not a boot image and does not close the device boot gates:
- no production board DTS/DTB has been built;
- HOS4.3 final ABL-to-Linux memory/reserved-memory handoff remains unknown;
- PM8150 physical input-parent topology remains unresolved;
- HOS ARC/proxy semantics are not implemented as a proven equivalent;
- header-v2 boot/ramdisk/DTBO packaging and AVB footer/vbmeta descriptor coverage remain blocked;
- no ADB/fastboot, bootloader unlock, device reboot, partition write, flash, or hardware validation has been performed.

Phase D is therefore **PASS as an Image-build milestone**, while Stage A as a whole remains incomplete. Phase E/F remain BLOCKED and Phase G remains NOT RUN.
