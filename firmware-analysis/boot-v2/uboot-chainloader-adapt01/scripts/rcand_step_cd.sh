#!/bin/sh
set -e
OUT=/home/kerneldev/build/rcand
CW=/home/kerneldev/cowave
WS=/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf
# cowave cmdline = CoWave pack-recovery.sh line 43 (== stock recovery cmdline)
grep -oP "cmdline='\K[^']+" $CW/scripts/pack-recovery.sh > $OUT/cowave-cmdline.txt
wc -c $OUT/cowave-cmdline.txt
python3 $WS/UBOOT_CHAINLOADER_ADAPT01/scripts/pack_uboot_recovery_candidate.py \
  --stock-recovery /mnt/d/workbuddy/2026-11-25-22-04-11/r155/copies-primary/recovery.img \
  --uboot-bin /home/kerneldev/build/u-boot-2026.10/build/u-boot.bin \
  --mkbootimg $CW/tools/vendor/mkbootimg/mkbootimg.py \
  --unpack-bootimg $CW/tools/vendor/mkbootimg/unpack_bootimg.py \
  --unpack-dir $OUT/stock-unpack \
  --output $OUT/recovery-uboot-candidate.img \
  --cmdline cowave \
  --expected-stock-sha256 956417584d2deb409761316f262732859e356a15cb5fe85436df3d5f141c5548
echo '=== D. read-back verification ==='
python3 $CW/tools/vendor/mkbootimg/unpack_bootimg.py --boot_img $OUT/recovery-uboot-candidate.img --out $OUT/cand-unpack --format info > $OUT/candidate-unpack-info.txt 2>&1 || true
head -25 $OUT/candidate-unpack-info.txt
echo '-- component compare (stock vs candidate):'
for c in ramdisk dtb recovery_dtbo; do
  echo "$c stock=$(sha256sum $OUT/stock-unpack/$c | cut -c1-16) cand=$(sha256sum $OUT/cand-unpack/$c | cut -c1-16)"
done
echo '-- kernel gzip roundtrip:'
gzip -dc $OUT/cand-unpack/kernel > $OUT/uboot-roundtrip.bin
echo "roundtrip=$(sha256sum $OUT/uboot-roundtrip.bin | cut -c1-16) uboot=$(sha256sum /home/kerneldev/build/u-boot-2026.10/build/u-boot.bin | cut -c1-16)"
echo '-- header immutable-field compare (from info outputs):'
grep -E 'boot image header version|page size|kernel load|ramdisk load|tags load|dtb address|recovery dtbo offset|os version|os patch' $OUT/stock-recovery-unpack-info.txt > h1.txt || true
grep -E 'boot image header version|page size|kernel load|ramdisk load|tags load|dtb address|recovery dtbo offset|os version|os patch' $OUT/candidate-unpack-info.txt > h2.txt || true
diff h1.txt h2.txt && echo HEADER_IMMUTABLE_IDENTICAL
echo '-- partition fit:'
echo "candidate_bytes=$(stat -c %s $OUT/recovery-uboot-candidate.img) recovery_partition=100663296"
echo '-- recovery_vbmeta read-only parse:'
python3 /mnt/d/workbuddy/2026-11-25-22-04-11/r155/avbtool.py info_image --image /mnt/d/workbuddy/2026-11-25-22-04-11/r155/copies-primary/recovery_vbmeta.img 2>&1 | head -14
echo '-- TWRP backup registration:'
find /mnt/d -maxdepth 3 -iname '*twrp*' -type f 2>/dev/null | head -3
echo STEP_CD_DONE
