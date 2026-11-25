# ROUND128 — QMP UFS dual-rail state candidate V2 review

- Owner / author: **1号 AI（ChatGPT）**
- Candidate branch: `ai1/round128-qmp-ufs-rail-state-v2`
- Fixed ACK: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`
- Required Stage A base: `ai-parallel/stagea-port-until-boot@2f21233148a04afdd61e44b1be7688399967d9d0`
- Candidate patch: `kernel-baseline/round128/0001-qmp-ufs-rail-state-v2.patch`
- Patch Git blob after final stat correction: `22ccec1cabf2d78e61442d19219985135f8341e7`
- Patch SHA-256: to be independently recorded by ROUND129 Agent from the exact fetched bytes.
- Changed path: `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c` only.

## 1. Why V2 exists

ROUND127 applied the original ROUND125 patch cleanly and passed its source gates, but the target object compile failed with a duplicate definition:

- new candidate definition: `qmp_ufs_power_off()` around line 2028;
- existing ROUND63 definition: `qmp_ufs_power_off()` around line 2084.

ROUND63 already owns the power-off callback and it already calls `qmp_ufs_regulators_disable(qmp)`. ROUND125/V2 replaces that helper with the per-rail state-aware implementation. Therefore adding a second callback is unnecessary and incorrect.

## 2. Exact correction

V2 is the ROUND125 candidate with the newly-added duplicate `qmp_ufs_power_off()` block removed. It retains the existing source context for `qmp_ufs_phy_calibrate()` and keeps the ROUND63 callback in place.

No state-machine logic was intentionally changed:
- two independent `vreg_enabled[2]` and `vreg_load_active[2]` bits;
- exact two-rail layout check: `vdda-phy` then `vdda-pll`;
- load restoration before enable;
- load-zero before disable;
- failed transitions preserve the last confirmed per-rail state;
- retained L5 policy and L9 cleanup order;
- managed cleanup action drains L9 before L5;
- ordinary path without `vdda-phy-always-on` remains the bulk regulator path.

The earlier ROUND127 source-gate line references are not authoritative for this V2 hunk layout; the next Agent must re-check the actual V2-patched source and report fresh line numbers.

## 3. Preserved limitations

- This change addresses the duplicate-definition compile defect only. It does not resolve or overstate the regulator-core parent/coupling failure boundary already documented in ROUND125.
- A void devm cleanup action still cannot veto the following managed regulator put; persistent provider failure may still produce a nonzero-enable-count warning.
- No physical PMIC topology, RPMh ACK, rail voltage, device boot, or runtime behavior is claimed.
- This is an isolated AI1 candidate, not an accepted Stage A integration and not a merge to AI2.

## 4. Validation state

V2 has been prepared and its unified-diff hunk counts and single-function intent were checked during authoring. **It has not yet been applied to the 17-patch baseline, compiled, or built.** ROUND129 is the required independent verification.

ROUND127 historical result:
- ROUND126 passed its individual gates, including `proxy-consumer.o`.
- ROUND125 original failed `phy-qcom-qmp-ufs.o` because of the duplicate callback.
- full Image build and ROUND58 regression were not run due to the stop rule.

The ROUND129 taskbook requires a fresh combined run of V2 + ROUND126 on the exact 17-patch Stage A baseline. No previous PASS is carried forward as a substitute for the combined build.
