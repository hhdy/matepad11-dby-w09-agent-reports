# ROUND11 — HOS4.3 PM8150 RPMh parent-supply topology (read-only)

## Objective

Resolve one precise DTS question from the user's existing local HOS4.3 base boot FDT: do the PM8150 RPMh regulator provider groups under apps_rsc declare parent input-supply relationships, and if so, what are their phandle target nodes?

This is needed because the current ACK DTS draft intentionally removed a speculative fixed vph_pwr = 3.7 V node and vdd-s1-supply ... vdd-s10-supply links. The same-device public Linux 7.0 DTS says its PMIC supply topology was checked against HOS4.2, not the user's HOS4.3, so it must not be copied without local confirmation.

## Scope

Inspect only the already-existing HOS4.3 base boot-FDT candidate(s) and the PM8150 RPMh provider properties needed to resolve:
- /soc/rsc@18200000 (or equivalent provider path) and its PM8150 regulator child groups;
- vdd-s1-supply through vdd-s10-supply, vin-supply, *-supply, or any documented equivalent parent/input relationship;
- each present property's phandle target path and whether that target is a fixed regulator, PMIC rail, or another provider;
- if available without expanding scope, whether the same input is repeated consistently on the relevant PM8150 provider groups.

Do not enumerate unrelated regulator rails, PMIC GPIOs, devices, peripherals, or complete DTB contents.

## Tool and safety gate

1. Use only a read-only FDT inspection tool that is already installed, trusted, and auditable on this machine, or a previously reviewed extraction/report function already present in the existing workflow.
2. If no such tool/function is available, stop and report BLOCKED. Do not install or download anything; do not execute unknown EXE/DLL; do not write a parser; do not use WSL; do not change PowerShell or Windows security policy.
3. Do not inspect/re-extract ramdisk or EROFS. Do not repeat ROUND1–ROUND10.
4. No device connection, ADB, fastboot, unlock, root, flash, partition write, module load, writable mount or compile.
5. Do not output/upload DTB/DTBO/FDT, binary fragments, complete local file paths, complete local checksums, serial/MAC/IMEI, tokens or any sensitive values.

## Required result

Create only short sanitized text report(s) under firmware-analysis/round11/ on branch firmware-audit-v1.

Report:
- whether a suitable already-installed trusted tool was found (tool name/version only if safe);
- exact scope inspected (base FDT only; don't publish local absolute path);
- FOUND: property name, sanitized parent node path, and relevant generic voltage if useful;
- NOT_FOUND_IN_INSPECTED_SCOPE: only if the tool successfully inspected the entire relevant provider node/property set;
- BLOCKED: if tool unavailable, FDT candidate unreadable, phandle resolution not supported, or scope incomplete;
- UNKNOWN: any target that cannot be resolved;
- explicit NOT_RUN for any part not attempted.

Do not interpret a missing item in the old 7,939-row CSV as proof it is absent from the raw FDT. Do not infer HOS4.3 topology from the HOS4.2 Linux 7.0 public DTS.

## Stop condition

After committing the sanitized text report on firmware-audit-v1, stop. Do not update main, the ACK draft branch, or PR #1.
