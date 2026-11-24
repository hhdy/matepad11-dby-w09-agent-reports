执行 ROUND18。首先完整读取 main 分支 firmware-analysis/round18/AGENT_TASK.md，并严格遵守。

ROUND16 已完成 WSL Ubuntu 24.04.5 部署、官方 Repo 58 projects 同步，以及 common 精确 pin 到 ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a。Clang r584948c、Rust 1.91.1.p3、Bazel 8.7.0 已核验。

严禁重复部署、安装 Ubuntu、repo init、repo sync 或重新下载 kernel source/toolchain。现有工作区是 /home/kerneldev/work/matepad11/ack-6.18.33。先只读复核，从该 workspace 建立独立 ack-6.18.33-round18 副本；所有修改仅在副本内进行，保持原工作区 pristine。

本任务已明确授权在副本中真实应用指定补丁、运行 git apply/diff/checkpatch、UFS/QMP PHY dt_binding_check 和 dtc/dt-validate fixtures、Kleaf BUILD patch、Bazel query/cquery、实际 Kconfig/.config 解析及首次 Image-only 编译。补丁 SHA/来源、ROUND57 跳过原因、ROUND37 排除原因和安全边界以任务书为准。

WSL VM 约 7.3 GiB 内存。首次构建使用保守 jobs=2；不得修改 .wslconfig。如有明确 OOM，保存证据后暂停内存配置变更并等待单独授权；其他低资源检查仍继续。不得主动使用 sudo/passwd。

最终只上传脱敏报告到 firmware-audit-v1:firmware-analysis/round18/round18_patch_schema_kconfig_first_build.txt。不得修改 main / protected DTS / PR #1 / 二号 AI分支；不得连接或操作平板，不刷机、不写分区。失败要定位修复并继续其他可执行阶段，不得退回环境部署工作。

补充的强制修订（ROUND18 revision 1）：
- main 上旧 ROUND32 补丁 blob `efe2d932da34716c631de22d89aba19730cc7f50` 已废弃，禁止应用。固定 ACK 已在 `qcom,sc7180-ufshc.yaml` 选择 SM8250，不得在 `qcom,ufs.yaml` 重复添加 compatible。
- 二号 AI 的修正版候选 blob `fade9cb2bdfd544c6736c7595af8380726edf318` 也真实 `git apply --check` 失败，禁止原样应用。必须在 ROUND18 副本基于固定 ACK 文件上下文重新制作最小补丁，先确认 `git apply --check` 返回 0，再执行 apply/diff-check，再做 schema 验证。
- 如 clock schema gate 暂时无法通过，准确记录 BLOCKED，仍继续 Kleaf/Bazel/Kconfig 和 Image-only 构建。
- ROUND18 任务书为 revision 1；执行前以 main 当前 `firmware-analysis/round18/AGENT_TASK.md` 为准。二号 AI 分支保持只读，不得修改。
