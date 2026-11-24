# ROUND39 — ACK android17-6.18.33_r00 Kleaf build-system and toolchain baseline

Date: 2026-11-24

Status: **BUILD ENTRYPOINT AND TOOLCHAIN REQUIREMENTS SOURCE-REVIEWED; NO WORKSPACE SYNC OR BUILD PERFORMED.** This round prevents the DBY-W09 port from using a legacy kernel build path or an incorrectly pinned toolchain.

## 1. Fixed kernel source baseline

- Repository: kernel/common
- Tag: android17-6.18.33_r00
- Exact target commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Architecture: AArch64 / arm64
- Port target: DBY-W09 / SM8250 rev 2.1.

All build experiments must run against this immutable common-kernel commit. A manifest branch named android17-6.18 is not a substitute for checking out this exact common source ref.

## 2. Legacy build.config entrypoint is explicitly disabled

Pinned file:
- build.config.gki.aarch64
- Blob SHA: 0ad215e242afde04ceb5663685d5d68418e1485d

Its content says that it is no longer used by GKI and is retained only for external usage. Sourcing it emits “ERROR: Do not source build.config.gki.aarch64” and exits with status 1. It directly redirects build configuration to Kleaf attributes such as kernel_build.defconfig, kcflags, make_goals, and check_defconfig.

The companion build.config.gki is likewise an error stub. Android's current kernel build guide states that build.sh is not supported on Android 14 and newer, while Android 13+ Common kernels use Bazel/Kleaf.

**Decision:** do not use BUILD_CONFIG=common/build.config.gki.aarch64 build/build.sh for this Android 17 / 6.18.33 target. Do not create a custom legacy wrapper to work around the error.

## 3. Exact toolchain values recorded by the pinned common source

Pinned file:
- bazel/constants.scl
- Blob SHA: 43f76625eb9c8a9306458188a62c18a5de72aea3

Values:

| Setting | Value |
|---|---|
| BRANCH | android17-6.18 |
| KMI_GENERATION | 5 |
| CLANG_VERSION | r584948c |
| RUSTC_VERSION | 1.91.1.p3 |
| AARCH64_NDK_TRIPLE | aarch64-linux-android31 |
| X86_64_NDK_TRIPLE | x86_64-linux-android31 |
| ARM_NDK_TRIPLE | armv7a-linux-androideabi31 |

These are source-declared requirements. This review did not sync prebuilt tools or prove that the matching directories are present in any local checkout. The actual compiler, Rust, NDK, host-tool, and Bazel wrapper revisions must be verified after manifest sync.

## 4. Pinned ACK BUILD.bazel: GKI base target and device mixed-build examples

Pinned file:
- BUILD.bazel
- Blob SHA: 3c8178ebce1f27f2c417e4aeaa00fc7001a96be6

### 4.1 Stock arm64 GKI base

The common_kernel(name = "kernel_aarch64") definition specifies:
- arch = arm64
- defconfig = arch/arm64/configs/gki_defconfig
- build_gki_artifacts = True
- kmi_enforced = True
- base KMI symbol list gki/aarch64/symbols/base
- strict KMI mode by default for the normal page-size configuration (the tag explicitly disables strict mode for 16K and 64K configurations)
- trim_nonlisted_kmi = True
- GKI output set and module lists.

The public alias //common:kernel points to //common:kernel_aarch64; //common:kernel_dist points to //common:kernel_aarch64_dist.

This is the generic GKI base target, not a DBY-W09-specific device kernel. Building //common:kernel_aarch64_dist alone is useful as a baseline/toolchain sanity check, but it does not by itself add the board DTS, the storage-first device configuration, or DBY-W09 power/boot integration.

### 4.2 The pinned source already demonstrates mixed builds

The same exact BUILD.bazel has device/platform kernel_build examples that use base_kernel = ":kernel_aarch64":
- wonder_aarch64: module-only target, pre_defconfig_fragments = ["arch/arm64/configs/wonder.fragment"], with selected module_outs.
- db845c: GKI mixed build, base_kernel = ":kernel_aarch64", gki_defconfig, device pre-defconfig fragment, DTB outputs and module outputs.
- fips140: a further example using base_kernel and a post-defconfig fragment.

These examples are stronger evidence for the DBY-W09 build design than copying an unrelated legacy vendor build script.

## 5. Official manifest workspace and reproducibility limitation

The official manifest branch examined:
- URL: https://android.googlesource.com/kernel/manifest/+/refs/heads/common-android17-6.18/default.xml
- Blob SHA: 36a7fcc4482efec1c8b326d17601b22639b9d5a2

It declares:
- default project revision main-kernel-2026;
- superproject revision common-android17-6.18;
- build/kernel from kernel/build, with linkfiles:
  - kleaf/bazel.sh → tools/bazel
  - kleaf/bzlmod/bazel.MODULE.bazel → MODULE.bazel
- common from kernel/common, revision android17-6.18;
- prebuilt Clang, GCC host tools, build-tools, clang-tools, kernel build tools, Rust toolchain and NDK r27 projects, plus Bzlmod external repositories.

This manifest is a workspace/tooling recipe, not an immutable .33_r00 source lock: its common project uses a moving branch revision. The source ref required by this project must therefore be checked out explicitly after repo sync.

### Reproducible workspace capture procedure

After an authorized full-workspace sync in a disposable build workspace:

1. Initialize the official common-android17-6.18 manifest branch and run repo sync.
2. In common, check out detached commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a and verify git rev-parse HEAD.
3. Generate and preserve a fully revision-pinned manifest with repo manifest -r. Save the output as a project artifact; do not rely on the moving default revisions.
4. Record every project revision, especially build/kernel, prebuilts/clang, prebuilts/rust-toolchain, prebuilts/ndk-r27, build-tools, kernel-build-tools, and Bzlmod repositories.
5. Verify the tools/bazel and MODULE.bazel linkfiles resolve to the synced build/kernel checkout.
6. Compare the actual selected compiler and Rust versions with bazel/constants.scl (r584948c and 1.91.1.p3). Preserve the matching prebuilt project revisions in the pinned manifest.
7. Record host OS/tool versions and the exact tools/bazel --version output. Do not guess or manually install a Bazel binary separately from the wrapper.

The manifest branch examined is a moving workspace definition; capture its commit and the full repo manifest -r output at the time of the actual build. This review has not synced it.

## 6. DBY-W09 Kleaf target design

The first build should be split into two explicitly named steps:

### Step A — GKI base sanity check

Use the exact patched/unpatched ACK source workspace and build the stock arm64 target once as a toolchain/build-system baseline:

    tools/bazel query //common:kernel_aarch64
    tools/bazel run //common:kernel_aarch64_dist -- --destdir=out/dby-w09-gki-baseline

This verifies only that the pinned source + manifest toolchain can build the stock GKI target. It does not produce a board-ready DBY-W09 kernel.

### Step B — select the correct DBY-W09 target type (superseded by ROUND41)

The initial suggestion to use base_kernel = ":kernel_aarch64" as the default DBY-W09 target is now superseded. ROUND41 inspected the exact gki_defconfig and found that the Qualcomm UFS / QMP PHY / SM8250 GCC / RPMhPD / interconnect / SMMU components required by the current storage-first plan are not enabled by the stock GKI config. ROUND31 explicitly requires this chain built-in because early ramdisk module loading is still unproven.

The exact pinned BUILD.bazel provides a better full-image example named yukawa: kernel_build with srcs = [":kernel_aarch64_sources"], GKI defconfig, Image/modules/device-DTB make goals, full kernel outputs, and a board GKI fragment, **without base_kernel**. This is the current preferred DBY-W09 target pattern.

A base_kernel = ":kernel_aarch64" target is a mixed build (KBUILD_MIXED_TREE) used for additional modules and device DTB outputs; it may be considered only if the complete matching module set is proven loadable from the actual separate ramdisk before root-storage enumeration. See ROUND41.

The DBY-W09 full target design therefore needs:
- a full-image kernel_build in the common package, without base_kernel;
- srcs = [":kernel_aarch64_sources"], arch = "arm64", defconfig = gki_defconfig;
- full Image / System.map / vmlinux / symvers / builtin-module metadata outputs;
- make_goals for Image, modules and the final DBY-W09 DTB;
- the storage-first device fragment, placed in the Kleaf config stage that preserves the required =y options after defconfig/olddefconfig;
- complete module_outs/module_implicit_outs lists after the final .config is resolved;
- explicit KMI/ABI reporting, while describing the result as ACK-derived / GKI-based custom kernel, not officially certified GKI;
- dedicated rules_devicetree targets where supported by the pinned Kleaf API.

This is target-design guidance only. No BUILD.bazel target has been authored or run. Exact output paths, module lists, fragment stage, and DTB rules must be set from the real DBY-W09 DTS and the synced Kleaf workspace.

### Configuration fragment semantics

Kleaf applies a mixed target's inherited base-kernel pre-defconfig fragments first, then the device target's own pre_defconfig_fragments, and then runs the defconfig step. Later fragments override earlier ones. The Kleaf docs recommend keeping a single pre-defconfig fragment when possible; this also enables the target's _config helper. Post-defconfig fragments are applied after the defconfig and cause olddefconfig when present.

For DBY-W09, ROUND31's storage-first fragment is the candidate input, not a final resolved configuration. It still needs to be run through the real Kleaf configuration flow and the resulting .config audited for all critical built-in requirements. Do not label the fragment itself as a successful Kconfig closure.

## 7. Device-tree build separation

The current Kleaf guidance uses the rules_devicetree ruleset for dtb(), dtbo(), and composite device trees. The docs identify //common:dtc_includes_aarch64 as the kernel-source include dependency when DT sources need kernel .dtsi or binding headers. Kleaf's dtb_image concatenates DT blobs for embedding into a boot/vendor_boot image; dtbo_image creates the DTBO partition image with its table header.

This matters for DBY-W09's legacy boot header v2 + separate ramdisk + DTBO topology: do not assume the Pixel-style vendor_boot layout, and do not create an Android boot image target until ROUND12 AVB scope and actual HOS4.3 image layout are closed.

## 8. What remains NOT_RUN / BLOCKED

- No repo sync was run.
- No full manifest workspace exists in this session.
- No actual Clang/Rust/NDK/Bazel tool executable was run.
- No tools/bazel query, kernel_aarch64_dist, kernel_build, dtb() or dtbo() target was run.
- No Kleaf DBY-W09 target or BUILD.bazel patch was created.
- No Kconfig / olddefconfig or final .config resolution was run.
- No kernel, DTB, DTBO, modules or boot image was built.
- No dt_binding_check, dtbs_check, dtc or device test was performed.

## 9. Next source/build tasks

1. Finish the UFS patch-series integration gates in ROUND38: full-tree apply, schema, DTB, Kconfig and driver build.
2. Pin the complete repo manifest -r for the official toolchain workspace and verify the actual compiler/Rust/Bazel versions.
3. Add a review-only full-image DBY-W09 kernel_build target following the pinned yukawa example without base_kernel, so required Qualcomm storage/power drivers can be built into Image; keep base_kernel mixed build as a conditional module-loading alternative only.
4. Define dedicated Kleaf DTB/DTBO rules from the final real kernel DTS/DTBO source files; do not treat repository .dts.draft files as build inputs until migrated into a proper source tree.
5. Build the stock GKI baseline as a toolchain sanity check, then build the DBY-W09 full custom kernel target and its matching modules/artifacts.
6. Keep ROUND30 MMCX→MX corner equivalence and ROUND12 AVB/legacy boot layout as separate pre-boot gates.


## 11. Follow-up comparison: exact mixed-build examples and modern DT rules

The pinned ACK `.33_r00` `BUILD.bazel` was re-read at the exact source commit (blob SHA `3c8178ebce1f27f2c417e4aeaa00fc7001a96be6`). Its mixed-build examples give two complementary patterns:

- `wonder_aarch64`: `base_kernel = ":kernel_aarch64"`, device `pre_defconfig_fragments`, and `make_goals = ["modules"]`; it has no DTB output and only declares the modules that are built as modules.
- `db845c`: `base_kernel = ":kernel_aarch64"`, `defconfig = "arch/arm64/configs/gki_defconfig"`, a device pre-defconfig fragment, explicit DTB outputs and matching Make goals, plus a device KMI symbol list. This is a broader SoC/platform example, not a DBY-W09 template to copy verbatim.

The build/kernel Kleaf documentation on the main-kernel-2026 tooling line further clarifies the current DT build split:
- `rules_devicetree` supplies `dtb()`, `dtbo()` and `composite_dtb()` rules for compiling device-tree sources.
- Kernel source DTSI/binding include paths can be supplied via `//common:dtc_includes_aarch64` in the DT rule's dependencies.
- A separate `dtbo_image` packaging rule creates the DTBO partition image with a `dt_table_entry` header; `dtb_image` concatenates DTBs for embedding in a boot/vendor_boot image and is not the DTBO partition packager.
- Kleaf's current implementation guidance says not to put `dtbs` into `kernel_build.make_goals`; the dedicated DT rules build DTBs. This is why the DBY-W09 plan should not mechanically copy the older db845c DTB-as-kernel-build-outs pattern without checking the synced Kleaf module version.

For DBY-W09 the build graph should therefore be split as follows, subject to exact API validation after workspace sync:
1. `//common:kernel_aarch64` — stock GKI base sanity build.
2. A DBY-W09 mixed `kernel_build` target — `base_kernel = ":kernel_aarch64"`, `gki_defconfig`, and the storage-first device fragment. Its `make_goals` should contain module-related goals only; `module_outs` must be derived from the resolved .config, not guessed. Built-in UFS/QMP/RPMh/GenPD/ICC/SMMU symbols do not belong in `module_outs`.
3. Dedicated `rules_devicetree` `dtb()` and `dtbo()` targets for the real in-tree DBY-W09 DTS and reviewed rootparam overlay, using the common DTS include dependency.
4. A DTBO partition packaging target (Kleaf `dtbo_image`) only after the actual ABL and ROUND12 AVB checks confirm that this is the correct on-device artifact format. Do not create a `vendor_boot` image target by assumption.
5. A distribution target that exports the exact Image, matching modules, DTB, DTBO image and revision/config metadata together.

This narrows the target design but does not yet authorize writing a BUILD patch: the default manifest's build/kernel revision is still moving, no complete `repo manifest -r` has been captured, no Kleaf query has run, and the user-facing board source files still have the `.draft` suffix and live outside the kernel source tree.

No Bazel target was created or queried in this round; no repo sync, build, DTB, DTBO or device operation was performed.

## 10. Safety / branch boundaries

- This report is on main only.
- No protected DTS branch or PR was modified.
- ROUND12 remains the only local Agent task.
- No local tool installation, firmware extraction, device connection, flashing, partition writing or kernel compilation occurred.

**Conclusion:** ACK .33_r00 is a Kleaf/Bazel kernel source. The pinned source specifies Clang r584948c, Rust 1.91.1.p3, KMI generation 5, and an arm64 GKI base target with KMI enforcement. DBY-W09 should use a full ACK-derived custom kernel_build target (no base_kernel) while the early storage-driver chain must be built-in; a mixed build is only a conditional alternative after early ramdisk module loading is proven. The workspace has not been synced and no build has been run.

## 11. ROUND41 correction

ROUND41 supersedes the provisional base_kernel mixed-build recommendation in §6. The exact gki_defconfig does not enable the Qualcomm-specific UFS/QMP/GCC/RPMhPD/interconnect/SMMU chain required by the current built-in storage-first plan. The preferred target is therefore a full custom kernel_build with no base_kernel, following the exact pinned yukawa example in BUILD.bazel. Mixed build remains conditional on proving early initramfs module loading. See kernel-baseline/round41/gki-defconfig-storage-driver-gap-and-full-kernel-build-decision.md.
