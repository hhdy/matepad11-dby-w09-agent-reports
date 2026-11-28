# K1_DBY_W09_UBOOT_CHAINLOADER_ONEPASS01 — 综合报告

- 日期：2026-11-28；单次执行单报告；**无设备连接、无设备侧读取、无分区写入/刷写、无 AVB/vbmeta 修改**
- ABL PE SHA：`a14e29da…dbb404` ✓（会话内复核）；基线：AUDIT01 `7f03c2fd`、GATE02 `8d1f1190`（直接采用，未重复）

## 1. ABL 静态收敛（§2）

| 字段 | 值 |
|---|---|
| RECOVERY_ENTRY_CHAIN | **CONDITIONAL**（两次 BL/ptr 扫描 0 命中；按 §11.1 不再循环同类搜索——最小缺口仍为 blr 根数据流 pass） |
| RECOVERY_INITRD_LABEL | **PARTIAL**（候选 ramdisk/erecovery_ramdisk 在册，选择表未定位） |
| RECOVERY_INITRD_PAYLOAD_FORM | **UNKNOWN** |
| ABL_MEMORY_REG_MUTATION | NOT_FOUND_IN_ANALYZED_PATH（GATE02 900 指令窗基线沿用） |
| ABL_RESERVED_MEMORY_MUTATION | NOT_FOUND_IN_ANALYZED_PATH |
| ABL_INITRD_MEMRESERVE | UNKNOWN（chosen 写入已证，memreserve 未证） |
| ABL_RAM_BANK_VALUES | RUNTIME_DEPENDENT（EFI_RAMPARTITION provider 不在冻结 PE） |

## 2. recovery 链备份 provenance 闭环（§11.2）

| 文件 | SHA-256 | 备注 |
|---|---|---|
| recovery.img | `95641758…1c5548` | **== erecovery.img 逐字节相同 → provenance 异常**（采集副本混淆或分区内容同名；无法证明为独立 recovery 备份） |
| recovery_ramdisk.img | `1a703a84…2295` | **== erecovery_ramdisk.img 相同**（同上异常） |
| recovery_vbmeta.img | `bf59d55d…507b` | 独立哈希 ✓ |
| erecovery.img | `95641758…1c5548` | 与 recovery.img 同 |
| erecovery_ramdisk.img | `1a703a84…2295` | 与 recovery_ramdisk.img 同 |
| erecovery_vbmeta.img | `ed04c848…6c73f` | 独立哈希 ✓ |

来源 manifest：r155 copies-primary（2026-11-25 采集，PREP12 分区 inventory label 对应）。**判定：recovery/recovery_vbmeta 备份不构成已验证独立恢复能力 → 写入门禁维持 NO-GO**（recovery.img 身份必须先解决）。

## 3. U-Boot 源码/工具链/配置/构建（§3）

- CoWave repo 未在本 pass 固定 clone（时间预算内优先完成备份/FDT/容量项）；上游 v2026.10 源码未落盘。
- 工具链盘点（Ubuntu-24.04，gcc 13.3.0 host）：**aarch64-linux-gnu-gcc 缺失、dtc 缺失、mkimage 缺失**（任务书禁装新工具）→ **U-Boot 构建 BLOCKED**；FIT 实体构建 BLOCKED（缺 dtc/mkimage）。
- 最终 `.config` = MISSING（依赖构建）；14 项 CONFIG 未取值。

## 4. FIT 容量预算（§4.2，仅计算非构建）

- gzip ACK Image（`f89a2839…`，gzip -6 实测）= **17,860,410 B ≈ 17.04 MiB**
- VD DTB（`7bb9a1fb…`，1,216,399 B ≈ 1.16 MiB）+ ITS/元数据/对齐开销 ≈ 0.2 MiB
- **预算合计 ≈ 18.4 MiB < reserved3 25,165,824 B（24 MiB）→ 容量预算信号 PASS（算术）**；实际 FIT 文件 = UNKNOWN_NOT_BUILT（缺 mkimage/dtc）。gzip 路线使 24 MiB 方案可行——这是本轮最重要的正信号。

## 5. ACK / DTB / ramdisk 输入（§4）

- ACK Image `f89a2839…`（44,820,992 B，text_offset=0，flags=0xA）、VD DTB `7bb9a1fb…`（1,216,399 B）来源=PREP 冻结构建 ✓。
- live separate ramdisk `4dd6d91a…`（v0 wrapper，payload `4f71768a…`，cpio 含 init/init.real/ksu.ko）— ADDENDUM01 已解析，本轮未重复。
- wrapper 沙箱解析验证：未执行（无 U-Boot 源码/沙箱环境落盘）→ PARTIAL。

## 6. recovery 认证门禁（§5）

LoadImageAndAuth/VB2 路径存在（字符串/调用站点已证），但 **AVB/vbmeta 对 recovery 容器的实际验证行为未闭合**（前轮 auth 问题仍 UNKNOWN）。替换 kernel 的候选能否通过合法认证 = **UNKNOWN；若需 OEM 私钥/vbmeta 修改则 AUTH_BLOCKED**。未生成任何候选。

## 7. 最终门禁（§7）

| 门 | 值 |
|---|---|
| HOST_PACKAGE_READINESS | **BLOCKED**（缺 aarch64-gcc/dtc/mkimage；U-Boot 源码未固定） |
| DEVICE_BOOT_READINESS | **NO_GO / HOLD**（调用链 CONDITIONAL、initrd label PARTIAL、RAM UNKNOWN、备份 provenance 异常、认证 UNKNOWN、reserved-memory 37 节点对照未做） |
| USER_AUTHORIZATION_GATE | **AUTHORIZATION_REQUIRED**（唯一权威 final-FDT capture） |
| **ONEPASS_RESULT** | **PARTIAL_BLOCKED** |

## 8. 未闭合项与唯一最小证据

1. U-Boot 构建：安装 aarch64 交叉工具链 + dtc/mkimage（主机侧，需用户许可"安装工具"）后即可解 BLOCK。
2. recovery.img 身份异常：对照采集 manifest 或设备 label（只读，需授权）。
3. A1 blr 根数据流 pass；A2 label 表（静态，一次）。
4. final-FDT capture（设备只读，需授权）→ 唯一可解 RAM/RESERVED 全部 UNKNOWN。
5. CoWave 源码固定 + defconfig 落盘。

## 声明

无设备连接/读取、无 reboot/临时启动、无分区写入/刷写、无 AVB/vbmeta 修改、无原始固件上传 ✓。回读后任务结束，不再创建后续任务书。
