# ROUND158 — 2号 AI independent rootparam / fastboot-boot gate review

- Executor: **2号 AI**, the separate independent AI collaborator.
- Do not assign this task to WorkBuddy Window A or Window B.
- No local workspace, device, ADB, fastboot, partition, flashing or source-build operations.
- This is an independent evidence review and decision report only.

## 1. Required correction from ROUND157

The previous ROUND157 AI2 report (blob `cf87754c31630270a9cc6c03182fce7ddebd0328`) said the required AI1 ROUND156 integration report was unavailable. That claim was due to a branch/path lookup miss. The report exists and must now be read:

https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round156/AI1_ROUND156_DELIVERY_REVIEW_AND_ROUND157_PLAN.md

Also read all three exact ROUND157 reports:
- Window A: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round157-primary-build-abl-final-proof/firmware-analysis/round157/WORKBUDDY_A_ROUND157_PRIMARY_KERNEL_BUILD_AND_ABL_FINAL_PROOF_REPORT.md
- Window B: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round157-independent-build-repro/firmware-analysis/round157/WORKBUDDY_B_ROUND157_INDEPENDENT_KERNEL_BUILD_REPRODUCTION_REPORT.md
- Previous AI2: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round157-integrated-firstboot-go-no-go/firmware-analysis/round157/AI2_ROUND157_INTEGRATED_FIRST_BOOT_GO_NO_GO_REPORT.md

## 2. New public same-model evidence to assess critically

Read:
- https://github.com/svesnav/linux-dby-w09
- https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso
- https://github.com/svesnav/linux-dby-w09/blob/main/pack_dtbo.py
- https://github.com/Anglerfish314/matepad11-dby-w09-kubuntu

These public projects report a minimal /rootparam DTBO acceptance requirement and, in one case, that `fastboot boot` is refused. They also use `qcom,board-id=0x206a`, and a recent HOS4.2.0.213 sample reports 6GB RAM.

Do not transplant those values. Compare the external context with our direct target evidence:
- HOS 4.3.0.196(C00E100);
- ROUND151 live memory windows total 12,185 MiB / MemTotal about 11.7 GiB;
- ROUND153 live `androidboot.dtbo_idx=2`, selected stock Entry 2 with board-id `0x200e`;
- Entry 8 / `0x206a` was not the selected live entry;
- exact HOS4.3 ABL payload SHA `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`.

Use a strict evidence hierarchy: exact target capture/ABL > same-target independent report > same-model other-firmware public implementation > general inference.

## 3. Independent judgments required

Provide separate GO / NO-GO / CONDITIONAL decisions for:

1. **Offline kernel build** — incorporate Window B's completed full Kleaf build RC0 and Window A's environmental OOM. State whether the source/build gate is now passed.
2. **Offline minimal rootparam DTBO experiment** — whether it is useful and safe as a host-only artifact, and what values/selection metadata remain unknown.
3. **Integrated boot-v2 boot.img + DTBO package** — assess rootparam, actual selector index/board matching, RAM update, /chosen injection, overlay mutation atomicity, AVB/TZ/OEM digest and boot-v2 header contract.
4. **Temporary boot** — inspect the external claim that fastboot boot is refused, but do not assume it applies to HOS4.3 until exact ABL supports that conclusion.
5. **Partition write** — evaluate A-only layout, missing vbmeta_odm/eng_vendor/eng_system/version captures, GPT geometry, rollback metadata, restoration reachability and no restore rehearsal.
6. **What can be delegated next** — distinguish Window A (1号 Agent), Window B (2号 Agent), and 2号 AI correctly.

## 4. Safety constraints

No device interaction or command. No writes, flash, reboot, recovery or fastboot. No generated boot package. No key/AVB modification. Do not present a boot or flash recommendation while exact HOS4.3 rootparam/DTBO acceptance and recovery route remain unresolved.

## 5. Deliverable

Publish:
`firmware-analysis/round158/AI2_ROUND158_INDEPENDENT_ROOTPARAM_AND_FASTBOOT_BOOT_GATE_REVIEW_REPORT.md`

The report must correct the prior branch/path omission, cite the three ROUND157 results and public external evidence, compare firmware/RAM/board-id differences, and give distinct decisions for the six items above. Read back and verify the report, then STOP.

— END —