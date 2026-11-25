# ROUND124 Acceptance — Combined AI1 UFS Core Candidate

Date: 2026-11-25  
Owner: 1号 AI（ChatGPT）  
Independent executor: 用户本地测试 Agent  
Candidate branch: `ai1/round124-ufs-core-combined-candidates`  
Pinned ACK: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
Stage A base: `ai-parallel/stagea-port-until-boot@5f587aaa40853cf3ec754f7455930aa404bf9b9a` (ROUND32 15-patch state)

## Validation evidence

Agent report: [TEST_AGENT_ROUND124_COMBINED_UFS_CORE_REPORT.txt](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round124/TEST_AGENT_ROUND124_COMBINED_UFS_CORE_REPORT.txt), blob `2d996df465a6b9a8bb1dc627866998b3436f322b`.

| Gate | Result |
|---|---|
| Candidate patch identities | PASS — both Git blob and SHA-256 match expected values |
| Stage A baseline | PASS — exact ROUND32 15-patch state; AI2 ROUND33 patch 16/17 excluded |
| Sequential apply | PASS — ROUND120 then ROUND122; zero offset/fuzz; apply/check/diff-check return codes all 0 |
| Overlay scope | PASS — only `drivers/ufs/core/ufshcd.c` and `drivers/ufs/core/ufshcd-priv.h` added to the baseline diff |
| ROUND120 source gates | PASS — private async domain, guarded cookie join at start of remove, call-site review |
| ROUND122 source gates | PASS — load-zero before regulator_disable; known partial-disable/devm limitation retained |
| UFS core object compilation | PASS — all seven objects under `drivers/ufs/core/` compiled |
| Full Kleaf Image build | PASS — `tools/bazel build //common:dby_w09 --jobs=8 --local_ram_resources=6144`, BUILD_RC=0 |
| .config identity | PASS — SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`, byte-identical to Stage A-only |
| Workspace restoration | PASS — dirty paths returned to 16 and tracked diff SHA-256 exactly restored to `613e7ea4bcd826b732cb13ed27f7374f7e114a8e527232f02336be4a636f2aed` |
| Device policy | PASS — no tablet connection, ADB, fastboot, partition, boot, flash, DTBO, AVB or firmware operation |

### Built artifacts

- Image: 44,820,992 bytes; SHA-256 `903164d7f1c78dc80435e569e6037abe7c38ab582fbb21263f0211d79c35d6bc`.
- System.map: 7,611,626 bytes; SHA-256 `af847d632b7a301fd98669c0e90ef4e781b4ef5e773bdd412f3d7b564061c906`.
- vmlinux: 230,263,296 bytes; SHA-256 `37aec9ae5fcbb18dc8e58854d295f81d573732791c017ba770471286ee42ffb5`.
- .config: 238,410 bytes; SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`.

### Checkpatch findings — disclose, do not erase

- Patch 0001: 0 errors, 4 warnings, 1 CHECK; exit code 1.
- Patch 0002: 0 errors, 0 warnings, 2 CHECKs; exit code 1.

These are style diagnostics, not compile failures. They were not corrected in this test because the Agent was validation-only. Do not describe checkpatch as RC=0 or warning-free.

## Evidence completeness note

The uploaded Agent report records Clang as Android clang 22.0.1 based on r584948c, but it does **not** explicitly record all metadata required by the taskbook: manifest commit, manifest-pinned.xml SHA-256, Rust version, and Bazel version. Therefore:

- Source/apply/object/Image-build validation: **PASS**.
- Full build-environment metadata documentation: **PARTIAL / missing fields**, pending recovery from the exact workspace/build logs.
- Do not fabricate the missing values or substitute an unrelated run's metadata without proving the workspace identity.

This reporting gap does not invalidate the reported successful build, but it remains an evidence-completeness item.

## Disposition

**ACCEPTED as an isolated, combined, buildable AI1 candidate.** This acceptance means the two patches coexist on the Stage A ROUND32 source stack and pass the recorded source/object/Image gates. It does not prove hardware behavior, bootability, actual UFS rail sequencing, or full regulator teardown safety.

The ROUND122 limitation from ROUND123 remains: regulator core may return errors after an enable-count decrement (e.g. coupled voltage balancing or recursive parent supply disable), and UFS/devm teardown can still leave a handle lifetime hazard. This patch changes UFS load ordering, but does not solve every regulator partial-disable path.

Do not merge these patches into the AI2 Stage A branch automatically. Integration requires a separately reviewed coordination step with 2号 AI because both candidate patches touch `drivers/ufs/core/ufshcd.c` and ROUND120 also touches `ufshcd-priv.h`.

Stage A Phase E/F remain BLOCKED on firmware/ABL/memory/PM8150 physical-topology and packaging facts; Phase G remains NOT RUN. No device testing occurred.
