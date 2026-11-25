# ROUND124 — AI1 combined UFS core candidate validation review

- Owner: 1号 AI（ChatGPT）
- Test executor: 本地只读测试 Agent
- Result: **ACCEPTED AS AN ISOLATED BUILDABLE CANDIDATE**
- Test report: firmware-analysis/round124/TEST_AGENT_ROUND124_COMBINED_UFS_CORE_REPORT.txt
- Report blob: 2d996df465a6b9a8bb1dc627866998b3436f322b
- Fixed ACK: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Stage A 15-patch baseline: ai-parallel/stagea-port-until-boot@5f587aaa40853cf3ec754f7455930aa404bf9b9a; ROUND33 patch 16 excluded.

## 1. Accepted candidate identity

| Order | Patch | Git blob | SHA-256 |
|---|---|---|---|
| 1 | kernel-baseline/round124/0001-ufs-core-per-hba-async-domain.patch | f604c8672fcbc98f3e9645f5e8888c8a34b1c11e | 12efbe8a14d80f8b657bad763a344b5439abeb572158079beb32daba05e02bc7 |
| 2 | kernel-baseline/round124/0002-ufs-core-vreg-load-first.patch | 64dd2ad9022251e2411a1a745aeb920a0badfa85 | 2f335f513fd1f7013a0edbc2e0d9eb5dca9ae68055eff4fd526b1c4274cfca66 |

Patch 0002 is byte-identical to ROUND122. Both patches were applied in the required order.

## 2. Independent Agent validation

PASS:
- Exact patch identity and 15-patch Stage A baseline; ROUND33 patch 16 was not present.
- Sequential apply-check, apply, and diff-check for both patches: all return codes zero, zero offsets, zero fuzz.
- Exact overlay scope: only drivers/ufs/core/ufshcd-priv.h and drivers/ufs/core/ufshcd.c.
- All six async lifetime source gates and all four VCC load/disable source gates.
- All UFS core object compilation: make -j8 drivers/ufs/core/ RC=0; ufshcd.o contains async_synchronize_cookie_domain.
- Full tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144: BUILD_RC=0.
- .config byte-identical to Stage-A-only baseline, SHA-256 0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15.
- Workspace restoration byte-verified: dirty paths returned to 16 and tracked-diff SHA-256 exactly 613e7ea4bcd826b732cb13ed27f7374f7e114a8e527232f02336be4a636f2aed.
- No device connection or prohibited actions.

The full build artifacts were:
- Image 44,820,992 bytes, SHA-256 903164d7f1c78dc80435e569e6037abe7c38ab582fbb21263f0211d79c35d6bc;
- System.map 7,611,626 bytes, SHA-256 af847d632b7a301fd98669c0e90ef4e781b4ef5e773bdd412f3d7b564061c906;
- vmlinux 230,263,296 bytes, SHA-256 37aec9ae5fcbb18dc8e58854d295f81d573732791c017ba770471286ee42ffb5.

## 3. Checkpatch disclosure

Both patches had zero errors, but neither checkpatch command returned zero:
- Patch 0001: 0 errors, 4 warnings, 1 CHECK, RC=1 (four commit-log # warnings; one alignment CHECK).
- Patch 0002: 0 errors, 0 warnings, 2 CHECKs, RC=1 (alignment CHECKs inherited from the validated ROUND122 candidate).

No automatic repair was made. These findings remain visible and should not be restated as a completely checkpatch-clean series.

## 4. Disposition and boundaries

ROUND124 may be treated as an independently validated, full-Image-buildable AI1 candidate series over the 15-patch Stage A baseline. It is not integrated into AI2 Stage A and must not be merged automatically.

This candidate closes two software-side tasks:
1. per-HBA private async-domain join for the UFS-owned async scan, before UFS teardown;
2. UFS generic VCC disable load-zero ordering, to avoid the known nonzero-load post-decrement DRMS failure.

It does not close every generic regulator post-decrement failure or the managed put/nonzero-enable-count problem. It does not prove board memory handoff, PM8150 physical input topology, ABL DTBO selection, boot packaging, physical UFS rails, actual device boot or hardware operation. Phase E/F remain BLOCKED and Phase G remains NOT RUN.

ROUND125 is built on the same separate AI1 candidate workflow and is not implied to have passed any Agent validation.
