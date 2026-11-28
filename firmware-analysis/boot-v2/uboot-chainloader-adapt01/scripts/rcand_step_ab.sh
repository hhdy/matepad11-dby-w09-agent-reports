#!/bin/sh
set -e
OUT=/home/kerneldev/build/rcand
mkdir -p $OUT
R=/mnt/d/workbuddy/2026-11-25-22-04-11/r155/copies-primary
UB=/home/kerneldev/build/u-boot-2026.10/build/u-boot.bin
CW=/home/kerneldev/cowave
echo '=== A. input identity ==='
echo '-- manifest recovery entry:'
grep -E '^recovery\s' /mnt/d/workbuddy/2026-11-25-22-04-11/r155/evidence/capture_manifest.tsv
echo '-- local stock recovery recompute:'
sha256sum $R/recovery.img
stat -c 'size=%s' $R/recovery.img
echo '-- corrected u-boot.bin:'
sha256sum $UB
stat -c 'size=%s' $UB
echo '-- vendor tools:'
sha256sum $CW/tools/vendor/mkbootimg/mkbootimg.py $CW/tools/vendor/mkbootimg/unpack_bootimg.py
echo '=== CoWave reference cmdline (READ ONLY, from pack-recovery.sh) ==='
grep -n -i 'cmdline' $CW/scripts/pack-recovery.sh | head -5
grep -n -i 'cmdline\|console\|earlycon' $CW/tools/host/boot-linux.sh 2>/dev/null | head -8
echo '=== B. unpack stock recovery ==='
cd $OUT
python3 $CW/tools/vendor/mkbootimg/unpack_bootimg.py --boot_img $R/recovery.img --out $OUT/stock-unpack --format info > stock-recovery-unpack-info.txt 2>&1 || true
cat stock-recovery-unpack-info.txt
python3 $CW/tools/vendor/mkbootimg/unpack_bootimg.py --boot_img $R/recovery.img --out $OUT/stock-unpack --format mkbootimg -0 > stock-mkbootimg-args.txt 2>&1 || true
cat stock-mkbootimg-args.txt; echo
ls -la $OUT/stock-unpack/
echo '=== component hashes ==='
sha256sum $OUT/stock-unpack/* 2>/dev/null | head -12
echo STEP_AB_DONE
