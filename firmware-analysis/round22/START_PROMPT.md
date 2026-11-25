请执行 ROUND22，先读取 ROUND22/AGENT_TASK.md。

本轮目标是对现有 DBY-W09 storage-first board DTS 草案做只读的“能否安全编译 DTB”核验：
1. 用 ROUND19 已有 decompiled base_2.dts 核实 /memory 节点究竟不存在还是 reg 全零，解决 board DTS 草案注释与 ROUND19/20 报告冲突。绝不猜 RAM 地址。
2. 读取 main 中现有 dts/dby-w09-ack18-board.dts.draft，基于固定 ACK 6.18.33 sm8250.dtsi 检查 include、label、重复属性和语法；有 dtc 时只在 ROUND22 临时副本编译 DTB，禁止修改原稿。rootparam overlay 如本地已有则单独检查，禁止合并。
3. 逐项对照 ROUND18 实际已应用的 UFS driver/schema patches 与 board DTS 属性：host/PHY compatible、GDSC/power-domains、required-opps、vdd-hba、vcc/vccq/vccq2、qcom,vddp-ref-clk、qcom,vccq-parent、vdda-phy-always-on。确认每个属性确实有消费者且驱动能 bind。
4. 审核 PM8150 VRM 输入 supply 缺失是否被 binding/driver/regulator core 允许，dummy supply 的运行前提是什么；不能发明 vph_pwr 或其他 parent rail。
5. 给出 DTB/DTBO 是否可进入 syntax build、仍有哪些 runtime/electrical gate。

限制：只用 ROUND18/19 已有本地副本，不重新提取/部署/下载/安装；不改 source/config/DTS/DTBO，不 olddefconfig、不重编内核、不打包/签名/AVB；不连接或操作设备；不修改第二 AI 分支或受保护 DTS 分支。

只上传一个脱敏报告到 firmware-audit-v1/firmware-analysis/round22/round22_board_dts_compile_and_ufs_regulator_contract_audit.txt，成功后停止。