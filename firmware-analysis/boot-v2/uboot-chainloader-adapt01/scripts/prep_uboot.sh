#!/bin/sh
set -e
mkdir -p /home/kerneldev/build && cd /home/kerneldev/build
if [ ! -f u-boot-v2026.10.tar.gz ]; then
  curl -sfL --retry 3 -o u-boot-v2026.10.tar.gz https://github.com/u-boot/u-boot/archive/refs/tags/v2026.10.tar.gz
fi
echo "f943a88389c8fd70a6b0d061a88267465e143c7ca6ea2b75837ab20f5b60c739  u-boot-v2026.10.tar.gz" | sha256sum -c -
if [ ! -d u-boot-2026.10 ]; then tar xzf u-boot-v2026.10.tar.gz; fi
cd u-boot-2026.10
if [ ! -f .loa-patched ]; then
  for p in /home/kerneldev/cowave/uboot/patches/*.patch; do
    echo "== applying $p"; patch -s -d . -p1 < "$p" || { echo "PATCH_FAIL $p"; exit 1; }
  done
  install -m644 /home/kerneldev/cowave/uboot/dby-w09_defconfig configs/dby-w09_defconfig
  touch .loa-patched
  echo PATCHES_APPLIED
fi
make CROSS_COMPILE=aarch64-linux-gnu- O=build dby-w09_defconfig 2>&1 | tail -2
grep -E 'CONFIG_CMD_ABOOTIMG|CONFIG_ANDROID_BOOT_IMAGE|CONFIG_SAVE_PREV_BL_FDT_ADDR|CONFIG_SYS_BOOTM_LEN|CONFIG_INIT_SP_RELATIVE' build/.config || echo 'GREP_NO_MATCH'
echo PREP_DONE
