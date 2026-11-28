# Boot v2 repack analysis

Pinned svesnav commit: 116cb1fe06110543ce03217e8bd8f35c12ca89c3. README and repack_boot.py blob SHAs match the taskbook.

## Repack implementation

repack_boot.py reads backups/boot.img and rejects it unless SHA-256 equals 6fb82f6ca823c8acffaece13b161eca6c685a6e26f2c216b50293c3fd5da539d. It requires 96 MiB, invokes AOSP unpack_bootimg with --format=mkbootimg, requires header version 2, retains extracted mkbootimg flags and optionally replaces kernel, DTB and cmdline, then serializes with mkbootimg-android10.py.

STOCK_PAYLOAD_SIZE=24,412,160. In --full-partition mode, the script copies the complete 96 MiB stock partition, writes rebuilt payload at offset zero, zeroes from payload end to 24,412,160, and preserves bytes after that boundary. It does not independently parse/verify AVB footer metadata. The constant is a payload boundary, not partition size.

Target live stock boot SHA is 7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8. It differs from the public script guard; do not transplant the guard or use the script unchanged. The reported PREP10 candidate is 46,563,215 B, below 100,663,296 B by arithmetic, but exceeds the public 24,412,160-byte --full-partition payload limit.

build_dev_images.sh calls repack_boot.py without --full-partition, so the boot output is a compact boot image, not a full 96 MiB partition dump. It separately makes a gzip CPIO Linux initramfs, wraps it as a header-v0 image with 2048-byte pages, overlays it on a copy of the stock 2 MiB ramdisk partition and preserves the footer tail, then packs one DTBO entry.

matepad-kernel-install boot_with() parses header-v2 fields: kernel size/address, ramdisk size/address, second size/address, tags, page size, version, OS version, name, recovery size/offset and DTB size/address. It extracts embedded ramdisk, second and recovery components, computes SHA-1 over each component followed by its 4-byte little-endian length in kernel/ramdisk/second/recovery/DTB order, reconstructs the v2 header, then page-pads components. This is structurally the AOSP boot image ID component algorithm.

## Installer semantics

install_images.py permits only boot/ramdisk/dtbo; validates image SHA and capacity; saves the full current partition; writes image bytes, fsyncs and hashes only the written prefix. It does not compare untouched tail bytes and has no automatic rollback.

matepad-kernel-install checks capacity, compares current image prefix, backs up full contents for changed partitions, writes/fsyncs and verifies only image-length prefix. On mismatch it exits and tells the operator to restore the backup. No automatic restore is implemented; backups are only for partitions that need changing.

## Conclusion

A real same-model direct-ABL Linux method is confirmed. Its exact stock hash, 24,412,160-byte payload limit, Linux ramdisk and VG overlay must not be transplanted. Android adaptation should preserve stock boot-v2 metadata and Android embedded components, and remain blocked until exact ABL alignment and Android handoff are proven.
