执行 ROUND24，先读取 ROUND24/AGENT_TASK.md。

本轮重点盘点 HOS4.3 base DTB 中已有的 34 个 reserved-memory 子节点，以及所有 memory-region / memory-region-names / qcom,huawei 内存引用。

要求：
1. 只使用 ROUND19 已解码的 base_2.dts 和九个 dtbo_entry_N.dts，不重新解包。
2. 每个保留区记录名称、compatible、reg tuple 大小类别、no-map/reusable 等标志、消费者 phandle 指向关系、用途分类；所有物理 base/end 地址必须在上传报告中彻底脱敏，只保留大小类别。
3. 分别看 base 与各 DTBO，不合并九个 overlay，不假定 0x206a 是当前选中项。
4. 对照当前 main 的 board rev2 candidate 和固定 ACK sm8250.dtsi，确认其是否缺少关键 carveout，哪些设备消费者被禁用或延后，UFS 是否有 reserved-memory 依赖。
5. 参考同设备公开 Linux 7.0/HOS4.2 的四个 reserved nodes，只比较语义，不复制地址。不能把它误当成 HOS4.3 证据。
6. 给出最小内核/UFS 首次启动前是否必须保留一部分 HOS4.3 carveout；没有 final ABL FDT 证据时不要猜地址，保持 BLOCKED。

禁止修改 source/DTS/DTBO/config，禁止重提取、安装工具、编译、打包、AVB、设备连接、ADB/fastboot、重启、解锁、root、刷写。

只上传一个脱敏报告到 firmware-audit-v1/firmware-analysis/round24/round24-hos43-reserved-memory-and-consumer-map.txt，成功后停止。