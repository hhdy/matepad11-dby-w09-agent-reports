# AI1 — U-Boot previous-bootloader initrd capture and safe in-place reuse review

- Date: 2026-11-28
- Target: DBY-W09 / HOS4.3 / ACK android17-6.18.33 / U-Boot v2026.10
- Scope: source-level review only. No device operations, image build or partition write.
- Result: U-Boot can capture the previous bootloader's initrd start from its FDT; safe reuse is conditional and requires an exact end address, provenance, and LMB validation.

## 1. Built-in previous-BL initrd capture

U-Boot v2026.10 provides CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR.

Source chain:
1. ARM64 start code preserves the incoming x0 using save_boot_params().
2. ARCH_SNAPDRAGON selects SAVE_PREV_BL_FDT_ADDR. CoWave's DBY-W09 defconfig additionally enables CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR=y explicitly.
3. common/board_r.c calls save_prev_bl_data() during board_r init when either previous-FDT or previous-initrd support is enabled.
4. arch/arm/lib/save_prev_bl_data.c validates that the saved x0 address is accessible in U-Boot's mem_map and points to a valid FDT.
5. When CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR=y, it reads /chosen/linux,initrd-start from the previous FDT (64-bit first, then 32-bit fallback) and exports:
   - prevbl_fdt_addr (when SAVE_PREV_BL_FDT_ADDR is enabled);
   - prevbl_initrd_start_addr.

Pinned sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/cpu/armv8/start.S
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/save_prev_bl_data.c
- https://github.com/u-boot/u-boot/blob/v2026.10/common/board_r.c
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/Kconfig
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/Kconfig
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/dby-w09_defconfig

## 2. Important limitation: only start is saved

save_prev_bl_data() reads linux,initrd-start but does not read linux,initrd-end and does not calculate a length.

It also does not:
- identify which partition or Android image the initrd came from;
- distinguish recovery initrd from normal Android separate ramdisk;
- copy the initrd;
- add the source range to U-Boot's LMB reservation table;
- prove that the source range is still valid after U-Boot memory initialization.

The environment value is only an address hint. It is not a complete bootable initrd descriptor.

The exact HOS4.3 recovery path must first prove that /chosen/linux,initrd-start/end exist and identify the intended Android payload rather than the recovery environment's own ramdisk.

## 3. U-Boot's exact zero-copy behavior

U-Boot v2026.10 boot/image-board.c::boot_ramdisk_high() contains a zero-copy mode:
- if initrd_high is absent or a normal value, it allocates an LMB destination, then copies the input bytes to that destination;
- if initrd_high equals ~0, it sets final initrd_start/end equal to the source range, then calls lmb_alloc_mem(LMB_MEM_ALLOC_ADDR, 0, &initrd_addr, rd_len, LMB_NONE).

lib/lmb.c::_lmb_alloc_addr() then checks the exact source range against available memory and LMB overlap rules, and reserves it. It fails if the range is outside U-Boot's available RAM or conflicts with already reserved U-Boot memory.

After the range is accepted:
- bootm stores the final initrd_start/end;
- image_setup_libfdt()/fdt_initrd() adds a memreserve entry and writes /chosen/linux,initrd-start/end to the final Linux FDT.

Sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/image-board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/lib/lmb.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/fdt_support.c
- https://github.com/u-boot/u-boot/blob/v2026.10/boot/bootm.c

**Do not set initrd_high=~0 unless the exact previous-BL initrd start and size are known and the LMB exact-address reservation is verified.**

## 4. Why ordinary copy mode is not automatically safe for previous-BL initrd

The previous-BL initrd source range is not automatically inserted into the FIT FDT's memreserve map or /reserved-memory nodes. U-Boot's boot_fdt_add_mem_rsv_regions() works on the selected OS/FIT FDT, not by copying the previous ABL FDT reservations into it.

Therefore, if the previous initrd source range is not already represented in U-Boot's LMB used-memory list, the ordinary copy mode might allocate a destination overlapping its own source. The exact behavior depends on current LMB reservations and address layout. Do not assume source safety from memmove alone.

The zero-copy mode reserves the exact source range through LMB, but it requires a validated address and length and an exact range that is still in available memory.

## 5. Possible minimal implementation if the recovery ABL audit proves reuse is appropriate

Only after the precise recovery path confirms that ABL's /chosen initrd is the required Android payload:

1. Enable CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR=y and preserve final .config.
2. Extend save_prev_bl_data() with the matching read of linux,initrd-end, validate end > start, check arithmetic overflow, and export prevbl_initrd_size=end-start. Do not change FDT values.
3. Use the previous-BL start/size pair as a raw initrd input to bootm only after the U-Boot raw-initrd path and memory map have been validated.
4. Before bootm RAMDISK state, set initrd_high=~0 so boot_ramdisk_high() reserves the exact existing source range in LMB rather than copying from an unreserved source.
5. Confirm the range belongs to valid gd->dram[] RAM banks and does not overlap U-Boot relocation, stack, malloc, FIT kernel, or other reserved memory.
6. Confirm the final FIT/ACK FDT receives the new initrd memreserve and /chosen start/end from fdt_initrd().

This is a proposed code/config design only. It has not been implemented or sandbox-tested.

## 6. Target-specific unresolved question

The ABL recovery audit must distinguish:
- recovery.img embedded ramdisk;
- recovery_ramdisk partition, if the ABL uses it;
- normal separate ramdisk partition;
- any other initrd source.

The previous-BL initrd may be a recovery ramdisk, which would be wrong to pass as Android 17 first-stage initrd. Only the exact ABL LoadRamdisk caller, source pointer, copy length and final FDT properties can decide that.

The available ROUND64 Phase F report records a previous ramdisk.img candidate with a different SHA than the stock separate-ramdisk candidate in K1_FASTBOOT_GATE01. Do not infer equivalence or apply the former candidate's header fields to the latter.

## 7. Disposition

| Item | Result |
|---|---|
| U-Boot previous FDT x0 capture | SOURCE-CONFIRMED |
| U-Boot previous initrd start capture | SOURCE-CONFIRMED when CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR=y and FDT is accessible |
| Previous initrd end/size captured automatically | NO |
| Automatic LMB reservation of previous initrd at save time | NO |
| Exact zero-copy LMB reservation in boot_ramdisk_high() | SOURCE-CONFIRMED when initrd_high=~0 and range is valid/free |
| Recovery ABL initrd is the desired Android payload | UNKNOWN pending the ABL recovery audit |
| Live wrapper and ABL initrd provenance | UNKNOWN due distinct 2 MiB candidate hashes |
| Safe reuse for this device | HOLD / NOT APPROVED |

No device was connected. No ADB/Fastboot/OEM command, reboot, build, image creation, temporary boot or partition write was performed.
