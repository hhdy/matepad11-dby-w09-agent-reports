# PREP03-REDELIVERY — 重新交付两份私有二进制归档

- 发布者 / 总负责人：**1号 AI（ChatGPT）**
- 执行者 A：**WorkBuddy Window A / 1号 Agent**
- 执行者 B：**WorkBuddy Window B / 2号 Agent**
- 注意：**2号 Agent 不是 2号 AI**。本任务不需要 2号 AI，也不要把两个角色混淆。
- 设备：Huawei MatePad 11 DBY-W09 / SM8250
- 目标：Android 17 ACK 6.18.33 内核 bring-up；后续 DerpFest Android 17
- 任务性质：只重新交付 PREP03 已经导出的文件，不重新分析、不重编译、不访问设备。

## 0. 本次任务的唯一目的

用户已经确认 PREP03 执行完毕，但用户不知道两份 ZIP 保存在哪里。请不要让用户自己查找旧目录，也不要只回复“已完成”或给出一个用户无法访问的本机路径。

**每个窗口都必须把自己的 ZIP 重新交付为当前 WorkBuddy 对话中的可下载附件 / 文件产物**，并额外复制一份到用户桌面上容易找到的位置。

如旧 ZIP 仍存在，直接校验后复制并重新附加；如旧 ZIP 不存在，则只使用该窗口原工作区中仍存在的原始文件重新打包。不得重新读取平板或重新构建内核。

## 1. 统一交付位置与附件要求

每个窗口在本机建立以下目录（使用当前 Windows 用户的 Desktop Known Folder，不要猜测用户名）：

`%USERPROFILE%\Desktop\PREP03_REDELIVERY\WindowA\`

或

`%USERPROFILE%\Desktop\PREP03_REDELIVERY\WindowB\`

将本窗口 ZIP 保存到对应目录，并在本窗口的 WorkBuddy 回复中**直接附加 ZIP 文件本体，生成可点击下载的附件**。

重要：
1. 只回复文件路径不算交付。
2. 只提供 GitHub 链接不算交付。
3. 不要把原厂固件、内核、DTB、ABL 等二进制提交到公开 GitHub。
4. 若 WorkBuddy 当前界面不支持直接附加文件，必须在回复中明确说明“附件能力受限”，同时给出上述桌面目录中的完整绝对路径、文件大小、SHA-256，并将 ZIP 放在桌面目录中。不要声称已附加。
5. 不要要求用户自己从隐藏缓存、临时目录或 Agent 私有工作区寻找文件。

## 2. Window A / 1号 Agent — 设备启动链输入归档

归档文件名必须为：

`PREP03_WindowA_Device_Inputs.zip`

只使用 **Window A 自己的既有工作区**。不要访问 Window B 的目录、缓存、日志或会话；不要连接平板。

ZIP 根目录应包含以下文件（若存在）：

| 文件名 | 预期大小 | 预期 SHA-256 |
|---|---:|---|
| `stock-live-boot.img` | 100,663,296 B | `7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8` |
| `stock-live-ramdisk.img` | 2,097,152 B | `4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb` |
| `candidate-dby-w09.dtb` | 108,680 B | `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` |
| `abl-hos43-pe.bin` | 2,597,064 B | `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404` |

可选项：若 Window A 原工作区中已有以下文件，可一并放入；不得为此重新读取设备或下载固件：
- `stock-package-boot.img`，100,663,296 B，SHA-256 `027f88fd6f318523925ca27a4d681d17a9bbca904b0c471ccc05e651d3da19b8`。

必须同时包含：
- `SHA256SUMS.txt`：逐个记录实际入包文件的大小和 SHA-256。
- `provenance.txt`：说明每个文件来自哪个已有 ROUND / 报告 / 本地构建或备份副本；逐项标记“匹配 / 缺失 / 哈希不符”。
- 如有缺失或不匹配，必须如实记录，不得伪造、替代、重命名其他文件来冒充。

特别注意：
- 不得用 ROUND64 的 ramdisk 副本冒充 ROUND155 live ramdisk。
- 不得自行修改 DTB、boot 或 ramdisk。
- 不得包含 vbmeta 原始镜像、私钥、签名密钥、用户数据或其他无关分区。

## 3. Window B / 2号 Agent — 已成功构建内核归档

归档文件名必须为：

`PREP03_WindowB_Kernel_Inputs.zip`

只使用 **Window B 自己的既有工作区**。不要访问 Window A 的目录、缓存、日志或会话；不要重新编译内核。

应包含：
1. 已成功构建的 ARM64 原始内核 `Image`。
2. 同一次成功构建已产出的 `Image.gz` 或其他压缩形式（仅当原本就存在；禁止新压缩、改写或猜测 ABL 要求的格式）。
3. 该次成功构建实际使用的 `.config`。
4. `kernel-release.txt`（记录 kernel release；若主机无法执行目标 Image，则记录构建日志里对应的 release 信息并说明）。
5. `build-provenance.txt`：准确记录报告路径、分支、提交、source tree SHA、config SHA、Kleaf target、成功退出码、文件原始路径、大小、SHA-256。
6. `SHA256SUMS.txt`：逐个记录实际入包文件的大小和 SHA-256。

原始构建身份基准：
- ACK commit：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- 候选源码树 SHA：`c56d93eafa35057d65176db6594d67d5144868a0`
- 预期已接受 config SHA：`efb663e9c792840e2cfbbc03e115996bb486aefe964b448c1717828c55bf042f`

如果本地实际构建身份与上述值不同，必须如实记录差异；不要静默替换另一个 Image，不要重新编译，不要 strip / patch / recompress。

不得将内核二进制、私有凭据或签名密钥提交到公开 GitHub。

## 4. 打包前后必须执行的检查

1. 查找本窗口先前生成的 PREP03 ZIP；若存在，先计算哈希并检查其内部清单。
2. 若旧 ZIP 不存在，再从本窗口已有原始文件重新打包。
3. ZIP 内只能放入本任务指定文件、清单和来源说明。
4. 打包后重新列出 ZIP 内容，逐个核对文件大小和 SHA-256。
5. 对整个 ZIP 计算 SHA-256。
6. 检查桌面目标目录确实存在文件，文件大小大于 0。
7. 在 WorkBuddy 回复中直接附加 ZIP 文件，并给出 ZIP SHA-256、文件清单、缺失项。
8. 如果某一项缺失，不得因此停止交付其他已经存在的文件；将可用文件先装入 ZIP，明确标出缺失项。

## 5. 严格禁止

- 不执行 ADB、USB、fastboot、EDL、串口或任何实时设备访问。
- 不执行 root 命令、重启、临时启动、解锁、分区写入、擦除、格式化或刷机。
- 不重新编译内核，不重新编译 DTB，不重新生成 ABL。
- 不修改 AVB/vbmeta，不提取或使用签名私钥，不绕过设备安全机制。
- 不跨窗口读取文件或交换私有工作区内容。
- 不将私有二进制公开提交到 GitHub。

## 6. 回复模板（每个窗口必须完整填写）

```text
PREP03 重新交付完成
执行窗口：Window A / Window B
ZIP 文件名：
桌面保存路径：
WorkBuddy 当前对话附件：已附加 / 界面不支持附加（如实选择）
ZIP 大小：
ZIP SHA-256：

内部文件：
- 文件名 | 大小 | SHA-256 | 状态（匹配/缺失/不符）

缺失项及原因：
来源与构建身份：
设备访问：未执行
重编译：未执行
```

## 7. 结束条件

Window A 和 Window B 各自把 ZIP 作为**当前任务回复的可下载附件**交付给用户后，各自停止。不要擅自开始下一轮测试或启动包组装。

**AI1 收到两份 ZIP 后负责真实二进制解析、Android 17 ACK 6.18.33 候选启动包组装和主机端验证。**
