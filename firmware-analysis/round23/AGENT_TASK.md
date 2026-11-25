# ROUND23 — DBY-W09 rev2 board DTB and rootparam-only overlay composite validation

**Owner:** local WorkBuddy Agent; local, offline, read-only validation  
**Kernel source:** exact ROUND18 ACK android17-6.18.33_r00, common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## 0. Current inputs on main

Use the latest exact main-branch text of:
1. dts/dby-w09-ack18-board.dts.rev2.candidate
2. dts/dby-w09-ack18-rootparam.dtso.draft
3. ROUND22 report firmware-analysis/round22/round22_board_dts_compile_and_ufs_regulator_contract_audit.txt
4. ROUND18 local pinned ACK source worktree and ROUND19/21 existing decompiled firmware work copies.

The rev2 board source includes the UFS Host dual-domain property and corrected /memory text. The rootparam file is the five-property VG / 0x206a candidate. Do not treat its candidate board ID as proof of runtime selection.

## 1. Hard boundaries

- Read-only validation only. Do not edit either main source candidate, any source/config/fragment/DTS/DTBO/firmware, or prior report.
- Work only from byte-identical temporary copies under a dedicated ROUND23 temp directory.
- Do not re-extract firmware or redeploy WSL; do not install/download tools.
- Do not run Kleaf/Bazel, olddefconfig, dt_binding_check, dtbs_check or a kernel build in this round.
- Do not create dtbo.img / mkdtimg table package, boot.img, AVB footer/signature or any boot candidate.
- No device, ADB/fastboot, recovery, reboot, unlock/root, flash or partition write.
- Do not touch protected ack18-dby-w09-dts-draft, ai-parallel/stagea-port-until-boot or PR #1.

## 2. Work package A — compile the board rev2 candidate

Use ROUND22's proven two-step flow and exact pinned ACK paths:
- copy main rev2 source byte-identically to ROUND23 temp;
- cpp with kernel DTS include paths and same flags used in ROUND22;
- dtc 1.7.0 with -@, create only a temp DTB;
- record source SHA256, exact commands, exit codes, DTB size, warnings;
- compare warnings to ROUND22 baseline; distinguish inherited sm8250.dtsi warnings from new draft warnings.
- Verify that the two new headers resolve:
  include/dt-bindings/clock/qcom,gcc-sm8250.h;
  include/dt-bindings/power/qcom,rpmhpd.h.
- Verify the final Host power-domain specifiers resolve to MMCX ID 6 and GCC UFS_PHY_GDSC ID 4, in that order.

## 3. Work package B — compile rootparam-only overlay

- copy the current main rootparam .dtso byte-identically to temp.
- Compile as a plugin overlay with pre-installed dtc (use -@ and required alignment flags if needed). Record exact command / exit.
- Inspect the raw .dtbo with fdtdump/fdtget or existing preinstalled tools; confirm a fragment target fixup exists for rootparam, and root root identity fields remain as intended.
- Do not pack a DTBO partition image or assume that the overlay root qcom,board-id property alone sets dt_table_entry ID/rev.

## 4. Work package C — apply overlay to base DTB and inspect composite

If pre-installed fdtoverlay exists:
- apply only the one rootparam overlay to the rev2 base DTB in temp;
- no stock HOS overlay is to be applied;
- inspect the resulting composite DTB and confirm:
  a) /rootparam/qcom,boardid = <0x08 0x02 0x09 0x08>;
  b) /rootparam/qcom,board_name = DBY_W09_VG;
  c) /rootparam/qcom,product_name = DBY-W09;
  d) /rootparam/hardware_version = SH1DBSLM;
  e) /rootparam/huawei,modem_id has the intended 0xffffffff, 0 payload;
  f) root qcom,board-id/compatible values reflect the overlay's VG candidate;
  g) /soc/ufshc@1d84000 power-domains is two entries, first RPMHPD_MMCX, second GCC UFS_PHY_GDSC;
  h) /soc/ufsphy_mem@1d87000 retains GCC UFS_PHY_GDSC;
  i) UFS Host has expected vcc/vccq/vccq2, qcom,vddp-ref-clk and qcom,vccq-parent properties;
  j) UFS Host does NOT contain vdd-hba-supply pointing to GDSC.
If fdtoverlay is missing, mark package C BLOCKED; do not install tools.

Explicitly record that the composite operation validates symbol/fixup mechanics only; it does not prove HOS4.3 ABL selects VG or accepts a one-entry replacement DTBO table.

## 5. Work package D — recommendation

Report PASS/PARTIAL/BLOCKED for:
- rev2 base DTB syntax and header resolution;
- rootparam overlay syntax and fixup generation;
- fdtoverlay composite;
- UFS dual-domain value/order;
- rootparam payload values;
- runtime board variant selection (must remain UNKNOWN);
- full DTB/DTBO schema and Kleaf target (not tested this round);
- final memory handoff and PM8150 physical inputs (remain blocked).

Do not recommend boot/package. If all temporary checks pass, recommend the next stage as exact pinned-source dtc/schema and Kleaf rules integration, while preserving the final RAM/PMIC gates.

## 6. Deliverable

Upload one sanitized UTF-8 report only:
firmware-analysis/round23/round23_rev2_dts_and_rootparam_overlay_composite_validation.txt
to branch firmware-audit-v1.

Include exact local tool versions, commands, exit codes, SHA identities, warnings, fdtget/fdtput or fdtdump observations, and boundaries. Do not upload DTB/DTBO/composite binaries, scripts, firmware or private paths.

## 7. Stop rule

After the one report has been uploaded successfully, stop. Do not edit sources, add Kconfig, build kernel, package/sign or contact the tablet.

 
### ROUND23 addendum — DTBO blob alignment check

For the rootparam-only DTBO compile, use the AOSP-compatible dtc blob alignment option -a 4 when producing the packaging-candidate temporary .dtbo. This rounds the FDT blob to a 4-byte boundary; it is NOT the same as the DT table header page_size=4096. Do not pass -a 4096 merely because the stock table page size is 4096. Keep both the unaligned diagnostic and aligned output only in the ROUND23 temp directory if useful, and record exact dtc command/size. No dtbo.img packaging.
