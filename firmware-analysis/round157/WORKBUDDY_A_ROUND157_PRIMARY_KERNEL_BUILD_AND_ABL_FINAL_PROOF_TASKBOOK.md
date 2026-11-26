# ROUND157 — WorkBuddy Window A: primary kernel build + final ABL proof

- Executor: WorkBuddy Window A (1号 Agent).
- Window B is a separate WorkBuddy chat; do not access it or its workspace.
- Use only Window A's own source/build workspace and exact local ABL/XBL captured in ROUND155.
- Task type: full offline primary kernel build plus a narrowly scoped offline ABL control-flow supplement. No device operation.

## 1. Purpose

ROUND156 established:
- candidate RAM-patched DTB and no-overlay base are internally valid;
- exact ABL has a single-FDT path, conditional overlay skip, target-path support and a non-fatal overlay failure return;
- ABL actively rebuilds /memory/reg from DDR data;
- exact setter semantics, fixup failure atomicity and complete AVB top-level signature/OEM gate remain unresolved;
- the old AI2 ROUND156 report did not read the new A/B result reports at execution time.

ROUND157 should now produce a formal Image build and close the smallest ABL gaps. No broad device-tree audit.

## 2. Exact candidate identity

- ACK android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9.
- Frozen pre-change 23-patch tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b.
- Accepted 23 patches: use the exact identity.json and verify all 23 patch SHA-256 values and replay status before build.
- RAM/comment patched source tree expected: c56d93eafa35057d65176db6594d67d5144868a0.
- RAM patch commit reported by ROUND154 Window A: 491d0cbffb4d16e2840c1788674e6a05b26e88a2.
- Base DTB (before RAM edit) true SHA-256: cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e.
- RAM-patched DTB: 108680 B, SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60.
- The old 63-hex-character expected hash is invalid; do not use it.

If the local source tree does not equal expected tree SHA or the 23-patch replay fails, stop and report exact mismatch. Do not use a different ACK tag or patch base.

## 3. Task A — formal primary full kernel build

Use a fresh, separate output directory. Use the same proven toolchain, .config and build target as ROUND135/ROUND140 where possible.

Preferred command:
tools/bazel build //common:dby_w09 --jobs=2

If the local Kleaf wrapper path differs, identify the exact launcher but do not change the target. The build must not consume a stale DTB output.

Record:
- source commit and full source tree SHA;
- 23 patch hashes/replay result;
- exact RAM DTS patch hash;
- .config hash and its relationship to ROUND140 / accepted product config;
- Bazel/Kleaf version, clang version, build environment, dependency mirror/cache provenance;
- full untrimmed build log and exit code;
- Image, DTB, DTBO if generated, modules, BTF/vmlinux, System.map, Module.symvers and module-signing certificate hashes/sizes;
- generated timestamps and nondeterministic certificate material separately.

Do not claim success from a cached output unless the build log proves the relevant actions were executed. Capture the Bazel action/cache status and, if safe, use the supported clean/fresh output mode. Do not delete canonical outputs.

If full build fails, classify the first real failure. Do not patch unrelated code or start an unrequested extra build.

## 4. Task B — verify final DTB inside full-build output

After build:
- extract/decode the DTB actually embedded/packaged for dby_w09;
- prove exactly one device_type=memory node;
- record whether the source's three tuples are preserved in the built DTB;
- enumerate all 18 reserved-memory nodes and compare their full properties to ROUND154/156 baseline;
- verify UFS host/PHY, supply, clock, reset, power-domain, OPP and interconnect closure;
- verify candidate /chosen remains intentionally empty;
- compare built DTB SHA against ROUND154's 9d0d7600... only if the DTB compiler and flags are identical; explain any difference.

No boot.img creation this round.

## 5. Task C — ABL supplement from local ROUND155 binary only

Use only Window A's existing local extracted ABL PE; no ADB or additional device reads.

Resolve as much as possible of these three narrow issues:

1. RAM write primitive: identify the exact libfdt routine called in the /memory tuple loop at 0x3f9a4..0x3fafc. Is it setprop, appendprop, or a sequence clearing/rebuilding then writing? If decoder gaps remain, report the raw words and stop; do not infer.
2. Overlay failure safety: trace whether external fixups are completed before any fragments are merged into the base FDT. If a missing external label causes failure, can the base tree already be partially modified? Provide the exact calls/branches. This determines whether leaving the stock DTBO unchanged and allowing its fixup attempt to fail is a safe no-overlay hypothesis.
3. AVB: trace the exact ABL/libavb call path around AvbSlotVerify, top-level vbmeta signature verification, public-key validation, rollback, VERIFICATION_DISABLED, unlocked allow-verification-error continuation, and Huawei-specific vbmeta/TA digest checks. Determine which operations are before/after descriptor skip. Separate proven code from strings/inference.

Do not extract keys or change flags. Raw ABL remains local.

## 6. Task D — archive RAM patch

Publish the small reversible DTS patch as a separate text artifact:
firmware-analysis/round157/AI1_R157_RAM_DTS_PATCH.patch

Use only the minimal source patch; do not include raw firmware, build logs, secret paths or any other source files. This allows Window B to independently recreate the same source tree from its own base.

## 7. Deliverables

1. Sanitized report:
firmware-analysis/round157/WORKBUDDY_A_ROUND157_PRIMARY_KERNEL_BUILD_AND_ABL_FINAL_PROOF_REPORT.md
2. Minimal patch:
firmware-analysis/round157/AI1_R157_RAM_DTS_PATCH.patch
3. Read back both items and verify exact blob/hash/content.

Stop after this report. No boot.img, DTBO container, device command, flash, reboot, fastboot or recovery.

## 8. Prohibitions

- No device/ADB/root read, because current raw capture is sufficient for this offline task.
- No partition reads/writes, flash, reboot, fastboot, recovery or temporary boot.
- No key extraction, signing, AVB flag edits or bypass.
- No access to Window B's workspace or private logs.
- No broad ARC/proxy/CMA/display changes.

— END —