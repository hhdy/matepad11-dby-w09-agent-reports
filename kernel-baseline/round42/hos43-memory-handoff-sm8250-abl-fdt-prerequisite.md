# ROUND42 — HOS4.3 memory handoff: SM8250 Qualcomm ABL FDT prerequisite review

Date: 2026-11-24

Status: SAME-SOC-CLASS ABL SOURCE SHOWS THAT THE STANDARD SM8250 LINUXLOADER PATH EXPECTS /memory TO ALREADY EXIST. THE TARGET HUAWEI ABL REMAINS UNVERIFIED. This materially tightens ROUND19: do not assume a generic ABL memory-node injection step. No local firmware, device or bootloader was accessed; no code was built or flashed.

## 1. Scope and source identity

This round reviews public Qualcomm LinuxLoader source with an SM8250-capable implementation, then separates it from evidence about the specific Huawei DBY-W09 firmware.

### Same-SoC-class reference

- Repository: REG-Linux/FreeABL
- Main repository README: https://github.com/REG-Linux/FreeABL/blob/main/README.md
- Its supported-SoC table lists SM8250 and says the implementation was validated on the Mangmi Pocket Max. This is a different SM8250 product, not DBY-W09.
- The FreeABL repository uses the edk2-freeabl submodule (CodeLinaro LinuxLoader r34 plus FreeABL changes).
- Submodule branch freeabl, exact commit: 4cd7fb389e22d7a3761308006fc6d79410be9ddf (branch head observed 2026-10-13).
- The source is an open ABL-derived reference, not Huawei's proprietary HOS4.3 ABL source.

Files reviewed at that immutable submodule commit:
- QcomModulePkg/Library/BootLib/UpdateDeviceTree.c, blob 97ea961ffeecb9c24540ee0ab47c57afef2e1800.
- QcomModulePkg/Library/BootLib/BootLinux.c, blob c51e41c42fd6d58240290fdba10c86ef81e2218a.
- QcomModulePkg/Library/BootLib/Board.c, blob 05786cae0ef2fb4936f6620908bf0f2e771c96ab.
- QcomModulePkg/QcomModulePkg.dsc, blob c99ffd0fc9a7d6ffa0f90a1cbbfffe615b93b827.
- Root makefile, blob 256cea14d4148fe52f8cb4172f477abc97fe9e9e.

### Qualcomm platform-level SMEM contract

The TianoCore edk2-platforms QualcommMinPlatformPkg README documents the Qualcomm pre-UEFI contract:
- XBL initializes SMEM and populates the RAM Partition Table before UEFI starts.
- UEFI reads the shared table via SMEM_USABLE_RAM_PARTITION_TABLE (item ID 402).
- UEFI uses RamPartitionSysMemory + SDRAM entries to form its conventional-memory map and HOBs; preloaded firmware/ABL partition types are kept reserved.
- Current table versions distinguish Length from AvailableLength; the latter is the usable size for system-memory entries.

Source: https://github.com/tianocore/edk2-platforms/blob/4db2845d14425599238be86b8a73d288f7c0b4a6/Platform/Qualcomm/QualcommMinPlatformPkg/README.md

This establishes a public Qualcomm XBL → SMEM → UEFI memory-discovery model. It does not establish that Huawei's specific UEFI build uses this exact package or passes an equivalent resource map to Linux.

## 2. Critical finding: the SM8250 LinuxLoader path requires an existing /memory node

The exact FreeABL SM8250-capable UpdateDeviceTree() implementation does the following:

1. Validates and opens the input DTB for in-place update.
2. Unless built with AUTO_VIRT_ABL, calls FdtPathOffset(fdt, "/memory").
3. If the path lookup fails, logs "Could not find memory node" and returns EFI_NOT_FOUND.
4. Only after the node exists, calls target_dev_tree_mem() to update its reg property.

The relevant source range is lines 1377–1442 in the pinned UpdateDeviceTree.c.

This implementation does not create a missing /memory node in the standard path. It expects an existing node. This is materially different from the older Qualcomm SDM660 BDS LinuxLoader reference reviewed earlier, whose PrepareFdt() contains a missing-node fallback that creates /memory and writes device_type = "memory". The old SDM660 behavior cannot be generalized to the later SM8250 loader.

### Is this path reached for SM8250?

The FreeABL README lists SM8250 as a supported build. Its build script selects the classic kernel handoff for sm8250 via DISABLE_KERNEL_PROTOCOL=1; the root Makefile normalizes AUTO_VIRT_ABL to 0 when it is not supplied. In that non-AUTO-VIRT configuration, the shown UpdateDeviceTree() memory-node lookup is active.

In BootLinux.c, DTBImgCheckAndAppendDT() runs before LoadAddrAndDTUpdate(); the latter calls UpdateDeviceTree() and propagates its failure. Thus the lookup applies to the selected/combined FDT after the DTB/DTBO append stage, not merely to an untouched input file.

Caveat: this describes the public FreeABL build path and source. It is not evidence that Huawei HOS4.3 uses the identical source revision, build flags, or DTB selection policy.

## 2.1 Exact final-FDT timing: the check is after the DTB/DTBO composition stage

A second pass through the exact pinned `BootLinux.c` confirms the timing of the lookup:

1. `DTBImgCheckAndAppendDT()` calculates the boot-header-v2 DTB offset (or vendor_boot DTB offset for newer headers).
2. It validates the DTBO image and selects the appended DTB when present; otherwise it selects the SoC DTB.
3. In the SoC-DTB branch, it can add the selected board DTBO plus Hypervisor DTBOs, debug override DTB, and AVF DP DTBO to the overlay list.
4. It calls `ApplyOverlay()`. The overlay implementation creates the final tree and copies its total contents into `BootParamlistPtr->DeviceTreeLoadAddr`.
5. Later in the outer Linux boot path, `BootLinux.c` calls `LoadAddrAndDTUpdate()`.
6. `LoadAddrAndDTUpdate()` copies/concatenates ramdisk and then calls `UpdateDeviceTree((VOID *)BootParamlistPtr->DeviceTreeLoadAddr, ...)`.
7. The `UpdateDeviceTree()` call then performs the exact `FdtPathOffset(fdt, "/memory")` lookup discussed in §2.

Thus the lookup in this reference is performed on the final device-tree buffer after the ABL's own DTB selection / DTBO composition stage, not merely on the original boot.img DTB. This makes it unsafe to assume that a missing memory node in the raw base DTB is harmless unless the relevant overlay path demonstrably adds it before this stage.

Pinned source blob references:
- `BootLinux.c`: `c51e41c42fd6d58240290fdba10c86ef81e2218a`, especially `DTBImgCheckAndAppendDT()` around lines 558–840, `LoadAddrAndDTUpdate()` around lines 1183–1368, and the caller around lines 1830–1865.
- `UpdateDeviceTree.c`: `97ea961ffeecb9c24540ee0ab47c57afef2e1800`, `UpdateDeviceTree()` around lines 1377–1442.

## 3. Where the memory ranges come from in this reference

The same FreeABL code obtains RAM entries through the UEFI EFI_RAMPARTITION_PROTOCOL:

- Board.c::GetRamPartitions() locates gEfiRamPartitionProtocolGuid and calls GetRamPartitions().
- Board.c::BaseMem() uses the smallest reported RAM partition base for boot-image load-address calculations.
- UpdateDeviceTree.c::AddMemMap() calls ReadRamPartitions() and rewrites the existing /memory/reg entries using each partition's Base and AvailableLength.
- dev_tree_add_mem_infoV64() uses the FDT #address-cells / #size-cells to update a 64-bit memory description.

The UEFI protocol is the consumer-facing handoff; the public QualcommMinPlatformPkg README describes the common upstream implementation where this information is initialized from XBL-populated SMEM table 402. The FreeABL submodule does not itself prove that Huawei HOS4.3 UEFI exposes the same protocol implementation or same values.

## 4. Reserved-memory interaction: existing no-map descriptions are consumed, not synthesized

The FreeABL reference has a second important path:

- BootLinux.c can call GetUpdatedRamPartitions() before the final UpdateDeviceTree() call when REMOVE_CARVEOUT_REGION is enabled.
- GetNoMapRegions() requires an existing /reserved-memory root and scans its children for no-map and reg.
- The loader sorts and merges contiguous/overlapping no-map ranges.
- UpdateRamPartitions() subtracts those ranges from usable RAM partition intervals.
- AddMemMap() then writes the resulting usable intervals into the existing /memory/reg.

This means the loader can use the input DT's existing no-map reservations to adjust the memory ranges exported to Linux. It does not recreate the board-specific reserved-memory child nodes, recover their missing names, or infer missing no-map/reusable/size properties from SMEM.

The FreeABL build script does not explicitly request REMOVE_CARVEOUT_REGION; its Makefile forwards the variable and the DSC only defines the compile-time feature when the value is 1. Do not assume every SM8250 ABL enables this carveout-removal option.

The mechanism is intentionally limited to no-map nodes. It does not establish the handling of the HOS4.3 reusable/size/alignment pools, dynamic kerneldump node, or every named secure/firmware carveout.

## 5. Implication for DBY-W09 HOS4.3 and ACK DTB design

ROUND19 records that the sanitized HOS4.3 base-FDT property inventory had:
- no ordinary /memory node / device_type = "memory";
- an existing /reserved-memory root;
- 34 reserved-memory child nodes with different no-map, reusable, size/alignment and dynamic semantics.

The new same-SoC-class ABL source changes the risk assessment:

- A missing /memory in the raw firmware DTB is not proof by itself that Linux never receives memory information; the final FDT may be modified by XBL, a selected DTB/DTBO, another ABL stage, or a Huawei-specific patch.
- But the SM8250 FreeABL reference does not support the assumption that the standard LinuxLoader will create /memory if it is absent. In this reference, an absent node is a hard FDT-update error.
- Therefore, the DBY-W09 ACK DTB must not omit /memory on the unverified assumption that ABL will add it. We need either direct evidence that the final FDT entering the LinuxLoader already contains /memory, or a deliberately built and validated node populated from trusted DBY-W09 memory-map evidence.
- Do not invent the address or size. The exact usable RAM banks and carveouts must come from the HOS4.3 memory inventory / bootloader handoff evidence, with secure and firmware reservations reconciled.
- Keeping /reserved-memory and selected carveout child nodes is a separate task. Adding a correct /memory/reg does not reserve the 34 HOS4.3 regions. Conversely, listing reservations without a correct system-memory node does not satisfy the loader's /memory prerequisite.

Current target status remains UNKNOWN / NOT_ESTABLISHED: we have not read the actual final HOS4.3 ABL input/output FDT on the user's tablet, and the public FreeABL source is a same-SoC-class reference for a different device.

## 6. What this resolves and what it does not

| Question | Current evidence | Status |
|---|---|---|
| Does Qualcomm XBL commonly publish a RAM Partition Table in SMEM before UEFI? | QualcommMinPlatformPkg boot ABI documentation | SOURCE-ESTABLISHED FOR THAT PLATFORM STACK |
| Can a Qualcomm SM8250 LinuxLoader use UEFI RAM Partition Protocol to rewrite /memory/reg? | FreeABL edk2 source, SM8250 listed as supported | SOURCE-ESTABLISHED FOR THE REFERENCE BUILD |
| Does that SM8250 loader create /memory if absent? | It returns EFI_NOT_FOUND on failed /memory path lookup | NO — NOT IN THE STANDARD PATH REVIEWED |
| Does the loader read existing /reserved-memory no-map children? | FreeABL GetNoMapRegions / UpdateRamPartitions | YES, when carveout-removal flow is enabled |
| Does it recreate HOS4.3's 34 reserved-memory children? | No such creation logic observed in the reviewed flow | NO EVIDENCE |
| Does Huawei HOS4.3 ABL use this same code/flags? | No Huawei ABL source or final live FDT inspected | UNKNOWN |
| Does the current ACK board DTS have a verified memory map? | ROUND19 deliberately deferred it; addresses/sizes remain redacted | NO |

## 7. Required next checks

1. Keep ROUND12 as the only local Agent task. Its scope remains AVB footer / vbmeta descriptor metadata; do not add another local task.
2. Once the existing ROUND12 result is available, use only authorized existing sanitized boot-FDT evidence to determine whether it is a pre-ABL image DTB or a final post-ABL FDT. Do not infer this from the file name alone.
3. Find a trusted HOS4.3 source for the usable RAM partition table / final memory map and reconcile it with the 34 reserved-memory child classes; keep raw addresses private.
4. In the ACK DTS design, do not build or enable a board DTS lacking a validated /memory node. Do not add guessed memory ranges or copy HOS4.2 splash/DFPS addresses.
5. If later evidence requires the kernel DTB itself to carry /memory, add it only from a validated memory map and test the compiled final DTB with dtc/dtbs_check. Inspect the final DTB after all overlays and bootloader fixups separately.
6. Keep MMCX→MX, UFS power rails, AVB and first-stage ramdisk as separate gates.

## 8. Branch and safety boundaries

- This report is on the project main branch only.
- ack18-dby-w09-dts-draft is unchanged.
- PR #1 remains open / Draft / unmerged.
- firmware-audit-v1 is unchanged; ROUND12 has not been uploaded.
- No bootloader was modified, built, signed, flashed or tested. No device was connected. No local firmware was read in this round.

Conclusion: the public SM8250 ABL reference is stricter than the earlier SDM660 example: its normal LinuxLoader expects /memory to exist before it updates memory ranges from the UEFI RAM Partition Protocol. Its optional no-map carveout logic consumes reservations already present in the FDT; it does not synthesize the HOS4.3 reserved-memory tree. This makes the missing /memory issue an explicit pre-DTB-build blocker until the actual Huawei post-overlay/post-ABL handoff is established.
