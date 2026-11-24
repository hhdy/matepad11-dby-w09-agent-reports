# ROUND61 Phase E — board DTS, memory handoff and PM8150 power gates

**Date:** 2026-11-24  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Phase status:** BLOCKED — evidence review complete; no real board DTS migration is authorized by the available evidence

## 1. Scope

This is a parallel evidence-gate review only. It does not migrate or modify the review-only ROUND37 DTS draft, create a board DTB/DTBO, invent memory ranges, or infer PMIC rail parents.

## 2. Memory/FDT handoff

The ROUND42 and ROUND43 evidence establishes that the Linux kernel's usable RAM map must come from the actual final handoff path. Two distinct mechanisms must not be conflated:

- A classic arm64 entry path consumes the final FDT `/memory` nodes and relevant reserved-memory declarations.
- An EFI-stub entry path can consume the EFI memory map and has different reservation/ownership semantics.

The name or apparent capability of an ABL build is not enough to prove which path HOS4.3 uses on this tablet. The available evidence does not include a trusted, target-specific final HOS4.3 FDT captured at the kernel handoff point, nor a verified EFI memory-map handoff trace.

Therefore:
- No `memory@...` range is added or guessed.
- No `/reserved-memory` carveout is copied from a related SM8250 device.
- No assumption is made that the full physical RAM map can be inferred from the Android userspace-visible memory total.
- The ROUND37 draft remains review-only and is not applied to ACK DTS paths.

Required evidence to unblock:
1. A sanitized final HOS4.3 FDT (or exact handoff FDT dump) captured immediately before kernel entry.
2. ABL boot log/entry trace proving whether the kernel receives a direct FDT or EFI stub handoff.
3. Exact `/memory`, `/reserved-memory`, `linux,usable-memory`, `no-map`, and dynamic reservation content, with addresses and sizes preserved.
4. Evidence that any overlay/ABL mutation occurs before the captured final FDT, not merely an earlier vendor DTB.

## 3. PM8150 / VDDP / VCCQ parent-supply gate

The ROUND21 PM8150 VRM-parent review remains unresolved for the actual DBY-W09 board. The evidence set does not prove the physical PMIC parent rail or board wiring for the UFS VDDP REF_CLK supply. It also does not establish a safe parent-supply relationship for the legacy VCCQ-parent path.

Consequently:
- Do not map VDDP to `vph_pwr`, `vreg_s4a_1p8`, or another guessed regulator.
- Do not add `qcom,vccq-parent-supply` merely because a similarly named rail exists on a related Qualcomm platform.
- Keep the UFS driver changes tolerant of absent optional supply properties.
- The board DTS must only add supply phandles after board-specific schematic, bootloader regulator-tree, or trusted runtime regulator evidence identifies the exact parent.

Required evidence to unblock:
1. HOS4.3 PMIC regulator-tree dump with regulator names, parent relationships and voltage/current constraints.
2. Board-specific schematic or equivalent trusted hardware evidence for the UFS REF_CLK pad supply.
3. Evidence of whether VCCQ is parented or directly supplied on this board, including the actual consumer/enable owner.

## 4. DTS migration decision

**Do not migrate ROUND37 yet.** It remains a `.dts.draft` review artifact, not a patch against the real ACK board DTS path. A correct board DTS cannot be produced without both:
- trusted memory/FDT handoff facts; and
- board-specific PM8150 regulator parent facts.

Once those are available, create a new board DTS patch against the exact ACK path, then run:
- `git apply --check` and `git diff --check`;
- `make ARCH=arm64 dt_binding_check DT_SCHEMA_FILES=...`;
- `make ARCH=arm64 dtbs_check DT_SCHEMA_FILES=...` for the actual board DTS;
- a final DTB inspection to verify the intended memory and regulator nodes.

## 5. Phase F/G dependencies

ROUND62 same-device boot-chain cross-reference is useful but does not supply the missing local HOS4.3 artifacts. The following remain unverified:
- actual boot/vendor_boot/dtbo partition layout and whether the target kernel image is consumed as Image, boot image, or another packaging format;
- ramdisk ownership and required init/fstab/first-stage dependencies;
- AVB descriptor/footer layout and rollback metadata for the installed image set;
- ABL RAM-boot support and whether it preserves the final FDT/bootconfig state;
- any safe, reversible test-boot procedure for this exact device.

No boot image, vendor_boot, DTBO, AVB metadata, or device operation is claimed or generated.

## 6. Decision

Phase E is **BLOCKED on missing target-specific evidence**, not on a source-code implementation issue. Continue source-level validation and Kleaf candidate validation independently, but do not fabricate a board DTB or advance to Stage-B/DerpFest work until the memory, power, and boot-chain gates are closed.
