# AI1 — U-Boot PIE Entry and Runtime RAM Map Review

- Date: 2026-11-28
- Target: Huawei MatePad 11 DBY-W09 / VD / SM8250 / HOS4.3 / ACK android17-6.18.33
- Scope: U-Boot v2026.10 source, CoWave public DBY-W09 U-Boot configuration and board DTS, and existing project evidence. Static analysis only.
- Status: **PIE mechanism statically supported; target recovery handoff remains conditional; CoWave's built-in RAM map is not approved for this expanded-memory target.**
- No device interaction, build, image generation, reboot, ADB/Fastboot command, or partition operation was performed.

## 1. Executive findings

1. U-Boot v2026.10 with `CONFIG_POSITION_INDEPENDENT=y` is designed to start at an arbitrary **4 KiB-aligned** runtime address. `arch/arm/cpu/armv8/start.S` checks the runtime `_start` address and hangs if its low 12 bits are nonzero; it then applies embedded `.rela.dyn` relative relocations before normal C initialization.
2. U-Boot's early stack is also position-relative when `INIT_SP_RELATIVE` is enabled. In v2026.10 Kconfig, `INIT_SP_RELATIVE` defaults to y when `POSITION_INDEPENDENT` is enabled (with an ARCH_QEMU exception). CoWave's `CONFIG_SYS_INIT_SP_BSS_OFFSET=0x180000` therefore participates unless overridden. The generated `.config` is not published, so the final build still needs a config check.
3. **The more immediate target risk is the RAM map.** CoWave's U-Boot internal DTS includes three fixed RAM tuples totalling 8,517,582,848 bytes (7.932617 GiB), with the highest bank ending at physical address `0x280000000`. Snapdragon board code prefers this valid internal FDT and parses it first. It only tries the ABL-provided external FDT if internal parsing fails.
4. The same `gd->dram[]` banks are later used by ARM `arch_fixup_fdt()` to populate the final Linux FDT's `/memory/reg`. Thus, if this static CoWave map differs from the actual expanded target hardware, the discrepancy is carried into ACK kernel handoff; the generic memory fixup cannot correct a wrong source map.
5. U-Boot can obtain the previous bootloader's FDT: `save_boot_params()` stores entry register x0, and `get_prev_bl_fdt_addr()` returns it. CoWave enables `CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR=y`, which enables the shared previous-FDT accessor. But the current Snapdragon board policy still prefers the internal FDT.

## 2. U-Boot PIE and initial stack

### 2.1 Runtime entry alignment and relocation

Under `CONFIG_POSITION_INDEPENDENT`, U-Boot v2026.10 `arch/arm/cpu/armv8/start.S`:
- obtains the runtime `_start` address with `adr`;
- checks its low 12 bits against zero;
- enters a `wfi` loop if the address is not 4 KiB aligned;
- computes runtime-minus-linked offset and walks `.rela.dyn`, applying `R_AARCH64_RELATIVE` relocations.

This confirms the U-Boot image's own entry rule. It does not prove the Huawei ABL recovery branch places decompressed U-Boot at a 4 KiB-aligned address. Existing ABL analysis establishes 4 KiB EFI page allocation for examined paths, but did not close the exact HOS4.3 recovery branch.

Sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/cpu/armv8/start.S
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/relocate_64.S

### 2.2 Initial SP configuration

U-Boot v2026.10 `arch/arm/Kconfig` says `INIT_SP_RELATIVE` depends on ARM64 and defaults to y when `POSITION_INDEPENDENT` is enabled, except for the ARCH_QEMU default-n case. `SYS_INIT_SP_BSS_OFFSET` depends on `INIT_SP_RELATIVE`. With it enabled, `crt0_64.S` calculates initial SP from the runtime `__bss_start` plus the configured offset.

CoWave's `uboot/dby-w09_defconfig` sets `CONFIG_POSITION_INDEPENDENT=y` and `CONFIG_SYS_INIT_SP_BSS_OFFSET=0x180000`. It does not explicitly set `CONFIG_INIT_SP_RELATIVE=y`; Kconfig is expected to supply it. CoWave's build script does not publish the final `.config`, so this is **expected from Kconfig, not build-verified**.

Sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/Kconfig
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/crt0_64.S
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/dby-w09_defconfig
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/scripts/build-uboot.sh

## 3. CoWave internal RAM map

CoWave `uboot/patches/0004-dts-qcom-add-dby-w09.patch` provides:

| Bank | Start | Size | End (exclusive) |
|---|---:|---:|---:|
| 0 | `0x80000000` | `0x3BB00000` | `0xBBB00000` |
| 1 | `0xC0000000` | `0xC0000000` | `0x180000000` |
| 2 | `0x180000000` | `0x100000000` | `0x280000000` |

Arithmetic:
- Total listed capacity: **8,517,582,848 bytes = 7.9326171875 GiB**.
- Highest physical end address: **`0x280000000`** (10 GiB address).
- This is only the sum of the listed ranges, not a verified capacity for the user's current tablet.

The CoWave DTS comment says the layout came from a runtime device tree. Its public status/install documentation describes a HarmonyOS 4.2 test environment. This is same-model reference evidence, not proof that these ranges match the user's HOS4.3 device after its reported memory expansion to 12 GB. No exact target final-memory FDT was independently available in this review.

## 4. Why the built-in map wins over ABL's map

In U-Boot v2026.10 `arch/arm/mach-snapdragon/board.c::board_fdt_blob_setup()`: the compiled internal FDT is parsed first whenever its header is valid. The external FDT from `get_prev_bl_fdt_addr()` is parsed only if internal parsing returns an error. CoWave's internal control DTS has a valid `/memory/reg`, so the external ABL FDT is normally not consulted for RAM-bank discovery.

Later, `arch/arm/lib/bootm-fdt.c::arch_fixup_fdt()` copies `gd->dram[]` into the Linux FDT with `fdt_fixup_memory_banks()`. This can repair an empty ACK `/memory/reg`, but only with the RAM banks U-Boot selected earlier. It cannot correct incorrect input banks.

Sources:
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/mach-snapdragon/board.c
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/bootm-fdt.c
- https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/main/uboot/patches/0004-dts-qcom-add-dby-w09.patch

## 5. External ABL FDT is a potential source

`arch/arm/lib/save_prev_bl_data.c::save_boot_params()` stores x0 in `reg0`; `get_prev_bl_fdt_addr()` returns that value. CoWave's `CONFIG_SAVE_PREV_BL_INITRAMFS_START_ADDR=y` enables the shared previous-FDT accessor. The Snapdragon board code already obtains and validates this external FDT pointer.

An engineering option exists: prefer the external ABL FDT's RAM map when it is valid and contains usable `/memory` ranges, then fall back to the internal map only if it does not. The target HOS4.3 external FDT values must be verified before changing policy.

A safe implementation must parse candidate banks transactionally: use a temporary zeroed array; validate non-zero ranges, overflow, count, sorting and overlap policy; commit only on success; and clear temporary state before fallback. The current `qcom_parse_memory()` writes to a static global bank array during parsing, so an external-first/fallback implementation must prevent partial parse state from contaminating the next attempt.

Source:
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/lib/save_prev_bl_data.c
- https://github.com/u-boot/u-boot/blob/v2026.10/arch/arm/mach-snapdragon/board.c

## 6. Updated gate matrix

| Gate | Result | Meaning |
|---|---|---|
| U-Boot PIE 4 KiB entry rule | **CONFIRMED** | Exact v2026.10 startup source enforces it |
| CoWave relative initial-SP mechanism | **EXPECTED / CONFIG NOT BUILT-VERIFIED** | Kconfig default follows POSITION_INDEPENDENT; generated `.config` is absent |
| HOS4.3 ABL recovery placement | **CONDITIONAL** | Exact recovery branch and runtime address remain unproven |
| CoWave internal RAM tuple arithmetic | **PASS** | Three tuples parse arithmetically; total is 7.932617 GiB |
| CoWave RAM tuples match expanded HOS4.3 target | **NO-GO TO REUSE AS-IS** | These tuples do not establish the reported 12 GB target map |
| External ABL FDT accessor | **SOURCE-CONFIRMED** | x0 save and accessor exist when config gate is enabled |
| External ABL FDT contains usable HOS4.3 RAM map | **UNKNOWN** | Exact target final-FDT memory evidence remains unavailable |
| ARM Linux FDT memory fixup | **SOURCE-CONFIRMED, INPUT-DEPENDENT** | It passes `gd->dram[]`; it cannot repair wrong input banks |
| ACK final reserved-memory compatibility | **HOLD** | This review does not approve the 37 reserved-memory nodes or overlap safety |

## 7. Recommended next engineering step

Do not copy CoWave's three memory tuples into the target build and do not produce a recovery/FIT candidate yet.

The next U-Boot-specific step should be a narrowly scoped **external-FDT-first RAM discovery design review**:
1. Verify whether exact HOS4.3 recovery handoff supplies a valid FDT pointer in x0.
2. Obtain a trusted target-specific `/memory/reg` capture, including all actual RAM banks; do not substitute the HOS4.2 CoWave tuples.
3. Design external-first / internal-fallback selection with transactional parsing and explicit bank validation.
4. Archive the final generated U-Boot `.config` and verify `POSITION_INDEPENDENT`, `INIT_SP_RELATIVE`, `SYS_INIT_SP_BSS_OFFSET`, `OF_LIBFDT`, `FIT`, and bootm/Android image parser options.
5. Inspect the built U-Boot ELF/binary relocation table and confirm the early PIE relocation types are compatible with the startup routine.
6. Emit an auditable U-Boot log showing selected memory source, bank count and normalized ranges; compare them with target evidence before FIT address planning.

After the memory source is trusted, re-run kernel/FIT/initrd/FDT/reserved-memory/splash overlap checks against that exact map.

## 8. Safety boundary

This review is static source analysis only. It did not connect to the tablet; execute ADB, Fastboot, OEM, recovery or reboot commands; build U-Boot, FIT or recovery; create or modify boot artifacts; write partitions; or authorize a device test.

**Final conclusion:** U-Boot's PIE mechanism remains a sound way to decouple ACK Image placement from ABL's direct-kernel alignment constraint. The newly identified priority is to stop inheriting CoWave's fixed RAM tuples and establish the actual expanded HOS4.3 memory map as the source of truth.