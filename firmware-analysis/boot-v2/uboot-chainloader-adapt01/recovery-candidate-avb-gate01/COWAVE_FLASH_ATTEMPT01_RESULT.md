# COWAVE_FLASH_ATTEMPT01 — 按原版流程刷入（2026-11-29）

用户授权："根据原版的方式看看能不能成功刷入"。执行 CoWave `docs/install.md §6` 流程。

## 刷写前核验

- 进入方式：硬件按键（音量下 + USB + 电源）——CoWave 文档同款，USB 通路正常
- 候选 recovery：`recovery-uboot-candidate.img` 27,926,528 B，sha `b48e9185…811990`（BUILD01 冻结值一致）
- 新 vbmeta：`recovery_vbmeta-flags2.img` 1,048,576 B，sha `147d2ab1…24c39`；avbtool 1.3.0 `make_vbmeta_image --flags 2 --padding_size 1048576` → Algorithm NONE、Flags 2、rollback 0、无描述符（与 CoWave pack-recovery.sh L64-66 一致）
- 回滚备份在册：stock recovery `95641758…`、stock recovery_vbmeta `bf59d55d…`（r155，manifest 闭环）

## 终端输出

```
fastboot flash recovery recovery-uboot-candidate.img
  Fetching super (offset=0, size=100000)  FAILED (remote: 'unknown command')   ← host 37.0.3 的 fetch 探测，Huawei ABL 不支持，无害
  Sending 'recovery' (27272 KB)           OKAY [  0.650s]
  Writing 'recovery'                      OKAY [  0.129s]
fastboot flash recovery_vbmeta recovery_vbmeta-flags2.img
  Sending 'recovery_vbmeta' (1024 KB)     OKAY [  0.027s]
  Writing 'recovery_vbmeta'               OKAY [  0.009s]
```

## 判定

- **FLASH_RECOVERY = OKAY**、**FLASH_RECOVERY_VBMETA = OKAY** → **COWAVE_FLASH = PASS**
- 刷写在 UNLOCKED 态被 ABL 接受（此前 ATTEMPT02 证明的是 `fastboot boot` RAM 路径被拒；分区 flash 路径不受该限制）
- 设备侧变更：recovery 分区 = U-Boot 候选（**原 on-device TWRP 已被替换**；twrp.zip 备份 `d24331b5…` 保留可重刷）；recovery_vbmeta = flags=2（recovery 哈希/签名校验关闭）
- 未触碰：boot、vbmeta、misc、reserved3、dtbo、ramdisk 等其他分区
- 重启结果：待续（见后续记录）

## 回滚命令（硬件按键进 fastboot 后）

```
fastboot flash recovery <r155>/recovery.img            (95641758…)
fastboot flash recovery_vbmeta <r155>/recovery_vbmeta.img  (bf59d55d…)
fastboot reboot
```
