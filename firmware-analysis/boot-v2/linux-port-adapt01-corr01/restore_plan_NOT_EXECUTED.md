# 恢复计划（NOT EXECUTED — 仅文档）

**本计划不构成设备写入授权。仅当 PREP10 写入后需要恢复原厂 HarmonyOS 时使用。**

## 前提
- 用户持有原厂 boot 完整 96 MiB 备份，SHA-256 = `7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8`
- 恢复介质二选一：
  - **A. 设备侧备份**：`/data/local/tmp/boot_backup_96MiB.img`（若 PREP10 写入前已按 apply_plan 执行备份且可从 Linux root shell 读取）
  - **B. 主机侧备份**：`r155/copies-primary/boot.img`（100,663,296 B）通过 fastboot/adb 推送

## 恢复路径 A（设备侧备份仍在，设备可进系统或 recovery root shell）

```bash
BOOT_DEV=$(for base in /dev/block/by-name /dev/block/bootdevice/by-name; do
  [ -e "$base/boot" ] && echo "$base/boot" && break; done)

# 1. 核对备份哈希
sha256sum /data/local/tmp/boot_backup_96MiB.img
# 期望: 7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8

# 2. 写回完整 96 MiB
dd if=/data/local/tmp/boot_backup_96MiB.img of="$BOOT_DEV" bs=1048576 conv=fsync

# 3. 读回核验
READBACK=$(sha256sum "$BOOT_DEV" | cut -d' ' -f1)
[ "$READBACK" = "7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8" ] || {
  echo "FATAL: restore readback mismatch — STOP" >&2; exit 1; }
sync
```

## 恢复路径 B（设备无法启动，走 fastboot）

```bash
# 主机侧（fastboot 模式）
fastboot flash boot r155/copies-primary/boot.img
# fastboot 校验通过后
fastboot reboot
```

注意：
- `r155/copies-primary/boot.img` 是 100,663,296 B 完整分区副本（含全零尾部），`fastboot flash` 会整块写入，恢复后 boot 分区哈希应与 `7a95c897…39d24a8` 一致。
- 恢复后 DTBO / separate ramdisk / vbmeta 均未动过（本候选方案不写这些分区），无需额外恢复。
- 若之前做过 GhostLock ABL 替换（PREP13/14 轮次），ABL 不在 boot 分区内，恢复 boot 不影响 ABL 状态；HarmonyOS 恢复以 boot 分区为唯一必要项。

## 恢复验证
- 设备正常启动 HarmonyOS
- `adb shell sha256sum /dev/block/by-name/boot`（root）= `7a95c897…39d24a8`
