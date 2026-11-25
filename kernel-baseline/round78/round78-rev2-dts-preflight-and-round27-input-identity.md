# ROUND78 — rev2 DTS / rootparam preflight and ROUND27 input identity check

**Date:** 2026-11-25  
**Review owner:** 1号 AI（ChatGPT）  
**Task owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only  
**Purpose:** read-only source preflight before the ROUND27 Kleaf DTB/DTBO/composite test

## 1. Result

**TEXTUAL CONTRACT REVIEW: PASS WITH INPUT-IDENTITY BLOCKER.**

The current main-branch rev2 board candidate and rootparam overlay are structurally consistent with the reviewed two-domain UFS implementation and the known HOS4.3 VG rootparam candidate. However, the expected board DTS blob SHA recorded in 2号 AI's authoritative ROUND27 taskbook does **not** match the current main-branch board candidate blob. The overlay hash does match.

The testing Agent must not silently substitute a different source file and claim the existing taskbook's exact-input validation. 2号 AI must refresh/reissue the input identity in its taskbook (or explicitly pin the intended older source commit/blob) before the test is treated as validating the current candidate.

## 2. Exact source identities

| Input | ROUND27 taskbook expects | Current main branch fetch | Result |
|---|---|---|---|
| `dts/dby-w09-ack18-board.dts.rev2.candidate` | `9918efe3f253a3e4821689ffeb899d5a0f237e8f` | `f5449bac669ea71d7149ffb1fc858e39eb128572` | **MISMATCH** |
| `dts/dby-w09-ack18-rootparam.dtso.draft` | `c7e5b145d4308e0675ff648b4e046033c5560083` | `c7e5b145d4308e0675ff648b4e046033c5560083` | MATCH |

The fetched current board candidate at main ref was also fetched at commit `70e075e29fafa5dccd1f4564766a28d809867e8e` and returned the same blob `f5449bac...`. That commit's recorded diff changes the board candidate's memory section comment to document the inherited zero-size bootloader-fill `/memory` placeholder. This is a documentation-only hunk in the visible commit diff, but the blob identity still differs and must be reconciled explicitly rather than waived.

Sources:
- [Current rev2 board candidate](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/dts/dby-w09-ack18-board.dts.rev2.candidate)
- [Current rootparam overlay candidate](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/dts/dby-w09-ack18-rootparam.dtso.draft)
- [2号 AI authoritative ROUND27 taskbook](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round27/AI2_ROUND27_TASKBOOK.md)
- [Board-candidate memory-placeholder clarification commit](https://github.com/hhdy/matepad11-dby-w09-agent-reports/commit/70e075e29fafa5dccd1f4564766a28d809867e8e)

## 3. Textual board / overlay contract review

### Base DTB identity
- `model` and `compatible` identify Huawei MatePad 11 DBY-W09 / Qualcomm SM8250.
- Base root `qcom,board-id` remains `<0 0>`; this is separate from the overlay root's VG candidate `<0x206a 0>`.
- `qcom,msm-id` uses the SM8250 identity/revision constants documented in the candidate.
- The base defines a labelled empty `rootparam` node for the overlay target.

### Rootparam overlay
- The overlay targets `&rootparam`, not a vendor-only stock fragment set.
- The five HOS4.3 VG candidate properties are present: `qcom,boardid`, `qcom,board_name`, `qcom,product_name`, `hardware_version`, and `huawei,modem_id`.
- The overlay root board-id and the Android DT table entry id/rev remain distinct. This overlay source does not prove HOS4.3 ABL selection or table metadata acceptance.

### UFS Host / PHY board contract
- Host power-domain order is MMCX index 0 followed by GCC `UFS_PHY_GDSC` index 1, matching the ROUND33 driver contract.
- PHY retains only its own GCC `UFS_PHY_GDSC` domain.
- The Host candidate includes UFS VCC/VCCQ/VCCQ2, VDDP REF_CLK/L6 and VCCQ-parent/S8 topology properties; the S8 parent/electrical path remains unresolved and the candidate explicitly treats that property as topology metadata only.
- The PHY candidate declares `vdda-phy-always-on` with `vdda-phy` and `vdda-pll` supplies, matching ROUND63.
- `vdd-hba-supply` is absent; this is intentional because the relevant HOS node represented a GDSC, not an ACK regulator consumer.
- No guessed `vph_pwr`, physical `vdd-s*-supply` parent or invented PMIC input voltage was introduced.

### Memory and power gates
- The board candidate documents the inherited zero-size `/memory` placeholder from pinned `sm8250.dtsi`; it does not invent usable RAM.
- PM8150 physical input-parent paths remain unresolved.
- HOS4.3 MMCX→MX ARC corner/dropout equivalence remains unresolved after ROUND25.
- The 17/18 reserved-memory exact-match result from ROUND26 does not close final post-ABL RAM overlap or the `cdsp_secure_heap` dynamic-vs-fixed mismatch.

This is a textual review only. It is not dtc, Kleaf, dtbs_check, dt-validate, overlay application or runtime evidence.

## 4. Required action before ROUND27 result acceptance

1. **2号 AI:** update its authoritative `AI2_ROUND27_TASKBOOK.md` to pin the intended current board-candidate blob `f5449bac669ea71d7149ffb1fc858e39eb128572`, or state the exact immutable older commit/blob if it intends to test the earlier content. Preserve the overlay blob pin `c7e5b145d4308e0675ff648b4e046033c5560083` if still intended.
2. **Testing Agent:** if already executing against a preloaded `9918efe...` source copy, report the exact source used and do not relabel it as current-main validation. If the task's hash assertion fails, stop and report `BLOCKED_INPUT_IDENTITY_MISMATCH`; do not modify the candidate or silently continue with a different blob.
3. **1号 AI:** after taskbook correction and test report upload, independently verify the report's source hashes before accepting any DTB/DTBO/composite/schema result.

The expected ROUND27 report path remains `firmware-analysis/round27/AI2_ROUND27_KLEAF_DTB_DTBO_SCHEMA_REPORT.txt` on `firmware-audit-v1`. At the time of this review, that report path returned 404 / was not yet uploaded.

## 5. Work boundaries

1号 AI only fetched and read GitHub text files and commit diff metadata. It did not modify the board DTS, overlay, 2号 AI branch or 2号 AI taskbook. No compile, schema validation, device operation, boot packaging, AVB action or hardware test was run.

**Final status: current DTS text contract review is favorable, but ROUND27 exact-input gate is BLOCKED until 2号 AI reconciles the board candidate blob SHA.**
