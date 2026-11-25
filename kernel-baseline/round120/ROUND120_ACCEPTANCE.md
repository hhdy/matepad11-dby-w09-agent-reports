# ROUND120 — 1号 AI：UFS per-HBA async scan join implementation accepted after independent validation

**Owner / patch author:** 1号 AI（ChatGPT）  
**Independent executor:** 用户本地测试 Agent（只测试，不编写实现）  
**Pinned ACK:** `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (`android17-6.18.33_r00`)  
**Validation report:** [TEST_AGENT_ROUND116_UFS_ASYNC_DOMAIN_REPORT.txt](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round116/TEST_AGENT_ROUND116_UFS_ASYNC_DOMAIN_REPORT.txt)  
**Validated patch SHA-256:** `12efbe8a14d80f8b657bad763a344b5439abeb572158079beb32daba05e02bc7`  
**Patch Git blob:** `f604c8672fcbc98f3e9645f5e8888c8a34b1c11e`

## 1. Result

The per-HBA async-domain join candidate passes the independent test gate. The patch remains an isolated 1号 AI candidate and is **not** merged into the 2号 AI Stage A branch or any protected branch.

Implementation:
- Stores a registered `struct async_domain`, scan cookie and scheduled flag in the existing `struct ufs_hba_priv`; public `struct ufs_hba` is unchanged.
- Initializes the domain in `ufshcd_alloc_host()` before any scan can be scheduled.
- Replaces the discarded default-domain `async_schedule()` cookie with `async_schedule_domain()`.
- Joins only this HBA's UFS-owned scan at the first functional boundary of `ufshcd_remove()` using `async_synchronize_cookie_domain(cookie + 1, domain)`, before reading HBA fields or tearing down host/IRQ/PHY/regulator resources.
- Leaves unrelated SCSI async work and the default global async domain unchanged.

## 2. Independent validation

| Gate | Result |
|---|---|
| `git apply --check` at pristine pinned source | PASS; zero offset/fuzz |
| `git apply` and `git diff --check` | PASS |
| `git apply --check` with Stage A series already present | PASS |
| Required source-flow checks | 8/8 PASS |
| `checkpatch.pl --strict` | PASS with notes: 0 errors, 4 preamble-comment warnings, 1 alignment check |
| Patched `drivers/ufs/core/ufshcd.o` compilation | PASS |
| Full `tools/bazel build //common:dby_w09` | PASS, `BUILD_RC=0` |
| Disposable build workspace restored | PASS |

The patched object was distinguished from the pristine control in the same output directory: the patched object contains exactly one relocation to `async_synchronize_cookie_domain` inside `ufshcd_remove()` and one relocation to `async_schedule_node_domain`; the pristine object contains neither. Re-applying and recompiling reproduced the patched object hash byte-for-byte.

Full Image build artifacts (not uploaded):
- Image: 44,820,992 bytes; SHA-256 `f2aa719fddfddc1f20097bcf53fac5833813a92e5fadff1f6229969667c3d750`
- System.map: 7,611,344 bytes; SHA-256 `4f27b6fa8cf946bbc605a96b0db5bfed529f6d4a0d4e9b2e2e15e0a89edda7bd`
- vmlinux: 230,248,672 bytes; SHA-256 `8354c8d126c4a760aa02ba31a33e172d35133e2336501d86dea65e4d15516867`
- .config: 238,410 bytes; SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`

The .config is byte-identical to the Stage A baseline; the candidate adds no configuration changes. The Image links the candidate plus the Stage A series. This is compile/link validation only, not device boot or UFS hardware acceptance.

## 3. Remaining notes

- The checkpatch notes are style diagnostics only; the tester did not edit the candidate, per the test-only role boundary.
- No device, ADB, fastboot, partition, boot, DTBO, AVB or firmware operation was performed.
- The patch is **validated as an isolated source change**, but not yet integrated into `ai-parallel/stagea-port-until-boot`. Integration must be coordinated with 2号 AI to avoid overlapping changes in `ufshcd.c` or `ufshcd-priv.h`.
- Stage A Phase E/F remain BLOCKED and Phase G remains NOT RUN. A successful Image link does not prove bootability.

## 4. Files in this branch

- `kernel-baseline/round120/0001-ufs-core-per-hba-async-domain.patch`
- `kernel-baseline/round120/TEST_AGENT_ROUND116_UFS_ASYNC_DOMAIN_REPORT.txt`
- `kernel-baseline/round120/ROUND120_ACCEPTANCE.md`

Disposition: **ACCEPTED for source implementation and independent full Image build validation; not hardware validated and not merged into AI2 Stage A.**
