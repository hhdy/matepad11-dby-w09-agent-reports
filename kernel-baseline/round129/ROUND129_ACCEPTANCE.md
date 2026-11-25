# ROUND129 — AI1 combined UFS rail lifecycle candidate acceptance

**Disposition: ACCEPTED as an isolated, buildable AI1 candidate series.**

## Candidate identity

This branch is based on the exact validated Stage A snapshot:
`2f21233148a04afdd61e44b1be7688399967d9d0`, itself based on pinned ACK
`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.

The candidate overlay is exactly 2 patches after the existing 17-patch series:

1. ROUND128 V2 — QMP UFS dual-rail state, Git blob
   `22ccec1cabf2d78e61442d19219985135f8341e7`, SHA-256
   `53ef42bb997a46e776f65c256039b13285047f784fed506ab8b22ab7f76e3bfb`.
2. ROUND126 — proxy-consumer load-first teardown, Git blob
   `c180dbf458403d68b2c32c1d54776a7559e7e5db`, SHA-256
   `eae21b96d34ebff0e7bbd4843bcd4f96cda26b02f83dd6f323b8c571e51fef80`.

The exact copy and apply order are recorded in `round129-ai1-series.txt`.

## Independent validation

Agent report: [ROUND129 combined report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round129/TEST_AGENT_ROUND129_COMBINED_REPORT.txt), blob `ab49a598194aae6af5a13772c62731dcac7a6690`.

All required technical gates passed on the actual 19-patch tree:
- candidate patch identities matched, sequential applies and diff-checks passed;
- ROUND128 V2 has exactly one `qmp_ufs_power_off()` definition, inherited from ROUND63;
- ROUND128 and ROUND126 source gates passed;
- host tests: 38/38 and 83/83;
- both target objects compiled successfully;
- fresh full Kleaf build `//common:dby_w09`: BUILD_RC=0, elapsed 373s;
- .config remained byte-identical to Stage A-only baseline, SHA-256
  `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`;
- ROUND58 config validation 33/33 and helper tests 11/11;
- candidate overlay reversed and tracked-diff hash restored to the exact 17-patch baseline identity.

## Build artifacts

Not uploaded; hashes retained for identification:
- Image, 44,820,992 B:
  `2cbc52182c2addefbfa0bb91eb27953f1c5444ee4fefb51c6b7626af20c0ba35`
- System.map, 7,611,528 B:
  `8db5aed4b083a37b6939ac74474833789d3113e45a97f99afed4fecbe8ca2ad3`
- vmlinux, 230,251,360 B:
  `a8a18801058e903566ad1d14d4422cf6b8c7af6fcb484b0c6b1fe72964f42e2a`

## Checkpatch

Do not represent the candidate as zero-warning/zero-check:
- ROUND128 V2: RC=1, 0 errors, 1 warning (commit message line exceeds 75 characters), 0 CHECKs.
- ROUND126: RC=1, 0 errors, 0 warnings, 1 CHECK (existing `current_uA` CamelCase field).

These are recorded as style findings, not silently changed during Agent validation.

## Technical limits and project disposition

This acceptance is limited to source gates, mock host lifecycle tests, object compilation, full image build and config regression. It does not prove runtime PMIC behavior, physical rail voltages, ABL-selected DTBO, final FDT/EFI memory map, boot, or hardware stability.

The generic regulator post-decrement / parent-coupling uncertainty remains. A void devm cleanup action cannot veto later managed `regulator_put()`; persistent failure may still generate an outstanding-enable warning.

No tablet was connected and no device command was issued. **Phase E and Phase F remain BLOCKED; Phase G remains NOT RUN.** This candidate is not merged into AI2 Stage A and must not be treated as final hardware acceptance.

## Cleanup note

The Agent restored the source tree to the exact 17-patch baseline and removed object output and temporary logs. It intentionally retained its independent staging tree and Bazel artifacts as evidence; no other workspace was modified. This retained evidence is local only and no binaries were uploaded.
