# ROUND64 Phase E — HOS4.3 final memory handoff and PM8150 input-parent evidence

Executor: local Agent (independent of both AI task authors)
Taskbook: `kernel-baseline/round61/AGENT_TASKBOOK_PHASE_E_READONLY_SECOND_AI.md`, blob `09611b1d3e9be1d809ccdbea82d85493d8ffe6ee`, issued 2026-11-25T02:20:01Z by the Second AI
Target: Huawei MatePad 11 (2021), DBY-W09, HOS4.3
Mode: local, offline, read-only evidence triage. No device operation of any kind.

## 0. Result in one paragraph

Both required evidence packages are **BLOCKED**, for the exact reasons the taskbook anticipated. (A) The only candidate final post-ABL FDT capture, `/sys/firmware/fdt`, was attempted in ROUND2 and failed with `adb: error: failed to stat remote object '/sys/firmware/fdt': Permission denied`; its SHA-256 sidecar explicitly says NOT AVAILABLE. No other authorized local artifact is a post-ABL capture, and the stock base FDT already inspected in ROUND7/19 is a pre-ABL template with an all-zero `/memory` reg placeholder. (B) No board-specific schematic, PMIC power tree, or HOS4.3 final DT with explicit `vin-supply` / `vdd-s*-supply` / `vph-pwr-supply` exists in the authorized local corpus. Per the taskbook, an inferred map, an HOS4.2 public reference, a kernel-driver dummy-supply fallback, or a translation of ARC/proxy edges into electrical parents is **not** an acceptable substitute. No value was fabricated; no device access was attempted.

## 1. Per-field status

### Required output A — final ABL-to-Linux memory handoff

| Field | Status | Evidence |
|---|---|---|
| Source / firmware build identity | PARTIAL | HOS4.3 DBY-W09 identified by ROUND2 inventory and ROUND3 stock FDT `compatible = "qcom,kona-qrd", "qcom,kona"`. Exact firmware package revision: UNKNOWN. |
| Capture method and privilege level | BLOCKED | ROUND2 attempted `adb pull /sys/firmware/fdt`; failed `Permission denied`. Capture method exists in principle, privilege was insufficient. |
| Why this is the final post-ABL handoff | BLOCKED | No capture exists, so no artifact can be established as the final ABL→Linux FDT. |
| Entry path: classic FDT / EFI stub / unknown | UNKNOWN | ROUND20 showed the ROUND18 Image is a genuine PE/COFF EFI application, but also showed the *stock* kernel payload has no PE header, so it cannot take the EFI stub entry. The real HOS4.3 ABL entry decision remains unobserved. |
| Root cells | BLOCKED | Not available from a final capture. |
| RAM nodes and exact tuples | BLOCKED | Not available from a final capture. The stock base FDT has an all-zero `/memory` reg placeholder, which is a template value, not a handoff value. |
| Reserved-memory node count | BLOCKED | The stock base FDT holds 34 children, but no final post-ABL count/attribute set is available. |
| Reserved-memory ranges/attributes | BLOCKED | Same as above. |
| Chosen memory-related properties | BLOCKED | ROUND19 reported the stock base `/chosen` has only a bootargs string and no `linux,uefi-*` properties; final values unobserved. |
| Range-overlap/reconciliation result | BLOCKED | Cannot reconcile ranges that were never captured. |
| Unresolved fields | PASS | All fields above are explicitly unresolved; none were guessed. |
| Evidence file paths and SHA-256 | PARTIAL | Local inventory identifiers and hashes below; no final-capture hash exists. |

Verdict for output A: **BLOCKED — final ABL memory handoff unavailable**. Path A (classic FDT) has no sanctioned final FDT capture. Path B (EFI stub) has no evidence that HOS4.3 ABL actually enters via the EFI stub, no `linux,uefi-system-table` capture, and no UEFI memory-map descriptors tied to this kernel entry. ROUND20's kernel-source proof that the EFI path *can* rebuild memblock from UEFI descriptors does not establish that HOS4.3 *uses* that path; the taskbook explicitly forbids reporting Path B as proven merely because the kernel has EFI support.

### Required output B — PM8150 physical input-parent topology

| Field | Status | Evidence |
|---|---|---|
| Board revision / source identity | PARTIAL | Board DBY-W09 identified; specific board hardware revision UNKNOWN. No schematic/power-tree source present. |
| PMIC ID and output rail | PARTIAL | Six UFS-consumer rails are identifiable by name from ROUND3 base FDT: PM8150 L5, L6, L9, L17, S4 and PM8150L S8 (ROUND21 overlay audit). Their physical input parents are not stated there. |
| Rail class (VRM / XOB / ARC / proxy) | PARTIAL | HOS base FDT carries vendor `qcom,regulator-type` / `qcom,supported-modes`; ROUND13 audited these as vendor semantics, not physical topology. Distinguishing VRM vs ARC level vs proxy consumer requires the authoritative source that is missing. |
| Explicit physical input parent | BLOCKED | No `vdd-s1..s10-supply`, `vin-supply`, or `vph-pwr-supply` was found in the inspected stock FDT scope (ROUND13 global census: 0 hits for upstream mode properties; ROUND21 also reported no explicit input-parent properties). |
| Upstream provider | BLOCKED | Same as above. |
| Source path + page/node/property | BLOCKED | No authoritative board-specific engineering source in the authorized corpus. |
| Voltage/current evidence | UNKNOWN | Vendor mode/current-threshold properties exist in the stock FDT (ROUND13) but are not physical electrical input evidence. |
| Firmware/ABL handoff notes | UNKNOWN | No explicit documentation. |
| Is this a real electrical edge? | BLOCKED | Cannot be established. ARC proxy-supply and `qcom,vccq-parent-supply` are consumer-side voltage-level dependencies; converting them into parent regulators is expressly prohibited. |
| Unresolved facts | PASS | All physical input edges remain unresolved; none were invented. |
| Evidence file paths and SHA-256 | PARTIAL | Local identifiers below. |

Verdict for output B: **BLOCKED — PM8150 physical parent not established**. No `vph_pwr = 3.7 V` assumption, guessed `vdd-s*-supply`, fake fixed regulator, or proxy-to-parent translation was introduced.

## 2. Evidence actually inspected (sanitized identifiers)

- ROUND2 `device/live_dtb_status.txt` — contains the failed `adb pull /sys/firmware/fdt` transcript. No raw device identifiers published here.
- ROUND2 `device/live.dtb.sha256` — content: `NOT AVAILABLE: live.dtb could not be pulled read-only (see live_dtb_status.txt).`
- ROUND3 `dtb_work/boot_fdt_candidate_0.dtb` — prior-round stock base FDT work copy. ROUND19 audit: `/memory` reg all zero; `/chosen` bootargs only; 34 `/reserved-memory` children. This is a **pre-ABL template**, not a final handoff.
- ROUND19 `logs/boot_headers.json`, `logs/ramdisk_inventory.json`, `logs/dtbo_audit.json` — prior-round local inventory outputs, reused unchanged. Not new parsers, not final-handoff evidence.
- ROUND13 `round13_pm8150_mode_drms_findings.txt` — prior-round read-only stock-FDT regulator mode census, reused as evidence of what the base FDT does and does not contain. It does not establish electrical input parents.

No evidence file was modified. No raw firmware bytes, keys, signatures, salts, digests, rollback indexes, serial numbers, MAC addresses, IMEIs or user identifiers are reproduced.

## 3. Narrowest outstanding request

One narrow request would unblock output A: a sanitized capture of the **final** FDT passed to the Linux entry point on this exact board (`/sys/firmware/fdt` or equivalent), obtained through an already-authorized read-only route with sufficient privilege, plus a statement of how it was captured and why it is the final post-ABL blob. This round did not attempt to obtain it and did not change any device state.

One narrow request would unblock output B: an authoritative, board-specific PMIC power tree or schematic page for DBY-W09 that explicitly names the physical input of PM8150 L5/L6/L9/L17/S4 and PM8150L S8.

## 4. Limits observed

- No device connection, ADB, fastboot, reboot, unlock, root, flash, partition write, mount-write or regulator change.
- No installation, download, or new binary. No security-policy bypass or privilege escalation.
- No inferred addresses, rail parents, voltage values, offsets or phandles.
- No modification to the board DTS draft, source, config, Kconfig, DTS, DTBO, boot image or AVB metadata.
- No change to Phase E status: it remains BLOCKED pending the two authoritative inputs above.
