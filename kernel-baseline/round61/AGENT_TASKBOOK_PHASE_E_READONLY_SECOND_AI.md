# ROUND61 Phase E — local Agent read-only evidence taskbook

**Issued by:** Second AI (ChatGPT GitHub-connected implementation agent)  
**Target device:** Huawei MatePad 11 (2021), DBY-W09, HOS4.3  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Purpose:** Resolve the two hardware-fact blockers in Phase E without changing or operating the device.

## 0. Hard safety limits

This is an evidence-collection task only.

Do NOT:
- unlock bootloader, root the tablet, reboot it, change boot mode or modify bootloader settings;
- execute `fastboot`, flash, erase, format, sideload, partition-write or recovery commands;
- mount filesystems writable, change regulator settings, force-enable/disable rails or edit device-tree properties;
- install new binaries, bypass endpoint/security controls or upload raw firmware/partition data;
- infer or fabricate addresses, rail parents, voltage values, offsets or phandles.

Use only evidence already present in the authorized HOS4.3 local firmware inventory, or an already-approved read-only collection route. If obtaining the final live handoff would require a new device operation or elevated access that has not been separately approved, stop and report that exact dependency. Do not improvise.

## 1. Required output A — final ABL-to-Linux memory handoff

The known stock base boot FDT inventory (ROUND7/19) has no root `/memory` node and no `device_type = "memory"`, while it contains 34 `/reserved-memory` children. The fact that ABL may inject a final memory map has not been demonstrated.

Find the **actual final handoff evidence** used by HOS4.3 on DBY-W09. Accept exactly one proven path:

### Path A: classic FDT

Provide a sanitized final FDT capture known to be the one passed by ABL to the Linux entry point. The report must include:
- how/where the captured blob was obtained and why it represents the final ABL-to-Linux FDT, rather than the pre-ABL stock `boot.img` base FDT;
- root `#address-cells` and `#size-cells`;
- each enabled RAM node: path, `device_type`, exact `reg` tuples and any `linux,usable-memory` constraints;
- all 34 (or actual final count) `/reserved-memory` children, their path, `reg`, `no-map`, `reusable`, `status`, alignment/size constraints, and relevant phandle relationships;
- the full `/chosen` node and any memory-related bootargs/properties;
- evidence that ranges do not overlap incorrectly and how firmware/secure/DSP/QSEE/SMEM/mailbox/CMA/crash carveouts are preserved.

If values are private or sensitive, keep them in the authorized local report and provide only sanitized ranges/identifiers sufficient to verify consistency; do not upload raw firmware, raw partition data or device identifiers.

### Path B: EFI stub

If the real entry path is Linux EFI stub rather than classic FDT memory discovery, provide:
- evidence of EFI-stub entry in the actual HOS4.3 boot flow;
- final `/chosen/linux,uefi-system-table` presence/value classification;
- the UEFI memory-map descriptors used by Linux, including types, physical ranges and attributes needed to reconcile usable RAM and reservations;
- evidence that the memory map is the one handed to this kernel entry, not an unrelated firmware inventory.

Do not report Path B as proven merely because the kernel has EFI support.

### Memory output template

```text
Source / firmware build identity:
Capture method and privilege level:
Why this is the final post-ABL handoff:
Entry path: classic FDT | EFI stub | unknown
Root cells:
RAM nodes and exact tuples:
Reserved-memory node count:
Reserved-memory ranges/attributes:
Chosen memory-related properties:
Range-overlap/reconciliation result:
Unresolved fields:
Evidence file paths and SHA-256:
```

If the final handoff cannot be observed from existing authorized evidence, return **BLOCKED — final ABL memory handoff unavailable**, not an inferred map.

## 2. Required output B — physical PM8150 input-parent topology

Current draft maps PM8150 regulator outputs used by UFS (S4/L5/L6/L9/L17 and PM8150L S8), but not their own physical input parents. Existing HOS ARC parent-supply and proxy-supply relationships are virtual vendor voltage-level / temporary-consumer semantics and must not be relabeled as VRM input supplies.

Find a trustworthy DBY-W09 HOS4.3 board-specific source for the physical input path of every used PM8150 output. Preferred evidence:
- authoritative device schematic / PMIC power tree for this exact board revision; or
- a HOS4.3 final device tree/binding/firmware description that explicitly specifies the physical input rail and parent relationship; or
- an equivalently authoritative board-specific engineering source with traceable provenance.

For each output, report:
- PMIC identity, PMIC ID and output rail name (not only a legacy label);
- whether it is VRM, XOB, ARC level or proxy consumer;
- exact physical input supply name and upstream provider/source, if explicitly established;
- source filename/revision/page/node/property and relevant blob/file SHA-256;
- voltage/current constraints only where actually present in the source;
- ABL/firmware boot-handoff assumptions, if explicitly documented;
- what remains unknown.

Explicitly distinguish:
- PMIC VRM input supply vs UFS consumer supply (e.g. `qcom,vddp-ref-clk-supply`, `qcom,vccq-parent-supply`);
- ARC level-parent vs physical electrical input;
- proxy-supply / boot-time temporary vote vs persistent regulator enable.

The current inspected base-FDT scope did not find `vdd-s1..s10-supply`, `vin-supply`, or `vph-pwr-supply`. Do not add `vph_pwr=3.7V`, guessed `vdd-s*-supply`, fake fixed regulators, or translate proxy-supply edges into parent regulators.

### Power-tree output template

```text
Board revision / source identity:
PMIC ID and output rail:
Rail class (VRM / XOB / ARC / proxy):
Explicit physical input parent:
Upstream provider:
Source path + page/node/property:
Voltage/current evidence:
Firmware/ABL handoff notes:
Is this a real electrical edge?:
Unresolved facts:
Evidence file paths and SHA-256:
```

If the exact physical input path is not present in an authoritative source, return **BLOCKED — PM8150 physical parent not established**. A runtime regulator readout or ACK regulator-core dummy-supply fallback does not prove the electrical schematic connection.

## 3. Deliverable and independent validation

Create a sanitized Markdown report in this repository under:
`firmware-analysis/round64/round64-dby-w09-hos43-final-memory-and-pm8150-input-evidence.md`

The report must include:
- each source identifier, version/revision, evidence path and SHA-256;
- explicit PASS / BLOCKED / UNKNOWN per required field;
- no raw stock firmware, keys, signatures, partition bytes, serial numbers, user identifiers or secrets;
- a statement that no device state was changed and no device operation was performed.

Do not edit the review-only board DTS draft or create a DTS/DTB/boot package. The Second AI will consume the report and determine whether Phase E can be safely promoted.

## 4. Stop and hand back

Stop immediately when:
- both evidence packages are complete; or
- a required fact can only be obtained through unapproved device access/elevated privileges; or
- the available local sources do not actually establish the final memory handoff / physical input map.

Do not substitute another Android version, another SM8250 device, public HOS4.2 source, a guessed schematic or a kernel driver default. Return the report path, evidence hashes, and the single narrowest outstanding request if blocked.
