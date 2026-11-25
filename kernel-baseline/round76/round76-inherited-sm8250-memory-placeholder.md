# ROUND76 — inherited SM8250 memory-node placeholder in the actual DTB build graph

Date: 2026-11-25
Owner: Primary AI, exact pinned ACK source review
Baseline: ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
Scope: source-level analysis of sm8250.dtsi included by current board DTS; no DTB rebuild or device operation.

## 1. Executive result

The current DBY-W09 board source files do not explicitly declare a /memory node. However, they include the pinned ACK arch/arm64/boot/dts/qcom/sm8250.dtsi. That included SoC DTSI defines one top-level child named memory@... with:
- device_type = "memory";
- a two-cell address / two-cell size reg tuple;
- a nonzero base placeholder inherited from generic SM8250;
- a zero size placeholder;
- source comment: "We expect the bootloader to fill in the size".

Therefore the actual pre-boot DTB produced from rev2 is not missing a memory node. It inherits an ARM64/SM8250 bootloader-fill memory placeholder. The exact unit-address suffix and physical base are intentionally not repeated in this report.

This is structurally consistent with the expectation that the loader supplies usable memory before normal arm64 entry, and it explains why a board source can omit /memory explicitly while still compiling a node through sm8250.dtsi.

It does NOT prove Huawei HOS4.3 ABL accepts this exact generic node shape, updates the size field, or writes the correct complete RAM tuple. HOS4.3 extracted base DTB itself has a /memory node whose reg cells are all zero. The generic ACK node differs in its initial base field even though its size is zero. ABL matching/fixup semantics remain UNKNOWN.

## 2. Exact pinned source observation

File: arch/arm64/boot/dts/qcom/sm8250.dtsi at lines 27–31:
- root #address-cells = <2>;
- root #size-cells = <2>.

At lines 683–686:
- one top-level memory node exists;
- device_type = "memory";
- reg has four cells;
- adjacent source comment explicitly expects the bootloader to fill its size.

The source node is inherited by the board candidate because it includes sm8250.dtsi. This applies to both original board draft and rev2 candidate.

## 3. Reconciliation with HOS4.3 ROUND19 / ROUND24

HOS4.3 local reports:
- ROUND19/20: extracted base FDT has a memory node with all-zero reg cells.
- ROUND24: board source rev2 has no explicit memory node in its own source text; it did not account for the inherited generic memory node from sm8250.dtsi.
- HOS4.3 actual final live FDT is unavailable; prior /sys/firmware/fdt read returned Permission denied.

Correct interpretation:
- The board source file does not spell out /memory itself.
- The compiled tree includes sm8250.dtsi's top-level memory@ node.
- HOS4.3 stock FDT and generic ACK DTSI both provide a zero-size bootloader-fill memory placeholder, but their initial base fields differ.
- The actual runtime ABL fixup remains unobserved.

## 4. Consequences

- Do not add a second manual /memory node on top of the included sm8250.dtsi; that risks duplicate memory nodes and unpredictable scanner/bootloader selection.
- Do not change the inherited node's reg or hardcode a RAM size/address without final FDT evidence.
- The correct next verification is to inspect the actual rev2 compiled DTB's memory node and compare its schema/shape with the HOS4.3 base template, then verify ABL updates that node in the real final handoff only when a legal authorized runtime FDT evidence path is available.
- A successful dtc compile or fdtoverlay composite is not proof that ABL will fill the node.

## 5. Status

- Pinned sm8250.dtsi inherited memory node exists: SOURCE PASS.
- Current board candidate compiled DTB contains that inherited node: STRONGLY DEDUCED from include graph and ROUND23 successful compile; raw temporary DTB output was not separately queried for this node in ROUND23.
- HOS4.3 ABL will update the inherited memory node: UNKNOWN.
- Actual RAM base/size and reserved-memory final map: BLOCKED.
- No source, DTS, DTB, config, branch-protected artifact or device changed.


## Same-device public Linux cross-check

The public same-device Linux 7.0 board DTS (svesnav/linux-dby-w09/sm8250-huawei-dby-w09.dts) includes the same SM8250 SoC DTSI and does not explicitly define its own /memory node. It therefore inherits the same generic memory placeholder from sm8250.dtsi. The project README describes a working boot path on an earlier HOS generation.

This is useful evidence that the generic SM8250 bootloader-fill memory node shape can work on the same device with an earlier ABL/HOS generation. It is not proof that the user's current HOS4.3 ABL performs the same fixup, nor that it writes the exact same RAM range. Keep current HOS4.3 final FDT unknown.
