# ROUND135 patch-23 deduplication — 1号 AI source review

Date: 2026-11-26
Owner: 1号 AI (ChatGPT)
Branch: `ai1/round130-stagea-ufs-lifecycle-integration`

## Finding

The original 23-item manifest duplicated the SM8250 UFS dual-GenPD / required-OPP driver implementation.

- Frozen patch 5: `kernel-baseline/round61/patches/round33-checkpatch-clean.patch`, blob `f1d54e5e0379183fbdfb3ca6132c6d0fc61d4622`.
- Former ROUND135 patch 23: `kernel-baseline/round135/series/23-round135-ufs-dual-genpd-driver.patch`, blob `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5`.

The diff bodies were compared against one another. They are identical except one alignment whitespace character in the function parameter line:
- frozen patch 5: `+					  struct device_node *opp)`
- former patch 23: `+					 struct device_node *opp)`

Both already add the same includes, validation helpers, GenPD attach routine and UFS probe call. The duplicate patch cannot legitimately be applied a second time after frozen patch 5; its first include hunk would target code already inserted by patch 5. Retaining it in a sequential 23-patch list would turn an otherwise duplicate change into a guaranteed apply conflict.

## Series correction

To preserve 23 distinct and meaningful ordered inputs while keeping the board integration atomic and independently testable:

- Patch 22 is now **DTS file only**:
  `kernel-baseline/round135/series/22-round135-huawei-dby-w09-real-dts.patch`
  Git blob: `ab0108364c835d87ac35ca670347d9d0001a821d`
  It adds `arch/arm64/boot/dts/qcom/huawei-dby-w09.dts`.

- Patch 23 is now **qcom Makefile DTB target only**:
  `kernel-baseline/round135/series/23-round135-huawei-dby-w09-dtb-makefile.patch`
  Git blob: `ceb72ed206d97beb2c2fa8558cb120ee186cb685`
  The context and inserted line use literal TAB characters before `+=`, matching the fixed ACK Makefile exactly.

- The former duplicate driver patch was deleted from the candidate series. Its implementation remains present through immutable frozen patch 5; frozen manifest and all patch 1–21 inputs remain unchanged.

- Updated 23-patch manifest blob: `6268dd363c08f549e2fd092364adafc65bce93e9`.
- Latest candidate DTS blob: `58293f7a62a50f8109886c92ce4b9cd14d7980e2`.

## Current exact boundaries

1. This is a source-series correction, not proof of real application.
2. Patch 22 and patch 23 must be checked/applied separately and in order on the exact ACK tree.
3. The full 23-patch result-tree SHA is **not yet independently established**. Do not invent or infer it from the 17-patch tree SHA.
4. The next Agent taskbook revision 2 is therefore a two-tree **identity and result-tree establishment preflight only**. It must stop after both independent clean trees produce the same full-series tree SHA and raw logs are uploaded.
5. 2号 AI independently audits the preflight report, exact patch identities, offsets, raw logs and final tree SHA. Only after that review will 1号 AI pin the verified full-series expected tree SHA in a follow-on taskbook and authorize schema/DTB/Kconfig/build/regression validation.
6. No Agent modification to source or patches, no local patch repair, no device/firmware/boot/partition operations.

This review is not an acceptance of the corrected 23-patch integration. ROUND135 remains pending its R2 preflight and subsequent full validation.
