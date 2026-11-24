# AGENT_TASK.md — DBY-W09 GKI / ACK 内核移植调研总入口

> **当前本地 Agent 唯一任务：阅读 AGENT_TASK_ROUND9.md。** ROUND8 已完成 145/145 fragment target 解析和 UFS/rootparam 映射；ROUND9 只补齐尚未解析的 supply / pinctrl / GPIO / camera / USB endpoint，不重复 fragment target、PATH 探测或上游公开研究。

## 当前任务

- [AGENT_TASK_ROUND9.md](./AGENT_TASK_ROUND9.md)：只读使用 ROUND3 已有 FDT candidate 0 + DTBO entry 8，补充 UFS supply phandle、THP/panel/WLAN GPIO-pinctrl、camera sensor board properties、USB-C/DP endpoints。只上传四份脱敏文本报告。
- [ROUND9 ChatGPT 独立驱动兼容矩阵](./kernel-baseline/round9/dby-w09-6.18-driver-compatibility-matrix.md)：已比对 HOS4.3、同型号 Linux 参考与 Linux v6.18 upstream driver/binding；不要重复公开源码研究。
- [AGENT_TASK_ROUND8.md](./AGENT_TASK_ROUND8.md)：已完成 145/145 fragment target 解析，确认 fragment@143 -> /rootparam，并确认 entry 8 的 fragment@63/@64 修改 UFS PHY/Host；只作历史任务参考。
- [ROUND8 HOS4.3 与同型号 Linux 对照](./kernel-baseline/round8/harmonyos43-hardware-reference-comparison.md)：历史阶段报告，target 解析前版本。
- [ROUND7 本地 FDT 属性清单](./AGENT_TASK_ROUND7.md)：已完成，13/13 FDT VALID，9 个 DTBO entries 已有属性清单。
- [ROUND6 上游 GKI 基线报告](./kernel-baseline/round6/upstream-baseline-research.md)：由 ChatGPT 完成，区分 6.18.33 活跃源码分支和 6.18.32 已发布 GKI release；Android 12 / Android 17 兼容风险、Kleaf/KMI 已调查。ROUND6 PATH 工具探测不是 ROUND8 前置条件，暂时不阻塞。

## 已完成阶段

- ROUND1：Android 12 / API 31、原内核 4.19.157-perf+、KONA / SM8250、传统 boot + 独立 ramdisk；固件 43 项清单。
- ROUND2：DTBO 头修复验证和 9 个 entries；super.img sparse 结构识别。
- ROUND3：sparse / LP metadata / DTBO / boot DTB 只读解析；确认 vendor、odm 等逻辑分区。
- ROUND4：vendor / odm 已在本地独立提取；两者 EROFS 签名识别通过。
- ROUND5：可信 EROFS 工具链不可用，内容枚举 BLOCKED；模块、firmware、VINTF、KMI 兼容性 UNKNOWN。
- ROUND7：读取现成的 13 个 FDT 工作副本，13/13 结构有效；7937 行属性 inventory；9 个 DTBO board-id 已校验。
- 同型号主线 Linux 公开参考项目：svesnav Linux 7.0.14、youzjuzi Linux 7.2.10、CoWave Linux 7.3.4；只作硬件资料/bring-up 参考，不是可直接复用的 Android GKI 包。

## 当前关键技术判断

- Huawei board-id 0x206a / DBY_W09_VG 与本机 HOS 4.3 DTBO entry 8 对应；ROUND8 已解析 145/145 fragment，fragment@143 确认为 /rootparam。
- ROUND8 entry 8 fragment@63/@64 将 UFS PHY/Host status 设为 ok 并配置供电属性；Linux v6.18 有 SM8250 UFS host + QMP UFS PHY，HOS PHY compatible 与主线 match 字符串不同，板级 DTS 必须规范化。
- 同型号 port 证据表明 THP / panel / audio / camera / USB-C 有较多 Huawei 专属适配；本机活动 panel profile、部分 GPIO/pinctrl、camera sensor model 尚未全部由本地 HOS4.3 属性闭环。
- Round9 driver compatibility matrix 已列出主要 upstream-compatible 字符串差异与 vendor firmware/configuration 阻塞。
- EROFS 内容层仍 BLOCKED；没有 vendor/odm 模块清单、vermagic、firmware、VINTF 或供应商 KMI 证据。
- Android 12 userspace + android17-6.18 不在 Google 官方支持矩阵中；项目最终 platform target 仍需后续产品决策。
- 详细对照见 ROUND6 / ROUND7 / ROUND8 ChatGPT research reports。

## 仓库和安全边界

- 仓库：hhdy/matepad11-dby-w09-agent-reports
- 本地 Agent 历史分析分支：firmware-audit-v1
- ChatGPT 公开研究和任务书放在 main。
- PR #1 仍 Draft；未经用户明确授权不得合并。
- 优先由 ChatGPT 完成公开资料、GitHub、源码阅读、对照、架构分析和任务规划。
- 只有本机文件系统、本地固件内容、本机工具环境和本地只读测试交给 Agent。
- 不刷机、不解锁、不连接设备、不 root、不写分区、不加载模块、不挂载可写文件系统。
- 不上传固件/分区/boot/DTB/DTBO/FDT/内核/模块/firmware 二进制、manifest 原件、完整本地 SHA-256、设备序列号/MAC、token/PAT 或私人完整路径。
- 不绕过 Windows 命令安全策略、不修改执行策略、不关闭安全软件、不调用 WSL、不下载来源不明的 EXE。
- 未实际执行的操作标记 NOT_RUN / BLOCKED / UNKNOWN，不得虚报成功。

## 历史任务书

- [ROUND8](./AGENT_TASK_ROUND8.md)
- [ROUND2](./AGENT_TASK_ROUND2.md)
- [ROUND3](./AGENT_TASK_ROUND3.md)
- [Xiaomi ZIP 审计](./AGENT_TASK_XIAOMI_ZIP.md)
- [ROUND4](./AGENT_TASK_ROUND4.md)
- [ROUND5](./AGENT_TASK_ROUND5.md)
- [ROUND6 本机工具探测](./AGENT_TASK_ROUND6.md)
- [ROUND7 FDT 属性 inventory](./AGENT_TASK_ROUND7.md)

本地 Agent 完成 ROUND9 后，只回传可安全解析的供电/pinctrl/GPIO/camera/USB属性摘要。随后由 ChatGPT 继续把这些字段与 ACK 6.18.33 的实际设备树/驱动绑定核对；不重复进行已完成的公开研究。
