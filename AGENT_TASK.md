# AGENT_TASK.md — MatePad 11 DBY-W09 固件分析任务

> **本文件是本轮本地 Agent 的唯一任务入口。** 请先完整阅读，再按顺序执行。不要要求用户重复上传已经在本机的 HarmonyOS 4.3 固件包。

## 任务目标

针对 Huawei MatePad 11 **DBY-W09**，对用户本机已有的 HarmonyOS 4.3 固件做一轮**本地只读分析**，为后续 Android / Qualcomm SM8250 / GKI 6.18.33 内核移植收集启动镜像和分区证据。

本轮只做固件文件分析和报告回传，**不编译内核、不修改固件、不连接平板、不刷机**。

## 仓库与代码位置

- 仓库：`hhdy/matepad11-dby-w09-agent-reports`
- 本任务入口：`AGENT_TASK.md`（main 分支）
- 本轮工具分支：`firmware-audit-v1`
- 工具脚本：`tools/Analyze-DBY-W09-Firmware.ps1`
- 使用说明：`tools/README-FIRMWARE-ANALYSIS.md`
- 详细 Agent 步骤：`tools/AGENT-RUN-INSTRUCTIONS.md`
- 对应 Draft PR：[#1 Add read-only DBY-W09 local firmware analyzer](https://github.com/hhdy/matepad11-dby-w09-agent-reports/pull/1)

## 第 1 步：取得工具分支

不要覆盖用户现有工作区的未提交文件。建议在临时目录单独克隆仓库：

```powershell
git clone https://github.com/hhdy/matepad11-dby-w09-agent-reports.git
cd matepad11-dby-w09-agent-reports
git fetch origin firmware-audit-v1
git switch --track -c firmware-audit-v1 origin/firmware-audit-v1
```

如果本机已有该仓库，可先检查工作区状态；不要为了切换分支而丢弃或覆盖用户未提交的改动。

读取并遵循以下文件：
1. `tools/AGENT-RUN-INSTRUCTIONS.md`
2. `tools/README-FIRMWARE-ANALYSIS.md`
3. `tools/Analyze-DBY-W09-Firmware.ps1`

## 第 2 步：在本机定位正确的 HarmonyOS 4.3 固件

优先寻找此前用于生成 `firmware-hos43/package_inventory.csv` 的本地解压目录或 ZIP。不要只按文件名猜测；应核对清单中的文件名和大小。

已知的原始固件清单包含约 43 个镜像条目，关键参考值：

| 文件 | 清单记录大小（字节） |
|---|---:|
| boot.img | 100663296 |
| dtbo.img | 25165824 |
| ramdisk.img | 2097152 |
| recovery.img | 100663296 |
| recovery_ramdisk.img | 33554432 |
| vbmeta.img | 1048576 |
| super.img | 7114729004 |

注意：
- `package_inventory.csv` 中 `super.img` 约 6.6 GiB；本轮不提取、不解包、不上传它。
- 如果找到多个候选目录/固件包，比较至少上述 5 个文件的名称与大小，并尽量与仓库原清单的 43 条记录交叉核对。
- 不要重新解压到原固件目录，不要重命名、移动或删除原始文件。
- 如果本机找不到能与清单可靠对应的固件，停止并报告候选路径和差异；不要擅自选择不确定的固件，也不要让用户重复上传之前已存在的文件。

原始清单位置：`firmware-hos43/package_inventory.csv`。

## 第 3 步：执行只读解析脚本

先确认输出目录位于固件源目录之外。使用 Windows PowerShell 5.1 或 PowerShell 7，执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\Analyze-DBY-W09-Firmware.ps1" -FirmwarePath "<确认后的本地固件目录或ZIP完整路径>" -OutputPath "$env:USERPROFILE\DBY-W09_FirmwareAnalysis"
```

要求：
- 保持默认 `MaxExtractMiB=512`。
- **不要**添加 `-HashLargeFiles`。
- **不要**运行 ADB、fastboot、WSL、固件包自带脚本或其他刷机工具。
- 脚本会清点镜像；把符合条件且不超过 512 MiB 的启动相关镜像复制到输出目录的 `payloads/`，并读取可识别的 boot / DTBO 头部字段。
- 该脚本**不会真正解包内核、ramdisk、DTB 或 super.img**。报告必须如实描述为“镜像格式/头部识别”，不能写成“已完成内核解包”。
- 超过 512 MiB 的启动相关文件会跳过复制并在报告中列出。大分区只做清单记录。
- 如果脚本报错，保留完整错误信息，停止继续处理，不要通过修改原始固件或放宽安全限制来绕过。

## 第 4 步：检查输出结果

输出目录应至少包含：

| 文件 | 需要确认的内容 |
|---|---|
| `partition_inventory.csv` | 镜像路径、文件名、大小、分类 |
| `firmware_analysis.txt` | 文件 magic、boot header 字段、DTBO header 字段、跳过项、工具可用性 |
| `selected_images_sha256.csv` | 本地复制镜像的大小与 SHA-256 |
| `summary.json` | 设备目标、源类型、清单数量、输出文件和安全说明 |
| `payloads/` | 本地分析工作副本，不得上传公开仓库 |

逐项检查：
1. 四份报告都存在且不是空文件。
2. 报告中的镜像数量是否与原清单接近；缺少哪些文件要说明。
3. 是否正确识别 `boot.img`、`dtbo.img`、`ramdisk.img`、`recovery.img` 和各类 vbmeta。
4. 将报告中检测出的 boot header version、kernel size、ramdisk size、cmdline、DTB size、DTBO entry count 等字段原样记录，不要猜测缺失值。
5. 检查上传报告不包含设备序列号、MAC、访问令牌、个人目录敏感信息或其他私人数据。必要时仅在报告副本中脱敏，不要修改源固件。
6. 确认源固件的文件名、大小和时间戳未被改动。

## 第 5 步：把报告回传 GitHub

只允许上传以下四个文本/CSV/JSON 报告：

- `partition_inventory.csv`
- `firmware_analysis.txt`
- `selected_images_sha256.csv`
- `summary.json`

目标目录：`firmware-analysis/round1/`

推荐在当前 `firmware-audit-v1` 分支创建该目录并提交报告。上传前进行隐私检查。

**严禁上传：**
- `payloads/` 目录；
- `boot.img`、`dtbo.img`、`ramdisk.img`、`recovery*.img`、`vbmeta*.img`；
- `super.img`、`vendor.img`、`odm.img` 或任何固件二进制；
- 包含令牌、设备序列号或 MAC 地址的文件。

使用当前已经配置的 GitHub 登录/连接器权限。如果没有上传权限，保留本地四份报告并告知用户；**不要索要或创建 PAT，也不要把 PAT 写入 remote URL、脚本或仓库。**

不要自行合并 PR #1，不要直接改写 main 分支。

## 第 6 步：完成后给用户的报告

请用中文简要汇报：

1. 找到的固件目录/ZIP 名称（不要披露含个人用户名的完整路径）。
2. 是否与原始 43 项清单匹配；匹配/缺失的关键镜像。
3. 脚本是否成功运行；PowerShell 版本；完整错误（如有）。
4. boot header version、kernel size、ramdisk size、cmdline、DTB size、DTBO entry count 等实际检测结果。
5. 哪些镜像因超过限制而跳过。
6. 四份报告是否成功上传，以及 GitHub 提交链接。
7. 明确指出本轮没有做内核编译、没有真实解包镜像、没有连接设备或写入任何分区。

## 本轮完成标准

只有在本地脚本成功运行、四份报告经过隐私检查并上传至 `firmware-analysis/round1/` 后，才可标记为完成。否则必须报告具体阻塞点，不能虚报成功。


---

## Next task

Round 3 已完成。请继续读取仓库根目录的 [`AGENT_TASK_ROUND4.md`](./AGENT_TASK_ROUND4.md)，按 round3 已验证的 Logical Partition extent 只读提取 vendor / odm 并盘点模块、固件和 VINTF。不要合并 PR #1，不上传任何固件二进制，也不要要求用户重新上传已有固件。


---

## Parallel task: Xiaomi Pad 5 Pro split-package audit

用户另有两套 Xiaomi Pad 5 Pro 分卷移植包，位于本地 `D:\123pan\Downloads`。在不影响 DBY-W09 round3 分析的前提下，可并行读取 [`AGENT_TASK_XIAOMI_ZIP.md`](./AGENT_TASK_XIAOMI_ZIP.md)，先识别两套分卷组、校验完整性和列出包内结构。不要把原始压缩包或固件二进制上传到 GitHub；不要运行包内脚本或刷机。


---

## Latest handoff

- Round 1, round 2, and round 3 reports are available on `firmware-audit-v1`.
- Round 3 confirmed two identical metadata slots and the Huawei logical partitions `vendor` and `odm`; both remain unextracted.
- Read [`AGENT_TASK_ROUND4.md`](./AGENT_TASK_ROUND4.md) next. Extract only these two local work copies by the AOSP-verified LINEAR extent mapping; keep source firmware read-only.
- Xiaomi audit found one complete `elish` split-ZIP set; a second package was not found under `D:\123pan\Downloads`. Do not scan unrelated user folders unless user supplies another path.
- PR #1 remains Draft and must not be merged unless the user explicitly authorizes it.
