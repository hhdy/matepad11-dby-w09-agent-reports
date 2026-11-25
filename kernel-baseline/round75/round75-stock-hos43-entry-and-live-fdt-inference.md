# ROUND75 — stock HOS4.3 kernel entry-route constraint and live-FDT inference

Date: 2026-11-25
Owner: Primary AI, exact ACK source + ROUND19/20 artifact reasoning
Baseline: HOS4.3 stock kernel/DTB and ACK android17-6.18.33_r00
Scope: inference review only; no local artifact modification or device operation.

## 1. Executive result

ROUND20 proved the decompressed stock HOS4.3 kernel Image has ARM64 magic but res5 at offset 0x3c equals zero, i.e. no PE/COFF header. The stock kernel is therefore not an EFI application and cannot be launched through the EFI Stub PE entry. Its stock payload is gzip-compressed; the loader decompresses it before the normal arm64 entry.

The stock kernel's normal arm64 boot contract receives x0 = FDT pointer and discovers usable RAM from the FDT memory node. The pinned arm64 source skips a memory node with zero size; on the non-EFI path, arm64 memory initialization does not invent RAM ranges from another source.

The stock HOS4.3 base DTB file that ROUND19 decompiled has /memory reg=<0 0 0 0>. But the stock system does run. Therefore the zero-reg value is a property of the extracted base/template FDT, not a proven value of the final FDT passed to the stock kernel. The successful stock boot requires that, before handoff, ABL or another boot-chain stage:
- modifies that node with a real RAM range; or
- selects/constructs a different final FDT with a usable memory node.

The exact actor and actual final memory tuples remain UNKNOWN because /sys/firmware/fdt read was denied and ABL binary is absent.

## 2. Evidence chain

1. ROUND19: base FDT contains /memory with all-zero reg; none of the nine stock DTBO entries changes /memory.
2. ROUND20: decompressed stock kernel header res5=0; no PE header. Stock kernel payload is gzip.
3. ROUND20 ACK source tracing: normal arm64 early FDT scan skips size=0; arm64_memblock_init contains no independent RAM discovery path. EFI memory reinitialization exists only when EFI table metadata is recognized.
4. Therefore, for the observed stock non-EFI kernel to run, the final x0 FDT must contain usable RAM information or be replaced with an alternate valid FDT before entry. This is a deduction from the artifact + source contract, not a direct observation of ABL fixup code.

## 3. Implication for the new ACK Image

The ROUND18 Image has a valid EFI PE entry, but do not assume ABL calls it. The safer primary compatibility assumption for Stage A is still the stock normal arm64 entry:
- preserve the ARM64 Image header and pass the final platform FDT in x0;
- retain the stock-style gzip payload container as the compatibility-first packaging candidate, because the stock loader is proven to decompress gzip;
- make sure the DTB embedded in boot is based on the minimal ACK board tree plus rootparam overlay and that ABL's rootparam/table contract is satisfied;
- the final live FDT memory/reserved-memory content must be valid even if the extracted base template contains a zero placeholder.

EFI Stub remains a possible alternate route only if ABL invokes the PE entry and supplies the platform DTB configuration table / complete UEFI handoff. If the stub receives no DEVICE_TREE_GUID table, the pinned ACK config has EFI_ARMSTUB_DTB_LOADER disabled, so it can synthesize an empty DTB and lose /firmware/android/fstab. Do not force the EFI path without ABL evidence.

## 4. Status and boundary

- Stock kernel is not PE/COFF EFI executable: ESTABLISHED by ROUND20.
- Stock system's successful run requires a valid live memory description in the normal arm64 handoff: DEDUCED from ACK source contract + stock boot premise.
- Whether ABL mutates the extracted base DTB or selects another FDT: UNKNOWN.
- Actual RAM tuples and reserved-memory final map: BLOCKED / unavailable.
- Whether the new Image is accepted at the normal arm64 entry with the final ABL FDT: NOT TESTED.
- Whether ABL invokes EFI Stub for the new Image: UNKNOWN.
- No boot package or device action.
