#!/bin/sh
set -e
OUT=/home/kerneldev/build/rcand
echo '-- TWRP backup hash (register only):'
sha256sum "/mnt/d/解锁bl/download/twrp.zip" || true
echo '-- component_hashes.tsv:'
{
  echo -e "file\tsha256\tbytes"
  echo -e "stock-recovery.img\t956417584d2deb409761316f262732859e356a15cb5fe85436df3d5f141c5548\t100663296"
  echo -e "stock-unpack/kernel\tnone(gz,not-needed)\t22254704"
  echo -e "stock-unpack/ramdisk\t$(sha256sum $OUT/stock-unpack/ramdisk | cut -d' ' -f1)\t519986"
  echo -e "stock-unpack/dtb\t$(sha256sum $OUT/stock-unpack/dtb | cut -d' ' -f1)\t1664243"
  echo -e "stock-unpack/recovery_dtbo\t$(sha256sum $OUT/stock-unpack/recovery_dtbo | cut -d' ' -f1)\t25165824"
  echo -e "u-boot.bin\t3374173973336c263259ca6c545b2dda072f09af7f2b0f468a12ec0b0a3f3e46\t1548664"
  echo -e "candidate-kernel.gz\t$(sha256sum $OUT/recovery-uboot-candidate.img.kernel.gz | cut -d' ' -f1)\t$(stat -c %s $OUT/recovery-uboot-candidate.img.kernel.gz)"
  echo -e "recovery-uboot-candidate.img\tb48e9185e0260706f4f8275bd73ab9c4f22a8bdaa5bba366a25d2f0704811990\t27926528"
  echo -e "recovery_vbmeta.img\tbf59d55d664b9f6295273b10701845b9e4e3f184b6e7c5140f29681d1c5b507b\t1048576"
  echo -e "twrp.zip\t$(sha256sum '/mnt/d/解锁bl/download/twrp.zip' | cut -d' ' -f1)\t$(stat -c %s '/mnt/d/解锁bl/download/twrp.zip')"
} | tee $OUT/component_hashes.tsv
cd $OUT
sha256sum recovery-uboot-candidate.img component_hashes.tsv stock-recovery-unpack-info.txt stock-mkbootimg-args.txt candidate-unpack-info.txt recovery-uboot-candidate.img.report.json > SHA256SUMS
cat SHA256SUMS
echo FINALIZE_DONE
