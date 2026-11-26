# ROUND140 — 2号 Agent 独立构建复现与首启前测试任务书

- 执行方：**2号 Agent（第二个本地执行 Agent）**
- 派发方：AI1（ChatGPT）
- 明确区分：本任务不是 2号 AI 的任务，也不是当前执行 ROUND139 的 WorkBuddy Agent 的任务
- 设备：Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- 内核：ACK android17-6.18.33_r00
- 固定上游 commit：8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- 已验收候选 patch tree：afe9517f8062b96bfeb5b4dd5714942861e6a44b
- 任务类型：独立离线复现、构建测试、产物校验、首启前证据交叉核验
- 设备访问权限：**未授权**
- 报告提交分支：agent2/round140-independent-preboot-tests
- 报告路径：firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md

---

## 0. 任务目的与角色隔离

ROUND140 由 **2号 Agent** 独立执行，目标是从另一套隔离工作目录验证 AI1 已验收的 R3 候选内核能否被独立复现，并在已有 ROUND138 / ROUND139 证据基础上制作首启前测试矩阵。

必须遵守角色定义：

1. **AI1（ChatGPT）**：负责任务设计、源码移植、结果独立审查和最终首启门槛判定。
2. **2号 AI**：独立 AI 协作者，不是本任务执行者。
3. **WorkBuddy Agent**：当前负责 ROUND139 的本地 Agent，不得与 ROUND140 共用工作树、构建输出目录或报告文件。
4. **2号 Agent**：本任务唯一执行者，必须独立记录实际执行命令、返回码、输入身份和输出哈希。

本任务允许 2号 Agent 在本地建立独立 worktree 并执行构建测试，但不得修改已验收源码、补丁、设备分区或任何启动镜像。不得把本任务转交给 WorkBuddy Agent 或 2号 AI。

## 1. 已知基线（不得擅自改变）

ROUND135 R3 已通过离线构建和 DTB 集成验收，范围仅限 BUILD/DTB INTEGRATION，不代表设备可启动。

已知基线：

| 项目 | 已验收值 |
|---|---|
| 上游 ACK commit | 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a |
| 23-patch 最终 content tree SHA | afe9517f8062b96bfeb5b4dd5714942861e6a44b |
| tree17 SHA | 77e2b2b1515b3813f7538aedffe4c5a4e90edb57 |
| 最终 .config SHA256 | 0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15 |
| 目标 DTB | qcom/huawei-dby-w09.dtb |
| 已验收 DTB 大小 | 108648 bytes |
| 已验收 DTB SHA256 | cab82fe3901dbb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e |
| 已验收 Image 大小 | 44820992 bytes |
| 已验收 Image SHA256 | ee94c4fa0364018244d4aa467dcc4318a816b53363a25b3b717acb6a002e82c6 |
| 构建目标 | //common:dby_w09 |
| 已验收构建命令 | tools/bazel build //common:dby_w09 --jobs=2 |

23 个补丁的完整顺序、文件身份及受控 offset 以 ROUND135 R3 最终报告为准。不得自行重排、改写、重新生成或“修复”任何补丁。

参考报告：
- ROUND135 R3： https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round135/r3-validation/ROUND135_R3_FINAL_REPORT.txt
- AI1 R3 审核： https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round135/AI1_ROUND135_R3_FINAL_AUDIT.md
- ROUND138 Agent 报告： https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round138/round138-dtbo-variant-and-live-fdt-delta-audit.md
- ROUND138 AI1 验收： https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round138/AI1_ROUND138_INDEPENDENT_REVIEW_AND_ROUND139_DISPOSITION.md
- ROUND139 任务书： https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/firmware-analysis/round139/AGENT_TASKBOOK_HOS43_PMIC_UFS_AND_BOOT_AVB_AUDIT.md

ROUND139 目前由 WorkBuddy Agent 负责。如果 ROUND139 报告在 ROUND140 执行时尚未提交，2号 Agent 仍应先完成本任务中可独立进行的源码和构建复现部分；不得读取半成品工作目录、干扰对方工作或自行要求对方中断。报告未出现时，在 ROUND140 中将 ROUND139 交叉核验项记为 PENDING / BLOCKED，并按本任务规定停止，不得声称首启门槛已关闭。

## 2. 工作目录与执行隔离

必须建立独立目录，不得复用或清理 WorkBuddy Agent 的 ROUND139 工作树、缓存或构建输出。

建议：
- 独立 Git worktree：在已确认的 ACK 源码仓库旁创建 round140-agent2 专用目录；
- 独立构建输出：使用当前已安装 Bazel/Kleaf 支持的独立 output user root 或独立输出根目录；
- 报告和日志：存放于 round140-agent2 专用目录。

要求：

1. 先确认现有源码仓库位置、磁盘剩余空间、可用内存和已安装工具版本。
2. 不得扫描任意个人目录、云盘或整块磁盘来找源码。
3. 若固定 ACK 源码 checkout、23 个补丁或构建依赖不在已知工作区，标记缺失并停止该子项；不得下载新的固件或源码包来填补。
4. 不得复用 ROUND135 的编译输出作为“独立重建结果”。允许读取 ROUND135 输出哈希作为比较基准。
5. 不得删除旧 worktree、build cache、报告或用户文件来腾出空间。空间不足时报告 BLOCKED，不得擅自清理。
6. 若 Bazel/Kleaf 无法使用独立输出目录，先评估是否会污染其他 Agent 的构建状态；不能保证隔离就跳过完整重建，并记录原因。

## 3. Stage A — 独立确认 source / patch tree 身份

在独立 worktree 中执行：

1. 读取上游 HEAD，确认其 commit 严格等于：
   8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
2. 确认 worktree 初始 clean，无用户改动；保存 git status、branch、HEAD、submodule 状态（若有）。
3. 按 ROUND135 报告所列的原始顺序，对同一组 23 个补丁执行 apply-check 和应用。
4. 对每个补丁记录文件名、SHA256、apply-check 返回码、apply 返回码；不得改写补丁内容或 offset。
5. 完成后计算最终 content tree SHA，预期必须等于：
   afe9517f8062b96bfeb5b4dd5714942861e6a44b
6. 验证 tree17 中间节点 SHA：
   77e2b2b1515b3813f7538aedffe4c5a4e90edb57
7. 执行 git diff --check，并保存完整日志。
8. 不允许通过 cherry-pick、手工编辑 DTS、手改补丁、调整 offset 或跳过失败 patch 来获得目标 SHA。

判定：
- 全部 patch 身份、顺序和结果一致且最终 tree SHA 一致：Stage A PASS。
- 缺补丁、基础 commit 不符、patch 应用失败或 tree SHA 不符：Stage A BLOCKED / FAIL；保留日志并停止后续编译，不得自行修补。

## 4. Stage B — 独立 Kleaf / Image / DTB 构建复现

仅在 Stage A PASS 后继续。

### B1. 环境记录

记录以下信息：
- OS/kernel、CPU 架构和可用 RAM；
- Bazel 版本、Java 版本、Python 版本；
- Clang/LLVM 或 Kleaf toolchain 的实际版本和来源路径；
- build 命令、输出目录、开始/结束时间和总耗时；
- 是否启用远端缓存、是否复用了本地缓存、是否发生下载请求。

禁止安装、升级或替换任何工具。若构建需要联网拉取依赖而本机现有缓存无法满足，则中止并记录，不得下载或绕过限制。

### B2. 完整目标构建

使用隔离输出目录执行已验收目标：

~~~sh
tools/bazel build //common:dby_w09 --jobs=2
~~~

可根据当前 Bazel 版本使用其正式支持的独立 output user root 参数，但必须把具体参数和最终输出位置写入报告。不要自行猜测 Kleaf 私有参数。

必须保留：
- 完整 stdout/stderr；
- 最终 BUILD_RC；
- 目标 action 失败摘要；
- 输出文件的实际路径、大小、SHA256。

### B3. 产物对比

独立构建成功后，分别核对：

1. Image 大小和 SHA256 是否与 ROUND135 基准一致：
   - 预期大小：44820992 bytes
   - 预期 SHA256：ee94c4fa0364018244d4aa467dcc4318a816b53363a25b3b717acb6a002e82c6
2. qcom/huawei-dby-w09.dtb 是否存在，大小和 SHA256 是否与 ROUND135 基准一致：
   - 预期大小：108648 bytes
   - 预期 SHA256：cab82fe3901dbb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e
3. 最终 .config SHA256 是否与：
   0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15
   一致。
4. 若输出路径不同，必须证明它来自本次独立构建，而非复制 ROUND135 文件。
5. 若 Image 或 DTB hash 不同，不得立即认定源码错误，也不得替换 R3 候选。需记录差异并在已安装工具可用时进行只读比较，判断差异是否来自 build metadata、时间戳、工具链差异或真实二进制内容差异。不能证明原因时标记 UNRESOLVED。

如果因磁盘、工具、依赖缓存或构建环境限制不能完整构建，允许结束为 PARTIAL/BLOCKED；不得使用旧 build 输出冒充重建产物。

### B4. 针对性结构检查

构建成功后，使用已有工具对本次产物执行只读检查：
- DTB header / total size / alignment；
- huawei,dby-w09 compatible 与目标板级节点；
- UFS host、UFS PHY、PMIC regulator 和 power-domain phandle 是否可解析；
- DTB 是否存在 unresolved phandle/fixup 或明显重复节点；
- 目标 DTB 是否仍满足 pinned ACK 的 arm64 FDT 大小与对齐限制。

记录工具、完整命令、退出码和关键输出。不得仅凭 grep 文本宣称 DTB 结构正确；应优先用现有 dtc/fdtget/fdtdump 或仓库内已有校验器。没有工具时标记 NOT RUN，不得安装工具。

本阶段只检查本次生成产物，不得修改 DTS/DTBO、补丁、config 或 DTB。

## 5. Stage C — ROUND138 / ROUND139 独立结论交叉核验

此阶段是证据审查，不得重新执行 ROUND139 的固件扫描，也不得读取设备。

### C1. ROUND138 已确认事实（直接采用）

- entry 2 对应 VD / board-id 8206 / 0x200E。
- entry 8 对应 VG / board-id 8298 / 0x206A。
- 既有设备属性 ro.boot.dtbo_idx=2，使 entry 2 成为更强的条件性参考；但设备 DTBO 分区 hash 未读回，不能宣称已确认当前设备包就是 E1 提取包。
- 九个 overlay 都通过 __fixups__ 指向基础 FDT 的 /rootparam；overlay 内没有 literal /rootparam node。
- entry 2 与 entry 8 的 UFS / PMIC / regulator / RPMh / power-domain 相关 payload 相同。
- 39 是目录 st_nlink；按 kernfs 语义对应 37 个子目录；ROUND24 基础 FDT 也有 37 个 direct children。数量差异已消除，但 live 节点属性及最终 RAM tuples 仍未知。
- 不得重新把 39 描述成 live reserved-memory 子节点数量；不得把当前 variant 从 conditional 改成 confirmed。

### C2. ROUND139 报告的处理

检查 ROUND139 的最终报告是否已经上传到：
firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md
报告应来自 firmware-audit-v1 分支。

若该最终报告存在：
1. 读取完整报告及所引用的本地证据路径；
2. 对其结论做独立逻辑核验，关注证据是否真正支持其 DIRECT / CONDITIONAL / UNKNOWN / NOT FOUND 标签；
3. 特别检查是否将 RPMh ARC、corner 同号或 proxy supply 错当成物理电源输入；
4. 检查是否将静态 DTS power-domain 声明误写成运行时 vote 已验证；
5. 检查是否把同设备 HOS4.2 Linux 7.0 项目的做法误当成 HOS4.3 ABL contract；
6. 检查是否将 vbmeta_cust.img 的 footer/size anomaly 过度推断成损坏或可修复；
7. 检查是否把“已有备份文件”直接等同于“已验证的 HOS4.3 恢复路径”；
8. 记录每个不一致点及支持该不一致的报告路径/行号。

若 ROUND139 尚未交付：
- 记录 ROUND139_DEPENDENCY=PENDING；
- 不得读取 WorkBuddy Agent 的临时目录、日志或未上传文件；
- 本轮只完成 Stage A / B 及 ROUND138 可完成的独立核验；
- 首启矩阵对应 PMIC/UFS/boot/AVB 项标记 BLOCKED/PENDING；
- 上传报告并停止，不得自行要求 WorkBuddy Agent提前交付或修改其任务。

### C3. 首启前测试矩阵

必须给出以下每一门槛的结论及证据：

| Gate | 必须回答的问题 | 允许的结论 |
|---|---|---|
| Candidate source identity | 23 patches 是否独立重放到精确 tree SHA？ | PASS / FAIL / BLOCKED |
| Image / DTB reproduction | 是否独立构建并验证输出身份？ | PASS / PARTIAL / FAIL / BLOCKED |
| Final FDT / RAM | 是否有最终 post-ABL FDT bytes、完整 /memory reg tuples、reserved-memory 节点和值、实际 handoff 路径？ | PASS / BLOCKED |
| DTBO variant | 是否有设备 DTBO 分区 readback identity 和实际选择证据？ | PASS / CONDITIONAL / BLOCKED |
| PMIC physical inputs | 每条 UFS 消费 rail 是否有权威物理输入 parent 和实际控制关系？ | PASS / BLOCKED |
| UFS performance domain | 是否有足够证据证明 UFS 所需 MMCX/MX / CMD DB / RPMh 请求与实际运行时 vote？ | PASS / BLOCKED |
| Boot-v2 / ramdisk / DTBO | 是否证明 HOS4.3 ABL 的真实消费规则、embedded stock ramdisk 保留方式和 DTBO 选择？ | PASS / BLOCKED |
| AVB | 是否有完整、无歧义的 vbmeta descriptor/chain 解释及合法启动方式？ | PASS / BLOCKED |
| Recovery | 是否存在针对本台 HOS4.3 设备、可实际执行且已验证的恢复路线及足够原始备份？ | PASS / BLOCKED |
| First device boot | 所有硬门槛是否闭合，且是否已有单独明确用户授权？ | NOT AUTHORIZED / BLOCKED |

严禁把缺失项用“应该”“通常”“同型号如此”提升为 PASS。任何未知值必须保留 UNKNOWN / BLOCKED。

## 6. 严格禁止事项

**设备访问完全未授权。以下操作一律禁止：**

- 连接平板、USB、ADB、fastboot、recovery、串口或 bootloader；
- 读取任何设备分区、ABL 分区或 /sys/firmware/fdt；
- 重新尝试此前 Permission denied 的 FDT 拉取；
- root、提权、权限绕过、解锁或更改设备状态；
- reboot、fastboot boot、临时启动、刷写、擦写、分区写入；
- 运行任何需要设备在线的测试；
- 打包、重打包、签名、修改 boot/ramdisk/DTBO/vbmeta；
- 修改 23 个已验收补丁、任何 DTS/DTBO、Kconfig、config、manifest 或候选分支；
- 修改 main、AI1、AI2、firmware-audit-v1、ack18-dby-w09-dts-draft 等已有工作分支；
- 下载或重新提取 HOS4.3 固件、私有镜像或任何新固件；
- 安装/升级系统工具、编译器、Python package 或其他依赖；
- 删除缓存、旧 worktree、报告、日志或用户数据；
- 将本任务交给 WorkBuddy Agent 或 2号 AI。

禁止上传完整固件、boot、ramdisk、DTB/DTBO、vbmeta、密钥、签名或其他敏感二进制。GitHub 仅允许上传脱敏 Markdown 报告和安全的文本摘要。

## 7. 报告格式与证据要求

创建报告：
firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md

报告至少包含：

1. 执行身份声明：明确“2号 Agent”，明确不是 2号 AI，也不是 WorkBuddy Agent。
2. 执行时间、主机环境、已安装工具版本。
3. 独立工作树路径及隔离证明。
4. 上游 HEAD、patch list、每个 patch SHA256、顺序、返回码。
5. tree17 与最终 tree SHA。
6. 完整构建命令、输出目录、完整 BUILD_RC、日志位置、构建耗时。
7. 本次 Image、DTB、.config 的大小和 SHA256，与 ROUND135 的逐项比较。
8. DTB 结构校验表、实际命令及返回码。
9. ROUND138 / ROUND139 交叉核验表，明确本轮独立确认或保留的 UNKNOWN。
10. 首启前测试矩阵。
11. 失败、未运行、资源限制和依赖缺失项，不能只写成功部分。
12. 明确列出本轮到底关闭了什么、仍有哪些阻塞项。

最终结果只能选其一：

- **PASS — INDEPENDENT BUILD REPRODUCED**：Stage A 完全通过，完整独立构建成功，关键输出身份一致，DTB 结构检查通过。该 PASS 仅表示构建复现，不代表设备可启动。
- **PARTIAL — SOURCE REPRODUCED, BUILD OR SOME CHECKS INCOMPLETE**：源码身份复现通过，但完整构建或部分检查因明确限制未完成。
- **BLOCKED — BASELINE OR REQUIRED INPUTS MISSING**：上游、补丁、独立工作树或必要输入无法确认。
- **FAIL — REPRODUCTION MISMATCH**：存在可复现的源码身份、patch 顺序、tree SHA 或实质构建结果不一致。保留原始日志，不得自行修补。

## 8. 上传、回读和停止

- 仅将脱敏 Markdown 报告上传到 agent2/round140-independent-preboot-tests 分支。
- 不得修改本任务书、ROUND135/138/139 报告或其他 Agent 的文件。
- 上传后必须从远端重新读取报告，确认内容与本地报告逐字节一致，并在报告或交付消息中记录 commit SHA、blob SHA 和回读结果。
- 完成上传和回读后立即停止。
- 不执行设备测试，不创建启动包，不安排后续轮次，不自行宣布首启获准。

**ROUND140 的成功标准是独立复现与验证结果可信，而不是强行得到 PASS，更不是直接启动平板。**
