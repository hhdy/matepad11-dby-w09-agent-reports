#!/bin/sh
cd /home/kerneldev/cowave
echo "HEAD=$(git rev-parse HEAD) tree=$(git rev-parse HEAD^{tree})"
for f in uboot/dby-w09_defconfig \
  uboot/patches/0001-gpio-qcom-pmic-add-bias-and-input-config.patch \
  uboot/patches/0002-button-gpio-apply-pinctrl-default.patch \
  uboot/patches/0003-input-button-kbd-initialize-state.patch \
  uboot/patches/0004-dts-qcom-add-dby-w09.patch \
  uboot/patches/0005-board-qualcomm-add-dby-w09-env.patch \
  scripts/build-uboot.sh scripts/pack-fit.sh scripts/fetch-sources.sh; do
  echo "$(git rev-parse "$f")  $f"
done
echo '=== fetch-sources.sh (source URL + expected SHA) ==='
grep -n 'v2026.10\|sha256\|\.tar\|URL\|url' scripts/fetch-sources.sh | head -10
echo '=== build-uboot.sh key lines ==='
grep -n 'patch\|defconfig\|CROSS_COMPILE\|make\|CONFIG' scripts/build-uboot.sh | head -12
echo '=== pack-fit.sh key lines ==='
grep -n 'load\|entry\|0x9\|gzip\|mkimage\|its' scripts/pack-fit.sh | head -20
echo '=== defconfig relevant ==='
grep -n 'POSITION_INDEPENDENT\|INIT_SP\|SNAPDRAGON\|SAVE_PREV\|ABOOTIMG\|ANDROID_BOOT\|FIT\|BOOTM\|OF_LIBFDT\|OF_BOARD_SETUP\|NR_DRAM_BANKS\|BOOTM_LEN\|USB_FUNCTION_FASTBOOT\|DEFAULT_DEVICE_TREE' uboot/dby-w09_defconfig
