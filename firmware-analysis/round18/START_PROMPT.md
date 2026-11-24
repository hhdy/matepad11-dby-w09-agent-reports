执行 ROUND18。首先完整读取 main 分支 firmware-analysis/round18/AGENT_TASK.md，并严格遵守。

ROUND16 已完成 WSL Ubuntu 24.04.5 部署、官方 Repo 58 projects 同步，以及 common 精确 pin 到 ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a。Clang r584948c、Rust 1.91.1.p3、Bazel 8.7.0 已核验。

严禁重复部署、安装 Ubuntu、repo init、repo sync 或重新下载 kernel source/toolchain。现有工作区是 /home/kerneldev/work/matepad11/ack-6.18.33。先只读复核，从该 workspace 建立独立 ack-6.18.33-round18 副本；所有修改仅在副本内进行，保持原工作区 pristine。

本任务已明确授权在副本中真实应用指定补丁、运行 git apply/diff/checkpatch、UFS/QMP PHY dt_binding_check 和 dtc/dt-validate fixtures、Kleaf BUILD patch、Bazel query/cquery、实际 Kconfig/.config 解析及首次 Image-only 编译。补丁 SHA/来源、ROUND57 跳过原因、ROUND37 排除原因和安全边界以任务书为准。

WSL VM 约 7.3 GiB 内存。首次构建使用保守 jobs=2；不得修改 .wslconfig。如有明确 OOM，保存证据后暂停内存配置变更并等待单独授权；其他低资源检查仍继续。不得主动使用 sudo/passwd。

最终只上传脱敏报告到 firmware-audit-v1:firmware-analysis/round18/round18_patch_schema_kconfig_first_build.txt。不得修改 main / protected DTS / PR #1 / 二号 AI分支；不得连接或操作平板，不刷机、不写分区。失败要定位修复并继续其他可执行阶段，不得退回环境部署工作。
