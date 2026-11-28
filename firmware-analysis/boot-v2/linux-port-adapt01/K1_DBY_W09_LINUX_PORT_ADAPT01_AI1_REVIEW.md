# K1-DBY-W09-LINUX-PORT-ADAPT01 — AI1 独立审核

**审核日期：2026-11-28**  
**输入 ZIP：** `K1_DBY_W09_LINUX_PORT_ADAPT01_REPORT.zip`  
**ZIP SHA-256：** `bbb97b82eb04c69be230fe4e12c60c2dfb38bb607d18a1abcec2786684bbcc46`  
**审核结论：PROMISING / NOT READY FOR WRITE AUTHORIZATION（核心 VD overlay 发现成立；刷入候选包和 DTBO 选择证据仍不完整）**

## 1. 总结

报告有一项重要且本次可以独立复核的正面发现：

**提取出来的 Stock DTBO Entry 2 FDT 内容确实标识 DBY-W09_VD，且其 overlay fixup 明确把 fragment 的 target 指向 `rootparam`。**

AI1 对 ZIP 内的 `entry_2_rev0.dtbo` 独立解析，确认：

- FDT 根节点 `qcom,board-id = <0x200e 0x0>`；
- `/__fixups__` 节点 `rootparam = "/fragment@143:target:0"`；
- `/fragment@143/__overlay__`：
  - `qcom,boardid = <0x8 0x2 0x0 0x6>`；
  - `qcom,board_name = "DBY_W09_VD"`；
  - `qcom,product_name = "DBY-W09"`；
  - `hardware_version = "SH1DBSLM"`；
  - `huawei,modem_id = <0xffffffff 0x00>`。

Entry 8 也独立解析出 VG 标识：根 `qcom,board-id = <0x206a 0x0>`，overlay `qcom,boardid = <0x8 0x2 0x9 0x8>`、`qcom,board_name = "DBY_W09_VG"`。

因此，**Entry 2 的 overlay 内容与既有 VD 板级字段相符**，这是可信进展。

但报告有 4 个影响刷入准备的重大问题：
1. DTBO table parser 把 `id` 和 `rev` 字段错位命名，Entry 的硬件匹配 metadata 没有被正确报告；
2. 对 `androidboot.dtbo_idx=2` 的解释不正确：该参数是 bootloader 报告已应用 overlay 的索引，不是命令 ABL 选择 Entry 2；
3. ZIP 没有包含 PREP10 `boot.img` 候选、完整 stock DTBO 表或独立 ramdisk 参考件，不能称完整候选包已就绪；
4. 报告明确承认 boot 分区尾部数据/AVB footer 未完全核验，却把 `BOOT_CANDIDATE=PASS`、`IMAGE_PACKAGE=READY_FOR_REVIEW` 写成无条件通过。

## 2. ZIP 和内部完整性

- ZIP size：524,649 B；
- SHA-256 与用户报告的值完全一致；
- ZIP CRC / `testzip()`：PASS；
- ZIP 共 22 个条目；
- `SHA256SUMS.txt` 中所有 21 个非清单文件重新计算均匹配；
- 未发现 CRC 损坏或内部哈希不匹配。

但该 ZIP 包含 9 个提取后的 DTBO overlay、8 个参考文件、3 个脚本、报告和清单；**不包含**：
- 完整原始 stock `dtbo.img`（25,165,824 B）；
- PREP10 `boot.img`（46,563,215 B）；
- stock separate ramdisk 原件（2,097,152 B）；
- `partition_map.md`、独立 `apply_plan_NOT_EXECUTED.md`、`restore_plan_NOT_EXECUTED.md` 或 `packaging_repro.md`。

所以 `IMAGE_PACKAGE=READY_FOR_REVIEW` 只能表示“报告与解析素材交付”，不能表示三分区候选包已完整交付。当前报告实际上拟议的是 boot-only 更新，DTBO 和 separate ramdisk 保持不写。

## 3. Entry 2 VD overlay：独立解析结果

AI1 使用独立 FDT token parser 对 ZIP 内 Entry 2 / Entry 8 二进制解析，并检查 `__fixups__`：

| 属性 | Entry 2 | Entry 8 |
|---|---|---|
| Root `qcom,board-id` | `<0x200e 0x0>` | `<0x206a 0x0>` |
| `/rootparam` qcom,boardid | `<0x8 0x2 0x0 0x6>` | `<0x8 0x2 0x9 0x8>` |
| `/rootparam` qcom,board_name | `DBY_W09_VD` | `DBY_W09_VG` |
| `/rootparam` qcom,product_name | `DBY-W09` | `DBY-W09` |
| `/rootparam` hardware_version | `SH1DBSLM` | `SH1DBSLM` |
| `__fixups__.rootparam` | `/fragment@143:target:0` | `/fragment@143:target:0` |

这确认 Entry 2 overlay 的 `fragment@143` 目标是 rootparam，而不是仅仅因为二进制字符串中出现 `rootparam` 就推断。Entry 2 的 `/rootparam` 属性值与此前记录的本机 VD live FDT 关键字段相符。

**证据等级：**
- Entry 2 overlay FDT 字节内容：AI1 独立确认；
- Entry 2 fragment target 通过 `__fixups__` 指向 `rootparam`：AI1 独立确认；
- 与此前 live FDT 关键字段一致：基于既有冻结 live FDT 记录；
- 该 Entry 在本机启动时一定被 ABL 选择并应用：尚需正确解析原始 DTBO table metadata 与本机 bootloader 选择行为，不由 overlay 内容本身单独证明。

## 4. 重大修正一：DTBO table parser 字段错位

Android DTBO table entry 标准布局为：

```c
struct dt_table_entry {
    uint32_t dt_size;
    uint32_t dt_offset;
    uint32_t id;
    uint32_t rev;
    uint32_t custom[4];
};
```

官方 AOSP 文档说明，`id`、`rev`、`custom[0..3]` 是可供 bootloader 用于识别目标 DTBO 的硬件标识字段：
- https://source.android.com/docs/core/architecture/dto/partitions
- https://source.android.com/docs/core/architecture/bootloader/dtb-images

交付脚本 `scripts/dtbo_parse.py` 使用：

```python
(dsize, doff, rev_id, custom0, custom1, custom2, custom3, _) = struct.unpack(">8I", ...)
```

这会造成错位：
- `rev_id` 实际是 `id`；
- `custom0` 实际是 `rev`；
- `custom1`、`custom2`、`custom3` 实际是 `custom[0]`、`custom[1]`、`custom[2]`；
- 被丢弃的 `_` 实际是 `custom[3]`。

因此报告里的 `dtbo_rev=0` 与 `custom=[0,0,0,0]` 并非从正确字段映射得出；真正的 `id` 没被作为 id 报告，真正的 `custom[3]` 被丢弃。由于完整原始 stock DTBO 未随 ZIP 提供，AI1 不能从当前包恢复原始 table entry metadata。

**修正要求：**从本机已有 stock `dtbo.img` 原始备份离线重跑正确解析，输出每个 entry 的真实 `id`、`rev`、`custom[0..3]`、`dt_size`、`dt_offset`，验证边界/重叠/对齐与 9 个 extracted blobs 一一对应。不得连接设备重新读取。

## 5. 重大修正二：`androidboot.dtbo_idx=2` 不是选择命令

报告称 PREP10 cmdline 中 `androidboot.dtbo_idx=2` “正是选中了 Entry 2”，这一表述必须改写。

AOSP 文档明确规定：
- bootloader 先识别设备并选择对应 overlay；
- 然后把 `androidboot.dtbo_idx` 参数追加到 kernel command line；
- 该参数表示 bootloader 实际应用于 base DT 的 DTBO 分区条目零基索引，按应用顺序记录。

参考：
- https://source.android.com/docs/core/architecture/dto/compile （“Indicate applied overlays”及“Implement the DTBO partition”）
- https://source.android.com/docs/core/architecture/bootloader/dtb-images （`androidboot.dtb_idx` 用于报告 bootloader 已选择的 DT index）

因此，**cmdline 中出现 `androidboot.dtbo_idx=2` 本身不是要求 ABL 选择 Entry 2 的指令**。它应理解为“当前被传递的 cmdline 声称索引 2 已被应用”或历史 stock cmdline token。是否由当前 ABL 再次选择 Entry 2，要依赖它自身对板级 ID、DTBO table metadata 或 root-level board property 的处理逻辑。

结合 Entry 2 与本机 VD 字段一致，这是强支持证据；但需要先修复 table parser 并确认实际匹配 metadata，不能靠 `dtbo_idx` token 自证。

## 6. 重大修正三：boot prefix 与分区尾部安全

报告记载：
- boot 分区为 100,663,296 B；
- PREP10 文件为 46,563,215 B；
- 按项目脚本设计，只写分区前缀，尾部约 54,100,081 B 保留；
- 但报告明确说尾部是否存在 AVB footer 或私有数据仍未完全闭合。

这意味着：
- `46,563,215 < 100,663,296` 只能证明候选文件长度小于分区容量；
- 不能单独证明 prefix write 一定安全；
- 必须核验 stock boot 完整 96 MiB dump 的末尾 footer、AVB footer magic/descriptor、末端非零区域及相关 metadata；
- 并确认 bootloader 对 boot 分区是按 header payload size 读取，还是还验证分区尾部数据/签名。

如果 stock boot 已经有独立证据证明无 AVB footer，也应在报告中引用该证据文件、偏移、扫描范围和 hash，不应留成未确认状态。

**修正前，BOOT_CANDIDATE 不应标为无条件 PASS。** 可以标为 `PREP10_PAYLOAD_FORMAT_PASS / PARTITION_PREFIX_WRITE_GATE_PENDING`。

## 7. 其他审核项

1. `matepad.sh` 路径 404 是引用路径问题，不是仓库文件确实不存在。README/Installer 中实际脚本在 `app/src/main/assets/matepad.sh`；后续应按该路径冻结 blob SHA。
2. `BOOT_V2_REPACK=PASS` 用词不严谨。本次没有生成新的 repacked boot；报告是验证既有 PREP10 v2 头部和 payload。应拆成 `PREP10_BOOT_V2_PARSE=PASS` 与 `STOCK_BASE_REPACK_REPRODUCED=NOT_PERFORMED`。
3. 报告只核对 header_version/page_size 和 payload size/hash。若最终保留 PREP10 作为候选，还需用 stock boot 与 PREP10 的解析结果逐项比较 kernel/ramdisk/second/recovery_dtbo/dtb size、各 offset/base、cmdline、header fields、boot ID，并说明为何不需要重新打包。
4. PREP10 的 `ignore_loglevel` 是调试参数；是否保留应在用户授权前作出清晰决定。它不能补救 K1 无 console 的限制。
5. Separate ramdisk KEEP_STOCK_NO_WRITE 与本机目标相比是合理、保守的决策；不要把参考项目的 Kubuntu initramfs 移植进 Android ACK。
6. DTBO 原分区如果保持 stock，实际计划应该是不写 DTBO；不要为了“刷三分区”而无意义地重写同一个 25 MiB 原厂 DTBO。

## 8. 修正后的状态

```text
REPORT_ZIP_SHA256_AND_CRC       = PASS
INTERNAL_SHA256SUMS             = PASS
PROJECT_REFERENCE_FILES         = PASS (8/9; matepad.sh path needs correction)
ENTRY_2_FDT_CONTENT             = PASS (AI1 independently parsed)
ENTRY_2_ROOTPARAM_FIXUP         = PASS (AI1 independently parsed)
ENTRY_2_VD_PROPERTIES           = PASS (matches frozen VD fields)
STOCK_DTBO_TABLE_METADATA       = UNKNOWN (parser mis-mapped id/rev/custom)
ANDROIDBOOT_DTBO_IDX_SEMANTICS  = CORRECTED (reports applied index; not selector)
ABL_SELECTS_ENTRY_2             = STRONGLY_SUPPORTED / NOT_FULLY_PROVEN
STOCK_BOOT_IDENTITY             = PASS (executor-reported; original not in ZIP)
PREP10_BOOT_V2_PARSE             = PASS (existing candidate)
STOCK_BASE_REPACK_REPRODUCED     = NOT_PERFORMED
BOOT_PREFIX_TAIL_SAFETY          = PENDING
BOOT_CANDIDATE                   = CONDITIONAL / NOT READY FOR WRITE
DTBO_ACTION                      = KEEP_STOCK (pending table metadata correction)
SEPARATE_RAMDISK_ACTION           = KEEP_STOCK_NO_WRITE
COMPLETE_CANDIDATE_PACKAGE        = INCOMPLETE (boot binary and partition map/plan omitted)
DEVICE_WRITE_PERFORMED            = NO
DEVICE_REBOOT_PERFORMED           = NO
FINAL_RESULT                      = VD_OVERLAY_CONFIRMED_BOOT_WRITE_GATE_PENDING
```

## 9. 下一步最小修订范围

无需重复编译内核或重新分析 9 个 overlay 的完整内容。仅做一次有限的离线更正：

1. 对原始 stock DTBO 重新解析并修正 `dt_table_entry` 字段映射，提供全部 9 项正确 `id/rev/custom[]`。
2. 将 `androidboot.dtbo_idx=2` 解释改为“bootloader 选择结果索引”，再用正确的 table metadata 与历史 live FDT 证明本机 VD 对应 Entry 2。
3. 用本机 stock 96 MiB boot 原件确认尾部 AVB footer/非零元数据情况；如果无法证明，保持 prefix write gate blocked。
4. 用 frozen stock boot 与 PREP10 parser 输出完整头字段/组件差异；不必生成新镜像，除非发现确实要 repack。
5. 交付 PREP10 候选文件本身（或清晰指向其精确本地路径和 SHA）及 `partition_map.md`、`apply_plan_NOT_EXECUTED.md`、`restore_plan_NOT_EXECUTED.md`、`packaging_repro.md`。原始 stock 96 MiB boot、DTBO、ramdisk 完整镜像不必上传公开 GitHub，可保留本地并在 report 中给哈希。
6. 更新 SHA256SUMS 并提交修订包。

**本次审核不授权任何设备写操作。不要执行 dd、fastboot flash、reboot、ADB 或设备连接。**

**审核结论：核心 VD overlay 内容发现通过；由于 DTBO table metadata 解码错位、`dtbo_idx` 语义误读、boot 尾部安全待核实和候选二进制缺失，目前还不能授权写入。**