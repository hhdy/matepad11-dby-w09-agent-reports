# ROUND137 — WorkBuddy Agent taskbook: existing HOS4.3 ABL artifact and boot-trace availability audit

- **Executor:** WorkBuddy Agent (local executor only; not AI2)
- **Dispatched by:** AI1 (ChatGPT)
- **Target:** Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250
- **Kernel project:** ACK `android17-6.18.33_r00`, pinned commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`
- **Related review:** `kernel-baseline/round137/AI1_ROUND137_BOOT_LAYOUT_STATIC_AUDIT.md`
- **Purpose:** determine whether an already-existing, authorized HOS4.3 ABL binary or ABL/runtime handoff evidence is available for further offline review.
- **Mode:** strictly local, offline, read-only availability/metadata audit.

## 0. Role and task boundary

This task belongs to **WorkBuddy Agent** because it requires searching the user's existing local evidence directories. It is not an AI2 task. AI2 is not being assigned work.

This task does not reopen ROUND135 R3 and does not change the validated 23-patch candidate. It is a precondition check for whether the bootloader-specific D gate can advance without collecting new firmware or connecting to the device.

## 1. Authoritative existing starting points

Use only the already-existing HOS4.3 evidence corpus and file locations previously used by the project. The GitHub evidence already records:
- `firmware-hos43/package_inventory.csv` (43 rows) and `firmware-hos43/REPORT_README.txt`;
- existing sanitized ROUND64 Phase F boot-v2 / ramdisk / DTBO / AVB report;
- existing ROUND65 fstab / ramdisk / vbmeta_cust / boot-tool report;
- existing ROUND19 boot-header and DTBO/ramdisk inventory references.

Known extracted directory recorded in the existing README:
`D:\workbuddy\2026-11-23-22-29-12\MatePad11_HOS43_LocalCheck_20261123_230849`

If that directory is absent, do not search arbitrary drives or unrelated locations. Use only already-established evidence workspace paths. Do not enumerate personal directories.

## 2. Exact read-only questions

### A. Is an ABL artifact already present?

Search only existing authorized HOS4.3 extracted firmware/evidence directories for obvious ABL candidates:
- `abl.elf`
- `abl.img`
- `abl.mbn`
- `abl.bin`
- a file or folder explicitly named `abl` / `ABL`
- an already-extracted equivalent file identified by an existing partition manifest.

Also inspect existing package/partition inventories and existing extraction manifests for an ABL entry. Do not infer an ABL binary from `xbl.img`, `xbl_config.img`, `tz.img`, or `uefisecapp.img`.

### B. If an ABL artifact is found

Use only already-installed read-only tools:
- file type / ELF header identification;
- file size and SHA-256;
- non-sensitive version/build strings (e.g., build tag, date, version, platform identifier);
- existing parser output or logs that explicitly identify its build.

Do not execute the binary. Do not patch, disassemble-and-modify, repack, or upload it. Avoid printing public-key material, signatures, certificates, salts, hashes embedded as security metadata, rollback values, serials, MACs, IMEIs, or other sensitive device identifiers. A plain file SHA-256 is allowed only for artifact identity.

Finding strings that mention DTBO, FDT, rootparam, boot, ramdisk, or EFI is only a lead; it is not proof of runtime policy or actual selected entry.

### C. Are ABL / runtime handoff traces already present?

Search existing reports/logs only for directly recorded evidence of:
- ABL build/version;
- selected DTBO entry and the exact selection result;
- `/rootparam` contents after ABL overlay;
- final post-ABL FDT passed to Linux;
- classic arm64 direct entry vs EFI-stub entry;
- kernel entry register evidence confirming FDT physical address in x0.

Report each item as DIRECT EVIDENCE / INDIRECT LEAD / NOT FOUND. A DTBO entry whose board ID resembles DBY-W09 is not proof it was selected.

## 3. Explicitly do NOT do

- Do not connect the tablet, USB, serial, ADB, fastboot, recovery or bootloader shell.
- Do not reboot, unlock, root, remount, flash, write a partition, run `fastboot boot`, or change device state.
- Do not re-run an ADB pull that previously failed with Permission denied. Do not bypass permissions or escalate privilege.
- Do not extract or unpack any new HOS4.3 firmware/update package. Do not download firmware or tools.
- Do not upload raw ABL, boot, ramdisk, DTB, DTBO, vbmeta or firmware bytes to GitHub.
- Do not re-run the complete ROUND64/65 boot/AVB inventory; those reports are already accepted. This task only searches for the missing ABL artifact/version/trace evidence.
- Do not create a boot package or make any source/DTS/DTBO/AVB changes.

## 4. Required report and result semantics

Create:
`firmware-analysis/round137/round137-hos43-abl-existing-artifact-and-trace-audit.md`

Report:
1. exact evidence roots inspected (sanitized; do not publish unrelated personal paths);
2. whether an ABL artifact is found, with sanitized relative path, size, SHA-256 and file type;
3. available non-sensitive ABL version/build strings, with source offsets or file line references only if safe;
4. evidence table for DTBO selection, `/rootparam`, final FDT and entry-route observations;
5. distinction between direct evidence and mere string/filename leads;
6. exact missing item if blocked;
7. a final outcome of exactly one:
   - `FOUND — EXISTING ABL ARTIFACT; STATIC REVIEW POSSIBLE`
   - `PARTIAL — ABL ARTIFACT FOUND, BUT NO RUNTIME SELECTION/HANDOFF TRACE`
   - `BLOCKED — ABL ARTIFACT/TRACE NOT PRESENT`

Upload only the sanitized Markdown report and any safe text-only metadata log. Read back the uploaded file and verify it is byte-identical. Do not upload raw binary files.

## 5. Stop conditions

Stop immediately if a required input is missing, a tool attempts write access, a path escapes the existing authorized corpus, or any step would require device access/new firmware extraction/permission bypass. Report BLOCKED rather than expanding scope.

No subsequent package, test, device connection, or flash is authorized by this taskbook.
