# ROUND61 Phase E — board DTS, memory handoff and PM8150 power gates

**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Fixed ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Phase status:** BLOCKED — evidence review complete; no real board DTS migration is justified by the available HOS4.3 evidence.

## 1. Existing HOS4.3 facts (read-only reports reused)

No new firmware parsing or extraction was performed. The following completed reports on `firmware-audit-v1` remain the evidence source:

- ROUND7 / ROUND42: HOS4.3 base boot FDT has no root `/memory` node and no `device_type = "memory"` property. It has 34 `/reserved-memory` children across firmware, secure, DSP, reusable and crash-record classes. Physical addresses are not published.
- ROUND8: stock DTBO entry 8 resolves 145/145 fragment targets. Its UFS host/PHY fragments describe board supplies and `vdda-phy-always-on`; overlay contents establish intent, not actual runtime selection or final post-ABL FDT.
- ROUND11: four explicit ARC parent-supply edges and six proxy-supply edges were resolved in the inspected base FDT. Proxy-supply is a distinct RPMh mechanism, not an external PMIC input. A whole-base-FDT property-name scan found no `vdd-s1..s10-supply`, `vin-supply` or `vph-pwr-supply`.
- ROUND13/14/48/51: UFS PM8150 rails and vendor regulator mode/corner semantics were reviewed against public KONA source. This does not establish the missing physical PM8150 input connections or runtime rail enable state.
- ROUND12: AVB metadata inspection is separately blocked; no footer or descriptor state was established.

## 2. Memory handoff is a hard first-boot gate

The fixed ACK 6.18.33 classic ARM64 path scans enabled root-level nodes with `device_type = "memory"`, then imports `reg` or `linux,usable-memory` ranges. The `/reserved-memory` scan is separate; reserved children do not create system RAM.

ROUND42's pinned public SM8250-capable FreeABL reference shows a classic LinuxLoader path that resolves `/memory` after its DTB/DTBO composition stage and fails if no unambiguous memory node exists. This is a same-SoC-class reference, not proof that Huawei HOS4.3 uses the same ABL source or build flags.

ROUND43 establishes a real alternative: if the kernel is actually entered through Linux's EFI stub, and the final `/chosen` carries the complete trusted UEFI system-table and memory-map metadata, ACK EFI initialization can replace the earlier DT-derived memblock map with UEFI descriptors. A UEFI ABL or Qualcomm EFI_KERNEL_PROTOCOL alone does not prove Linux EFI-stub entry.

**DBY-W09's actual HOS4.3 kernel entry route and final post-ABL FDT remain UNKNOWN.** Do not infer the final tree from the raw boot-image DTB, borrow RAM ranges from another SM8250 product, or copy HOS4.2 splash/DFPS carveouts.

Required evidence:
1. Sanitized final FDT captured after the real ABL DTB/DTBO selection and overlay composition, immediately before kernel entry.
2. Actual kernel entry classification: classic ARM64 Image entry or Linux EFI-stub entry.
3. For classic entry, valid enabled system-memory ranges; for EFI-stub entry, complete trusted `/chosen/linux,uefi-*` metadata and proof the stub was entered.
4. Reconciliation of all 34 reserved-memory classes against usable RAM, including secure firmware, DSP, reusable and crash-dump regions.
5. Selected DTBO entry and any ABL memory mutation demonstrated in the same final-tree evidence.

## 3. PM8150 physical input-parent gap

The review-only board draft `dts/dby-w09-ack18-board.dts.draft` describes evidence-backed UFS consumer connections to PM8150 S4/L5/L6/L9/L17 and PM8150L S8. The UFS host's `qcom,vccq-parent-supply` link to S8 and `qcom,vddp-ref-clk-supply` link to L6 are consumer links; they do not resolve the physical input supply of S8 itself.

The pinned ACK PM8150 VRM table expects physical input supply names for the relevant regulators, including vdd-s4, grouped LDO input names and vdd-s8. HOS4.3's inspected base FDT does not expose the corresponding upstream input-supply properties. The board draft correctly leaves those physical parent paths unresolved.

Do not add `vph_pwr=3.7 V`, guessed `vdd-s*-supply` links, fake fixed regulators, vendor ARC nodes, or proxy-supply translations. Regulator-core dummy-parent fallback is not evidence that a physical rail is present or enabled.

Required evidence:
1. Trusted HOS4.3 regulator-tree or bootloader regulator evidence showing exact PM8150 physical input parents and voltage/current constraints.
2. Board-specific schematic or equivalent authoritative evidence for the UFS REF_CLK pad supply.
3. Evidence identifying the VCCQ parent/enable owner and S8's own input path.

## 4. DTS migration decision

**Do not migrate ROUND37 yet.** The board file remains a review-only `.dts.draft`, not an ACK DTS build input. It intentionally does not reconstruct `/memory` or the 34 reserved-memory children. No board DTB or `dtbs_check` has been run.

Once the memory and power evidence is available, create a new board DTS patch against the exact ACK board path, then run real `git apply --check`, `git diff --check`, binding checks, `dtc`, `dtbs_check`, and final DTB inspection. Do not use the draft as an input before that point.

## 5. Phase E verdict

**BLOCKED on target-specific memory/FDT and PM8150 physical parent evidence.** Kernel-only Image compilation may proceed independently. Board DTB generation and any first boot remain gated.
