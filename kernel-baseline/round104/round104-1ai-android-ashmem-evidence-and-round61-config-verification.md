# ROUND104 — 1号 AI：Android ashmem 兼容性线索与 ROUND61 最终构建配置实证

**Date:** 2026-11-25  
**Ownership:** 1号 AI（ChatGPT）独立固定源码/构建产物审查  
**Implementation owner:** 2号 AI（如后续需要改驱动或 Kconfig，由 2号 AI 承担）  
**Test executor:** 本轮未需要本地 Agent  
**Pinned ACK:** android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Input clue:** 用户提供的群聊转述：AOSP can boot far enough to logcat; one GSI path reportedly failed because /dev/ashmem was missing; a discussion also mentions a device-specific multi-firmware framework and keystore2 startup delay.  
**Result:** **The clue is useful for classifying a userspace compatibility failure, but the actual ROUND61-built DBY-W09 Image configuration already includes CONFIG_ASHMEM=y. Do not blindly import a second ashmem driver or mark ashmem as an outstanding missing-kernel feature. Runtime device-node existence is still untested.**

---

## 1. Executive finding

The user's conversation is useful because it warns that kernel entry/early Android startup and full Android system-server readiness are separate gates. A logcat-reachable boot that later fails around shared-memory creation is not automatically a kernel boot failure.

However, the reported missing `/dev/ashmem` does **not** establish that the project's current ROUND61 image has the same gap.

A fresh audit of the immutable ACK source and the actual downloadable ROUND61 build artifact established:

- pinned ACK `arch/arm64/configs/gki_defconfig` explicitly sets `CONFIG_RUST=y`, `CONFIG_STAGING=y`, and `CONFIG_ASHMEM=y`;
- pinned ACK uses the Rust ashmem implementation from `drivers/staging/android/ashmem.rs`; it registers a misc device whose device name is `ashmem`;
- the exact final `dby_w09.config` extracted from GitHub Actions artifact 14985348694 also contains `CONFIG_RUST=y`, `CONFIG_STAGING=y`, `CONFIG_SHMEM=y`, and `CONFIG_ASHMEM=y`;
- its SHA-256 is `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7`, matching ROUND61's published artifact and progress records.

Thus, **the actual built candidate already has the ashmem driver selected in the final configuration**. There is no evidence-based reason to import an old C ashmem driver or add a duplicate driver patch.

This only proves build configuration/source inclusion. The device has not booted this Image, so actual runtime creation and SELinux access to `/dev/ashmem` remain untested.

## 2. Pinned ACK source evidence

Commit:
`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`

Relevant source blobs:
- `arch/arm64/configs/gki_defconfig`: `a3e1c0d60d5220b6be8b306157a331fc1696afb0`
- `drivers/staging/android/Kconfig`: `b432280beeb4b16c70c8294999ff1848033331e7`
- `drivers/staging/Makefile`: `855245a173cdc17a08a96b8513f4f62009e4348d`
- `drivers/staging/android/Makefile`: `0732228e3aabeec157f5aa6b01318581ff3a8d6a`
- `drivers/staging/android/ashmem.rs`: `8d4e156d40e541da5a33230eaeb2a098f54ee511`

Source facts:
- `drivers/staging/android/Kconfig` defines boolean `ASHMEM` and requires `SHMEM && RUST`.
- `drivers/staging/Makefile` enters `drivers/staging/android/` when `CONFIG_ASHMEM` is enabled.
- `drivers/staging/android/Makefile` builds `ashmem.o` and `ashmem_exports.o`.
- `drivers/staging/android/ashmem.rs` is the Rust implementation; it registers a misc device with the name `ashmem`, which provides the `/dev/ashmem` node.
- The GKI defconfig explicitly selects `CONFIG_RUST=y`, `CONFIG_STAGING=y`, and `CONFIG_ASHMEM=y`.

Source links:
- [Pinned GKI defconfig](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/arch/arm64/configs/gki_defconfig)
- [Pinned ashmem Kconfig](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/staging/android/Kconfig)
- [Pinned ashmem Makefile](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/staging/android/Makefile)
- [Pinned Rust ashmem driver](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/staging/android/ashmem.rs)

Important: at this pinned baseline the C file `drivers/staging/android/ashmem.c` is absent; the enabled implementation is the Rust driver. Do not copy in an older kernel's C ashmem source simply because a different kernel lacked `/dev/ashmem`.

## 3. Exact ROUND61 final build artifact verification

GitHub Actions run: `45529395645`  
Artifact ID: `14985348694`  
Artifact name: `round61-ack-6.18.33-image-build`  
Archive size: `210,441,171` bytes  
Artifact archive digest published in ROUND61: `0c8fabcd626d15aa36f32b3b7652d32b0f5389bc7fdca45bcd4d770e80123cf4`

The artifact was downloaded and its `round61-artifacts/dby_w09.config` member extracted read-only.

Extracted .config:
- size: 238,376 bytes;
- SHA-256: `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7`;
- hash exactly matches the already published ROUND61 record.

Actual selected values:
```
CONFIG_SHMEM=y
CONFIG_RUST=y
CONFIG_STAGING=y
CONFIG_ASHMEM=y
```

This is the exact final configuration associated with the compiled 44,820,992-byte ARM64 Image, not merely a defconfig inference.

The existing 33-symbol storage-first validator did not include ashmem in its required-symbol list, so the previous 33/33 PASS did not independently check ashmem. ROUND104 supplies the direct artifact check. A future config validator may add `CONFIG_ASHMEM=y` as an Android compatibility invariant, but this is a validator improvement, not a missing driver implementation.

The compiled Image has not been booted on the tablet. No claim is made that runtime misc-device registration, SELinux access or userspace compatibility has been tested.

## 4. Android 17 shared-memory compatibility context

Current Android 17 AOSP compatibility guidance says:
- `ASharedMemory_create()` conditionally chooses legacy ashmem or memfd;
- memfd is selected when vendor API level is 202604 or higher and kernel is `android16-6.12` or newer, with targetSdkVersion-dependent behavior;
- devices that do not meet the memfd prerequisites fall back to ashmem for compatibility with older vendor partitions/kernels;
- Android 17 updates SELinux domain policy for legacy ashmem access.

Source: [Android 17 SELinux compatibility — shared memory](https://source.android.com/docs/security/features/selinux/compatibility)

The project's kernel is based on `android17-6.18.33_r00`, satisfying the cited kernel-version floor. The HOS4.3 vendor API level has not been established by this conversation, so do not presume that the runtime system will exclusively use memfd. Retaining `CONFIG_ASHMEM=y` is appropriate for legacy compatibility.

The exact runtime issue can be in one of several distinct layers:
1. the running kernel lacks the ashmem driver or did not register its misc device;
2. `/dev/ashmem` exists but SELinux/device-node permissions prevent a process from opening it;
3. userspace selects an ashmem path or memfd compatibility ioctl path inconsistent with the driver's supported behavior;
4. a vendor service or framework component assumes an older shared-memory contract.

A real log must distinguish these cases. A kernel panic is not established merely by a system_server Java exception or zygote restart loop.

## 5. Interpretation of the supplied group conversation

What is useful:
- AOSP getting far enough to emit logcat suggests the tested image passed at least some early boot layers.
- A specific missing `/dev/ashmem` message is a concrete lead for shared-memory compatibility and can explain a userspace framework failure.
- A GSI-only failure is a warning not to attribute every boot failure to the kernel. System/vendor interface, SELinux policy, vendor API level, framework services and GSI compatibility must be separated.
- A prolonged `keystore2` initialization is another observable stage; the chat does not prove ashmem is its cause. Exact log timestamps and preceding fatal errors are required to establish causal ordering.
- The phrase “multi-firmware framework” is not technically specific enough to implement. It may refer to a vendor/OEM multi-firmware loading framework or another device-specific layer. No kernel subsystem or patch should be inferred from this phrase without its exact project/component name or source reference.

What is **not** established:
- that the log belongs to the DBY-W09 unit or identical HOS4.3 firmware;
- that the failure was a true kernel panic rather than an Android userspace crash/reboot loop;
- that ashmem caused the keystore2 delay;
- what “multi-firmware framework” means, where it belongs, or how it is wired;
- whether the current Image has a functioning runtime `/dev/ashmem` node, since Phase G has not run.

## 6. Implementation consequence

No ashmem driver patch is requested. The current candidate already builds the Rust ashmem driver with `CONFIG_ASHMEM=y`.

Before a future real-device log is collected, keep the following diagnostics separate:
- Kernel: `CONFIG_ASHMEM=y`, driver registration, misc-device node creation.
- Android init/ueventd: device-node permissions and ownership.
- SELinux: actual denial records for opening `/dev/ashmem` or invoking ashmem ioctls.
- Userspace: `ASharedMemory_create()` return, ashmem ioctl failures, and memfd fallback decision.
- System services: system_server/keystore2 crash, timeout or retry chronology.

A future device-test task may ask the local Agent to collect targeted logcat/dmesg and SELinux evidence only after the planned Phase-G safety gates are authorized. Do not use the current chat transcription as a substitute for device logs.

ROUND104 changes no source, patch, DTS, Kconfig, config fragment, Image, branch owned by 2号 AI, protected branch or PR. It is an independent evidence report only.

**Final verdict:** the chat is a useful compatibility clue for earlier GSI testing and for the eventual Android userspace acceptance checklist. But the exact ROUND61-built kernel candidate already has ashmem enabled in both its source defconfig and actual final `.config`. Do not re-import ashmem into this candidate; reserve the runtime `/dev/ashmem`/SELinux check for real-device validation, and treat the multi-firmware framework and keystore2 delay as separate unresolved leads.
