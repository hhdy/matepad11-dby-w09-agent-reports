# ROUND136 — ACK 6.18.33 UFS async-scan and regulator lifecycle static review

Date: 2026-11-26  
Reviewer: 1号 AI (ChatGPT)  
Target source: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
Scope: immutable source review of ROUND135 candidate patch inputs 18–21 on AI1's isolated branch. This is not a build/test/device result.

## 1. Exact candidate inputs

| Series item | Purpose | Patch blob |
|---|---|---|
| 18 / ROUND120 | Per-HBA async domain and remove-time scan join | `f604c8672fcbc98f3e9645f5e8888c8a34b1c11e` |
| 19 / ROUND122 | UFS regulator load-first enable/disable | `64dd2ad9022251e2411a1a745aeb920a0badfa85` |
| 20 / ROUND128 V2 | QMP UFS two-rail retained-state handling | `22ccec1cabf2d78e61442d19219985135f8341e7` |
| 21 / ROUND126 | Proxy-consumer load-first cleanup | `c180dbf458403d68b2c32c1d54776a7559e7e5db` |

The review used the exact fixed ACK source files listed below; the patch input identities above were read from the AI1 branch, not regenerated.

## 2. Patch 18 — per-HBA async scan lifetime

### Source facts checked

- `include/linux/async.h` blob: `19b778d08600f1d1e1bf25a8cd0e8a390b39cac5`. `struct async_domain` consists of a pending list and a registered flag. The `ASYNC_DOMAIN()` initializer sets `registered = 1`.
- `kernel/async.c` blob: `4c3e6a44595fa176f06108c869d164cca26546a1`. `async_schedule_node_domain()` queues the cookie in the domain pending list; if allocation/work limits prevent queuing, it executes the callback synchronously and returns the generated cookie. `async_synchronize_cookie_domain(cookie, domain)` waits until the earliest pending cookie in that domain is at least the supplied fence.
- `drivers/ufs/core/ufshcd.c` blob: `2cf7aa8e0a9472f9024d4251ac2f9d7da830e219`. `ufshcd_init()` takes a runtime-PM reference before scheduling the asynchronous scan; `ufshcd_async_scan()` releases that reference at completion. The scan callback uses the HBA and its host semaphore, probes the device and adds LUs.
- `drivers/ufs/core/ufshcd-priv.h` blob: `6ba126dc052824efa73a8a41540151a1e2cecaa1`. `struct ufs_hba_priv` embeds `struct ufs_hba` as its first member; the candidate's `to_hba_priv()` conversion is consistent with that layout and with `scsi_host_alloc(sizeof(struct ufs_hba_priv))` in `ufshcd_alloc_host()`.
- `drivers/ufs/host/ufshcd-pltfrm.c` blob: `5ac7afe759346debfc2910fb219d8e491ba08b64`. The standard platform remove wrapper calls `ufshcd_remove()`; the Qualcomm probe uses this common platform initialization/removal path. The remove wrapper takes a runtime-PM reference before removing the HBA.

### Review

The candidate initializes the per-HBA domain list before any scan can be scheduled and sets `registered = 1`, preserving participation in global async synchronization like the default async domain used by the original `async_schedule()`.

Only one `ufshcd_async_scan` callback is scheduled for each successful `ufshcd_init()`. Saving its cookie and waiting on `cookie + 1` is the correct fence to include that cookie: the synchronization API waits for entries strictly earlier than its fence. The wait is placed at the beginning of `ufshcd_remove()`, before runtime-PM, SCSI-host, interrupt, HBA and variant teardown. The platform remove path is serialized after probe returns, so the flag is set before the normal remove callback can run. The synchronous fallback of `async_schedule_node_domain()` is also safe for this state: the callback has already completed before the scheduling call returns, and the later join sees an empty domain.

**Disposition: PASS for static lifetime/API ordering review.** This does not establish absence of runtime races under actual controller operation; runtime stress remains unrun.

## 3. Patch 19 — UFS regulator load-first transitions

Fixed ACK source path: `drivers/ufs/core/ufshcd.c`, blob `2cf7aa8e0a9472f9024d4251ac2f9d7da830e219`.

The candidate moves load restoration before the already-enabled early return in `ufshcd_enable_vreg()`. This allows a later power-on to restore the active load if a prior disable cleared the load but a provider disable failed while leaving the enable reference held. The disable path clears the DRMS load while the consumer enable reference is still held, then calls `regulator_disable()`; it leaves `vreg->enabled` true if disable reports an error. A failed load-clear aborts before dropping the enable reference.

This ordering addresses the normal fallible DRMS transition that could otherwise occur after the regulator core decremented the consumer enable count. It relies on the target board not introducing regulator-coupling or physical parent-supply relationships that re-enable the generic post-decrement balancing/parent-disable error path.

ROUND134 already established the current candidate-DTS boundary: no `regulator-coupled-with` is specified for these UFS PM8150 rails and no physical PMIC `vdd-*-supply` parents are defined. That is only a software-tree observation; the actual PMIC electrical input topology remains UNKNOWN. If future DTS work adds coupled regulators or parent-supply links, this failure-order analysis must be repeated before accepting the state-tracking logic.

**Disposition: PASS for the intended load-first source path, conditional on the current reviewed DTS topology.** Persistent provider disable failure during final detach remains an open teardown issue, not fixed by this patch.

## 4. Patch 20 — QMP UFS two-rail state machine

Fixed ACK source files:
- `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`, blob `8af777f7ddd0385a6bb9d9b9563f0e6329699cd3`.
- `drivers/regulator/devres.c`, blob `2cf03042fddf4263d05c95e29dd534003fb8246c`.
- `drivers/regulator/core.c`, blob `39d317ad73a33c4aa27e179cc436d8bf4daf5bcc`.

The fixed SM8250 QMP UFS configuration has exactly two regulator entries, in the candidate-required order:
1. `vdda-phy`, `init_load_uA = 89900`;
2. `vdda-pll`, `init_load_uA = 18800`.

The ACK `devm_regulator_bulk_get_const()` copies the static regulator entries and calls `devm_regulator_bulk_get()`; the underlying `_regulator_bulk_get()` applies each nonzero `init_load_uA` using `regulator_set_load()`. The candidate's initial `vreg_load_active[]` state therefore matches the actual ACK bulk-get behavior, rather than assuming that the load vote is absent before the first PHY power-on.

The special path fails closed unless there are exactly two entries named `vdda-phy` then `vdda-pll`. It tracks load votes separately from enable references, clears the PLL load before dropping its enable reference, retains the PHY enable reference while clearing its idle load, restores loads before reuse, and preserves the original regulator-bulk path when `vdda-phy-always-on` is absent. The devm cleanup action is registered after managed regulator acquisition, so LIFO cleanup runs the action before the bulk regulator handles are released.

**Disposition: PASS for static SM8250 list/API/state-transition consistency.** This remains conditional on the same regulator failure boundary as patch 19. A persistent disable failure at detach is still unsafe: managed release cannot be vetoed by the cleanup action. If the board later acquires parent/coupled supply topology, post-decrement failure can also make software state diverge from the consumer enable count and requires a fresh review.

## 5. Patch 21 — proxy-consumer load-first cleanup

The candidate moves the proxy consumer's `regulator_set_load(..., 0)` ahead of `regulator_disable()`, reducing the normal risk of a DRMS update failing after the final consumer enable count is decremented.

The source deliberately continues best-effort disable if clearing the load itself fails. This is documented as a limitation because this cleanup is reached from `regulator_unregister()` and the void teardown callback cannot veto unregister. Therefore this patch must not be described as guaranteeing that the post-decrement failure path is impossible. It also explicitly does not solve a persistent provider disable failure or the managed-handle warning that may follow it.

**Disposition: PASS for the intended best-effort ordering, with the stated final-cleanup limitation.**

## 6. Overall source-review disposition and boundary

- No new source-level blocker was found in the async domain initialization/join ordering, the UFS load-first transition logic, or the SM8250 QMP two-rail list/state initialization.
- The remaining disable/teardown limitation is real and must remain visible. The board's physical PMIC parent topology is still UNKNOWN; no fabricated input rails or ARC-to-VRM equivalence may be added to make this review appear complete.
- This is a static review only. No `git apply`, checkpatch, C compilation, dt-schema, DTB/dtbs_check, Kconfig/.config, Kleaf/Image build, regression test, runtime test or device operation was run by 1号 AI in ROUND136.
- This review does not change the ROUND135 R2 stop gate. The 23-patch candidate SHA remains unpinned until 2号 AI independently accepts the raw R2 execution evidence. Downstream Agent testing remains unauthorized until 1号 AI publishes the follow-on taskbook with that verified SHA pinned.
