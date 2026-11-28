# AI1 — U-Boot FIT gzip kernel decompression limit review

- Date: 2026-11-28
- Target: DBY-W09 / ACK android17-6.18.33 / U-Boot v2026.10
- Scope: Offline comparison of pinned upstream source and existing ACK Image header fields. No build, device execution, or device access.

## 1. Conclusion

U-Boot FIT's gzip decompression output limit is not an apparent blocker.

U-Boot v2026.10 boot/Kconfig sets SYS_BOOTM_LEN to 0x08000000 (128 MiB) by default for ARM64 / PPC / RISC-V. The target ARCH_SNAPDRAGON selects ARM64, and the CoWave dby-w09_defconfig does not explicitly override SYS_BOOTM_LEN.

The target ACK Image header records image_size=45,547,520 bytes (about 43.44 MiB including BSS), comfortably below 128 MiB. The raw Image payload is about 44,820,992 bytes (about 42.75 MiB), also below the limit.

Therefore, provided the final U-Boot .config retains the ARM64 Kconfig default and the FIT contains this exact ACK Image, bootm_load_os() has sufficient global gzip decompression capacity.

## 2. Source path

1. boot/Kconfig::SYS_BOOTM_LEN defines the ARM64 default as 0x08000000.
2. boot/bootm.c::bootm_load_os() initializes the gzip decompression capacity decomp_len from CONFIG_SYS_BOOTM_LEN and calls image_decomp() to decompress the FIT kernel to its declared load address. On success it records the actual decompressed image length.
3. The later ARM64 booti_setup() reads the decompressed Image header's text_offset, image_size and flags, then calculates the final kernel address according to the ARM64 Image contract.
4. For the candidate address 0x91000000:
   - It is 2 MiB aligned.
   - ACK Image text_offset=0 and flags=0xA (PHYS_BASE).
   - The expected relocation base remains 0x91000000 rather than ABL's ImageBuffer+0x80000 path.

Sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/Kconfig
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/bootm.c
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/image.c
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/dby-w09_defconfig

## 3. Important distinctions

- SYS_BOOTM_LEN=128 MiB is U-Boot's decompression output capacity; it does not mean Linux will reserve the entire 128 MiB.
- image_size=45,547,520 is the Linux Image memory size including BSS. Safe reservation must not use only the compressed gzip file length.
- FIT load=0x91000000, the actual decompressed end, FIT staging, FDT, ramdisk, U-Boot relocation/stack and LMB reservations still require a complete non-overlap audit.
- reserved3 has a known capacity of 25,165,824 bytes (24 MiB). The compressed ACK Image length, DTB size, whether ramdisk is embedded in FIT, metadata and alignment budget remain UNKNOWN. The 128 MiB decompression limit does not prove that the FIT itself fits in reserved3.
- If the final .config overrides SYS_BOOTM_LEN to a value smaller than the actual decompressed Image, it must be raised and read back. Do not assume a Kconfig default survived without checking the built .config.

## 4. Required final .config readback

Record and verify:
- CONFIG_ARM64=y (selected by ARCH_SNAPDRAGON)
- CONFIG_CMD_BOOTM=y
- CONFIG_FIT=y
- CONFIG_SYS_BOOTM_LEN=0x08000000 or a larger value justified by measured output
- FIT kernel image metadata: arch/type/os/compression/load/entry
- Exact decompressed ACK Image SHA and header fields against the frozen ACK candidate

## 5. Evidence boundary

This result closes only the concern that U-Boot's default gzip decompression buffer is smaller than the ACK Image. It does not prove:
- ABL accepts the U-Boot recovery wrapper;
- the final FDT / 12GB RAM map is closed;
- Android separate ramdisk is handed to the kernel correctly;
- Android bootargs/bootconfig/UFS handoff is complete;
- the compressed FIT fits in reserved3;
- AVB/OEM authorization, recovery rollback or device boot has passed.

No device operation, image creation or partition write was performed.
