# AI2-ROUND35S — KUnit test option tristate / compile-guard consistency

**任务归属：2号 AI 专属任务书**  
**执行者：本地 Agent**  
**分支：firmware-audit-v1**

## 背景

ROUND35R 的核心可复现性修复已通过审查：固定 ACK + 冻结 17 个生产补丁 + 独立 seam 补丁，在第二棵干净树上真实 UML KUnit 运行 1/1 PASS；host 回归 38/38 与 83/83 PASS；产品 `.config` 未变化。

独立审查发现一个未覆盖的 Kconfig 边界：`REGULATOR_PROXY_CONSUMER_KUNIT_TEST` 声明为 `tristate`，但 `core.c`、`proxy-consumer.c` 和头文件使用 `#ifdef CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST`。若选择 `m`，生成的是 `CONFIG_..._MODULE`，测试模块可能被 Makefile 选中，但 helper/observer 声明和定义不会编译，导致配置/链接不一致。ROUND35R 实际使用 `y` 并已通过；本轮只修复未覆盖的 `m` 分支。

## 授权范围

1. 只修改 ROUND35R 独立 KUnit seam 补丁；冻结的 17 个生产补丁、生产 DTS/DTBO、产品 defconfig、Kleaf 产品目标和产品配置均不得修改。
2. 首选把 Kconfig 符号改为 `bool`，因为当前 seam 依赖 `#ifdef CONFIG_...` 且只需要 built-in KUnit 集成。除非有充分理由，不要引入模块生命周期复杂性。
3. 保留 `depends on KUNIT && REGULATOR_PROXY_CONSUMER && OF && OF_OVERLAY`、`depends on !KUNIT_ALL_TESTS`、`default n` 等隔离条件。
4. 证明 `y` 配置真实编译并运行；证明 `m` 已不再是可选值（若改为 bool），或若选择其他设计则证明 `m` 完整构建、链接。
5. 新 seam patch 仍必须以固定 ACK `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` + 完整 17 个冻结生产补丁为精确父基线。

## 必须验证

- 在全新第二工作树依序应用 17 个生产补丁和修正后的 seam patch；所有 `git apply --check`、`git apply`、`git diff --check` 成功且零 fuzz。
- 确认 Kconfig 选项为 bool、默认 n、依赖隔离条件仍在；测试配置启用 seam，产品 `.config` 不含该符号。
- 重新执行真实 UML KUnit（不是 compile-only），TAP 1/1 PASS、退出码 0；日志绑定 seam SHA-256 与源码树完整 diff SHA-256。
- 重新执行 host 回归 38/38 与 83/83；产品 `.config` 前后 SHA-256 必须一致。
- `git diff --check` 和 `checkpatch.pl --strict`。若 SPDX 子检查因缺少 `python3-ply` 仍无法执行，保留原始错误并如实注明，不得声称 SPDX checker 通过。
- 禁止完整产品 Image build、设备/ADB/fastboot/recovery/root、分区读写、boot/DTBO/AVB/vbmeta、HOS4.3 固件访问或上传。

## 交付文件

放在 `firmware-analysis/round35s/`：
- `AI2_ROUND35S_TASK_RESULT.md`
- `round35s-kunit-seam.patch`
- `round35s-kunit-final-TAP.log`
- `round35s-apply-check.log`
- `round35s-checkpatch.log`
- `round35s-symbol-and-kconfig-audit.txt`
- `round35s-config-and-host-regression.log`

报告需记录所有 SHA-256、ACK、17-patch series 身份、源码树完整 diff 哈希、KUnit config 哈希、命令和退出码。若无法完成必要验证，报告 PARTIAL/BLOCKED，不得写 PASS。

## 停止规则

本轮结束后立即停止，不得自动开始 ROUND36 或修改 Phase E/F/G。Phase E/F 仍 BLOCKED，Phase G 仍 NOT RUN；KUnit PASS 不代表设备启动或硬件验证通过。