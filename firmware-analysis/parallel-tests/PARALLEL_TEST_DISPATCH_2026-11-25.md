# DBY-W09 并行测试派发说明 — ROUND124 + AI2-ROUND33

日期：2026-11-25

本说明用于两个全新测试 Agent 窗口。请分别打开两个窗口，并分别只向对应窗口发送其任务书。两个窗口里的执行者都是用户本地 WorkBuddy 测试 Agent；不是 1 号 AI，也不是 2 号 AI。

## 项目背景

设备是 Huawei MatePad 11 2021，型号 DBY-W09，Qualcomm KONA / SM8250。项目目标严格分阶段：先完成 ACK/GKI-based 6.18.33 内核移植和设备启动/存储验收（Stage A），Stage A 验收通过后才开始 Android 17 DerpFest（Stage B）。当前两项任务都属于 Stage A 的离线源码和构建验证，不涉及 ROM 移植或设备启动。

固定 ACK 源码是 aosp-mirror/kernel_common 的 android17-6.18.33_r00，commit：
8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

参与者严格区分：
- 1 号 AI：ChatGPT，拥有 ROUND124 候选补丁，负责独立技术审查。
- 2 号 AI：另一套独立开发 AI，拥有 ai-parallel/stagea-port-until-boot 中的 Stage A 实现，负责 ROUND33 代码。
- 测试 Agent：用户本地 WorkBuddy，只做任务书授权的测试、验证、构建、证据收集和报告上传。它不是 2 号 AI，不得编写或修复内核代码。

## 两个窗口的任务分工

### 窗口 1：ROUND124（1 号 AI 候选）

完整任务书：
firmware-analysis/round124/TEST_AGENT_ROUND124_NEW_WINDOW_TASKBOOK.md

测试范围：
- 只在 ROUND32 的 15-patch Stage A 基线上测试 1 号 AI 的两个 UFS core 补丁。
- 0001：ROUND120 per-HBA async scan join。
- 0002：ROUND122 UFS VCC/VCCQ load-first shutdown。
- 按指定顺序 apply，做源码门槛、UFS object 编译、完整 Image build 和工作区还原。
- 明确不包含 2 号 AI ROUND33 的 patch 16/17。

输出唯一报告：
firmware-analysis/round124/TEST_AGENT_ROUND124_COMBINED_UFS_CORE_REPORT.txt

### 窗口 2：ROUND33（2 号 AI 候选）

完整任务书：
firmware-analysis/round33/TEST_AGENT_ROUND33_NEW_WINDOW_TASKBOOK.md

测试范围：
- 使用 Stage A 完整 17-patch series，即 ROUND31/32 的 15 patches + ROUND33 patch 16 + patch 17。
- 只验证 2 号 AI 已提交的 self-target-only 生命周期修复及 binding 描述。
- 不允许 Agent 重新设计、改写、修复或提交任何源码。
- 保留第一次失败报告，只新增本轮 revalidation 报告。

输出唯一报告：
firmware-analysis/round33/AI2_ROUND33_REVALIDATION_REPORT.txt

## 并行执行与资源调度（强制）

1. 两个窗口必须在独立的 Git clone / worktree / build workspace 中工作。不得共用一个正在 checkout、apply patch 或编译的工作目录；不得在一个窗口里为另一个窗口清理工作区。
2. 两个窗口可同时进行仓库读取、SHA 校验、patch apply/check、diff 检查、checkpatch、host tests、源码门槛和 schema 相关检查。
3. 为避免两次 full Bazel Image build 同时争抢内存和 CPU，ROUND124 窗口拥有第一完整构建时段。ROUND33 窗口先完成其余检查，抵达完整 Image build 前暂停，不得同时启动第二个完整 Image build。
4. ROUND124 完整构建结束、工作区清理并上传报告后，用户再通知 ROUND33 窗口继续完整 Image build。ROUND33 不得自行猜测 ROUND124 是否完成。
5. 两个窗口只上传各自任务书列出的唯一报告文件；报告分支均为 firmware-audit-v1。不得修改对方任务书、报告、源码分支或其他 Round 文件。
6. 报告必须写真实命令、退出码、SHA、工具链、PASS/FAIL/BLOCKED/NOT RUN 和清理结果。未执行不等于通过；源码审查、host tests、Image build 均不能冒充实机验证。

## 设备访问总闸门

两个任务均不需要连接平板。任何步骤如看起来需要 USB、ADB、fastboot、recovery、串口或其他设备接口，必须在连接前停止，写明需要哪种访问、具体原因和拟执行命令，交给用户决定。没有用户明确授权，不得连接或执行任何设备命令，即使只是只读采集。

禁止解锁、root、reboot、临时启动、刷写、分区读写、boot/DTBO/AVB/vbmeta 打包或验证状态修改；禁止上传原始 HOS4.3 固件、FDT、DTBO 或设备身份信息。

两项报告均完成后，Agent 停止，不自动开始下一轮。