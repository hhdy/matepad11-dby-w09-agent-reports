# 写入计划（NOT EXECUTED — 仅文档）

**本计划不构成设备写入授权。任何写入操作须用户另行明确授权并由用户或经授权的 Agent 执行。**

## 前提条件
- 设备处于 HarmonyOS 且已取得 KernelSU root（`uid=0(root) context=u:r:ksu:s0`）
- ADB 已连接且已授权
- 设备有足够电量（>50%）
- 已备份原厂 boot 分区完整 96 MiB 副本（`7a95c897…39d24a8`）

## 写入步骤（仅 boot 分区）

```bash
# 1. 确认分区路径
BOOT_DEV=$(for base in /dev/block/by-name /dev/block/bootdevice/by-name; do
  [ -e "$base/boot" ] && echo "$base/boot" && break; done)
echo "boot partition: $BOOT_DEV"

# 2. 核对分区容量（须 ≥ 46,563,215 B）
blockdev --getsize64 "$BOOT_DEV"
# 期望: 100663296

# 3. 完整备份原厂 boot 96 MiB
dd if="$BOOT_DEV" of=/data/local/tmp/boot_backup_96MiB.img bs=1048576
sha256sum /data/local/tmp/boot_backup_96MiB.img
# 期望: 7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8

# 4. 推送 PREP10 boot.img 到设备
adb push PREP10_BOOT.img /data/local/tmp/PREP10_boot.img
sha256sum /data/local/tmp/PREP10_boot.img
# 期望: d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091

# 5. 写入 boot 分区前 46,563,215 B
dd if=/data/local/tmp/PREP10_boot.img of="$BOOT_DEV" bs=1048576 conv=fsync 2>/dev/null

# 6. 读回核验（同长度 SHA-256）
READBACK=$(head -c 46563215 "$BOOT_DEV" | sha256sum | cut -d' ' -f1)
echo "readback sha256: $READBACK"
# 期望: d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091
[ "$READBACK" = "d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091" ] || {
  echo "FATAL: readback mismatch — STOP" >&2; exit 1; }

# 7. sync
sync

# 8. 重启（用户手动执行或经授权后执行）
# reboot
```

## DTBO / Separate ramdisk
- **不写入**——保持 stock 原样
- stock DTBO 分区（25,165,824 B）中 Entry 2 (VD) 已含正确 /rootparam
- stock separate ramdisk（2,097,152 B）中的 init/init.real 继续作为 kernel initrd

## 失败处理
- 任何 readback mismatch → 立即停止，不继续，不 reboot
- 恢复：dd boot_backup_96MiB.img → boot 分区，readback 验证 `7a95c897…`

## 注意
- PREP10 写入 boot 分区后，设备重启将使用 ACK kernel 而非 HOS kernel
- 恢复到 HOS 需要从完整 96 MiB 备份写回 boot 分区
