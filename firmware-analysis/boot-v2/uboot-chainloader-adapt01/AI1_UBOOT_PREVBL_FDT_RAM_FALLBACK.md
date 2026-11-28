# AI1 — U-Boot previous-bootloader FDT handoff 与 RAM bank fallback 设计

- 日期：2026-11-28
- 目标：Huawei MatePad 11 2021 DBY-W09 / VD / HOS4.3 / SM8250
- 参考：本仓库 BOOT_LOAD_MAP01 精确 ABL 静态报告 + U-Boot v2026.10 上游源码
- 范围：只读源码/既有脱敏反汇编交叉核验；没有设备访问、构建、镜像制作或写入。

## 1. 新闭环：ABL 在已分析 BootLinux 路径中以 x0 传入最终 FDT

本仓库现有报告：
- `firmware-analysis/boot-v2/boot-load-map01/K1_BOOT_LOAD_MAP01_REPORT.md`
- `firmware-analysis/boot-v2/boot-load-map01/hybrid_abl_load_path.md`
- 目标 ABL PE SHA-256：`a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747b404`（应以仓库文件中完整 SHA 为准：`a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747b404`）

BOOT_LOAD_MAP01 记录了已核验的 BootLinux 主函数尾段：
- ABL 对 DTB 先 CopyMem、再进行 ufdt overlay，最终 FDT 指针保存在 TagsAddress；
- separate ramdisk 的 initrd-start/end 写入最终 FDT；
- BootLinux 调用 ShutdownUefiBootServices，随后执行 ExitBootServices；
- 最终跳转序列在 VA 0x38868–0x3887C：x8=KernelLoadAddress，x0=TagsAddress（最终 FDT），x1/x2/x3 清零，随后 `blr x8`。
- 这与 ARM64 Linux boot protocol 的 x0=FDT handoff 一致。

证据等级：**ABL x0=最终 FDT 对已分析 BootLinux 路径 CONFIRMED**。该报告证明的是该精确函数路径的静态行为，不等于所有 recovery/fastboot 分支都已经被逐个证明使用同一路径。

## 2. U-Boot v2026.10 确实保存 previous-bootloader x0

源码链：

1. `arch/arm/cpu/armv8/start.S` 的 reset 入口先跳到 `save_boot_params`，随后才进入 U-Boot PIE fixup 和 C runtime。
2. 对 Qualcomm `ARCH_SNAPDRAGON`，`arch/arm/Kconfig` 选择 `SAVE_PREV_BL_FDT_ADDR`（在未启用 ARM SoC boot0 hook 的普通路径）。
3. `arch/arm/lib/Makefile` 因 `CONFIG_SAVE_PREV_BL_FDT_ADDR` 将 `save_prev_bl_data.o` 编进 U-Boot。
4. `arch/arm/lib/save_prev_bl_data.c::save_boot_params(ulong r0)` 执行 `reg0 = r0`；`get_prev_bl_fdt_addr()` 返回 `reg0`。
5. 因此，若 ABL 在跳到 U-Boot 时仍按 ARM64 BootLinux ABI 把最终 FDT 地址放入 x0，U-Boot 从第一条保存钩子起就能保留该指针，Snapdragon board code 可读取。

源码：
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/cpu/armv8/start.S
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/Kconfig
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/Makefile
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/save_prev_bl_data.c

## 3. 一个比复制 CoWave 静态 RAM tuples 更好的候选路径

U-Boot v2026.10 `arch/arm/mach-snapdragon/board.c::board_fdt_blob_setup()` 的真实逻辑：

- 取 U-Boot 自带 internal control FDT；
- 取 `get_prev_bl_fdt_addr()` 作为 external/previous-BL FDT；
- 若 internal FDT 有有效 /memory/reg，优先解析 internal；
- 若 internal 缺少可用 /memory/reg（`qcom_parse_memory()` 返回负值），再尝试解析 external FDT；
- 若 internal FDT 本身有效，即使它的 /memory 不可用，成功从 external 读取 RAM banks 后仍保留 internal FDT 作为 U-Boot control FDT；
- `dram_init_banksize()` 后续把解析结果转成 `gd->dram[]`；
- 最终 ARM `arch_fixup_fdt()` 用 `gd->dram[]` 调用 `fdt_fixup_memory_banks()`，修正传给 Linux 的 ACK DTB /memory/reg。

据此提出一个**条件式设计，不是已执行补丁**：

- 保留 CoWave U-Boot internal control DTS 中 UART、UFS、USB、PMIC、board ID、显示等其余已适配节点；
- 不在该 internal control DTS 中硬编码 CoWave 的 8 GiB /memory tuples；
- 让 internal DTS 的 /memory 不提供可用的 reg，以触发 Qualcomm Snapdragon board.c 的 external-FDT memory fallback；
- 前提是 recovery ABL 真正把最终 HOS4.3 FDT 放在 x0，且该 FDT 的 /memory/reg 含实际非零 RAM banks；
- 若该 FDT /memory/reg 仍是全零 placeholder、没有 memory node、地址不在 U-Boot 可访问映射、或不符合实际扩容 RAM，则 qcom_parse_memory() 会失败，U-Boot 会因无有效 memory ranges 而 panic；因此必须以准确本机 FDT 事实为门槛。

这个设计只借用 previous-bootloader FDT 的 RAM bank tuples；它**不会自动复制** HOS4.3 的 reserved-memory children、no-map/reusable 属性、secure carveouts 或其他设备节点到 U-Boot internal control FDT，也不会自动把它们复制到 ACK Linux DTB。ACK DTB 仍必须有经核验的全部必要 reserved-memory nodes。

## 4. 本机实际阻塞和证据边界

ROUND64 Phase E 明确记载：
- 唯一候选最终 post-ABL FDT `/sys/firmware/fdt` 读取失败：Permission denied；
- stock base FDT 的 /memory/reg 是全零模板占位；
- final post-ABL RAM tuples 和 reservation attributes 未取得；
- 不能把 stock base DTB、CoWave DTS 注释、普通内存总量或另一机型数据替代最终运行时 FDT。

因此：
- U-Boot previous-BL FDT 技术机制：源码 CONFIRMED；
- 本机 ABL 已分析 BootLinux 末端传 x0=final FDT：静态报告 CONFIRMED；
- **本机 ABL recovery 分支是否也调用同一 BootLinux 末端、传入同一类 final FDT：仍 CONDITIONAL，需要对 recovery 选择分支的精确调用闭环；**
- 本机 final FDT 是否有非零真实 12GB RAM bank tuples：BLOCKED / UNKNOWN；
- 现阶段不能仅凭 x0 机制声称 U-Boot 已能取得 12GB RAM map；
- 不能将 CoWave 三段约 8123 MiB（约 7.93 GiB）静态 tuples 复制到扩容后的目标设备。

## 5. 建议的最小下一步

1. AI1 继续只读检查精确 HOS4.3 ABL 的 recovery 分区选择与 BootLinux 调用，证明 recovery/U-Boot 最终路径是否落入报告中的 `0x36C1C–0x388E8` BootLinux 函数，并核对 x0 是否仍是最终 FDT。
2. 若 recovery 路径确认相同，优先让本地只读 Agent 从已有 final FDT / 授权采集重新审查 /memory/reg；若当前权限仍拿不到，就维持 BLOCKED，不重复无意义 adb pull。
3. 只有取得可信 RAM bank tuples 后，再评估 internal DTS 去掉固定 /memory/reg 的小型改动；改动应先在源码/构建配置层验证，不连接设备。
4. 独立核对 ACK 设备树 37 个 reserved-memory 子节点与 HOS4.3 final FDT 的所有范围与属性；不得把 RAM bank fallback 当成 reserved-memory 审计通过。

## 6. 操作边界

本补充没有连接设备、执行 ADB/Fastboot/OEM 命令、构建 U-Boot、生成 FIT/recovery/DTBO、刷写、重启、读取或写入任何分区。没有授权任何设备启动测试或写入。
