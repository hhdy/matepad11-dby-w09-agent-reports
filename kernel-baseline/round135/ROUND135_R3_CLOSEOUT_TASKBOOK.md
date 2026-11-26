# ROUND135 R3 — 最终收尾补充任务：补齐 full dtbs_check 与 DTS file-mode checkpatch

- Owner / dispatcher：1号 AI（ChatGPT）
- Executor：用户本地 WorkBuddy Agent
- Related result：ROUND135 R3-validation, firmware-audit-v1
- Existing R3 report blob：`7b8dc971d752bbffc1bab08a185c2aa43b05d8f0`
- Existing candidate tree SHA：`afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Pinned ACK：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- Scope：完全离线，只补两个遗漏检查，不重跑已通过的构建/Host suites

## 1. 背景与当前有效结果

ROUND135 R3 已成功完成并上传六份主要交付物。当前已被原始日志支持的结果：

- 23/23 补丁身份核验、按 manifest 顺序应用和 accepted-offset replay 完成；`tree17=77e2b2b1515b3813f7538aedffe4c5a4e90edb57`，`tree23=afe9517f8062b96bfeb5b4dd5714942861e6a44b` 精确匹配。
- Source assertions 通过，真实 `huawei-dby-w09.dtb` 生成成功，DTB SHA256 `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e`，大小 108,648 bytes；编译后 DTB 对照 assertions 28/28 PASS。
- `dt_binding_check` RC=0，四个目标 binding examples 构建成功；日志披露 gunyah schema parse warning 与 yamllint 缺失。
- Kleaf `tools/bazel build //common:dby_w09 --jobs=2`：BUILD_RC=0，Image 44,820,992 bytes，SHA256 `ee94c4fa0364018244d4aa467dcc4318a816b53363a25b3b717acb6a002e82c6`。
- 14 个必要 Kconfig symbols 全部 =y；5/5 affected C objects 编译成功。
- Host suites 38/38、83/83 均 PASS。
- final `git diff --check` RC=0；SPDX 因缺少 `ply` 按原任务书记录 NOT RUN，不安装软件。

这些结果保留，不得因为本收尾任务而重跑或覆盖。

## 2. 为什么需要本补充任务

1. 原 R3 taskbook §5.4 明确要求在最终候选树运行**完整 `dtbs_check`**。本轮实际只执行 `CHECK_DTBS=y` 的目标板 DTB targeted check；R3 schema log 自己注明 full-tree `dtbs_check` 未运行。因此不能把 §5.4 标记为完整 PASS。
2. 原 R3 taskbook §7 要求对新 board DTS 源文件运行 checkpatch。R3 已对 patch22 / patch23 运行 checkpatch，但对裸 `.dts` 的调用进入了 patch parser，产生 `Does not appear to be a unified-diff format patch`。应使用 checkpatch 的 `--file` 模式真正检查源文件；不能将这次工具调用错误算成文件级检查通过。

故当前 R3 状态应先记为：**PARTIAL — Image / target DTB / build / host tests passed; two mandatory closeout checks remain.** 不得在这两项完成前宣称严格 taskbook PASS。

## 3. 固定输入和本地路径

优先复用本轮 R3 已验证的只读源码树（不得修改源码）：

`/home/kerneldev/work/matepad11/round135-r3v-agent/vtree/common`

现有目标板 DTB/Kbuild 输出目录：

`/home/kerneldev/work/matepad11/round135-r3v-agent/a30build/out-dtbA`

若上述路径在 Agent 环境中仍存在，先验证 HEAD、root tree、工作区 overlay、当前 content tree SHA；必须确认目标 overlay 仍精确等于 `afe9517f8062b96bfeb5b4dd5714942861e6a44b`。可以只读复用源码树，但两个收尾动作必须将所有生成文件/临时输出放在源码树之外的新目录。若路径已不存在，使用固定本地 ACK 对象库重新建立独立 clone、精确重放 23 patches 并验证 tree SHA；不得下载新 repo、工具或固件。

## 4. 收尾 A：完整 dtbs_check（必须运行）

目标：按原 R3 taskbook §5.4，在同一最终 23-patch source tree、固定 ACK toolchain、独立全新 `O=` 输出目录运行完整 Kbuild `dtbs_check`，不是仅检查 `huawei-dby-w09.dtb`。

执行要求：

1. 保存完整环境身份：ACK HEAD/root tree、最终 candidate tree SHA、git status、git dir/alternates、clang/DTC/dtschema 版本、make 版本和实际 O= 路径。
2. 使用独立输出目录，例如 `out-dtbs-fullA`；不得与 `out-dtbA`、`out-objA` 或 Kleaf 输出共用可变输出目录。复用 pinned toolchain，不安装包、不下载依赖。
3. 复用上次目标配置来源（可复制 `out-dtbA/.config` 到新的 O= 目录并按既有 ACK 流程更新配置），记录配置 SHA 和配置生成命令。不要修改源码树内 `.config` 或任何 tracked/untracked patch input。
4. 从仓库根目录执行标准完整 `make ... dtbs_check` 目标。沿用本轮真实 `ARCH=arm64`、固定 clang/DTC/dtschema 环境和现有 Kbuild 参数；不要加 `CHECK_DTBS=y qcom/huawei-dby-w09.dtb` 目标选择器，不要用单文件 `dtc` 代替。
5. 保存完整 stdout/stderr、真实命令、开始/结束时间、exit code。若存在 schema 错误，逐条归类：本轮目标 board DTS/新改动引入的错误、已知兼容警告、固定 ACK 中与本轮无关的历史错误。不得修改 schema、fixture、DTS 或 patch 来“修到通过”。
6. full `dtbs_check` 过程中若遇到大量上游历史失败，也必须完整记录，不得截断或只保留成功部分；说明目标板自身已执行的 targeted check 与全树检查结果之间的关系。不得擅自将失败全树检查标为 PASS。

建议的命令形态（Agent 必须根据当前本地 pinned tree 的真实工具链变量填充，不得凭空猜路径）：

```sh
make -C <validated-vtree/common> O=<new-out-dtbs-fullA> ARCH=arm64 LLVM=<same-pinned-LLVM-setting> dtbs_check
```

## 5. 收尾 B：新 DTS 源文件 checkpatch 正确 file mode

在已验证的源文件上运行 Linux checkpatch 的 `--file` 模式，不能把裸文件当作 patch：

```sh
scripts/checkpatch.pl --strict --no-signoff --file arch/arm64/boot/dts/qcom/huawei-dby-w09.dts
```

保存真实命令、checkpatch 脚本身份（来自固定 ACK tree）、完整 stdout/stderr、实际 E/W/C 统计和 RC。Warnings 必须如实报告；不自动修复、不使用 `--fix`、不修改文件。已有 patch22/patch23 checkpatch 结果保留，不重复跑。

## 6. 结束完整性复核

收尾后确认：

- tracked/untracked 源码状态和原 23-patch overlay 完全未变；
- 最终 content tree SHA 仍精确等于 `afe9517f8062b96bfeb5b4dd5714942861e6a44b`；
- `git diff --check` 仍 RC=0；
- 输出目录均在 source tree 之外；
- 没有运行额外 Image build、对象编译、Host regression，也没有改写前六个 R3 日志。

## 7. 安全边界

- 完全离线，不连接平板、不使用 USB/ADB/fastboot/recovery/serial。
- 不读取或写入分区，不提取新固件，不制作/签名/修改 boot、ramdisk、DTBO、vbmeta 或 AVB。
- 不修改 source、patch、DTS、schema、Kconfig、config、tests、manifest 或历史日志。
- 不安装工具或 Python 包；SPDX 继续按原任务书记录 NOT RUN。
- 如任何操作要求设备或固件访问，立即停止并报告，不要执行。

## 8. 上传与回读

在 `firmware-analysis/round135/r3-validation/` 新增一个文件：

`round135-r3-closeout-dtbs-check-checkpatch-file.log`

该文件必须包含完整 full-tree dtbs_check 与 DTS file-mode checkpatch 原始输出、命令、版本、RC、失败分类、最终 tree SHA 与状态。上传后从 GitHub 回读并验证 byte-identical，记录 blob SHA 和上传 commit SHA。

## 9. 最终状态规则

- 若完整 dtbs_check 全部执行且符合原任务书，DTS file-mode checkpatch 也真实执行，源树 SHA 未改变：提交补充证据，交 1号 AI 最终复核。1号 AI 决定是否可把 R3 记为 `PASS — BUILD/DTB INTEGRATION ONLY`。
- 若完整 dtbs_check 有本轮候选相关失败：报告 FAIL，保留证据，不修改源码。
- 若 full-tree dtbs_check 因固定 ACK 历史工具/环境问题不能完整完成：报告 PARTIAL/BLOCKED，列出原始错误；不把 targeted board check 伪装成 full-tree PASS。

完成上传与 byte-readback 后停止。不要自行启动 Phase E/F/G 或设备测试。
