WorkBuddy Agent：现在开始执行 **ROUND139 — HOS4.3 PMIC/UFS 与 boot/AVB 静态证据收口审计**。

这是 **WorkBuddy Agent 本地执行任务，不是 AI2 的任务**。AI1 已完成 ROUND138 独立验收并批准 ROUND139 继续。

完整任务书：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/firmware-analysis/round139/AGENT_TASKBOOK_HOS43_PMIC_UFS_AND_BOOT_AVB_AUDIT.md

## ROUND138 已验收结果（必须直接采用，不要重复审计）

1. Entry 2 文件身份确认：board-id 8206 / 0x200E / DBY_W09_VD；entry 8 是 8298 / 0x206A / DBY_W09_VG。
2. 既有设备属性记录 ro.boot.dtbo_idx=2，因此 entry 2 是更强的当前 variant 参考，但只在设备 DTBO 分区与现有 E1 包一致时成立。设备 DTBO 分区没有 readback hash；E1 包与 104.3.0.196C00 的 build 关联也未建立。
3. 九个 overlay 都通过 __fixups__ 指向基础 FDT 的 /rootparam；ROUND7 的 literal-node 统计不等同于 fragment target 统计。
4. Entry 2 与 entry 8 的 UFS / regulator / PMIC / RPMh / power-domain 相关静态 payload 完全相同。variant 不确定性不会改变当前最小存储 DTS 的静态 UFS/PMIC 声明依据。
5. E5 live rootparam 属性列表没有 qcom,product_name，原因未知；不能据此猜测 ABL 修改或实际 DTBO 包版本。
6. 原报告所谓 reserved-memory “39 children” 已纠正：39 是目录 st_nlink，按 kernfs 目录链接数规则对应 37 个子目录；ROUND24 base FDT 也有 37 个 direct children。数量差异已消除，但 live child identity/value 和最终 RAM reg tuples 仍未知。
7. ROUND138 报告：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round138/round138-dtbo-variant-and-live-fdt-delta-audit.md
8. AI1 验收记录：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round138/AI1_ROUND138_INDEPENDENT_REVIEW_AND_ROUND139_DISPOSITION.md

## 本轮工作

严格按 ROUND139 taskbook，只检查已有本地 HOS4.3 文件、parser 输出和既有日志：
- PM8150/PM8150L 六条 UFS 消费轨的供电 provider、是否存在真实物理 input parent；
- UFS OPP / MMCX / MX / CMD DB / RPMh 相关静态证据和 ACK 运行时支持差异；
- boot-v2、embedded stock ramdisk、独立 ramdisk、DTBO、vbmeta 链、vbmeta_cust 异常；
- 原始分区备份、已知分区大小/hash 与恢复路线证据。

物理电源 parent、RPMh ARC/corner 与 proxy supply 必须分开。没有权威证据就保持 UNKNOWN / BLOCKED。不要把静态 DTS 推断成 runtime vote。

## 禁止事项

本任务 **不授权任何设备访问**。严禁连接平板、ADB、fastboot、recovery、USB/串口、读取 ABL、读取任何 /sys/firmware/devicetree/base 文件（包括 ROUND138 建议的 rootparam/qcom,board_name）、重试 /sys/firmware/fdt、提权、root、重启、打包、构建、AVB 修改、刷写或源代码修改。

ROUND138 建议的 qcom,board_name 是一个后续可能需要用户另行授权的设备读取；本轮不执行它。

上传仅限脱敏 Markdown 报告到 firmware-audit-v1 的 firmware-analysis/round139/，回读核验后停止。不要自行开启后续任务。