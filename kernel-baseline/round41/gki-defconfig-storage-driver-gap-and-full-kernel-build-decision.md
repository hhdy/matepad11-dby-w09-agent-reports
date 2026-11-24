# ROUND41 — GKI defconfig storage-driver gap and full-kernel build decision

Date: 2026-11-24

Status: **DEVICE BUILTIN DEPENDENCY GAP CONFIRMED; SELECT FULL CUSTOM KERNEL BUILD PATH FOR THE CURRENT STORAGE-FIRST PLAN.** This supersedes ROUND39's provisional suggestion to make the DBY-W09 target a base_kernel mixed build by default.

## 1. Exact fixed-source inputs

- ACK tag: android17-6.18.33_r00
- Exact commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- BUILD.bazel blob: 3c8178ebce1f27f2c417e4aeaa00fc7001a96be6
- gki_defconfig blob: a3e1c0d60d5220b6be8b306157a331fc1696afb0
- DBY-W09 storage-first fragment draft blob: 20f88ec3ea2d42e59d297268cce15940c1630a9d

This is a source/config review only. No Kconfig resolution or kernel build was run.

## 2. What the pinned stock GKI defconfig actually enables

The exact arm64 gki_defconfig contains these relevant enabled values:

- CONFIG_SCSI_UFSHCD=y
- CONFIG_SCSI_UFSHCD_PLATFORM=y
- CONFIG_BLK_DEV_DM=y
- CONFIG_EROFS_FS=y

But the exact file does not enable the Qualcomm-specific items required by the DBY-W09 SM8250 UFS/device tree:

- CONFIG_SCSI_UFS_QCOM
- CONFIG_PHY_QCOM_QMP
- CONFIG_PHY_QCOM_QMP_UFS
- CONFIG_SM_GCC_8250
- CONFIG_INTERCONNECT_QCOM_SM8250
- CONFIG_QCOM_COMMAND_DB
- CONFIG_QCOM_RPMH
- CONFIG_QCOM_RPMHPD
- CONFIG_REGULATOR_QCOM_RPMH
- CONFIG_ARM_SMMU

These symbols are all explicitly requested by the current storage-first fragment (with the SMMU Qualcomm provider selected by its Kconfig dependency/def_tristate rule). The generic UFS core being enabled does not provide the missing Qualcomm UFS host glue, QMP UFS PHY, GCC GDSC, RPMhPD, interconnect or SMMU drivers.

The GKI defconfig's omission means those device-specific components are not enabled by that stock configuration. The exact final resolved config still must be generated and audited because Kconfig select/default dependencies can affect the final value.

## 3. Why a base_kernel mixed build is not the correct default for this stage

The exact pinned BUILD.bazel provides two distinct patterns:

### Mixed target with base_kernel

- wonder_aarch64 sets base_kernel = ":kernel_aarch64", has outs = [], and builds make_goals = ["modules"] with selected module_outs.
- db845c sets base_kernel = ":kernel_aarch64", has device DTB outputs, builds "modules" plus DTB goals, and its distribution explicitly includes the original kernel_aarch64 and its additional GKI artifacts.

The comment immediately above db845c says “Enable mixed build”. Kleaf's kernel_build API explains that setting base_kernel copies the base kernel artifacts and sets KBUILD_MIXED_TREE, which enables a mixed build. Its pre_defconfig_fragments examples for mixed builds describe adding in-tree modules such as CONFIG_FOO=m.

This mode is appropriate when device-specific drivers can be delivered as modules and loaded at the correct point in first-stage initramfs. It does not replace the stock GKI Image with a newly linked DBY-W09 kernel containing new built-in drivers.

### Full custom kernel target without base_kernel

The same pinned BUILD.bazel has a direct full-kernel pattern named yukawa:
- no base_kernel attribute is set;
- srcs = [":kernel_aarch64_sources"];
- defconfig = arch/arm64/configs/gki_defconfig;
- outs include Image, System.map, vmlinux, vmlinux.symvers, modules.builtin, modules.builtin.modinfo and board DTBs;
- make_goals include Image, modules and the device DTB goals;
- it uses a device-specific GKI fragment and declares its module_outs.

This rule builds a full kernel image from the common source tree using a GKI base defconfig plus a device fragment. It is the correct in-tree analogue for DBY-W09's current requirement to link the Qualcomm UFS / PHY / clock / RPMh / interconnect / SMMU path into the kernel when those components are required before root storage is available.

## 4. Decision for DBY-W09 Stage A

**Default path: full ACK-derived custom device kernel target, without base_kernel.**

Build design to follow the exact yukawa pattern:
- kernel_build target in the common package;
- srcs = [":kernel_aarch64_sources"];
- arch = "arm64";
- defconfig = "arch/arm64/configs/gki_defconfig";
- full-kernel outputs, not only module outputs: Image (and the required compressed variant if used), System.map, vmlinux, vmlinux.symvers, modules.builtin and modules.builtin.modinfo;
- make_goals include Image, modules and the actual DBY-W09 board DTB output path;
- include the reviewed DBY-W09 board config fragment and an accurate complete module_outs / module_implicit_outs list after final .config resolution;
- use explicit KMI/ABI reporting separately; do not label the resulting custom build officially GKI-certified unless the applicable certification process passes.

For critical built-in symbols, the final Kleaf config must be explicitly audited. Do not assume a fragment was applied correctly merely because Bazel completed. The final .config must show every ROUND31-required storage chain component as =y, especially SCSI_UFS_QCOM, PHY_QCOM_QMP, PHY_QCOM_QMP_UFS, SM_GCC_8250, INTERCONNECT_QCOM_SM8250, QCOM_RPMHPD, REGULATOR_QCOM_RPMH and ARM_SMMU/ARM_SMMU_QCOM as resolved by Kconfig.

The exact placement of the device fragment in pre_defconfig_fragments versus post_defconfig_fragments must be decided using the pinned Kleaf implementation and verified final .config. Prefer the configuration mode that demonstrably preserves the requested =y states after defconfig/olddefconfig. Set check_defconfig appropriately and archive the resulting config.

## 5. Module-based alternative remains conditional, not default

A base_kernel mixed build may be reconsidered only if both of these are proven:
1. The device's actual ABL/ramdisk layout can load the complete set of matching .ko files before UFS root-storage enumeration, and the module metadata (modules.dep, aliases, softdeps, options, load list and kernel release/page-size) is correct.
2. The matching modules can safely satisfy the RPMh, GCC, QMP PHY, interconnect and UFS probe dependency chain before the logical partitions are mounted.

ROUND10's ramdisk/module inventory remains unread, and ROUND12 AVB metadata remains pending. Therefore this alternative is not currently established. Keep all first-stage storage dependencies built-in under the current plan.

## 6. KMI/certification distinction

The stock //common:kernel_aarch64 target is a GKI base built by common_kernel with kmi_enforced = True, a base KMI symbol list, strict-mode default for the normal page size, and trim_nonlisted_kmi = True.

The full custom yukawa-style kernel_build is a different target. It does not automatically inherit the stock common_kernel macro's KMI enforcement simply because it uses gki_defconfig or the same source tag. Add an explicit kernel_abi/KMI comparison workflow if useful, and report its actual result. The product of the DBY-W09 full custom build should be described as ACK-derived / GKI-based custom kernel, not a certified GKI unless separately certified.

## 7. Other constraints

- Do not use legacy build.config.gki.aarch64 / build.sh; pinned ACK has the legacy file deliberately exit with an error.
- Pin the official Kleaf toolchain workspace using repo manifest -r, explicitly checkout the common source to commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a, and verify Clang r584948c and Rust 1.91.1.p3.
- DTB/DTBO should use rules_devicetree rather than deprecated kernel_build.dtstree. The pinned yukawa example still demonstrates in-tree make-goal DTB production; the selected device-tree rule must match the checked-out Kleaf API version.
- Do not create a boot image yet. DBY-W09 has boot header v2 and separate ramdisk; the current generic Kleaf boot_image API defaults to header v3 if not specified, so the eventual image target must be explicitly aligned with confirmed boot/ramdisk and AVB metadata after ROUND12.
- ROUND30 MMCX-to-MX power-corner equivalence remains a separate hardware/power validation gate.

## 8. Next actions

1. Keep ROUND12 as the only local Agent task; finish the read-only AVB metadata inspection.
2. Complete the full ACK workspace/toolchain revision pinning described by ROUND39.
3. In a disposable full source workspace, integrate ROUND32 + ROUND36 + ROUND37 + ROUND33.
4. Add a review-only DBY-W09 full-kernel Kleaf target following the exact pinned yukawa pattern (no base_kernel), with the final device config fragment and DTB outputs.
5. Run Kleaf config, inspect final .config, dt_binding_check, dtbs_check, compile Image/modules/DTB and archive outputs.
6. Only after the kernel and storage path validate, close boot image/AVB layout and proceed to the Android 17 DerpFest system stage.

**Conclusion:** the stock GKI defconfig is missing the Qualcomm-specific storage and power drivers required by this port. Because the current plan explicitly needs them built-in and early module loading is not yet proven, build the DBY-W09 image as a full ACK-derived custom kernel using the pinned no-base_kernel Kleaf pattern. A base_kernel mixed build is only a later alternative if early module loading is proven.
