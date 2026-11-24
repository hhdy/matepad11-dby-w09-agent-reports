# AGENT_TASK.md — DBY-W09 GKI 6.18.33 移植调研总入口

> **当前唯一执行入口：先阅读 `AGENT_TASK_ROUND6.md`。** ROUND1–ROUND5 已有报告，不要重复执行，不要重复索要用户已有固件。

## 当前任务

- [AGENT_TASK_ROUND6.md](./AGENT_TASK_ROUND6.md)：GKI 6.18.33 上游分支身份、官方 release 状态、Android 平台兼容矩阵、Kleaf / KMI 构建定义及本机工具环境的只读核验。
- 当前不编译内核、不执行 repo sync / git clone、不下载大文件、不调用 WSL、不安装软件。
- ROUND5 的 EROFS 内容枚举仍为 BLOCKED；没有可信 EROFS 工具时不要自行解码，也不要下载来历不明的 EXE。
- 本轮不需要重新读取或提取 super.img、vendor.img、odm.img。

## 项目基线（依据已完成报告）

设备：Huawei MatePad 11 DBY-W09，Qualcomm KONA / SM8250，soc_id 356 rev 2.1；原系统 Android 12 / API 31，原内核 4.19.157-perf+，CPU 频率特征符合 Snapdragon 865 档位。传统 boot + 独立 ramdisk 布局，无 vendor_boot / init_boot。

固件分析：
- ROUND1：43 项固件清单及 boot / 分区头部初检。
- ROUND2：DTBO 头部修复验证，9 个 entry；super.img 识别为 sparse。
- ROUND3：sparse / LP metadata / DTBO / boot DTB 只读解析验证。
- ROUND4：vendor / odm 按 LINEAR extent 提取到本地工作副本，长度及本地校验通过；两者文件系统签名为 EROFS。
- ROUND5：无可信 EROFS 读取器，停止在内容层之前。所有目录、模块、vermagic、firmware、VINTF 与 GKI 可移植性仍 UNKNOWN / BLOCKED。

小米参考包：
- 仅确认一套 elish 分卷 ZIP；CRC 检查通过，但无 kernel source、DTS、defconfig 或 patch。
- Xiaomi 870 的板级信息不能覆盖 Huawei 865/SM8250 设备树；包内预编译镜像不可直接用于 DBY-W09。

## 仓库与分支

- 仓库：`hhdy/matepad11-dby-w09-agent-reports`
- 最新本地 Agent 报告分支：`firmware-audit-v1`
- ROUND1–ROUND5 和 Xiaomi 报告均保留在该分支对应目录。
- 任务书放在 `main` 分支根目录；不得因此改写 `firmware-audit-v1` 上的历史报告。
- PR #1 仍为 Draft，未经用户明确授权不得合并。

## 严格边界

1. 不刷机、不解锁、不连接设备、不 root、不写分区、不加载模块、不挂载可写文件系统。
2. 不上传任何固件 / 分区 / boot / DTB / DTBO / 内核 / 模块 / firmware 二进制。
3. 公开仓库只允许上传脱敏文本、CSV、JSON 和必要的纯文本分析源码。
4. 不上传完整本地 SHA-256、个人路径、用户名、设备序列号/MAC、token/PAT。
5. 不绕过 Windows 命令安全策略，不修改执行策略，不关闭安全软件，不调用 WSL。
6. 未实际执行的操作必须标注 NOT_RUN / BLOCKED / UNKNOWN，不得虚报成功。

## 历史任务书

- [ROUND2](./AGENT_TASK_ROUND2.md)
- [ROUND3](./AGENT_TASK_ROUND3.md)
- [Xiaomi ZIP 审计](./AGENT_TASK_XIAOMI_ZIP.md)
- [ROUND4](./AGENT_TASK_ROUND4.md)
- [ROUND5](./AGENT_TASK_ROUND5.md)

本地 Agent 完成 ROUND6 后，只上传任务书列出的脱敏报告至 `kernel-baseline/round6/`，并回报实际完成项、阻塞项与提交 SHA。不要自行合并 PR #1。
