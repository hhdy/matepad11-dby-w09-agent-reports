# ROUND27 — real Kleaf/Bazel DTB + DTBO + composite build and schema validation

**[2号AI任务书 / LOCAL_AGENT_TASK]**

- 任务编号：ROUND27
- 执行者：**2号 AI（本地 WorkBuddy Agent）**
- 委托与最终审核：**1号 AI（ChatGPT）**
- 执行环境：用户本机已有 ROUND18 WSL/ACK workspace 的一次性副本
- 当前状态：**AUTHORIZED / READY TO EXECUTE**（ROUND25/26 已经主 AI 审查通过）
- 交付物：仅一份脱敏报告，上传至 `firmware-audit-v1/firmware-analysis/round27/round27_kleaf_dtb_dtbo_composite_schema_validation.txt`

**归属规则：本文件只发给2号 AI。2号 AI 按本任务书执行；1号 AI 负责后续审查，不要把本地命令要求转交给用户。**


Owner: local WorkBuddy Agent; isolated local build-copy validation only.
Baseline: ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.
Prerequisites: ROUND25 and ROUND26 reports must both be uploaded to firmware-audit-v1 and reviewed by 1号 AI. This gate was satisfied on 2026-11-25; the primary-AI review record is `firmware-analysis/round25-26/PRIMARY_AI_REVIEW_2026-11-25.md`. ROUND27 is released to 2号 AI.

## 0. Start gate and ownership

This is a **[2号AI任务书]**. It is explicitly assigned to the local WorkBuddy Agent, not 1号 AI and not the user.

Before doing any work, confirm these two report files exist on branch `firmware-audit-v1`:
- `firmware-analysis/round25/round25-hos43-mmcx-mx-arc-request-semantics.txt`
- `firmware-analysis/round26/round26-sm8250-vs-hos43-reserved-memory-interval-audit.txt`

Read both reports and the primary-AI review record:
- `firmware-analysis/round25-26/PRIMARY_AI_REVIEW_2026-11-25.md`

The review record authorizes ROUND27. If either report or the review record cannot be accessed, STOP and report ROUND27 NOT_STARTED. Do not bypass the primary-AI review gate or guess.

## 1. Inputs and purpose

Use only the existing ROUND18 workspace and its already-checked-out Kleaf toolchain. Do not redeploy WSL, repo init/sync, download source or toolchain, or rebuild the kernel.

Main source candidates:
- dts/dby-w09-ack18-board.dts.rev2.candidate
- dts/dby-w09-ack18-rootparam.dtso.draft

Validation goals:
- move beyond ROUND22 raw cpp/dtc and ROUND23 raw dtc/fdtoverlay validation by testing the exact pinned Kleaf/Bzlmod ruleset;
- build the board DTB, rootparam DTBO and composite DTB through real Bazel targets;
- validate the composite against pinned UFS/PHY/regulator/power-domain bindings;
- determine whether the target graph is ready for repeatable DTB/DTBO source builds.

This is not an Image build, boot image package, dtbo.img package or device boot.

## 2. Hard boundaries

- Do not modify tracked ACK source, Kconfig, .config, storage fragment or any patch.
- Do not run kernel_build/Image, olddefconfig, menuconfig or a full kernel compile.
- Do not build dtbo_image or choose table id/rev metadata; HOS4.3 ABL matching remains UNKNOWN.
- Do not modify firmware, AVB footer/vbmeta, sign or pack boot.img.
- No device/ADB/fastboot/recovery/reboot/unlock/root/flash/partition write.
- No downloads, installations, repo sync, source fetch or WSL configuration changes.
- Do not modify main project DTS sources, protected ack18-dby-w09-dts-draft branch, ai-parallel/stagea-port-until-boot or PR #1.

Temporary BUILD.bazel, staged source files and generated outputs are allowed only inside a disposable ROUND18 workspace copy. All newly created files under the common source copy must be removed before completion. Do not delete or overwrite pre-existing ROUND18 outputs or patch/config files.

## 3. Work package A — exact Bzlmod / rules_devicetree pin

Read the already checked-out build/kernel workspace and:
- inspect the linked root MODULE.bazel, build/kernel/kleaf/bzlmod/bazel.MODULE.bazel, MODULE.bazel.lock, repo manifest and resolved local repo;
- record the exact rules_devicetree version/revision, Bazel version and devicetree toolchain selected;
- verify that the loaded API supports dtb(), dtbo() and dtb_composite() with the intended attributes;
- verify that the exact //common:dtc_includes_aarch64 target exists in the pinned ACK BUILD.bazel.

Do not use current upstream HEAD as a substitute for the local pinned dependency. If lock/version information is unavailable, report BLOCKED for exact pin and do not guess.

## 4. Work package B — temporary source staging and BUILD package

Use the exact main-branch source candidates. Verify their Git blob identities or SHA-256 before staging. If the exact candidate sources cannot be obtained from the existing connected GitHub/project checkout without downloading or installing anything, mark BLOCKED.

Inside the disposable ROUND18 source copy:
- stage the rev2 board DTS as temporary huawei-dby-w09.dts in common/arch/arm64/boot/dts/qcom/;
- stage the separate rootparam overlay as temporary huawei-dby-w09-rootparam.dtso in the same directory;
- create a temporary BUILD.bazel in common/arch/arm64/boot/dts/qcom/.
- The base target must use rules_devicetree dtb() and generate symbols; list both the board .dts and same-directory sm8250.dtsi in srcs; depend on //common:dtc_includes_aarch64.
- The overlay target must use dtbo().
- The composite target must use dtb_composite() against the base DTB and the rootparam overlay.
- Use only attributes supported by the exact pinned rule version. Inspect the rule source/docs already checked out locally before writing the temporary BUILD.

Do not create a dtbo_image target. The HOS4.3 table metadata is not known.

## 5. Work package C — targeted Bazel build

Run:
1. bazel query for the three temporary target labels;
2. bazel cquery --output=files for each target;
3. bazel build for only:
   - base board DTB target;
   - rootparam DTBO target;
   - composite DTB check target.

Do not build //common:dby_w09 or any kernel_build/Image target. Record exact command, target label, exit code, output file size and warnings. If rules cannot load or Bazel analysis fails, capture the exact error and stop that subtask; do not modify source to make it pass.

## 6. Work package D — composite property and schema validation

Inspect the generated composite DTB with existing fdtget/fdtdump/dtc tools. Verify:
- root model/compatible and root qcom,board-id;
- /rootparam five values exactly match the intended VG candidate but retain the caveat that VG runtime selection is unknown;
- rootparam overlay qcom,board-id remains distinct from Android dt_table_entry.id/rev;
- UFS Host power-domains order: RPMhPD MMCX (index 0) then GCC UFS_PHY_GDSC (index 1);
- UFS PHY retains GCC UFS_PHY_GDSC only;
- Host vcc/vccq/vccq2, qcom,vddp-ref-clk and qcom,vccq-parent metadata are present;
- PHY vdda-phy, vdda-phy-always-on and vdda-pll properties are present;
- no vdd-hba-supply is present.

Run the narrowest supported DT binding validation for the composite:
- prefer targeted dtbs_check with the exact pinned schema set if Makefile supports a specific DTB target;
- otherwise run the exact pinned dtschema dt-validate against the generated composite DTB using the processed schema from the checked-out tree.
Include UFS host/common, SM8250 clock/power-domain, QMP UFS PHY, and PM8150 RPMh regulator schemas as applicable.
Do not suppress diagnostics; report every warning/error and exact return codes. A DTC syntax pass is not schema validation.

## 7. Cleanup and integrity

Before stopping:
- remove temporary huawei-dby-w09.dts, huawei-dby-w09-rootparam.dtso and temporary qcom BUILD.bazel;
- leave all tracked source patches, .config, Image, DTS candidate files and pre-existing output artifacts unchanged;
- verify the qcom source directory returns to its prior state and common source git status contains only the pre-existing ROUND18 patch/config modifications, with no new temporary files;
- do not upload any raw DTB/DTBO/composite binary, source or build log containing sensitive paths or addresses.

## 8. Deliverable

Upload one sanitized UTF-8 report only:
firmware-analysis/round27/round27_kleaf_dtb_dtbo_composite_schema_validation.txt
to branch firmware-audit-v1.

Include exact Bzlmod/rules_devicetree pin, target labels, commands/exit codes, output sizes, property checks, schema diagnostics, cleanup integrity and explicit boundaries. Do not upload binaries or source.

## 9. Stop rule

After the single sanitized report is uploaded, stop. Do not create a kernel Image, dtbo.img, boot.img, AVB package/signature or contact the device.
