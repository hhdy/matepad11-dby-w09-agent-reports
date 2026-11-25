请执行 ROUND26，先读取 ROUND26/AGENT_TASK.md。

本轮只做本地内存区间比对：
1. 从固定 ACK sm8250.dtsi 提取 /reserved-memory 所有子节点（不限前五个），对照 ROUND19 已解码 HOS4.3 base_2.dts 和 ROUND24 37 节点表。
2. 所有物理 reg tuple 仅在本机计算，逐项判定 EXACT_MATCH / SAME_BASE_DIFFERENT_SIZE / OVERLAP / ACK_ONLY / HOS_ONLY / NO_CLEAR_MATCH。
3. 动态 size/alloc-ranges pool 不得假装与固定 reg 区域相同。
4. 列出 rev2 通过 include sm8250.dtsi 会继承的 generic no-map / shared-dma-pool / CMA 节点，以及被哪些 SoC 消费者引用。
5. 报告只输出匹配分类、大小粗略量级与节点名称，所有 start/end/base/reg 原始数字和坐标必须脱敏。绝对不要把物理地址或 tuple 上传 GitHub。

限制：只使用 ROUND18/19 已有本地文件；不得重提取/下载/安装/编译/改 DTS/改配置/设备连接或刷写。
只上传一份脱敏报告到 firmware-audit-v1/firmware-analysis/round26/round26-sm8250-vs-hos43-reserved-memory-interval-audit.txt，完成后停止。
 
补充：同一轮顺带比较 pinned sm8250.dtsi 和 HOS4.3 base_2.dts 的顶层 memory 节点结构：节点路径 unit-address 脱敏、device_type、地址/大小 cell 数、reg tuple 数、base 是零/非零、size 是零/非零、初始占位是否结构相同。不要输出任何物理地址或大小数值。确认 rev2 通过 include 确实继承该 memory 节点。不得修改或新增 memory node。
