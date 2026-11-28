#!/bin/sh
cd /mnt/d/workbuddy/2026-11-25-22-04-11/r155/copies-primary
for f in recovery.img recovery_ramdisk.img recovery_vbmeta.img erecovery.img erecovery_ramdisk.img erecovery_vbmeta.img; do
  sz=$(stat -c %s "$f")
  h=$(sha256sum "$f" | cut -d' ' -f1)
  echo "$f size=$sz sha256=$h"
done
DK=/home/kerneldev/build/u-boot-2026.10/build/tools/dumpimage
"$DK" -l /mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/UBOOT_CHAINLOADER_ADAPT01/fit/dby-w09-ack.itb > /dev/null 2>&1
echo "DUMPIMAGE_EXIT=$?"
