# WorkBuddy Agent — ROUND135 R3 closeout start prompt

你是本地 WorkBuddy Agent。请只执行以下两个剩余检查，不能重新编译内核，也不能连接设备。

完整任务书：
`kernel-baseline/round135/ROUND135_R3_CLOSEOUT_TASKBOOK.md`

GitHub 地址：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round135/ROUND135_R3_CLOSEOUT_TASKBOOK.md

角色：
- 1号 AI（ChatGPT）：任务下发方和最终审核人。
- 你（WorkBuddy Agent）：只负责本地离线验证。
- 2号 AI：独立审查 AI，不是你，不参与本任务执行。

## 已完成且不得重跑

ROUND135 R3 的 23-patch exact tree SHA gate、source assertions、dt_binding_check、真实目标板 DTB build/decompile、compiled-DTB assertions、Kconfig、5 个对象编译、完整 Kleaf Image build、38/38 + 83/83 Host regressions、patch22/23 checkpatch、diff-check 均已有报告与原始日志。完整 Image 已构建成功。不要为了重复确认而重跑这些工作。

本次只补两项：

1. **完整全树 `dtbs_check`**：原 taskbook §5.4 要求完整运行；此前只做了 `CHECK_DTBS=y` 的目标板 targeted check，报告自己已承认 full-tree 未运行。按新 taskbook 使用新的独立 `O=` 输出目录，运行标准 `make ... dtbs_check`，不带目标板选择器，完整保存输出与 RC。
2. **DTS 源文件 checkpatch**：此前裸 `.dts` 被当作 patch 解析，产生 unified-diff 错误，未完成文件级检查。现在用 `scripts/checkpatch.pl --strict --no-signoff --file arch/arm64/boot/dts/qcom/huawei-dby-w09.dts` 真正进行 file mode 检查。保存 E/W/C/RC，不修改任何 warning。

优先只读复用已经验证的源码树：
`/home/kerneldev/work/matepad11/round135-r3v-agent/vtree/common`

先验证其 HEAD、root tree、23-patch overlay 与预期 SHA `afe9517f8062b96bfeb5b4dd5714942861e6a44b` 精确一致。所有输出放在源码树外。若该路径不存在，则按任务书精确重建独立树并重新验 SHA；不要 repo sync、下载工具/固件或安装包。

输出唯一新增交付物：
`firmware-analysis/round135/r3-validation/round135-r3-closeout-dtbs-check-checkpatch-file.log`

上传后必须回读 byte-identical 并在日志中记录 Git blob SHA 和上传 commit SHA。完成后立即停止，等待 1号 AI 审核。

## 明确禁止

- 不连接平板，不使用 USB/ADB/fastboot/recovery/serial。
- 不读写任何分区，不打包/签名/修改 boot、ramdisk、DTBO、vbmeta、AVB。
- 不改源码、patch、DTS、schema、Kconfig、config、tests、manifest 和前六份历史 R3 日志。
- 不安装 Python 包；SPDX 继续记录 NOT RUN。
- 不修改或弱化检查，不清理所谓无关 schema warning，不用 targeted check 代替 full-tree check。

完成后报告准确状态：`PASS`、`FAIL` 或 `PARTIAL/BLOCKED`。不要因为此前 Image 已成功编译就自动宣称整个 R3 通过。
