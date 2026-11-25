# 2号 AI — ROUND36 独立验收记录

**结论：ACCEPTED（仅验收本轮只读取证审计交付物；Phase E 不解除）**

## 审查范围

已读取并审查以下交付物：
- `AI2_ROUND36_EVIDENCE_AUDIT.md`
- `abl-memory-evidence-matrix.md`
- `pm8150-physical-topology-matrix.md`
- `missing-evidence-request.md`
- `source-hashes.txt`

已独立重新获取 10 个关键输入文件，Git blob SHA 与 `source-hashes.txt` 登记的 blob SHA 全部匹配（10/10）：ROUND64、ROUND24、ROUND11、ROUND13、live FDT 状态与节点清单、Stage A ROUND61/42/43 资料及 board DTS draft。

## 独立结论

### A — ABL 最终内存交接

- 接受 `BLOCKED — direct evidence absent`。
- 静态 base DTB 的 `/memory/reg` 全零只证明 L2 模板状态；不能当作 Linux 收到的最终 FDT。
- 现有 live `/sys/firmware/fdt` 仅有文件存在、800316 B 和权限拒绝记录，没有成功读取的内容；RAM bank 数值、carveout 区间和最终交接数据仍缺失。
- live `/memory/reg` 长度 48 B 与静态模板 16 B 不同，是结构性旁证，不足以推导任何 RAM 地址或容量。
- 接受 34/37 差异的解释：ROUND7 CSV 的 34 个唯一直接子路径与完整节点清单/live 目录的 37 个子目录属于统计口径差异，不构成硬件冲突。

### B — PM8150 L5/L9 物理供电

- 接受 `BLOCKED — direct evidence absent`。
- 软件 regulator 类型、输出电压、driver supply-name 和 proxy 请求有证据；它们不证明 PCB 上的物理输入 rail。
- 没有与 DBY-W09 主板 revision 绑定的原理图、电源树、netlist 或测量记录。不得据此填写 L5/L9 parent、输入电压、电流能力或时序。
- dummy-regulator fallback 的源码证据说明 probe 成功不能代替物理供电验证。

## 独立审查的限定/修正

1. `missing-evidence-request.md` 的 D-1（最终 FDT blob）是 A 工作流最有价值的单项证据，但不能预先承诺它单独关闭 EFI memory descriptor 与 kernel entry classification：矩阵 A-21/A-25 仍列为 MISSING。若实际走 EFI-stub 路径，还需相应 EFI memory map / boot log 证据；应按最终 FDT 中的 `/chosen` 内容和实际入口路径再判定。
2. U-2 原理图页可证明 pin/net/upstream connection，但若文件不包含额定电流、输入范围或时序信息，B-37/B-38 仍需 U-3、U-4 或合格测量补足。不能把一张原理图自动视为所有电气规格均已证明。
3. 所有 D 类设备读取/测量请求均不构成本轮授权。不得自行连接设备、使用 ADB/fastboot、读取分区或进行硬件测量；必须等待用户明确授权。不得重新要求上传 HOS4.3 固件。

## 验收边界

- ROUND36 作为只读取证盘点：**ACCEPTED**。
- Phase E：**BLOCKED**（A、B 两条工作流均未解除）。
- Phase F：**BLOCKED**。
- Phase G：**NOT RUN**。
- 不授权 ROUND37、DTS/DTBO 修改、产品构建、boot/AVB 打包或任何设备操作。
- Agent 本轮停止规则已满足；后续工作须由 2号 AI 在用户明确选择下一步后另行下达。

**审查者：2号 AI**  
**审查日期：2026-11-26**