# AGENT_TASK.md — DBY-W09 GKI / ACK 内核移植调研总入口

> **当前本地 Agent 唯一优先任务：阅读 AGENT_TASK_ROUND7.md。** ROUND6 的公开上游研究已由 ChatGPT 完成；本轮真正需要本地 Agent 的是读取本机 HOS 4.3 DTB / DTBO 工作副本并生成脱敏属性清单。

## 当前任务

- [AGENT_TASK_ROUND7.md](./AGENT_TASK_ROUND7.md)：只读解析 ROUND3 已有的 13 个本地 FDT 工作副本，输出 DTB 属性 inventory 和 9 个 DTBO board/rootparam matrix。
- [同型号主线 Linux 研究报告](./kernel-baseline/round7/same-device-mainline-port-audit.md)：ChatGPT 已经完成公开项目和 Linux v6.18 上游源码对照，Agent 不要重复做网页搜索或 GitHub 调研。
- [ROUND6 上游 GKI 基线研究](./kernel-baseline/round6/upstream-baseline-research.md)：已区分 6.18.33 活跃源码分支和 6.18.32 已发布 GKI release，并列出 Android 12 / Android 17 兼容风险、Kleaf 和 KMI 规则。
- [AGENT_TASK_ROUND6.md](./AGENT_TASK_ROUND6.md)：Windows PATH 工具探测任务仍可执行，但不是 ROUND7 的前置条件，不要为了它重复检查固件或上游文档。

## 项目现状

- 设备：Huawei MatePad 11 DBY-W09，Qualcomm KONA / SM8250，当前原系统 Android 12 / API 31，内核 4.19.157-perf+。
- 原厂启动结构：Android boot header v2，单独 ramdisk 分区，无 vendor_boot / init_boot。
- ROUND3 已确认 boot DTB 的 msm-id 为 [356, 131073]，9 个 DTBO entry 全部 FDT VALID，其中一个 board-id 为 8298（0x206a）。
- ROUND4 已将 vendor / odm 提取到本地工作副本，文件系统签名为 EROFS。
- ROUND5 因缺少可信 EROFS 只读工具而 BLOCKED；模块、firmware、VINTF 和供应商 KMI 信息仍 UNKNOWN。
- 小米 Pad 5 Pro ZIP 审计只确认一套 elish 分卷包，无 kernel source / DTS / defconfig；仅保留参考价值。

## ChatGPT 已完成的公开研究

- 同型号 DBY-W09 主线 Linux 项目已经公开：svesnav Linux 7.0.14、youzjuzi Linux 7.2.10、CoWave Linux 7.3.4。
- 同型号 DTS / rootparam overlay 显示 Huawei board-id 0x206a，与 ROUND3 的 HOS 4.3 DTBO board-id 列表交叉吻合。
- Linux v6.18 已有 Qualcomm UFS host / QMP UFS PHY、SM8250 SoC DTS、MSM DRM、ath11k、WCD938x SoundWire、OV13B10 / Hi846 / DW9714 等基础支持。
- 主要风险在 Huawei 板级 DTS、panel 初始化/供电、THP 触摸协议、固件/校准数据、音频路由和旧启动链；不能因为 generic driver 存在就推断设备已经适配。
- 详细内容见 round6 / round7 research reports。

## 仓库与协作边界

- 仓库：hhdy/matepad11-dby-w09-agent-reports
- 本地 Agent 历史分析分支：firmware-audit-v1
- ChatGPT 公开研究和任务书放在 main。
- PR #1 仍为 Draft；未经用户明确授权不得合并。
- 不要求用户重新上传已存在固件或重复提供路径。

## 严格边界

1. 优先由 ChatGPT 完成公开资料、GitHub、源码阅读、对照、架构分析和任务规划。
2. 只有本机文件系统、本地固件内容、本机工具环境和本地只读测试交给 Agent。
3. 不刷机、不解锁、不连接设备、不 root、不写分区、不加载模块、不挂载可写文件系统。
4. 不上传任何固件/分区/boot/DTB/DTBO/内核/模块/firmware 二进制、manifest 原件、完整本地 SHA-256、设备序列号/MAC、token/PAT 或私人完整路径。
5. 不绕过 Windows 命令安全策略、不修改执行策略、不关闭安全软件、不调用 WSL、不下载来源不明的 EXE。
6. 未实际执行的操作标记 NOT_RUN / BLOCKED / UNKNOWN，不得虚报成功。

## 历史任务书

- [ROUND2](./AGENT_TASK_ROUND2.md)
- [ROUND3](./AGENT_TASK_ROUND3.md)
- [Xiaomi ZIP 审计](./AGENT_TASK_XIAOMI_ZIP.md)
- [ROUND4](./AGENT_TASK_ROUND4.md)
- [ROUND5](./AGENT_TASK_ROUND5.md)
- [ROUND6 本机工具探测](./AGENT_TASK_ROUND6.md)

本地 Agent 完成 ROUND7 后，只回传本机 HOS 4.3 设备树事实。之后的逐项源码差异审查、GKI 驱动复用判断与移植策略由 ChatGPT 继续独立完成。
