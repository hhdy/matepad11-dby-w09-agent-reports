# ROUND102 — 1号 AI：用现有 UFS 私有 host wrapper 承载生命周期状态，并采用每 HBA registered async domain

**Date:** 2026-11-25  
**Task ownership:** 1号 AI（ChatGPT）源码架构审查  
**Implementation owner:** 2号 AI（独立开发 AI）  
**Test executor:** 本地测试 Agent（仅测试任务，不负责实现）  
**Pinned ACK:** android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Related:** ROUND95, ROUND96, ROUND97, ROUND98, ROUND100, ROUND101  
**Result:** **A better KMI-safe storage location exists in the pinned source: the private struct ufs_hba_priv allocated as Scsi_Host private data. Put lifecycle/VCC state there instead of consuming the HBA OEM slot or registering a separate devres allocation. Pair it with a per-HBA async_domain whose registered bit preserves async_synchronize_full() participation.**

---

## 1. Executive result

ROUND95–101 used the existing `ufs_hba::android_oem_data1` OEM reserve as a candidate pointer to a devm-managed sidecar. A fresh exact-source review found an even simpler storage option already present in the fixed ACK source:

- `drivers/ufs/core/ufshcd-priv.h` defines `struct ufs_hba_priv { struct ufs_hba hba; bool zwor_sup; }`.
- `ufshcd_alloc_host()` calls `scsi_host_alloc(..., sizeof(struct ufs_hba_priv))` and `hba = shost_priv(host)`.
- `ufs_hba_priv` is a core-private wrapper; it is not a member of the exported `struct ufs_hba`, nor part of the Qualcomm KMI-visible UFS variant-op / ufs_vreg layouts.
- The wrapper already has `to_hba_priv(hba)` in the private header.

**Recommendation:** add a private lifecycle-state substructure to `struct ufs_hba_priv` and use that for the async domain/cookie and the private VCC vote state. This avoids:
- adding any field to KMI-visible `struct ufs_hba`;
- pointer casting through `android_oem_data1`;
- dependence on `CONFIG_ANDROID_VENDOR_OEM_DATA`;
- a second devm allocation and its reverse-unwind ordering;
- a callback-side completion protocol.

The wrapper's private allocation size increases, but `ufshcd_alloc_host()` owns that allocation size and external host drivers receive only the `struct ufs_hba *` output pointer. The public `struct ufs_hba` layout remains unchanged.

For asynchronous scan synchronization, prefer an embedded per-HBA `struct async_domain`, initialized with `registered = 1`, and use `async_schedule_domain()` plus `async_synchronize_cookie_domain(cookie + 1, &domain)`. This avoids waiting for unrelated default-domain work while retaining participation in global `async_synchronize_full()` synchronization.

This is a source-level design recommendation for 2号 AI, not a committed driver patch or build result.

---

## 2. Exact source evidence: private host wrapper already exists

Pinned source files and blob identities:

| File | Blob SHA |
|---|---|
| `drivers/ufs/core/ufshcd-priv.h` | `6ba126dc052824efa73a8a41540151a1e2cecaa1` |
| `drivers/ufs/core/ufshcd.c` | `2cf7aa8e0a9472f9024d4251ac2f9d7da830e219` |
| `drivers/ufs/host/ufshcd-pltfrm.c` | `5ac7afe759346debfc2910fb219d8e491ba08b64` |
| `include/ufs/ufshcd.h` | `ee5c1c607237d5eaf743d4a267a760c1e0efcf97` |

Exact pinned lines:
- `drivers/ufs/core/ufshcd-priv.h:9-17`:
  - `struct ufs_hba_priv { struct ufs_hba hba; bool zwor_sup; };`
  - `to_hba_priv(struct ufs_hba *hba)` returns `container_of(hba, struct ufs_hba_priv, hba)`.
- `drivers/ufs/core/ufshcd.c:10822-10863`:
  - `ufshcd_alloc_host()` calls `scsi_host_alloc(&ufshcd_driver_template, sizeof(struct ufs_hba_priv))`;
  - registers `ufshcd_devres_release(host)`;
  - obtains `hba = shost_priv(host)`;
  - initializes HBA core fields and returns the HBA pointer.
- The public `struct ufs_hba` ends at `include/ufs/ufshcd.h:1299` with the existing `ANDROID_OEM_DATA(1)` reserve. ROUND95 correctly established that this OEM slot could store a pointer without growing the public struct, but it is not necessary if the existing private wrapper is extended.

There is no in-tree host-driver source use of `to_hba_priv()` or `struct ufs_hba_priv` outside the UFS core in the pinned host source set. The wrapper definition and accessor live in the core-private header. The platform glue can include that private header to fill the new state during regulator parsing; it must not duplicate the struct layout locally.

Source links:
- [ufshcd-priv.h](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd-priv.h)
- [ufshcd_alloc_host()](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)
- [ufshcd-pltfrm.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.c)

### 2.1 Why extending this wrapper is KMI-safer than using the OEM pointer

`struct ufs_hba_priv` is the private host-data tail allocated by `scsi_host_alloc()`. It is not the type passed by pointer through `ufshcd_alloc_host()`; the exported helper returns a pointer to its first member, `struct ufs_hba`. Adding a private field after `zwor_sup` does not change:
- `sizeof(struct ufs_hba)`;
- the offset or type of `ufs_hba` members;
- `struct ufs_vreg`;
- `struct ufs_hba_variant_ops`;
- the signature of `ufshcd_populate_vreg()`;
- any Qualcomm KMI-visible function signature.

The `ufshcd-priv.h` file already exists precisely to share internal core-only host state and inline accessors. The platform parser can use the same shared definition by including the core-private header, rather than adding a new exported setter API or duplicating a cast/layout.

The existing `android_oem_data1` remains reserved and unused; ROUND102 does not recommend appropriating it for this implementation.

---

## 3. Host allocation coverage — the relevant host paths use the common allocator

The fixed ACK `drivers/ufs/host` source set was inspected for the host initialization entry points:

- `ufshcd-pltfrm_init()` calls `ufshcd_alloc_host()` before setting vops, parsing clocks/regulators and calling `ufshcd_init()`.
- Qualcomm, MediaTek, Exynos, HiSilicon, Cadence, Rockchip, Renesas, Spreadtrum and other platform UFS host drivers use `ufshcd_pltfrm_init()`.
- The PCI UFS paths `ufshcd-pci.c` and `tc-dwc-g210-pci.c` call `ufshcd_alloc_host()` directly before `ufshcd_init()`.

Thus the private wrapper is established before the async scheduling point for both common platform and PCI paths in the pinned in-tree host set. This is stronger coverage than allocating a lifecycle token only in the platform regulator parser.

If an out-of-tree downstream host bypasses `ufshcd_alloc_host()` and directly fabricates `struct ufs_hba`, it is outside this pinned-tree result; 2号 AI must check the complete integration tree before assuming universal coverage.

---

## 4. Recommended private state shape

The exact field names are implementation choices, but a nested private structure is recommended to keep all new lifecycle state grouped:

```c
struct ufshcd_private_state {
        struct async_domain async_domain;
        async_cookie_t async_scan_cookie;
        bool async_scan_cookie_valid;

        /* Parsed VCC range and independent vote/request states. */
        u32 vcc_min_uV;
        u32 vcc_max_uV;
        /* Further voltage/load/pending-cleanup state as required. */
};

struct ufs_hba_priv {
        struct ufs_hba hba;
        bool zwor_sup;
        struct ufshcd_private_state state;
};
```

The exact VCC subfields must preserve ROUND84/89/90/93/94's distinction among:
- parsed target voltage interval;
- current ON vs OFF-relaxed voltage request state;
- regulator consumer enable-reference state (continue using existing `ufs_vreg.enabled` only as the existing reference state after fixing error semantics);
- DRMS load vote state;
- pending voltage/load cleanup state.

Do not duplicate the existing regulator enable state without a clear reason, and do not put these fields into `struct ufs_vreg`.

### 4.1 Initialization

In `ufshcd_alloc_host()` after `hba = shost_priv(host)`:
- initialize the private async-domain pending list with `INIT_LIST_HEAD(&state.async_domain.pending)`;
- set `state.async_domain.registered = 1`;
- clear `async_scan_cookie_valid` and its cookie;
- explicitly initialize any enum state to its invalid/no-request value if that is not guaranteed by the zeroed SCSI private allocation.

The `scsi_host_alloc()` private area is allocated before any caller can invoke `ufshcd_init()`. Therefore the async domain exists for platform and PCI users before any async callback can be scheduled.

### 4.2 VCC parser timing

Pinned `ufshcd_pltfrm_init()`:
1. calls `ufshcd_alloc_host()`;
2. assigns `hba->vops`;
3. calls `ufshcd_parse_clock_info()`;
4. calls `ufshcd_parse_regulator_info()`;
5. parses OPP data;
6. calls `ufshcd_init()`.

The private state therefore exists before parsing and well before `ufshcd_init()` first enables VCC. `ufshcd-pltfrm.c` can populate the VCC interval in `to_hba_priv(hba)->state` after the normal VCC descriptor is created. Keep the exported `ufshcd_populate_vreg()` generic and unchanged. The existing HBA pointer is available here; do not rely on `dev_get_drvdata()`, which is not set yet.

Because VCC state and async cookie share the private state allocation, it cannot be accidentally absent when an optional voltage property is absent. The UFS async join is therefore guaranteed to have storage for every host allocated through the common helper.

---

## 5. Per-HBA registered async domain and exact checkpoint

Pinned async implementation sources:
- `include/linux/async.h` SHA `19b778d08600f1d1e1bf25a8cd0e8a390b39cac5`
- `kernel/async.c` SHA `4c3e6a44595fa176f06108c869d164cca26546a1`

The default `async_schedule()` path uses the shared default domain. ROUND101 explained why `async_synchronize_cookie(C + 1)` works, but its default-domain checkpoint also waits for unrelated earlier default-domain work.

A per-HBA domain avoids that unnecessary wait while preserving global async synchronization:

- `async_schedule_domain(func, data, domain)` adds the task to the specified domain.
- `async_synchronize_cookie_domain(cookie, domain)` waits for pending entries in that domain submitted before the checkpoint.
- The `async_domain.registered` bit controls whether each pending entry is also added to the global pending list used by `async_synchronize_full()`.
- The `ASYNC_DOMAIN()` macro initializes a registered domain; `ASYNC_DOMAIN_EXCLUSIVE()` initializes an unregistered one.
- The per-HBA domain should be initialized with its pending list head and `registered = 1`. This retains global async_full participation but gives the remove path a private synchronization domain.

At the existing `ufshcd_init()` submission point, capture:

```c
state->async_scan_cookie =
        async_schedule_domain(ufshcd_async_scan, hba,
                              &state->async_domain);
state->async_scan_cookie_valid = true;
```

At the first lines of `ufshcd_remove()`, before PM, sysfs, workqueue, SCSI, IRQ, host or regulator teardown:

```c
if (state->async_scan_cookie_valid) {
        async_synchronize_cookie_domain(state->async_scan_cookie + 1,
                                        &state->async_domain);
        state->async_scan_cookie_valid = false;
}
```

The exact implementation must guard the state accessor and preserve the current callback signature. The callback should not dereference the private state merely to report completion; the async framework removes its pending entry only after the callback function has fully returned, including the final `pm_runtime_put_sync()` and error log.

### 5.1 Why registered=1 matters

Do not initialize the per-HBA domain as an exclusive/unregistered domain for this first implementation. The existing UFS call uses the default registered async domain, and other kernel code may rely on global `async_synchronize_full()` covering its callback. Setting `registered = 1` preserves that property while scoping this HBA's teardown wait to its own domain.

The global async cookie sequence is shared, but `async_synchronize_cookie_domain()` checks the specified domain's pending list only. A per-HBA domain contains only this controller's async tasks, so it avoids waiting for unrelated subsystem work.

### 5.2 Synchronous fallback and cookie races

Pinned `async_schedule_node_domain()` can execute the callback synchronously if it cannot allocate an entry or the async queue is over its limit. It still returns its cookie after the callback has completed. Capturing that cookie and waiting at cookie+1 remains safe: the domain pending list will be empty, so the remove wait completes immediately.

When asynchronous scheduling succeeds, the entry is placed on the domain pending list before it is queued. The caller stores the returned cookie before the synchronous `ufshcd_init()` path returns to driver core. The async callback may complete before or after the cookie assignment; both cases are safe.

The checkpoint must be `cookie + 1`, not `cookie`, because the API waits for functions submitted strictly before the checkpoint. The framework removes the pending entry only after the callback has returned.

---

## 6. Private wrapper lifetime

The private state is embedded in `ufs_hba_priv`, which shares the `Scsi_Host` private allocation with the HBA:

- it is allocated by `scsi_host_alloc()`;
- it is retained while the Scsi_Host has references;
- the devres action registered by `ufshcd_alloc_host()` calls `scsi_host_put(host)`;
- any active SCSI async scan reference delays final host/private-data release;
- no separate devm allocation or pointer free is needed.

This removes the sidecar devres-order dependency from ROUND95/100 for the generic UFS private state. It does **not** remove the need to join the UFS-owned callback before HBA teardown: that callback is scheduled independently and does not itself own a Scsi_Host reference.

The Qualcomm VDDP cleanup action remains registered after `devm_regulator_get()` and must still execute while `ufs_qcom_host` and the regulator handle are alive. Its cleanup error policy remains as stated in ROUND100/101.

---

## 7. Interaction with ROUND84–94 VCC requirements

The private wrapper can hold all VCC state without modifying `struct ufs_vreg`:
- parse `vcc-voltage-level` as exactly two u32 cells for the generic VCC descriptor only, before `ufshcd_init()`;
- store the on-state interval and derive the off-relaxed interval `[0, max_uV]`;
- set voltage before the first VCC enable;
- keep software voltage-request state updated only after regulator API success;
- track voltage request independently from enable reference and load vote;
- clean voltage/load votes even when a regulator enable attempt failed before `vreg->enabled` became true;
- move load zero before disable on the PM8150 L17/L6 DRMS shutdown path, with explicit rollback and pending-cleanup handling;
- route runtime PM and recovery VCC transitions through private helpers carrying HBA context, as ROUND96 requires.

Do not modify `ufshcd_populate_vreg()` or append callbacks to the exported `ufs_hba_variant_ops`. Do not claim KMI PASS until the exact pinned Kleaf ABI check is run after the integrated implementation.

---

## 8. Required 2号 AI implementation and verification sequence

This is a **2号 AI implementation assignment**, not a local Agent implementation task:

1. Extend the already-existing core-private `struct ufs_hba_priv` (via `ufshcd-priv.h`) with the lifecycle state; leave public `struct ufs_hba` unchanged.
2. Initialize one registered async domain per HBA during `ufshcd_alloc_host()`.
3. Change only the UFS-owned scan scheduling call to `async_schedule_domain()`, capture its cookie, and join with `async_synchronize_cookie_domain(cookie + 1, domain)` at remove entry.
4. Ensure all direct `ufshcd_init()` users in the pinned host set are covered; all in-tree platform and PCI entry paths examined use `ufshcd_alloc_host()`.
5. Have `ufshcd-pltfrm.c` use the existing core-private header/accessor for early VCC parsing and state updates; keep the exported populate helper and KMI-visible layouts untouched.
6. Preserve the VCC state/error rules from ROUND84–94.
7. Revise ROUND52-0002 VDDP cleanup to load-zero-before-disable and document the remaining RPMh provider request-submission failure policy; do not force-disable shared L6.
8. Provide the complete diff for 1号 AI review before advancing any device-readiness gate.
9. Run real pinned ACK patch application, strict checkpatch, dt-schema fixtures, Kleaf Image build, and the exact KMI ABI diff after implementation. An Image build without the new integrated patches does not validate these changes.

Testing Agent work is separate and must be tasked only after the implementation diff exists. Do not ask the Agent to write or repair the driver.

---

## 9. Scope and project gates

- Phase A–D: previously recorded PASS for the pre-ROUND101 Image patch sequence.
- Phase E: BLOCKED — final ABL-to-Linux FDT memory handoff and physical PM8150 input topology missing.
- Phase F: BLOCKED — boot/DTBO selection and AVB/vbmeta_cust packaging evidence unresolved.
- Phase G: NOT RUN.
- ROUND102 is source-level design only; no patch application, compile, KMI run, dt-schema run, device connection, boot, flash, or runtime regulator test was performed.

**Final verdict:** use the existing private `ufs_hba_priv` host-data wrapper as the storage for UFS async lifecycle and VCC private state. It is simpler and more directly KMI-safe than an OEM-slot pointer plus separately managed sidecar. Use a per-HBA registered async domain so the teardown wait is exact and does not wait for unrelated default-domain work, while preserving `async_synchronize_full()` participation. Keep the VDDP failure policy open until its actual PM8150/RPMh path is validated.
