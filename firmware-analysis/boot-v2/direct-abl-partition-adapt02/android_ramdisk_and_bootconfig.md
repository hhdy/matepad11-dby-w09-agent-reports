# Android separate ramdisk and bootconfig policy

The svesnav project builds a static-busybox + sd_root_init.sh gzip CPIO initramfs, wraps it in an Android header-v0 image with an empty kernel and 2048-byte pages, then overlays it onto a copy of the stock 2 MiB separate ramdisk partition while retaining the reported AVB footer region. Its init script mounts ext4 label LINUX70ROOT on microSD and executes switch_root /newroot /sbin/init. The Linux cmdline includes rdinit=/init. This is a Linux SD-root path, not Android init.

The taskbook reports the target separate ramdisk contains Huawei init, init.real and KernelSU-related files. The boot embedded ramdisk is reported to contain fstab.qcom and e2fsck but not init/adbd. Exact wrapper/payload/footer boundaries were not re-read from raw partition bytes in this task.

ANDROID_RAMDISK_POLICY = KEEP_STOCK.

This preserves the Huawei Android init chain. It does not prove Android 12 stock ramdisk compatibility with ACK Android 17. Any later repack requires direct evidence for first-stage init, init.rc imports, fstab, dynamic partitions, vendor ramdisk interfaces, bootconfig and cmdline behavior.

The public Linux cmdline is not an Android template. The exact target Android bootconfig contents and HOS4.3 transfer mechanism are not fully established in reviewed evidence. Preserve required stock Android tokens until exact-target evidence approves changes. androidboot.dtbo_idx=2 is an observed selector output, not a command to select Entry 2.

Before claiming Android first-stage init viability, verify built-in/early availability of UFS host/PHY/interconnect/regulators/clocks/reset; devtmpfs; dm-verity/device-mapper and AVB interfaces; F2FS/EROFS/ext4 as required by fstab; fscrypt/crypto; binder/binderfs; bootconfig support and transfer; dynamic partition metadata dependencies.

No Linux initramfs was placed into Android ramdisk and no repack/test was performed.
