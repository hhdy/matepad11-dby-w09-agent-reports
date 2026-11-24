# AGENT_TASK.md — DBY-W09 GKI 6.18.33 移植调研总入口

> **本轮本地 Agent 唯一任务：先阅读 `AGENT_TASK_ROUND6.md`。** ChatGPT 已自行完成 ROUND6 的上游研究；Agent 只需做本机 Windows PATH 工具探测，不要重复网页调研。

## 当前结论与报告

- [ChatGPT 独立完成的上游基线研究](./kernel-baseline/round6/upstream-baseline-research.md)：已核实 android17-6.18 源码分支为 6.18.33、已发布 GKI release 为 6.18.32、Android 12 与 android17-6.18 不属于官方支持组合，并检查了 Kleaf ARM64 target 和 KMI 规则。
- [AGENT_TASK_ROUND6.md](./AGENT_TASK_ROUND6.md)：本地 Agent 只做 PowerShell PATH 工具可用性探测并回传两份脱敏文本报告。
- ROUND5 EROFS 内容枚举仍为 BLOCKED；无可信 EROFS 工具时不要自行解码或下载来历不明的 EXE。

## 已完成的调查阶段

- ROUND1：Android 12 / API 31、原内核 4.19.157-perf+、KONA / SM8250、传统 boot + 独立 ramdisk；固件 43 项清单。
- ROUND2：DTBO 头修复和 9 个 entry；super.img sparse 结构识别。
- ROUND3：sparse / LP metadata / DTBO / boot DTB 只读解析；确认 vendor、odm 等逻辑分区。
- ROUND4：vendor / odm 已在本地独立提取；两者 EROFS 签名识别通过。
- ROUND5：可信 EROFS 工具链不可用，内容枚举停止；模块、firmware、VINTF、KMI 可移植性继续 UNKNOWN。
- Xiaomi：仅确认一套 elish 分卷参考包，没有内核源码 / DTS / defconfig，不能直接复用其镜像或板级设置。

## 当前最重要的技术风险

Google 官方 Android Common Kernel 兼容矩阵中，Android 12 的对应分支是 `android12-5.10`，`android17-6.18` 对应 Android 17。若坚持 GKI 6.18.33，应先明确 Android userspace 是否也计划升级至 Android 17；不能把 6.18.33 看成当前 Android 12 环境的官方 GKI 组合。详见上游研究报告。

## 仓库与协作边界

- 仓库：`hhdy/matepad11-dby-w09-agent-reports`
- 历史分析分支：`firmware-audit-v1`
- 上游基线研究和任务书在 `main`。
- PR #1 仍为 Draft，未经用户明确授权不得合并。
- 不要求用户重复上传已经在本机的固件。

## 执行边界

1. 优先由 ChatGPT 完成可通过公开资料、GitHub、源码阅读和已有报告完成的研究、分析、对照和任务规划。
2. 只有需要访问用户本机文件系统、本机工具环境、本地固件内容或运行本地只读测试时，才交给 Agent。
3. 不刷机、不解锁、不连接设备、不 root、不写分区、不加载模块、不挂载可写文件系统。
4. 公开仓库只上传脱敏文本、CSV、JSON 和必要的纯文本分析源码；绝不上传固件二进制、分区镜像、内核/模块/firmware 二进制、manifest 原件、完整本地 SHA-256、设备序列号/MAC、token/PAT 或个人目录路径。
5. 不绕过 Windows 命令安全策略，不修改执行策略，不关闭安全软件，不调用 WSL。
6. 未实际执行的操作必须标注 NOT_RUN / BLOCKED / UNKNOWN，不得虚报成功。

## 之前的任务书

- [ROUND2](./AGENT_TASK_ROUND2.md)
- [ROUND3](./AGENT_TASK_ROUND3.md)
- [Xiaomi ZIP 审计](./AGENT_TASK_XIAOMI_ZIP.md)
- [ROUND4](./AGENT_TASK_ROUND4.md)
- [ROUND5](./AGENT_TASK_ROUND5.md)

本地 Agent 完成 ROUND6 后只回报本机 PATH 探测结果。之后的上游驱动、DTS、KMI 和启动链研究继续由 ChatGPT 直接完成。
