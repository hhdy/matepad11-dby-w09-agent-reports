# K1_UBOOT_CHAINLOADER_PREBUILD_GATE02 — 报告

- 日期：2026-11-28；一次性有界只读门禁；无设备操作、无构建、无镜像生成、无分区写入
- PE 身份门禁：本轮会话内多次复核 `a14e29da…dbb404` ✓（与任务书一致）

## 组 A

- **A1 `RECOVERY_ENTRY_CHAIN = CONDITIONAL`（维持基线）**：本轮一次 pass 内以 BL 目标扫描（0x36BF0–0x36C30 / 0x4B640–0x4B680）与 8B 对齐指针池再查仍 0 命中——BootLinux 入口经间接机制持有，向函数指针槽赋值者未定位。最小缺失窗口：以尾段 `blr x8`@0x38868 与 loader 族 `blr` 站点为根的寄存器数据流 pass（下一轮唯一静态项）。基线 `RECOVERY_HANDOFF_FINAL_X0_FDT=CONFIRMED` 保持（共享尾段不变量，不单独证明 recovery 到达）。
- **A2 `RECOVERY_INITRD_LABEL = PARTIAL`**：LoadRamdisk@0x3969C 以 label 参数读分区；二进制内在册候选 label：`ramdisk`（0xBE6E4）、`erecovery_ramdisk`（0xC0CBD）；bootmode→label 选择表未定位。**`RECOVERY_INITRD_PAYLOAD_FORM = UNKNOWN`**（recovery 路径 wrapper 剥离未独立复核；PREP04 结论仅限 HOS normal 路径，不套用）。

## 组 B（UpdateDeviceTree 0x3D9D4 + 900 指令窗，新增 dump evidence_updtdt_full.txt）

- `ABL_MEMORY_REG_MUTATION = NOT_FOUND_IN_ANALYZED_PATH`（窗内 149 BL、gBS 加载 @0x3E1A0 等，无 /memory/reg 写路径证据）
- `ABL_RESERVED_MEMORY_MUTATION = NOT_FOUND_IN_ANALYZED_PATH`（同窗）；`ABL_INITRD_MEMRESERVE = UNKNOWN`（chosen start/end 写入 @0x3F0F0/0x3F33C 在窗外沿已证，memreserve 未证——**不得声称 LMB 自动保护 initrd**）
- `ABL_RAM_BANK_VALUES = RUNTIME_DEPENDENT`（EFI_RAMPARTITION provider 不在冻结 PE；GUID-only）
- provider 缺失标注：{9DA5B6E3 族 EFI_RAMPARTITION} 实现不在现有资料 → 不得由协议名推断返回内容。

## 组 C

- **C1 `UBOOT_FINAL_CONFIG = MISSING`**：本地无 CoWave U-Boot v2026.10 构建目录/最终 `.config`（D:\Downloads 仅 PREP06 ACK 包；其 config 为 ACK kernel 配置，非 U-Boot）→ 14 项 CONFIG 值全部缺失，不得由 defconfig 推断。
- **C2 `FIT_RESERVED3_CAPACITY = UNKNOWN_NOT_BUILT`**：本地无 ACK gzip、VD DTB、ITS 或完整 FIT 产物；reserved3 = 25,165,824 B（partition_map 已证）仅作预算上限记录。已存在文件盘点：仅源级输入（ACK Image `f89a2839…`、PREP10 boot、candidate DTB `7bb9a1fb…`），无派生候选。
- **C3 `RECOVERY_WRITE_SURFACE_BACKUPS = INCOMPLETE`**：r155 copies-primary 内 `recovery.img`、`recovery_ramdisk.img`、`recovery_vbmeta.img`、`erecovery.img`、`erecovery_ramdisk.img`、`erecovery_vbmeta.img` 在册（PREP12 采集），但本轮未完成逐项 SHA-256/manifest provenance 闭环 → 按任务书规则维持写入门禁 **NO-GO**。

## 总判定

| 阶段 | 结论 |
|---|---|
| 继续静态源码准备 | 可继续（blr 根数据流 pass + label 表 + UpdateDeviceTree 全函数窗为仅余三项） |
| host-side package preparation | 未具备（.config 缺失、FIT 未构建、initrd label/payload form 未定） |
| 生成/修改 recovery 或 FIT 候选 | 不授权 |
| 设备临时启动 / 刷写 | **NO-GO**（C3 provenance 未闭环） |

**`PREBUILD_READINESS = HOLD`**（任一关键静态信息未知 + 备份 provenance 未闭环）。不解释为任何设备写入授权。

## 未闭合项与唯一最小证据

1. A1：blr 根寄存器数据流 pass（一次，静态）。
2. A2：LoadRamdisk 调用者 label 参数窗口（一次，静态）。
3. B：UpdateDeviceTree 全函数边界 + FDT 写路径窗（一次，静态）。
4. C1：获取 CoWave U-Boot 最终 `.config`（主机侧文件）。
5. C3：recovery 链 6 文件 SHA-256 + manifest provenance 闭环（本地只读）。
6. 设备侧 final-FDT capture（/memory/reg 唯一权威证据）——需用户另行授权，本轮未做。

停止：单报告 + GitHub 回读后停止，不自动开启下一轮。
