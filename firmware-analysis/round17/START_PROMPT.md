请完整执行 GitHub 仓库中的 ROUND17 本地 Agent 任务书：

仓库：https://github.com/hhdy/matepad11-dby-w09-agent-reports
分支：main
任务书：firmware-analysis/round17/AGENT_TASK.md

先注意：ROUND16 已结束，不能重复执行旧任务。ROUND17 有两个必须由用户先完成的前置条件：
1. 用户在 Security Center → Command Security → Program Blacklist 中手动移除/允许 C:\Windows\System32\wsl.exe。
2. 用户以“以管理员身份运行”方式重新启动本地 Agent，使本次任务所需的进程上下文确实提升。

在用户明确确认这两个条件之前，不要调用 wsl.exe，也不要试图重新检查是否仍被拦截。若未提升或仍被策略拦截，按任务书停止报告。不能自行修改安全策略、关闭防护、换 shell、改名复制程序、重试其他路径或绕过 UAC。

固定方案：保留原有 C 盘 Ubuntu，不迁移、不注销、不覆盖；新装 Ubuntu-24.04 到 D:\WSL\Ubuntu-24.04。不要让 Agent 自行更改这一决定。

Store WSL 2.7.3.0 已存在且 VirtualMachinePlatform 已启用。先验证 WSL CLI；不要盲目重新安装 WSL 或开启 legacy Windows 可选组件。除非具体错误证明必需，否则不启用 legacy Microsoft-Windows-Subsystem-Linux，也不启用 HypervisorPlatform。

按任务书完成部署、官方 kernel manifest 同步、ACK commit pin 和工具链版本采集。上传脱敏报告至 firmware-audit-v1 的 firmware-analysis/round17/round17_wsl_ack_workspace_deployment.txt，上传后停止。本轮不打补丁、不编译、不连接平板、不刷机。
