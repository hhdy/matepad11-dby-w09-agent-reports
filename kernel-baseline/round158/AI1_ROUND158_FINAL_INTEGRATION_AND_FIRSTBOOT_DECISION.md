
# AI1 ROUND158 Final Integration and First-Boot Decision

- Reviewer: 1号 AI (ChatGPT)
- Date: 2026-11-27
- Target: DBY-W09 / HOS 4.3.0.196 (C00E100) / SM8250
- Candidate ACK: android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- This is the final integrated review of ROUND158, not a new test task. No device operation occurred.

## 1. Reports integrated

1. Window A exact HOS4.3 ABL / rootparam / fastboot report:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round158-exact-hos43-rootparam-abl/firmware-analysis/round158/WORKBUDDY_A_ROUND158_EXACT_HOS43_ROOTPARAM_DTBO_AND_FASTBOOT_BOOT_AUDIT_REPORT.md
   Blob: 285c34f99ce8b1c4b0d5056c5c1362aa6dcb1aee.
2. Window B independent rootparam / target-path / DTBO-container / module-output report:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round158-independent-rootparam-dtbo/firmware-analysis/round158/WORKBUDDY_B_ROUND158_INDEPENDENT_ROOTPARAM_DTBO_VARIANT_AND_CONTAINER_AUDIT_REPORT.md
   Blob: a7a8a70b7300423e48bf9239bb2ec581e693621f.
3. 2号 AI independent gate review:
   https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round158-independent-rootparam-bootgate/firmware-analysis/round158/AI2_ROUND158_INDEPENDENT_ROOTPARAM_AND_FASTBOOT_BOOT_GATE_REVIEW_REPORT.md
   Blob: 014b6d9b64b95c026157dc117aa0deb3935aa26d.

The 2号 AI report is conservative on safety, but its rootparam subsection still treats the exact HOS4.3 facts as unknown and its next-delegation section asks for A/B work that is now complete. For rootparam facts, the completed Window A report is the primary exact-target evidence; Window B independently verifies candidate DTB and host overlay behaviour. The AI2 report's NO-GO decisions for boot package, temporary boot and partition writes remain consistent with completed evidence.

## 2. Exact HOS4.3 /rootparam finding

### 2.1 ABL-level hard gate

Window A re-hashed the exact target ABL payload:
- 2,597,064 bytes;
- SHA-256 a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404.

Its exhaustive ASCII/case/UTF-16/partial-token search found no rootparam, /rootparam, qcom,boardid, qcom,board_name, qcom,product_name, hardware_version, or huawei,modem_id strings, and no candidate ADRP/ADD reference to those names.

**Decision:** an explicit ABL /rootparam lookup/validation/fatal gate is NOT FOUND in this exact HOS4.3 ABL. This does not prove that later kernel/userspace code has no use for these fields. The public HOS4.2 report that a missing rootparam makes ABL fall back to fastboot is not confirmed by the HOS4.3 ABL.

### 2.2 What stock HOS4.3 actually does

The captured stock boot-v2 base FDTs each contain an empty /rootparam node with phandle 0x3e. The selected stock DTBO Entry 2 (qcom,board-id=<0x200e 0>) contains fragment@143, whose target=<0xffffffff> is resolved through external __fixups__ symbol rootparam.

The exact HOS4.3 Entry 2 rootparam payload observed in the captured live FDT / stock DTBO is:
- qcom,boardid = [08 02 06];
- qcom,board_name = "DBY_W09_VD";
- qcom,product_name = "DBY-W09";
- hardware_version = "SH1DBSLM";
- huawei,modem_id is an opaque non-ASCII byte payload in the report; its exact byte sequence was not published in printable form;
- phandle 0x3e on the base /rootparam node.

Thus /rootparam is a real stock board-identity overlay target, but it is populated by the selected DTBO, not by ABL code. Do not replace this target's qcom,boardid with the public HOS4.2 value <8 2 9 8> or substitute board ID 0x206a.

### 2.3 Candidate mismatch

Current RAM-patched candidate source tree:
- tree SHA c56d93eafa35057d65176db6594d67d5144868a0;
- candidate DTB SHA 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60;
- /rootparam path exists but has no properties, no phandle and no target relationship;
- compiled DTB has no /__symbols__, /__fixups__, or /__local_fixups__.

The DTS source contains a source label rootparam:, but because the DTB was not built with -@, no externally bindable /__symbols__/rootparam was emitted.

Consequences:
- stock Entry 2 cannot be safely applied to this candidate: its 166 external fixups do not resolve (earlier validation measured 0/166 bound).
- merely adding a phandle label to source is insufficient unless a DTB built with exported symbols is used.
- even exporting only rootparam would not resolve the other stock Entry 2 vendor symbols, so do not assume stock Entry 2 then becomes safe.
- target-path /rootparam overlay is the host-tested route that avoids an external symbol lookup.

## 3. Window B host-only prototype results

Two target-path prototype DTBOs were compiled:
- P/0x200e: 483 B, SHA-256 7c6f179a49ff3042642f050468e5a9ec76e21a552837d0e7fa3a50e155c64824;
- P/0x206a: 483 B, SHA-256 03855c4447106f38020fc00c31a1fbd4ba52486dee5ba26584b59f4d618508ef.

Both apply cleanly to the current candidate under host fdtoverlay, changing only five /rootparam properties, with zero unrelated changes. However, these prototypes use the HOS4.2 public payload (or a grade-C decimal-digit derivation for 0x200e); they are not exact HOS4.3 payload reproductions and must not be used as final device DTBOs.

The phandle-target Q prototypes compiled with a single external rootparam fixup but failed against the candidate base because it lacked /__symbols__. They passed only against a disposable scratch base that added one rootparam phandle and one symbol property.

The four one-entry Android DTBO table prototypes were internally self-consistent:
- header magic 0xD7B7AB1E;
- 32-byte header + 32-byte entry;
- total-size/bounds/embedded-FDT/hash/roundtrip checks passed;
- table offset 64, page size 4096, but DTBO payload offset and total file size were not page-aligned.
This validates packer/parser roundtrip only. It does not prove the exact HOS4.3 ABL accepts a one-entry compact table or the chosen id/rev/custom metadata.

## 4. DTBO selector and fastboot

### 4.1 Board selection

The captured stock DTBO table has nine entries. Entry 2 is 0x200e; Entry 8 is 0x206a. Live HOS4.3 boot reported androidboot.dtbo_idx=2, corresponding to Entry 2.

The ABL match path references local board identity and matches candidate DTBO properties including MSM ID, board ID major/minor, subtype and DDR size. The report did not fully complete an end-to-end proof of every selector field and table metadata interaction. Treat Entry 2 / 0x200e as the observed target truth; do not force Entry 8 / 0x206a.

### 4.2 fastboot boot

The exact ABL has a CmdBoot path, boot token, invalid-header and authentication error branches, plus the message "Fastboot boot command is not available in locked device". The ABL report did not decode the complete command dispatch table or prove unlocked-device behaviour.

**Decision:** static fastboot-boot support exists; locked-device refusal is evidenced; unlocked-device behaviour is INDETERMINATE. The live verifiedbootstate=orange is a useful unlocked-state indicator under standard AVB semantics, but it does not substitute for the undecoded CmdBoot dispatch/policy path. No fastboot command should be attempted until a valid, reversible test plan exists.

## 5. Remaining build/package details

- ROUND157 full kernel build gate is PASS: Window B completed the exact Kleaf target RC=0 using the accepted source tree and config.
- Window A's build failure is an environmental OOM during pahole/BTF; it is not a source compile failure.
- The early UFS/storage dependency symbols are built-in (=y), so the initial kernel/initramfs storage path is not blocked by missing loadable UFS modules.
- Window B found CONFIG_MODULES=y, with 108 modular symbols and 2,224 built-in symbols. The empty module archive and zero-byte Module.symvers are caused by Kleaf target make_goals=["Image"], which does not run modules_install; it emits placeholder outputs.
- This is a build-graph/package-output gap for later Android/system operation, not a first-stage UFS driver omission. Do not claim a complete Android module package exists.
- ABL /memory/reg custom property-builder semantics (whole-tree replace vs append) remain PARTIAL.
- UFDT external-fixup / fragment failure mutation atomicity remains PARTIAL.
- Candidate /chosen is empty and bootargs/initrd handoff values/order remain to be specified.
- AVB/Huawei TA/TZ digest authorization remains unresolved.
- The exact rootparam huawei,modem_id byte payload should be extracted from the already captured stock Entry 2 only if a later package demonstrably needs stock-equivalent rootparam data; do not guess it from the public HOS4.2 sentinel.

## 6. Final go/no-go

| Activity | Decision | Reason |
|---|---|---|
| Exact ACK source / full kernel build | PASS | Complete Kleaf build RC=0 on exact accepted source tree. |
| Host-only target-path overlay mechanics | PASS | Works against candidate and modifies only /rootparam. |
| Exact HOS4.3 rootparam payload overlay | NOT YET READY | Most values known, modem_id bytes not exposed in report; target-specific board/selector/table metadata not fully closed. |
| Integrated boot-v2 boot.img + DTBO package | NO-GO | Need accepted HOS4.3 DTBO table/selector metadata, overlay atomicity decision, chosen handoff, RAM semantics and AVB/OEM authorization. |
| Temporary boot | INDETERMINATE / NO-GO FOR NOW | CmdBoot exists; locked path refuses; unlocked dispatcher behaviour not proven. |
| Partition write | HARD NO-GO | A-only device, incomplete AVB-chain backups (vbmeta_odm, eng_vendor, eng_system, version missing), missing full GPT/rollback metadata, no demonstrated restoration route or rehearsal, no write authorization. |

No boot image, DTBO partition image, vbmeta, signed package, temporary boot, flash, reboot or partition write was created/performed in ROUND158.

## 7. Project process decision: stop the audit loop

ROUND158 has resolved the central same-model rootparam confusion:
- The HOS4.3 ABL does not contain a rootparam-specific hard gate.
- The stock DTBO Entry 2 fills /rootparam through an external symbol fixup.
- The current candidate's node is present but not exported as a symbol; stock Entry 2 has too many unresolved symbols to reuse.
- Host target-path overlay mechanics work, but the test payload is not yet exact HOS4.3 and the Android DT table/ABL selector contract is not proven.

**Do not automatically open ROUND159 or another broad audit round.** The next phase should be implementation-led and bounded:
1. If the user elects to continue, produce one frozen host-side boot candidate using only target-derived values and the proven DTBO table contract; no repeated speculative variants.
2. Finish the minimal boot-v2 handoff description and confirm a viable non-destructive test route before any device attempt.
3. Keep all partition writes blocked until a complete recovery route and exact write authorization exist.

No general ARC/proxy/display/audio/camera audit is requested. A new task should be opened only if a concrete implementation or actual boot log exposes a specific blocker.

**STOP — ROUND158 integrated. No new Agent tasks automatically issued.**

— END —
