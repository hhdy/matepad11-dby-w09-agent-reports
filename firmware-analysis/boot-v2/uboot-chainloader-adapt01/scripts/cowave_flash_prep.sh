#!/bin/sh
# CoWave original flow step 1: generate flags=2 recovery_vbmeta + pre-flight identity checks
set -e
OUT=/home/kerneldev/build/rcand
AVB=/mnt/d/workbuddy/2026-11-25-22-04-11/r155/avbtool.py
WT=/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/rcand-tmp
cd "$OUT"
echo '== generate flags=2 recovery_vbmeta (CoWave pack-recovery.sh L64-66) =='
python3 "$AVB" make_vbmeta_image --flags 2 --padding_size 1048576 --output recovery_vbmeta-flags2.img
stat -c 'bytes=%s' recovery_vbmeta-flags2.img
sha256sum recovery_vbmeta-flags2.img
python3 "$AVB" info_image --image recovery_vbmeta-flags2.img
cp recovery_vbmeta-flags2.img "$WT/"
echo '== files to flash (Windows-accessible copy) =='
cd "$WT"
sha256sum recovery-uboot-candidate.img recovery_vbmeta-flags2.img
stat -c '%n %s' recovery-uboot-candidate.img recovery_vbmeta-flags2.img
echo '== rollback backups present (r155, manifest-closed) =='
sha256sum /mnt/d/workbuddy/2026-11-25-22-04-11/r155/copies-primary/recovery.img /mnt/d/workbuddy/2026-11-25-22-04-11/r155/copies-primary/recovery_vbmeta.img
echo '== CoWave install.md flash section =='
sed -n '104,121p' /home/kerneldev/cowave/docs/install.md
echo PREP_DONE
