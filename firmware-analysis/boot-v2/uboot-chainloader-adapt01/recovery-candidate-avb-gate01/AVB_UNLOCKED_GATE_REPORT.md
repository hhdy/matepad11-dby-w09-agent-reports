# K1_DBY_W09_UBOOT_RECOVERY_UNLOCKED_AVB_GATE01 — AVB_UNLOCKED_GATE_REPORT

日期：2026-11-29。只读分析（r155 备份、候选镜像、twrp.zip、冻结 ABL PE 引用）。零设备操作。

## 最终矩阵

| Gate | 值 |
|---|---|
| INPUT_IDENTITY | **PASS**（五项冻结输入逐一重算一致：ABL PE `a14e29da…`、stock recovery `95641758…`/100,663,296B、recovery_vbmeta `bf59d55d…`、candidate `b48e9185…`/27,926,528B、u-boot.bin `33741739…`/1,548,664B） |
| STOCK_RECOVERY_AVB_FOOTER | **PRESENT**（分区级 footer @0x5FFFFC0=100,663,296−64B 规范位；ver1.0；original_image_size=49,614,848；vbmeta_offset=0x2F51000 size=1,344） |
| STOCK_RECOVERY_CHILD_VBMETA | **PRESENT**（AVB0 @0x2F51000，1,344 B，algo=1 SHA256_RSA2048，rollback=0；含 recovery 内容 hash 描述符组） |
| CANDIDATE_AVB_FOOTER | **ABSENT**（分区级 footer 不存在；mkbootimg 不产 AVB footer；唯一 AVBf 为内嵌 recovery_dtbo 自带 footer @0x190AFC0，指向候选内 0x3DF000 的 dtbo vbmeta ✓） |
| CANDIDATE_CHILD_VBMETA | **ABSENT**（分区级 child vbmeta 不存在；dtbo 级保留 ✓） |
| RECOVERY_VBMETA_CHAIN_MATCH | **FAIL（对 signed 路径）**：recovery_vbmeta 含 Chain Partition descriptor → recovery (rb_loc=23)，链式验证要求 recovery 分区尾部有被 OEM key 签名的 child vbmeta；candidate 缺失该层 → 签名链不可满足 |
| ABL_UNLOCKED_RECOVERY_ACCEPTANCE | **UNKNOWN**（见 §B；沿 CLOSE01→AUTH 轮结论，全部 auth 判定字段此前即 UNKNOWN，本轮未推翻亦未闭合） |
| TWRP_INSTALL_EFFECT | **PARTIAL**（ZIP 仅含 ramdisk-only twrp.img：boot v0/page2048/kernel_size=0/ramdisk 33,384,890 B、无 AVB footer、无安装脚本；无 vbmeta 修改证据。若用户以 fastboot flash recovery 方式刷入，则当前分区=stock kernel+TWRP ramdisk 且无分区级 AVB footer——若 TWRP 曾实际启动，构成"无分区级 footer 的 recovery 也能被 ABL 加载 kernel"的设备侧观察，但其先决条件（解锁态下 ABL 是否校验）仍未知） |
| FASTBOOT_TAIL_SEMANTICS | **UNKNOWN**（ABL 'partition erasing…' 字符串存在但 erase→write 语义未静态闭合；host fastboot 行为不可作证据） |
| **RECOVERY_CANDIDATE_DEVICE_READY** | **HOLD** |

## 核心问题 A：footer / child vbmeta 明细

| 对象 | AVBf | 位置 | original_size | 指向 vbmeta | child vbmeta |
|---|---|---|---|---|---|
| stock recovery.img（100,663,296B 全分区 dump） | 2 处 | 0x5FFFFC0（分区尾 −64B）；0x2DB9FC0（内嵌 dtbo 自带） | 49,614,848；2,963,810（=dtbo 表尺寸） | 0x2F51000；0x188E000（=recovery_dtbo_offset 0x15BA000+0x2D4000 ✓） | 1,344 B；dtbo 级 1,472 B |
| candidate.img（27,926,528B） | 1 处 | 0x190AFC0（内嵌 dtbo 自带） | 2,963,810 | 0x3DF000（=0x10B000+0x2D4000 ✓） | dtbo 级 1,472 B 保留 ✓ |
| recovery_vbmeta.img（1MiB） | 无 footer（本体即 AVB0 @0x0） | — | — | — | — |

**要点**：① stock recovery 尾部有完整 AVB 链（footer+签名 child vbmeta），candidate 刷入后该尾部区域**不被写入**（write-length-only 假设下残留 stock footer）或**被擦除**（erase 假设下无 footer）——两种语义对应不同的残留状态，均未被证明；② candidate 缺失链式验证所需的签名 child vbmeta；③ recovery_vbmeta 本体不变（本任务未触碰）。
链公钥匹配检查：未执行公钥级比对（OEM key blob 不在本地明文材料中）→ 该子项 UNKNOWN。

## 核心问题 B：ABL UNLOCKED recovery 分支

本轮仅做一次聚焦检查：ABL 含 device_state/unlock 相关字符串（`androidboot.vbmeta.device_state`、`PHONE Relocked`、`RELOCKED`、`secure` 等）与 `LoadImageAndAuth/VB2` 族；**解锁状态的数据源（EFI 变量/devinfo/TEE）与 UNLOCKED→跳过校验的精确条件分支未能在本轮一次 pass 内闭合**。沿 AUTH 轮结论：七项 auth 判定字段全部 UNKNOWN 且未被本轮推翻 → **ABL_UNLOCKED_RECOVERY_ACCEPTANCE=UNKNOWN**。不可把"设备已解锁"直接等同"ABL 忽略 recovery 的 footer/child vbmeta"。
（ADDENDUM01 已证：recovery→共享 BootLinux 尾段、gz→+0x80000、4KiB 对齐、x0=FDT——本轮引用不重复。）

## 核心问题 C：TWRP

`twrp.zip` → 单文件 `twrp.img`：ANDROID! v0（page 2048），**kernel_size=0**，ramdisk=33,384,890 B（TWRP），无 second，无 AVBf，无安装脚本。= "ramdisk-only swap" 形态（保留原 kernel，仅换 recovery ramdisk）。`TWRP_INSTALL_EFFECT=PARTIAL`（无刷入日志/无 vbmeta 修改证据；用户报告的 TWRP 可启动为设备侧既有观察）。

## 核心问题 D：尾部语义

`FASTBOOT_TAIL_SEMANTICS=UNKNOWN`。禁止为保险盲目 pad 96 MiB / 保留旧尾 / 补 footer / 写 recovery_vbmeta——全部留待证据。

## GO/HOLD

**HOLD**。解锁路径：① 需要 ABL UNLOCKED 分支的精确二进制证据（或受控设备侧一次 `fastboot boot` 非持久实验的授权，另行申请）；② 或对 candidate 补齐 AVB footer/签名 child vbmeta——该动作**被本任务与此前任务书禁止**（需签名材料与明确授权）。二者任一闭环后方可重评。
