# ROUND43 — ACK 6.18.33 memory discovery: classic FDT handoff vs EFI-stub handoff

Date: 2026-11-24

Status: **THE KERNEL HAS TWO DISTINCT MEMORY-DISCOVERY INPUTS. CLASSIC ARM64 HANDOFF DEPENDS ON FDT MEMORY NODES; A REAL EFI-STUB HANDOFF CAN REPLACE THE DT MEMORY MAP FROM UEFI MEMORY DESCRIPTORS. DBY-W09's actual HOS4.3 entry path remains UNKNOWN.** This refines ROUND42 and prevents treating "UEFI ABL" as equivalent to "Linux booted through the EFI stub".

## 1. Fixed source baseline

- ACK tag: android17-6.18.33_r00
- Exact commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

Files reviewed at that commit:

| File | Blob |
|---|---|
| drivers/of/fdt.c | a931cd4beaaa6e3becc3692e3b4b8a0e42d6a691 |
| drivers/of/of_reserved_mem.c | d54cbaac9b822979b4d4479636969c7f452e4cee |
| arch/arm64/kernel/setup.c | 56e69b249c2c5ec911f01c4a4b0a1ee96ae33707 |
| arch/arm64/mm/init.c | 87257fe5d4a5386cb48410763d64f901427209fd |
| drivers/firmware/efi/efi-init.c | a65c2d5b9e7b6d119206ed0380b4e7574e436c01 |
| drivers/firmware/efi/fdtparams.c | b815d2a754eef33b5157830fc739ca47dd666d3f |
| drivers/firmware/efi/libstub/fdt.c | 6a337f1f8787b3bc68f771500f9fcd4b44a7b4f7 |
| Documentation/arch/arm64/booting.rst | e4f953839f7181ef5016e7f25e3f729dc5cb7bd7 |

## 2. Classic ARM64 boot path: FDT is the source of system RAM ranges

The pinned ACK `drivers/of/fdt.c::early_init_dt_scan_memory()`:
1. Iterates direct subnodes of the FDT root.
2. Accepts only nodes whose `device_type` property is exactly `memory`.
3. Skips disabled nodes.
4. Reads `linux,usable-memory` when present; otherwise reads `reg`.
5. Parses each address/size tuple using the root `#address-cells` and `#size-cells`.
6. Calls `early_init_dt_add_memory_arch(base, size)` for every non-zero range, which adds it to the architecture memory allocator (memblock).

The function returns whether it found memory, but the ordinary FDT node scan does not synthesize an absent memory node. A FDT with no accepted memory description adds no system-RAM ranges through this path.

This is independent of the node's unit-address suffix: the kernel scans by `device_type = "memory"`, not by requiring the node name to be exactly `memory`.

### Consequence for DBY-W09

If Huawei ABL uses the ordinary ARM64 direct-entry convention (x0 = physical FDT address, x1-x3 = 0, MMU off) and supplies no EFI-stub memory-map metadata, the final FDT must contain valid enabled system-memory nodes with trusted ranges. A root-level `/reserved-memory` tree alone is not a substitute for the system-RAM description.

Source: pinned `drivers/of/fdt.c` blob above, `early_init_dt_scan_memory()` around lines 1033–1089; ARM64 handoff requirements in `Documentation/arch/arm64/booting.rst` around lines 163–180.

## 3. Reserved memory is a separate input, not a replacement for system RAM

The pinned ACK `drivers/of/of_reserved_mem.c` handles the reservation side separately:

- `fdt_scan_reserved_mem_reg_nodes()` looks for `/reserved-memory`, validates the root cells/ranges, and records enabled children with `reg`.
- `fdt_scan_reserved_mem()` performs the separate reserve/allocate processing for static and dynamic reserved-memory children.
- The absence of `/reserved-memory` is logged/handled independently from the system memory scan.

Therefore, adding the 34 HOS4.3 reserved-memory child regions does not add a usable RAM bank. Conversely, adding a correct memory node does not reserve firmware, secure, DSP, reusable or crash-dump carveouts. Both classes must be reconciled.

Source: pinned `drivers/of/of_reserved_mem.c` blob above, `fdt_scan_reserved_mem_reg_nodes()` around lines 228–284 and `fdt_scan_reserved_mem()` around lines 286 onward.

## 4. EFI-stub boot path: the UEFI memory map is an alternative system-RAM source

The exact ACK arm64 setup order is important:
- The initial FDT is scanned before normal architecture memory setup.
- Later in `arch/arm64/kernel/setup.c`, `efi_init()` is called before `arm64_memblock_init()`.

The pinned EFI path works as follows.

### 4.1 EFI stub writes a UEFI memory-map handoff into /chosen

The pinned `drivers/firmware/efi/libstub/fdt.c::update_fdt()`:
- opens/copies the supplied FDT (or creates an empty FDT only when no source FDT is present);
- adds EFI handoff properties under `/chosen`, including `linux,uefi-system-table`, `linux,uefi-mmap-start`, `linux,uefi-mmap-size`, `linux,uefi-mmap-desc-size` and `linux,uefi-mmap-desc-ver`;
- updates the memory-map values during `ExitBootServices()` through `update_fdt_memmap()`.

This function does not synthesize a `/memory` node. The EFI path carries its own memory-map description separately.

### 4.2 Kernel EFI initialization imports the EFI memory map

The pinned `drivers/firmware/efi/fdtparams.c::efi_get_fdt_params()` looks for the complete EFI property set under `/chosen`. If the EFI system-table property or required memory-map properties are absent, it returns 0.

The pinned `drivers/firmware/efi/efi-init.c::efi_init()`:
- obtains the UEFI system table and memory-map metadata from those FDT properties;
- returns without enabling EFI boot when the metadata is absent;
- maps the EFI memory descriptors when the metadata is present;
- calls `reserve_regions()`, which explicitly discards earlier DT-derived memblock regions (outside the KHO scratch exception) because UEFI uses its own map;
- adds usable EFI memory descriptors to memblock and marks non-usable ranges as no-map/reserved according to their type/attributes.

The source comment in `reserve_regions()` explicitly says that most previous memblocks originate from memory nodes in the DT and UEFI instead uses its own memory map.

Therefore a genuine EFI-stub handoff with the complete trusted `/chosen/linux,uefi-*` metadata can supply usable memory without relying on the ordinary DT memory-node ranges. This is a real exception to the classic-FDT requirement; it is not automatic merely because the bootloader itself is UEFI.

Sources:
- pinned `drivers/firmware/efi/libstub/fdt.c`, `update_fdt()` around lines 30–138 and `update_fdt_memmap()` around lines 147–181;
- pinned `drivers/firmware/efi/fdtparams.c`, `efi_get_fdt_params()` around lines 84–133;
- pinned `drivers/firmware/efi/efi-init.c`, `efi_init()` and `reserve_regions()` around lines 130–278;
- pinned `arch/arm64/kernel/setup.c`, `efi_init()` before `arm64_memblock_init()` around lines 317–335.

## 5. Do not conflate UEFI firmware with Linux EFI-stub boot

These are different statements:

- "The bootloader is a UEFI/EDK2 ABL" — true of Qualcomm ABL family, but does not tell us which Linux entry point is used.
- "The ABL uses Qualcomm EFI_KERNEL_PROTOCOL" — a Qualcomm kernel-stack interface; this is not the Linux EFI-stub PE/COFF entry by itself.
- "The ABL starts the kernel through the EFI stub" — requires an actual EFI image/application-style entry at the PE header's `efi_stub_entry`, followed by the EFI stub constructing and passing the UEFI memory-map properties.
- "The ABL uses classic ARM64 Image handoff" — direct branch to the Image's `primary_entry`, with x0 carrying the FDT pointer; this relies on the FDT memory description unless another explicitly supported memory handoff exists.

ROUND42's FreeABL SM8250 reference is particularly informative here:
- Its SM8250 build script selects `DISABLE_KERNEL_PROTOCOL=1` for classic handoff.
- The pinned `BootLinux.c` says the SM8250 stock ABL family uses the classic path and directly invokes the kernel entry as `LinuxKernel(DeviceTreeLoadAddr, 0, 0, 0)` after shutting down UEFI boot services.
- This is a same-SoC-class reference for another product, not proof of Huawei DBY-W09's exact HOS4.3 ABL.

For the current DBY-W09 port, boot header v2 + separate ramdisk and the Android ABL context are consistent with a classic Android boot-image route, but the actual Huawei kernel entry path has not been directly inspected. Do not infer EFI-stub memory-map support merely from the presence of UEFI ABL.

## 6. Updated DBY-W09 gate

The exact Huawei HOS4.3 path must be classified before selecting the memory solution:

| Evidence found in final FDT / handoff | Interpretation | Required design |
|---|---|---|
| Valid enabled `device_type = "memory"` nodes with trusted `reg` or `linux,usable-memory` | Classic FDT memory path is satisfied | Reconcile all banks and reserved regions |
| No memory node, but complete trusted `/chosen/linux,uefi-*` metadata and actual EFI-stub entry | EFI memory-map path may supply memblock RAM | Verify EFI map descriptor semantics and all secure/firmware reservations |
| No memory node and no complete EFI memory-map handoff | Neither ordinary FDT scan nor EFI path supplies system RAM | **BLOCKED**; do not build/boot a board DTB relying on implicit memory |
| ABL-specific proprietary memory injection/fixup is claimed but final FDT not captured | Unverified claim | **UNKNOWN**; do not rely on it |

The HOS4.3 base-FDT inventory has no `/memory` node and 34 reserved-memory children. ROUND42's same-SoC-class ABL reference shows a standard path that requires an existing memory node before its own LinuxLoader completes the FDT. The new EFI-stub exception narrows the correct statement: the final boot-time FDT may not need a DT memory node only if a verified EFI-stub handoff supplies the complete UEFI memory map. Whether Huawei's ABL does that remains UNKNOWN.

Do not create guessed RAM addresses. The usable DDR banks, available lengths and security carveouts must come from trusted HOS4.3 memory-map evidence, not another SM8250 product's RAM map.

## 7. Next checks

1. ROUND12 remains the only local Agent task; no new local firmware task is created here.
2. When the existing sanitized boot-FDT / AVB evidence is available, identify whether it is raw boot image DTB, post-overlay FDT, or final post-ABL FDT.
3. From trusted evidence only, check whether the final tree has enabled system-memory nodes with valid cell counts and ranges.
4. Separately check whether `/chosen` contains the complete EFI system-table + mmap property set. These properties alone are not enough; establish that the kernel was entered through the EFI stub path.
5. Reconcile the 34 HOS4.3 reserved-memory nodes with the usable RAM map, especially no-map, reusable, secure firmware, DSP and dynamic dump ranges.
6. Do not promote the board DTS to DTB build input until one of the valid memory-source paths is established.

## 8. Safety / branch boundaries

- This report is on project main only.
- `ack18-dby-w09-dts-draft` is unchanged.
- PR #1 remains open / Draft / unmerged.
- `firmware-audit-v1` is unchanged; ROUND12 has not been uploaded.
- No device, local firmware, ABL image or partition was accessed or modified; no kernel was built or flashed.

**Conclusion:** ACK .33 confirms that classic FDT boot gets system RAM from root-level `device_type = "memory"` nodes, while `/reserved-memory` is a separate reservation database. A verified Linux EFI-stub boot can instead import the UEFI memory map and replace DT-derived memblocks, but only when all `/chosen/linux,uefi-*` data are supplied and the actual EFI-stub entry path is used. Huawei HOS4.3's path remains unknown. This is why the memory gate must be closed from actual handoff evidence rather than assumptions about the ABL being UEFI.
