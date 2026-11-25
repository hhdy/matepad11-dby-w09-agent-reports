# ROUND124 — 1号 AI：UFS core 双候选组合审查

**Owner / patch author:** 1号 AI（ChatGPT）  
**Validation executor:** 用户本地测试 Agent（只执行验证和构建，不编写内核代码）  
**Purpose:** 将已经分别完成 Agent 构建验证的 ROUND120 与 ROUND122 串成一个独立候选，验证它们在同一 Stage A 工作树中的共同效果。  
**Pinned ACK:** `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (`android17-6.18.33_r00`)  
**Candidate branch:** `ai1/round124-ufs-core-combined-candidates`

## 1. Combined patch sequence

Apply in this exact order:

1. `0001-ufs-core-per-hba-async-domain.patch` — copied byte-for-byte from validated ROUND120 blob `f604c8672fcbc98f3e9645f5e8888c8a34b1c11e`, SHA-256 `12efbe8a14d80f8b657bad763a344b5439abeb572158079beb32daba05e02bc7`.
2. `0002-ufs-core-vreg-load-first.patch` — copied byte-for-byte from validated ROUND122 blob `64dd2ad9022251e2411a1a745aeb920a0badfa85`, SHA-256 `2f335f513fd1f7013a0edbc2e0d9eb5dca9ae68055eff4fd526b1c4274cfca66`.

The order is deliberate. ROUND120 touches later regions of `ufshcd.c` (remove/alloc/init); ROUND122 changes the earlier regulator helper block. Applying ROUND120 first, then ROUND122, preserves the original line/context location for the ROUND122 hunk and is expected to allow zero-offset application. Do not reverse the order or hand-edit hunk headers.

## 2. Scope of each candidate

### ROUND120 — per-HBA UFS async scan join

- Adds `async_domain`, scan cookie and a scheduled flag to private `struct ufs_hba_priv`; public `struct ufs_hba` remains unchanged.
- Initializes the domain in `ufshcd_alloc_host()` using the same pending-list / registered semantics as ACK's `ASYNC_DOMAIN` macro.
- Replaces the discarded global-domain `async_schedule()` cookie with `async_schedule_domain()`.
- At the first functional point in `ufshcd_remove()`, joins only this HBA's scan through `async_synchronize_cookie_domain(cookie + 1, domain)`, before reading or tearing down HBA resources.
- ROUND120 Agent validation previously passed: patch apply, source gates 8/8, UFS object compile, full Stage A Image build. It remains isolated and not merged into AI2.

### ROUND122 — UFS regulator load-first disable

- Applies load-zero configuration while the consumer enable reference is still held; a load/DRMS error returns before `regulator_disable()`.
- Clears `vreg->enabled` only after successful `regulator_disable()`.
- Reapplies active load before the already-enabled fast path, allowing load restoration when a prior disable error retained the enable reference.
- ROUND122 Agent validation previously passed: exact apply, `ufshcd.o`, full `//common:dby_w09` Image build. `checkpatch --strict` reported 0 errors, 0 warnings, 2 CHECKs (RC=1); those findings were not silently fixed.

## 3. Fixed-source cross-review

Against the pinned ACK source:

- `include/linux/async.h` defines `struct async_domain { pending, registered }`; the per-HBA initialization matches the `ASYNC_DOMAIN` initializer fields. `async_schedule_domain()` records the entry in the domain pending list; `async_synchronize_cookie_domain(cookie + 1, domain)` waits until the work entry at `cookie` has completed.
- ROUND120's three core edit areas are in `ufshcd-priv.h` and later `ufshcd.c` lifecycle/scheduling locations. ROUND122 changes only the earlier `ufshcd_enable_vreg()` / `ufshcd_disable_vreg()` helper block in `ufshcd.c`. There is no textual hunk overlap. The required order above must still be proven by real Git apply.
- ROUND122 is not a complete regulator error-lifetime fix. Fixed ACK still permits errors after consumer `enable_count` decrement from coupled-voltage balancing or recursive parent-supply disable. UFS can retain `vreg->enabled == true` after such an error even if the core count has already changed. `ufshcd_hba_exit()` ignores setup-vreg shutdown errors and devm release later calls `regulator_put()`, which warns on nonzero count but still destroys the handle. See [ROUND123 audit](../round123/round123-1ai-regulator-disable-post-decrement-error-audit.md). These remain explicit limitations, not claimed fixed.
- Neither candidate validates DBY-W09's physical PM8150 parent topology or runtime regulator behavior.

## 4. Stage A overlay baseline

The full combined validation must use the already validated AI2 ROUND32 Stage A source stack of 15 patches, whose ordered record is `kernel-baseline/round61/round32-stagea-series.txt` on `ai-parallel/stagea-port-until-boot`, at AI2 branch head `5f587aaa40853cf3ec754f7455930aa404bf9b9a` (ROUND61 evidence published). The Stage A stack's immutable ACK base is the same pinned commit above.

Do not include the unverified AI2 ROUND33 patch 16 (`round33-0001-regulator-proxy-self-target-only.patch`) in this round. It is a separate 2号 AI change whose local apply/build checks were still pending at the time this candidate was prepared. Do not alter AI2's branch.

## 5. Required Agent verification

See `TEST_AGENT_ROUND124_TASKBOOK.md`. Agent must validate the candidates byte-for-byte, on a disposable copy of the exact Stage A ROUND32 15-patch tree, and must not edit the candidates.

## 6. Acceptance boundary

If combined apply, source gates, UFS object compilation and complete Kleaf Image build all pass, ROUND124 may be accepted as a **combined buildable AI1 candidate**. This does not authorize integration into the AI2 branch, modify board DTS, close Phase E/F, or claim hardware/boot validation. Phase E/F remain BLOCKED and Phase G remains NOT RUN pending their separate boot-path and hardware evidence.
