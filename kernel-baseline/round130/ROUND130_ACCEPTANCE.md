# ROUND130 — Four-patch UFS lifecycle integration acceptance

- **Disposition: ACCEPTED as an isolated, buildable AI1 candidate series.**
- Owner / reviewer: 1号 AI (ChatGPT)
- Test executor: user-local WorkBuddy test Agent
- Agent report: [TEST_AGENT_ROUND130_COMBINED_REPORT.txt](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round130/TEST_AGENT_ROUND130_COMBINED_REPORT.txt)
- Report blob: `def62019b5760d991f41d674e227b9e1af0761df`
- Tested Stage A base: `ai-parallel/stagea-port-until-boot@2f21233148a04afdd61e44b1be7688399967d9d0`
- Immutable ACK: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (`android17-6.18.33_r00`)

## Integrated series

The exact 17-patch Stage A series was followed by these four byte-identified AI1 candidates, in this order:

| Series position | Candidate | Origin blob | SHA-256 |
|---|---|---|---|
| 18 | ROUND120 per-HBA async scan join | `f604c8672fcbc98f3e9645f5e8888c8a34b1c11e` | `12efbe8a14d80f8b657bad763a344b5439abeb572158079beb32daba05e02bc7` |
| 19 | ROUND122 UFS regulator load-first | `64dd2ad9022251e2411a1a745aeb920a0badfa85` | `2f335f513fd1f7013a0edbc2e0d9eb5dca9ae68055eff4fd526b1c4274cfca66` |
| 20 | ROUND128 V2 QMP UFS dual-rail state | `22ccec1cabf2d78e61442d19219985135f8341e7` | `53ef42bb997a46e776f65c256039b13285047f784fed506ab8b22ab7f76e3bfb` |
| 21 | ROUND126 proxy-consumer load-first | `c180dbf458403d68b2c32c1d54776a7559e7e5db` | `eae21b96d34ebff0e7bbd4843bcd4f96cda26b02f83dd6f323b8c571e51fef80` |

The 17 base patch identities and all four candidate identities matched. All 21 patches applied in order; `git apply --check`, apply, and `git diff --check` passed with zero fuzz. The report records existing-series offsets and the ROUND128 V2 hunk offset (-19 lines); no candidate was fuzz-applied.

## Validation results

- Source gates: ROUND120 async lifecycle, ROUND122 UFS regulator ordering, ROUND128 V2 QMP rail state, and ROUND126 proxy-consumer load-first all PASS.
- Host tests: 38/38 legacy lifecycle checks and 83/83 ROUND32/33 checks; no failures or crash.
- Target objects: 9/9 compiled successfully (7 UFS core objects, QMP UFS PHY, proxy consumer).
- Full Kleaf build: `//common:dby_w09`, `BUILD_RC=0`, elapsed 368s.
- Config: SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`, byte-identical to the Stage A baseline.
- ROUND58 regression: storage config 33/33 and helper tests 11/11 PASS.
- Image: 44,820,992 bytes, SHA-256 `4ef82e03b2300fa37abc7927474d0f2357b27ca1e80ddf658b63a79f44c804f1`.
- System.map SHA-256: `3887cd87acc7e07dfe27abc14e5ddd54a1e767cd9043bf9b4`.
- vmlinux SHA-256: `1701b18ff918d0654ff155f72cbdca09e21636e008281a9961`.

Checkpatch is not fully clean and the findings remain visible: ROUND120 0E/4W/1C (RC=1); ROUND122 0E/0W/2C (RC=1); ROUND128 V2 0E/1W/0C (RC=1); ROUND126 0E/0W/0C (RC=0). No automatic style edits were made.

## Restore and safety

The four candidates were reverse-applied in reverse order. The tracked diff SHA returned exactly to the 17-patch baseline:
`3e47464fadffa8663fa9560846d42a476d69bc6106482265f05a79aa8ad89bbf`.
Dirty-path and untracked-path sets matched the baseline; candidate residue count was zero. Disposable staging, object outputs, Bazel outputs and temporary logs were removed. The pre-existing `a30` workspace remained unchanged.

No device was connected; no USB, ADB, fastboot, recovery, serial, partition, boot, flash or root operation was performed. No binary artifact was uploaded.

## Acceptance boundary

This acceptance is limited to **an integrated, buildable AI1 candidate series**. It does not establish UFS runtime stability, actual PMIC rail behavior, final ABL-to-kernel memory/FDT/EFI handoff, selected DTBO/boot mode, successful device boot, or hardware acceptance. Stage A Phase E/F remain BLOCKED and Phase G remains NOT RUN. Do not merge this candidate into the AI2 Stage A branch automatically; AI2 remains an independent development stream.
