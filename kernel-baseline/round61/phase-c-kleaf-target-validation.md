# ROUND61 Phase C — manifest-pinned Kleaf target validation

**Owner:** Second AI  
**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Target:** `//common:dby_w09`  
**Fixed ACK common commit:** `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Status:** PASS — exact manifest/ACK pin, Kleaf target query and cquery output inventory passed in hosted run `45529395645`; Image build is a separate Phase D gate now running in stage 8/9.

## 1. Target design

The branch-local ROUND58 patch adds a full custom `kernel_build` target named `dby_w09` to the pinned ACK `common/BUILD.bazel`:
- source set `kernel_aarch64_sources`;
- `arch = "arm64"`;
- base `gki_defconfig`;
- storage-first fragment applied as `post_defconfig_fragments`;
- `make_goals = ["Image"]`;
- declared outputs `.config`, `Image`, `System.map`, and `vmlinux`;
- no `base_kernel`, no GKI certification claim, and no DTB/DTBO/boot/ramdisk/flash outputs.

The target is deliberately Image-only because the HOS4.3 final memory handoff, board-specific PM8150 physical input supply tree, and stock boot/AVB packaging facts remain separate gates.

## 2. Immutable manifest and source identity

Run `45529395645`, job `138920645396`, passed:
- official Repo init and immutable manifest sync (stage 2);
- exact ACK tag/object verification and detached checkout (stage 3);
- manifest recording;
- Kleaf wrapper/Bazel version discovery.

Fixed revisions:
- manifest commit: `46a1a5274ff0b40419952c861a8958bba5f28cfc`;
- ACK `common`: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`;
- `build/kernel`: `2bebe7c443d0e6d5d549fb2a2377dce980d1b15e`;
- pinned manifest XML SHA-256: `6449879cd7081345cf0a2e7060a1e40b9edfe1b8b22629263c96f8e2141a1f11`.

## 3. Exact pinned toolchain discovery — PASS

The first nine-stage attempt, `45463060672`, correctly passed repo sync and ACK pin but failed at stage 4 because the script searched for `build/kernel/build.config.constants`. JDK 11 and Bazel 8.7.0 had already started; Clang/Rust discovery was not reached. This was a workflow path error, not a missing compiler.

The second AI fetched the actual constants file from the exact pinned ACK commit:
- `common/build.config.constants`, blob `cc08dcbb5cbb543fc508dca51d14ad00d2b665b8`;
- `CLANG_VERSION="r584948c"`;
- `RUSTC_VERSION="1.91.1.p3"`.

The retry workflow reads `$WORK/common/build.config.constants`, asserts those pinned version strings, and verifies the exact manifest prebuilt executable paths:
- `prebuilts/clang/host/linux-x86/clang-r584948c/bin/clang`;
- `prebuilts/rust-toolchain/linux-x86/1.91.1.p3/bin/rustc`.

Hosted stage 4 passed at `2026-11-25T02:02:40Z`. This replaces the earlier invalid first-on-disk lookup that had reported `clang-3289846` and Rust `1.91.1.p2`.

## 4. Patch integration and target query — PASS

In run `45529395645`:
- stage 5 real ordered UFS / ROUND63 PHY / Kleaf patch application passed;
- stage 6 strict checkpatch, buildifier, and all 11 config-helper unit tests passed;
- stage 7 Bazel `query //common:dby_w09` and `cquery //common:dby_w09 --output=files` passed.

The current ordered patch stack includes the previously validated UFS GenPD/VDDP binding and driver changes, ROUND63 QMP UFS PHY driver/binding changes, and ROUND58 Kleaf target patch. Real `git apply --check`, apply, and `git diff --check` are performed in the disposable manifest workspace. The strict checker narrowly ignores only CAMELCASE for the existing kernel API member `init_load_uA` in the ROUND63 driver patch; all other strict checks remain enabled.

Earlier hosted run `45457083961` independently passed the authoritative UFS/PHY `dt_binding_check` and positive/negative fixtures (Phase B).

## 5. Prior real Image-build evidence

Before the nine-stage workflow refactor:
- run `45453412267` built the DBY-W09 Image successfully;
- run `45455279898`, the watchdog-created duplicate, also completed successfully and uploaded artifact `14951574600`.

The latter completed log recorded:
- `.config`: 238,376 bytes; SHA-256 `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7`;
- `Image`: 44,820,992 bytes; SHA-256 `8a90e4fa5bd77ce266e9c095cc8e451815cf10bf27099c6e408e6b865a8747de`;
- `System.map`: 7,610,772 bytes;
- `vmlinux`: 230,254,408 bytes.

The archived .config has subsequently been independently rechecked against the hardened current 33-symbol requirement list: **33/33 =y, no missing symbols, no non-y assignments, and no duplicate assignments**. The same config SHA is present in the duplicate successful run. Those earlier build results are not device-boot acceptance.

## 6. Current separate Phase D build gate

In run `45529395645`, stage 8/9 `Build DBY-W09 Image` is currently `in_progress` (started `2026-11-25T02:03:17Z`). Stage 9/9 will validate the generated final .config against the 33-symbol checker and hash/size the resulting kernel artifacts.

Do not mark the current retry's Phase D complete until stage 8 and stage 9 both pass and the uploaded artifact is inspected. Earlier successful Image builds remain valid independent evidence.

## 7. Scope boundary

Phase C passing proves the real pinned Kleaf target graph is accepted and its output inventory resolves. It does not prove:
- final HOS4.3 board DTS/DTB is correct;
- the post-ABL RAM/reserved-memory handoff is known;
- PM8150 physical input-parent topology or HOS ARC/proxy semantics are closed;
- AVB footer/vbmeta descriptor coverage or header-v2 + separate ramdisk packaging is validated;
- the tablet has booted this kernel.

Phase E remains BLOCKED, Phase F remains BLOCKED, and Phase G has NOT RUN. Keep the board DTS as review-only and do not create a boot/flash package or issue device operations without the separately reviewed evidence and explicit authorization.
