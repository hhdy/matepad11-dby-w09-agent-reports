# ROUND158 — WorkBuddy Window A: exact HOS4.3 ABL rootparam / DTBO / fastboot-boot audit

- Executor: **WorkBuddy Window A (1号 Agent)**.
- This is not 2号 AI and not WorkBuddy Window B.
- Use only Window A's own ROUND155/157 workspace and already captured HOS4.3 boot-chain/ABL files.
- Target: DBY-W09, HOS 4.3.0.196 (C00E100), ABL payload SHA-256 `a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404`.
- Task is offline reverse engineering and read-only analysis. No new ADB, no device command, no partition read/write, no reboot, no fastboot session, no boot.img/DTBO output intended for use.

## 1. Why this task exists

ROUND157 established:
- source tree `c56d93eafa35057d65176db6594d67d5144868a0` is exact;
- 2号 Agent completed a fresh full Kleaf build successfully (RC=0);
- RAM-patched DTB is reproduced at 108680 B / SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60`;
- Window A's full build alone failed from a host OOM kill of `pahole`, not a source compile defect;
- exact HOS4.3 ABL still has unresolved overlay mutation atomicity, RAM property-write primitive, and AVB/OEM acceptance details.

A new public same-model Linux 7.0 port reports an important possible hard gate:
- its ABL requires the selected DTBO entry to populate `/rootparam` with the board identity in the stock format; other DTBO entries reportedly return to fastboot;
- it reports `fastboot boot` is refused;
- its public rootparam overlay uses `qcom,board-id=<0x206a 0>` and fields `qcom,boardid`, `qcom,board_name`, `qcom,product_name`, `hardware_version`, and `huawei,modem_id`.
References:
- https://github.com/svesnav/linux-dby-w09
- https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso
- https://github.com/svesnav/linux-dby-w09/blob/main/pack_dtbo.py

**Do not copy its board ID blindly.** That public example may be a different HOS / hardware configuration. Our direct target capture says HOS4.3.0.196, live `androidboot.dtbo_idx=2`, selected Entry 2 board-id `0x200e`; Entry 8 uses `0x206a` and was not selected in that stock boot. The exact HOS4.3 ABL and captured partitions take precedence.

## 2. Priority A — Does this exact HOS4.3 ABL require /rootparam?

Using only the existing decompressed ABL PE and existing ROUND155 captured stock DTB/DTBO/boot-v2 data:

1. Inspect the exact ABL for `rootparam`, `qcom,boardid`, `qcom,board_name`, `qcom,product_name`, `hardware_version`, `huawei,modem_id`, root `qcom,board-id`, and relevant failure strings.
2. Trace their xrefs and control flow. Determine whether the ABL:
   - looks up `/rootparam` unconditionally or only under a particular board/boot path;
   - validates required properties/values;
   - copies root properties from the DTBO into the selected base FDT;
   - treats missing/mismatched rootparam as fatal, selects another DTBO, or continues.
3. Report exact instruction addresses and call sites. Separate decoded control-flow (A) from strings/xrefs (B) and inference (C).
4. Identify the exact `/rootparam` state in the captured stock Entry 2 and Entry 8 after host-side application if those objects are available. Do not infer from the public HOS4.2 overlay.
5. Inspect the candidate source/DTB tree for the actual `/rootparam` node:
   - exact path and properties;
   - whether a label/phandle exists;
   - whether the compiled DTB has `/__symbols__`, `/__fixups__`, or `/__local_fixups__`;
   - whether a `target-path="/rootparam"` overlay would be structurally possible.
6. Give a decisive HOS4.3-specific outcome: REQUIRED / NOT REQUIRED / INDETERMINATE. Explain what evidence supports it.

## 3. Priority B — Which DTBO entry can HOS4.3 select for this candidate?

1. Reconcile the captured runtime Entry 2 (`board-id=0x200e`) vs Entry 8 (`0x206a`) with the candidate base root `qcom,board-id=<0 0>`.
2. Trace ABL's exact local-board / DTBO entry matching path sufficiently to state the inputs and selection criteria. Determine whether the candidate can be matched without retaining stock vendor fragments.
3. Determine whether a one-entry DTBO table with a target-path rootparam overlay is structurally accepted by this exact ABL and what metadata must be present in the DTBO header/table.
4. Do not decide board-id by majority vote between public repositories. Exact HOS4.3 captures win.
5. State whether the existing stock Entry 2 can safely be applied to the minimal candidate. ROUND154 already showed 0/166 external symbols bind and many fragment targets are missing; ROUND157 did not prove overlay transaction atomicity. Do not recommend relying on a failed stock overlay.

## 4. Priority C — Is fastboot temporary boot supported?

The external DBY-W09 port reports `fastboot boot` refused. Confirm from the exact HOS4.3 ABL if possible:

- search the ABL fastboot command registration/dispatch for `boot`, `download`, `continue`, `flashing`, and `oem` paths;
- determine whether a fastboot `boot` command is registered, rejected, or conditionally disabled;
- separate static command support from runtime policy. If the code does not decide it, say INDETERMINATE.
- Do not start a fastboot session or send a command.

## 5. Carry-forward narrow gaps

If the same disassembly work makes this low-cost, add only:
- exact `/memory/reg` property-builder semantics (ROUND157 C1 showed custom AllocatePool/property-builder code; whole-tree replace vs append is still not fully proven);
- whether external fixups complete before any fragment mutation / whether failed overlay can leave partial mutations (ROUND157 C2 remains PARTIAL).
Do not expand to ARC/proxy/display or broad AVB reverse engineering.

## 6. Deliverable

Publish:
`firmware-analysis/round158/WORKBUDDY_A_ROUND158_EXACT_HOS43_ROOTPARAM_DTBO_AND_FASTBOOT_BOOT_AUDIT_REPORT.md`

The report must include:
- ABL artifact SHA recheck;
- exact captured firmware/DTBO identities used;
- candidate rootparam node inspection;
- rootparam requirement conclusion;
- Entry2/Entry8 selection conclusion;
- fastboot boot support conclusion;
- exact instruction addresses, confidence grades, unresolved gaps;
- clear statement that no device or partition was accessed this round.

Read back the uploaded report and verify its blob/content. Stop.

## 7. Prohibitions

No device / ADB / root / fastboot command; no new partition reads; no flash, reboot, recovery or temporary boot; no boot.img, DTBO container or vbmeta generation; no keys/signing/AVB edits; no source edits; no access to Window B workspace/private files.

— END —