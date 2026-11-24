# AGENT_TASK_ROUND6.md — 仅做本机 GKI 构建环境探测（不重复上游研究）

> **本任务只包含本地 Agent 必须在用户电脑上完成的检查。** GKI 分支版本、官方 release、Android 兼容矩阵、Kleaf BUILD.bazel 与 KMI 规则已经由 ChatGPT 独立查阅官方资料，并写在 `kernel-baseline/round6/upstream-baseline-research.md`。请勿重复做网页搜索或把上游研究重新交回 Agent。

## 1. 项目事实（不需要重新分析）

设备：Huawei MatePad 11 DBY-W09，Qualcomm KONA / SM8250，原系统 Android 12 / API 31，原内核 4.19.157-perf+。ROUND1–ROUND5 已有报告，不要重复索取或重提取固件。

ChatGPT 已完成的上游结论：
- 当前 Google `android17-6.18` 活跃源码分支 Makefile 版本为 6.18.33。
- 当前官方 GKI release 页面所列 2026-09 release series 为 6.18.32，2026-11 无 release；不能把 6.18.33 branch HEAD 说成 certified GKI release。
- Google 兼容矩阵：Android 12 对应 `android12-5.10`；`android17-6.18` 对应 Android 17。Android 12 userspace + 6.18.33 不属于官方支持组合。
- `android17-6.18` 的 `BUILD.bazel` 包含 Kleaf，定义 ARM64 `kernel_aarch64` / `kernel_aarch64_16k`，GKI target 使用 KMI enforcement 和 symbol list。
- 详细证据、SHA 与官方资料链接见：
  `kernel-baseline/round6/upstream-baseline-research.md`

## 2. 唯一本机任务：Windows PATH 工具可用性探测

只在 Windows PowerShell 运行只读检测。请不要调用 WSL，不执行编译，不下载、不安装、不修改系统配置。

```powershell
$names = @('git','repo','bazel','bazelisk','python','python3','clang','clang-cl','make','ninja','gcc','java')
$results = foreach ($name in $names) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if ($cmd) {
    [pscustomobject]@{
      Name = $name
      Status = 'FOUND_ON_PATH'
      Source = [System.IO.Path]::GetFileName([string]$cmd.Source)
      CommandType = [string]$cmd.CommandType
    }
  } else {
    [pscustomobject]@{
      Name = $name
      Status = 'NOT_FOUND_ON_PATH'
      Source = ''
      CommandType = ''
    }
  }
}
$results | Format-Table -AutoSize
```

要求：
- 只记录命令是否在当前 PowerShell PATH 可见。
- 不要运行 `git --version`、`bazel --version` 等可执行文件；本轮不需要运行任何外部工具。
- 不扫描整个 C/D 盘，不扫描无关用户目录，不猜测软件安装位置。
- 不调用 `wsl.exe`，不调用 `repo init` / `repo sync`，不调用 `git clone`，不执行 Bazel / Make / Clang。
- 不安装 MSYS2、MinGW、Docker、Ubuntu 或任何依赖。
- 如果本地命令被策略拦截，只记录拦截情况，立刻停止，不要尝试替代调用或绕过。

## 3. 输出报告

本地建议目录：`DBY-W09_GKI_Baseline_Round6`

只生成两个脱敏文本报告：
1. `build_environment_probe.txt`：检测日期、PowerShell 主版本、上述命令 PATH 状态表。
2. `round6_summary.json`：`local_probe_status`、每个工具的 PATH 状态、本轮边界布尔值。

JSON 状态建议：
- 所有检测成功：`LOCAL_PROBE=COMPLETE`
- PowerShell 本身不可用或被命令安全策略拦截：`LOCAL_PROBE=BLOCKED`

上传前删除用户名、机器名、完整本地路径、设备序列号/MAC、访问令牌/PAT。不能上传任何 EXE、DLL、固件、镜像、模块、内核二进制或完整本地 SHA-256。

上传到 `firmware-audit-v1` 分支：
- `kernel-baseline/round6/build_environment_probe.txt`
- `kernel-baseline/round6/round6_summary.json`

如果没有该分支上传权限，只保留本地报告并回报；不索要 PAT，不改 remote URL，不碰 PR #1。

## 4. 严格禁止

- 不做任何上游网页搜索或 Gitiles 研究（该工作已经完成，直接引用第 1 节的 ChatGPT 报告）。
- 不执行 repo sync / git clone / Bazel / Make / Clang / Kleaf。
- 不下载 GKI kernel、GKI boot image 或任何大文件。
- 不调用 WSL，不更改 Windows 命令安全策略或执行策略。
- 不连接设备、不刷机、不解锁、不 root、不写分区、不加载模块。
- 不解析或修改 vendor / odm；ROUND5 EROFS 内容层仍 BLOCKED。
- 不上传固件及私有数据。

## 5. 完成标准

只有在 PowerShell 本机只读 PATH 探测完成、两份脱敏文本报告已上传（或明确报告上传阻塞）后才结束本任务。

本轮只确认“本机哪些构建命令可以在 PATH 中被找到”。**不得写成源码已同步、Kleaf 已执行、构建环境完整或内核已编译。**
