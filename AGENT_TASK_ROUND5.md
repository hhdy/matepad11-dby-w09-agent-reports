# AGENT_TASK_ROUND5.md — 使用可信 EROFS 工具读取 vendor / odm 内容

> 接续 round4。vendor.img 与 odm.img 已在本地选择性提取成功，文件系统签名为 EROFS，但内容清单因缺少可信 EROFS 工具而 BLOCKED。本轮目标是先解决工具链可信度，再只读枚举文件系统、内核模块、固件文件和 VINTF 配置。

## 一、已知输入与不可变边界

本地分析工作副本来自 round4，优先读取 round4 summary 中的真实输出目录；不要重新从 super.img 提取，除非本地副本丢失或长度校验失败。

Round4 已验证：
- vendor.img：1,022,038,016 bytes；EROFS magic `0xE0F5E1E2 @ offset 1024`。
- odm.img：51,593,216 bytes；EROFS magic `0xE0F5E1E2 @ offset 1024`。
- 本地 SHA-256 已核验，完整哈希留在本地，不公开。
- 原 super.img 源快照未改变。
- EROFS 内容解析 BLOCKED；无模块、固件、VINTF 数据可据此推断。
- 不要把“EROFS signature PASS”描述成“文件系统内容已验证”。

本任务严格不连接设备、不刷机、不 root、不写分区、不挂载可写文件系统、不修复镜像、不编译内核。

## 二、可信 EROFS 工具来源核验（最高优先级）

EROFS 官方用户空间工具是 `erofs-utils`，包括：
- `dump.erofs`：读取 superblock / image statistics / inode 信息 / 目录列表 / 文件内容。
- `fsck.erofs`：检查 EROFS 文件系统完整性；若使用 `--extract` 会向目标目录写出文件，因此默认本任务禁止使用该选项。
- 官方源码上游：`https://git.kernel.org/pub/scm/linux/kernel/git/xiang/erofs-utils.git`
- 官方代码镜像：`https://kernel.googlesource.com/pub/scm/linux/kernel/git/xiang/erofs-utils/`
- AOSP 镜像：`https://android.googlesource.com/platform/external/erofs-utils/`
- Linux kernel EROFS 文档：`https://www.kernel.org/doc/html/latest/filesystems/erofs.html`
- 官方安装/构建文档：`https://erofs.docs.kernel.org/en/latest/install.html`

工具来源检查：
1. 在 Windows 当前环境只检测、不安装：
   `Get-Command dump.erofs,fsck.erofs,erofsfuse,docker,git,gcc,clang,cmake,ninja,make,mingw32-make,7z -ErrorAction SilentlyContinue | Format-List Name,Source,Version`
2. 对任何现存 EROFS 工具记录绝对路径、版本、SHA-256、签名/包管理来源和依赖 DLL。不能确认来源的 EXE 不运行。
3. 检查本机是否存在可用 Docker Desktop / Docker Engine，以及是否已经有可用的 Linux image；只运行 `docker --version`、`docker image ls`、必要的 `docker info` 等环境检测。不要自动 pull image，不要运行未知容器。
4. 检查本地是否有 MSYS2 UCRT64 / MinGW-w64 / Cygwin 工具链；只检测。不要通过修改执行策略、关闭安全软件、绕过组织策略或切换到未授权环境来执行构建。
5. 检查系统是否已包含可信 `erofs-utils` 源码副本；记录 remote URL、tag、commit SHA、工作区是否干净。

### 当前上游状态核验（不能把邮件补丁当成已发布二进制）

- EROFS 邮件列表 2026-11-02 有一组原生 Windows / MinGW 支持补丁（包含 Win32 I/O 兼容层及 Docker cross-build 目标）。
- 2026-11-04 有后续 Windows 临时文件和 CRLF 修复补丁。
- 2026-11-22 出现“将 Windows binaries 加入 release artifacts”的补丁提案。
- 上述邮件/补丁提案本身不是已发布 Windows EXE 的证明；必须在执行时核实它们是否已合并进官方上游、对应 commit/tag 是否存在、Windows binaries 是否已由官方发布流水线产出。
- 不得从邮件正文附件、第三方网盘或个人 fork 下载并执行二进制。
- GitHub `erofs/erofs-utils` 页面如显示无 releases，不要把它当作官方发布；优先以上游 kernel.org tree / 官方 AOSP mirror 和可验证的官方发行包为准。

优先可用方式顺序：
A. 本机已有、来源可验证的官方 `dump.erofs` / `fsck.erofs`。
B. 官方仓库确实已发布且有 SHA-256 / 签名 / release provenance 的 Windows binaries；先验证哈希/签名，再记录版本；如果发布信息尚未落地，不得使用。
C. 如果本机 Docker 已安装、daemon 已正常运行，且已经有可信构建镜像，可评估用官方 erofs-utils 源码在容器内构建/运行 Linux 工具。不得自动 pull 未缓存镜像；不得执行未知 Dockerfile。
D. 如果官方上游原生 Windows 支持已正式合并、且本机已有 MinGW 工具链，则可按上游正式 commit 构建；依赖必须已存在，不能自动安装。
E. 全部不满足时，停止在工具来源核验阶段，明确 BLOCKED。不要自行实现 EROFS 解码器，也不要触碰 WSL 安全策略。

若需构建：
- 只使用官方上游仓库和明确的 release tag / commit SHA。
- 优先使用当前官方稳定标签；在执行时核对最新 tag / commit，记录确切来源。
- 编译只生成本地工具，不安装到系统路径；输出到独立目录。
- 只构建读取/检查需要的 `dump.erofs` 与 `fsck.erofs`；不需要 `mkfs.erofs`、`mount.erofs`、`erofsfuse`。
- 不执行 `make install`，不改 PATH / 系统注册表，不写系统目录。
- 保存完整构建日志、源码 commit、配置开关、工具 hash 和依赖版本。
- 对工具运行 `--version`、`--help`，确认实际支持的参数后再分析镜像。

## 三、只读 EROFS 完整性和目录枚举

仅在工具来源核验成功后执行。对 vendor.img 和 odm.img 分开处理：

### 1. 初步只读检查
- `dump.erofs -V`、`dump.erofs --help`；
- `dump.erofs -s <image>` 读取 superblock；
- `dump.erofs -S <image>` 输出文件系统统计；
- `fsck.erofs -V`、`fsck.erofs --help`；
- 如当前版本支持，运行普通只读完整性检查 `fsck.erofs <image>`；不要带 `--extract`、`--no-sbcrc`、修复或写入选项。
- 记录 magic、block size、feature incompat/compat bits、压缩算法、UUID（如有，公开报告应脱敏）、inode 数量、数据块和压缩统计。
- 如果检查失败，停止目录深挖并记录原始错误。

### 2. 目录递归枚举
根据实际 `dump.erofs --help` / man page 确认参数语法。只使用官方 dump 工具读取镜像：
- 从根目录开始：`dump.erofs --ls --path=/ <image>`
- 对输出中的目录递归执行 `--ls --path=<directory>`，生成路径、类型、inode NID、文件大小（工具能提供时）、权限/UID/GID（可得时）的目录索引。
- 禁止把输出写入源镜像；所有日志写到独立报告目录。
- 设置合理的最大目录深度、条目数和单文件输出限制；超过限制标 PARTIAL，不要无限递归。
- 对 vendor / odm 所有目录均收集文件名，但对大体积二进制只记录名称/路径/大小，不读文件内容。

优先目录（按实际存在情况，不假设一定存在）：
- `/lib/modules`、`/vendor/lib/modules`、`/vendor_dlkm/lib/modules`
- `/lib/firmware`、`/vendor/firmware`、`/vendor/firmware_mnt/image`、`/firmware`
- `/etc/vintf`、`/vendor/etc/vintf`、`/odm/etc/vintf`
- `/etc/init`、`/vendor/etc/init`、`/odm/etc/init`
- `/etc/permissions`、`/vendor/etc/permissions`
- `/etc/ueventd*`、`/vendor/etc/ueventd*`
- `/etc/selinux`、`/vendor/etc/selinux`

### 3. 提取并读取必要的小型文本配置（仅本地）

只有在 `dump.erofs --help` 确认存在 `--cat` / `--path` 且行为清楚时：
- 使用 dump 工具将 manifest、compatibility matrix、init rc、ueventd、permissions 等小型文本文件输出到本地单独目录。
- 按白名单逐个读取，设置单文件最大 4 MiB；拒绝符号链接逃逸和异常超大文件。
- 不输出原始序列号、MAC、设备 token、证书私钥、Wi-Fi 配置、账号数据。
- 公开 GitHub 只上传脱敏摘要，不上传原始 manifest 文件。

### 4. 内核模块清单与 vermagic

先列出模块，不执行、不加载模块：
- 记录 `.ko`、`.ko.xz`、`.ko.gz`、`.ko.zst`、`.ko.lz4` 等相对路径和文件大小。
- 查找模块索引文件：`modules.dep`、`modules.alias`、`modules.softdep`、`modules.load`、`modules.blocklist`。
- 只在 `dump.erofs --cat` 或其他已验证的只读接口能安全地把单个模块写到本地隔离工作目录时，才提取少量模块样本用于 `modinfo` / `readelf` 检查；模块二进制永远不上传。
- 若模块被压缩，只有本机已有可信解压工具才解压到本地；不要安装解压工具。
- 记录 vermagic、depends、ELF class/machine、license、签名字段（若可得）。
- 不能读出 vermagic 时，标记 UNKNOWN，不从文件名推断内核版本。
- 不执行模块、不尝试 insmod/modprobe。

### 5. 固件与 VINTF
- 固件候选按路径和名字清点，类别只是候选标签（UFS / Qualcomm / GPU / Wi-Fi / Bluetooth / DSP / camera / display / touch），不把名称当成硬件存在证明。
- VINTF 读取 vendor / odm manifest 与 compatibility matrix，记录 HAL interface / instance / version / transport、kernel FCM level、文件路径。
- 若存在 vendor / odm manifests，注意 merge / fragments 目录及多个 manifest，分别记录，禁止只挑一份。
- 只上传脱敏汇总，不上传 firmware binary、不上传 manifest 原件。
- 将模块依赖与 round3 Huawei DTB/DTBO 的 SoC、board ID、PMIC、GPIO、panel、touch 证据交叉分析。

## 四、GKI 6.18.33 可移植性结论（本轮只研究，不编译）

基于 round1 已确认的旧内核 `4.19.157-perf+`：
- 区分 GKI / vendor module / board-specific drivers；
- vermagic、KMI、symbol dependency、旧 vendor interface、模块签名和压缩格式；
- 标出 Qualcomm common driver 候选与 Huawei 板级专有部分；
- 对每个 driver group 分类：POTENTIAL_COMMON / HUAWEI_BOARD_SPECIFIC / LEGACY_VENDOR_ABI / UNKNOWN；
- 给出移植到 Android GKI 6.18.33 的风险与依赖，不宣称 4.19 .ko 可直接加载到 6.18；
- Xiaomi elish 线刷包无源码，仍仅为同平台参考，不可替代 Huawei vendor 数据。
- 不下载 GKI 源码、不启动 Kleaf、不编译内核、不解除 WSL 安全策略。本轮专注读清 vendor / odm。

## 五、输出与 GitHub 回传

本地输出目录建议：
`D:\DBY-W09_FirmwareAnalysis_round5\`

至少生成：
- `erofs_toolchain_provenance.txt`
- `vendor_erofs_superblock.txt`
- `odm_erofs_superblock.txt`
- `vendor_directory_inventory.csv`
- `odm_directory_inventory.csv`
- `kernel_modules_inventory.csv`
- `firmware_inventory.csv`
- `vintf_summary.txt`
- `gki_618_portability_assessment.txt`
- `round5_summary.json`

只允许上传脱敏 TXT / CSV / JSON / Python 源码；禁止上传任何 EROFS image、模块、固件、manifest 原件或本地 SHA-256 完整值。
不要上传绝对路径、用户名、设备序列号、MAC、token、PAT。
上传到 `firmware-analysis/round5/`，分支 `firmware-audit-v1`。
不要改写之前 round1–round4 历史报告，不要合并 PR #1，不要修改 main 之外的 branch protection。

## 六、停止条件与完成标准

若没有可信可运行的 EROFS 工具或允许的构建环境：
- 仅提交 `erofs_toolchain_provenance.txt` 与 `round5_summary.json`；
- 将所有 filesystem content / module / firmware / VINTF 项标为 BLOCKED；
- 不自行写格式解析器，不下载未知 EXE，不更改 WSL/系统安全设置。

若工具可用，分别报告：
- 工具来源、版本、SHA-256、依赖；
- vendor / odm EROFS superblock 与 integrity 检查状态；
- 目录完整/部分枚举情况和条目数；
- 模块数量、vermagic 证据及依赖；
- 固件文件清单；
- VINTF HAL / instance / version / FCM；
- 对 GKI 6.18.33 的可移植性评估；
- 哪些信息仍 UNKNOWN。
明确说明整个过程没有挂载可写文件系统、没有修复、没有连接设备、没有刷机、没有编译内核、没有加载模块。
