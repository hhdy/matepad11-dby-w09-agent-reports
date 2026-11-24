# ROUND19 — HOS4.3 memory node and reserved-memory handoff review

Date: 2026-11-24

Status: existing ROUND7 report analysis + same-device public DTS source review. No new local extraction, no device/live FDT access, no compile, no dtc, no boot-image packaging, no device write.

## 1. HOS4.3 base-FDT inventory findings

The already-published ROUND7 deterministic boot-FDT property inventory and hardware matrix establish:
- No /memory path or device_type = "memory" property was recorded in the stock boot-image base FDT inventory.
- A valid /reserved-memory root exists.
- The reserved-memory category contains 111 property rows across 35 distinct node paths (the parent plus 34 child nodes).
- The physical reg addresses are redacted in the report. This review does not reconstruct or publish any physical address or size.

The 34 child nodes fall into these evidence classes:

### 1.1 No-map firmware / boot / secure handoff nodes

The local property inventory records no-map for:
- hypervisor / XBL-AOP / SMEM / removed-region and XBL UEFI log reservations;
- PIL firmware regions for camera, WLAN, IPA firmware/GSI, GPU, NPU, video, CVP, CDSP, SLPI, ADSP and SPSS;
- CDSP secure heap;
- Huawei rainbow/boot-failure records;
- mailbox region.

These names indicate different consumers and lifetimes. They must not all be treated as interchangeable or all copied without understanding which firmware remains active during an Android 17 boot.

### 1.2 Reusable / size-based pools

The local inventory records reusable, size, and in most cases alignment for:
- ADSP, SDSP, CDSP, memory-dump, SP and user-contiguous pools;
- QSEECom and QSEECom TA pools;
- secure display and CNSS WLAN pools;
- Linux CMA.

Their sizes are redacted in the existing public report. They are not safe to reconstruct from node names alone.

### 1.3 Dynamic/resizable node

- kerneldump carries a resize property. The local property inventory does not provide enough information to recreate its exact range or bootloader interaction.

## 2. No /memory node: what can and cannot be concluded

The stock base-FDT inventory's lack of /memory does not prove that a final boot-time FDT lacks memory nodes. It is a base image DTB captured before any possible ABL fixups.

The same-device public svesnav/linux-dby-w09 Linux 7.0 board DTS also contains no explicit /memory or device_type = "memory" node. Its author says the board/memory map was checked against a stock HarmonyOS 4.2 DTB. This is a kernel DTS source, not a captured post-ABL Linux handoff FDT, and therefore does not prove that the final FDT lacks or gains /memory.

ROUND42 adds a closer SoC-class reference: the public REG-Linux/edk2-freeabl SM8250-capable LinuxLoader (CodeLinaro r34-based, validated on a different SM8250 device) explicitly looks up /memory and returns EFI_NOT_FOUND if absent in its standard non-AUTO_VIRT_ABL path. It updates an existing /memory/reg via UEFI EFI_RAMPARTITION_PROTOCOL; it does not create the node. An older SDM660 BDS LinuxLoader reference does create /memory in PrepareFdt(), so Qualcomm ABL behavior differs by source generation/platform path and cannot be generalized.

Therefore mark the Huawei HOS4.3 ABL memory injection as UNKNOWN / NOT_ESTABLISHED. More importantly, do not assume ABL will create /memory: the same-SoC-class reference shows a valid SM8250 path where it expects the node to exist before LinuxLoader update. The public SM8250 reference is not Huawei's ABL; only the actual final FDT or exact Huawei source can close this.

References:
- Same-device public board DTS: https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts
- ROUND7 local evidence: firmware-analysis/round7/dby_w09_hw_matrix.txt and dtb_property_inventory.csv on firmware-audit-v1.

## 3. HOS4.2 public reserved-memory reference is not a direct HOS4.3 template

The same-device Linux 7.0 DTS defines only four board-specific reserved-memory children:
- splash_region (ABL splash framebuffer handoff);
- dfps-data;
- rainbow;
- bootfail.

ROUND7's HOS4.3 deterministic base-FDT inventory has rainbow_mem and bootfail_mem, but does not list splash_region or dfps-data under those names. It has many additional no-map and reusable nodes, including hyp_region, xbl_aop_region, smem_region, multiple PIL firmware areas, qseecom_region, secure_display_region, cnss_wlan_region, and linux,cma.

This mismatch matters:
- do not copy the HOS4.2 splash_region or DFPS addresses into the current HOS4.3 ACK DTS;
- do not assume the absence of HOS4.2-style named nodes means the underlying reservations are unnecessary;
- do not copy all HOS4.3 firmware pools into the minimal ACK base without determining which external processors / firmware remain active and which ranges ABL reserves elsewhere;
- no-map, reusable, and size semantics must be preserved if a selected region is later recreated.

## 4. First UFS milestone treatment

For the current storage-first DTS draft:
- Keep CONFIG_OF_RESERVED_MEM=y, needed by the Qualcomm Command DB configuration and reserved-memory infrastructure.
- Keep UFS Host/PHY and their verified resources isolated from display, DSP, WLAN, camera and other later consumers.
- Leave explicit /memory and /reserved-memory recreation unimplemented until the ABL handoff behavior and required system/secure carveouts are reconciled.
- Do not claim the board DTS is build-ready or boot-ready. The memory/reserved-memory handoff is an explicit pre-build gate, not an optional later cosmetic feature.

This is a deliberate evidence boundary. Omitting these nodes from a review-only .draft is not a recommendation to boot with them absent.

## 5. Source-side actions

- Updated the board DTS comment block to explain the no-memory-node evidence, possible ABL injection, reserved-memory classes and the risk of copying HOS4.2 values.
- Updated the DTS README and ROUND18 boot packaging review to record this separate memory handoff gate.
- No new local Agent task is issued. ROUND12 AVB inspection remains the only current local task.

## 6. Verification status

| Item | Status |
|---|---|
| ROUND7 HOS4.3 base-FDT /memory property/path inventory | NO MATCH |
| ROUND7 HOS4.3 /reserved-memory root | FOUND |
| Reserved-memory child nodes in deterministic base inventory | 34 |
| No-map / reusable / size/alignment property classes | INVENTORIED |
| Full physical reserved-memory address / size reconstruction | NOT_EXPORTED / NOT_RECONSTRUCTED |
| Same-device HOS4.2 public Linux board DTS memory/reservation pattern | SOURCE REVIEWED |
| Public SM8250 FreeABL LinuxLoader memory-node prerequisite / RAM partition update | SOURCE REVIEWED; requires existing /memory in standard path; not Huawei ABL |
| HOS4.3 ABL live /memory injection into replacement ACK DTB | UNKNOWN / NOT_ESTABLISHED; ROUND42 says do not assume generic injection |
| Exact set of HOS4.3 reserved regions required for UFS-only Android 17 | UNKNOWN |
| DTS/dt-schema/Kconfig/build/boot | NOT_RUN |

## 7. Next step

Continue GPT-side Android 17 first-stage / boot packaging design after ROUND12 AVB metadata findings. Keep memory/reserved-memory handoff as a required review gate before any actual DTB build or boot. No repeated local FDT scan is required at this stage.

## 8. ROUND42 update — same-SoC-class ABL reference tightens the gate

ROUND42 reviewed REG-Linux/edk2-freeabl commit `4cd7fb389e22d7a3761308006fc6d79410be9ddf`, whose project lists SM8250 support validated on a different device. Its standard LinuxLoader `UpdateDeviceTree()` requires `/memory` to exist and returns EFI_NOT_FOUND if absent; `target_dev_tree_mem()` then uses the UEFI RAM Partition Protocol to rewrite the node's `reg`. It does not create `/memory`. This differs from an older SDM660 ABL BDS source that could create a missing node in PrepareFdt(). The source is a reference, not Huawei's HOS4.3 ABL.

That same SM8250 reference optionally scans existing `/reserved-memory` children with `no-map`, subtracts the ranges from RAM partitions, then writes the reduced intervals into `/memory/reg`; it does not synthesize missing reserved-memory children or recover reusable/size/alignment semantics. The feature is conditional on REMOVE_CARVEOUT_REGION. See `kernel-baseline/round42/hos43-memory-handoff-sm8250-abl-fdt-prerequisite.md`.

Updated assessment: the final Huawei post-overlay/post-ABL FDT must be checked for `/memory`; do not leave it out of an ACK DTB relying on generic ABL injection. The HOS4.3 raw/base DTB's missing `/memory` remains non-conclusive about final handoff, but the former positive inference that ABL probably adds it is downgraded. Address/size and the complete reserved-memory set remain UNKNOWN and must not be guessed.
