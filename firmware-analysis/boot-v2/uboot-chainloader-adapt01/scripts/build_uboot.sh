#!/bin/sh
set -e
cd /home/kerneldev/build/u-boot-2026.10
# enable CMD_ABOOTIMG per taskbook §12.4 (explicit config adjustment)
echo CONFIG_CMD_ABOOTIMG=y >> build/.config
make CROSS_COMPILE=aarch64-linux-gnu- O=build olddefconfig 2>&1 | tail -1
echo '--- final values ---'
grep -E '^CONFIG_(POSITION_INDEPENDENT|INIT_SP_RELATIVE|SYS_INIT_SP_BSS_OFFSET|ARCH_SNAPDRAGON|SAVE_PREV_BL_FDT_ADDR|SAVE_PREV_BL_INITRAMFS_START_ADDR|CMD_ABOOTIMG|ANDROID_BOOT_IMAGE|ANDROID_BOOT_IMAGE_IGNORE_BLOB_ADDR|FIT|CMD_BOOTM|OF_LIBFDT|OF_BOARD_SETUP|NR_DRAM_BANKS|SYS_BOOTM_LEN|USB_FUNCTION_FASTBOOT|DEFAULT_DEVICE_TREE)=|^# CONFIG_(CMD_ABOOTIMG|INIT_SP_RELATIVE)' build/.config
echo '--- building ---'
make CROSS_COMPILE=aarch64-linux-gnu- O=build -j12 2>&1 | tail -5
ls -la build/u-boot build/u-boot.bin build/u-boot.map 2>/dev/null
aarch64-linux-gnu-readelf -h build/u-boot | grep -E 'Entry|Machine|Type'
aarch64-linux-gnu-readelf -l build/u-boot | grep -E 'LOAD|Entry' | head -4
echo BUILD_DONE
