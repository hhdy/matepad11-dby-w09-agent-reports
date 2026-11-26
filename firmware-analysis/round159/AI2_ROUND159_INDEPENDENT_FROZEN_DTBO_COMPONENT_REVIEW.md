# ROUND159 — AI2 Independent Frozen HOS4.3 Entry 2 DTBO Component Review

- Reviewer: 2号 AI independent reviewer (not WorkBuddy Window B / 2号 Agent)
- Target: Huawei MatePad 11 DBY-W09, HOS 4.3.0.196(C00E100), ACK android17-6.18.33
- Review date: 2026-11-27
- Result: **BLOCKED — required Window A and Window B artifacts are not published at the taskbook paths**
- Scope: one frozen host-side Entry 2 DTBO component only. No device interaction, fastboot, flashing, boot.img creation, or broad hardware audit was performed.

## 1. Inputs and availability

### Read successfully

1. ROUND159 START_PROMPT_AI2_ROUND159_INDEPENDENT_FROZEN_DTBO_COMPONENT_REVIEW.md
   - Branch: `ai2/round159-frozen-dtbo-candidate-review`
   - SHA: `bd9004008ea2c436b0e1c911ddc707d044df9aef`
2. AI2 taskbook
   - Branch: `ai2/round159-frozen-dtbo-candidate-review`
   - SHA: `db1056af02b8cc0e07f79b10c0a775e0d237fe96`
3. AI1 integration plan
   - Branch: `ai1/round159-entry2-candidate-integration`
   - Path: `kernel-baseline/round159/AI1_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_PLAN.md`
   - SHA: `a77703b235c1efbc7cecede44fdc7ea66dad6ca4`

The AI1 plan identifies the accepted source tree and base DTB, describes the exact HOS4.3 Entry 2 identity facts known so far, and explicitly says the full modem_id bytes and ABL table/selector contract must come from target evidence. It also states that ROUND158's HOS4.2 prototype values are not final.

### Required Window A/B artifacts: unavailable

The following exact taskbook paths were fetched from their named branches and each returned GitHub 404:

| Required artifact | Branch | Path | Result |
|---|---|---|---|
| Window A exact Entry 2 / ABL selector report | `workbuddy/round159-exact-entry2-facts` | `firmware-analysis/round159/WORKBUDDY_A_ROUND159_EXACT_ENTRY2_TARGET_FACTS_AND_ABL_SELECTOR_REPORT.md` | 404 |
| Window A machine-readable facts | `workbuddy/round159-exact-entry2-facts` | `firmware-analysis/round159/entry2-target-facts.json` | 404 |
| Window B frozen candidate report | `agent2/round159-entry2-preserving-dtbo-candidate` | `firmware-analysis/round159/WORKBUDDY_B_ROUND159_FROZEN_ENTRY2_DTBO_CANDIDATE_REPORT.md` | 404 |
| Window B candidate manifest | `agent2/round159-entry2-preserving-dtbo-candidate` | `firmware-analysis/round159/entry2-candidate-manifest.json` | 404 |

Both named Window A and Window B branches themselves are discoverable and exist. The required files are nevertheless absent at the exact paths specified by the taskbook. No alternate path or unverified artifact was substituted.

## 2. Independent review checklist

Because the candidate binary, manifest, and exact target facts are unavailable, the requested byte-level and parser checks cannot be executed. The results below deliberately distinguish unavailable evidence from a demonstrated failure.

- ROUND155/157/158 source artifact identities: **not re-hashed in this component review**; AI1 plan records the expected base DTB (108,680 bytes, SHA-256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60`) and captured stock DTBO partition (25,165,824 bytes, SHA-256 `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c`). Those plan values do not substitute for checking Window B's actual input/output files.
- Exact Entry 2 table metadata and selector properties: **not independently verifiable** without Window A report/JSON and the candidate manifest.
- Five exact HOS4.3 `/rootparam` properties: AI1 plan lists four known values:
  - `qcom,boardid`: raw bytes `08 02 06`
  - `qcom,board_name`: `DBY_W09_VD`
  - `qcom,product_name`: `DBY-W09`
  - `hardware_version`: `SH1DBSLM`
  - Full `huawei,modem_id` payload: **not supplied in the readable inputs; must not be guessed or borrowed from HOS4.2**.
- DTBO FDT payload bytes, DT table header, entry count/order, offsets, sizes, page_size, version, and total_size: **not inspectable** because the Window B candidate and manifest are missing.
- Structural host merge showing exactly five property changes and zero unrelated changes: **not reproducible or verifiable** without the frozen candidate and its build script/logs.
- Negative parser/fixup checks: **not verifiable** without Window B's test evidence and logs.
- A host-side merge, even if later shown to pass, would not establish HOS4.3 ABL acceptance, fastboot RAM boot, AVB/OEM authorization, or device bootability.

### Alignment interpretation correction

Do not treat 4096-byte alignment as an independent rejection criterion. The AI1 plan correctly points to the official AOSP DTBO format example using `page_size=2048` and `dt_offset=128`; the offset is not universally required to be a page_size multiple. The exact HOS4.3 ABL parser and selector behavior remains authoritative. Since Window A's exact selector evidence is missing, this review makes no conclusion about which table layout HOS4.3 accepts.

## 3. Required decisions

1. **DTBO FDT payload validity — INDETERMINATE.** No candidate payload or independently parseable manifest was available.
2. **Android DT table serialization — INDETERMINATE.** No serialized candidate bytes were available for independent header/offset/size/roundtrip checks.
3. **HOS4.3 ABL selector compatibility — INDETERMINATE.** The exact Window A selector report and target-facts JSON were not published at the required paths. The AI1 plan itself says the target table/selector contract is not fully closed.
4. **Integrated boot-v2 package — NO-GO.** This component review does not establish the boot-v2 handoff or resolve the known ABL `/memory/reg` rebuild, UFDT failure atomicity, or Huawei AVB/TZ/OEM authorization gates. No boot.img/package was created or reviewed here.
5. **Temporary boot and partition write — NO-GO.** Outside this review's scope and not authorized. No device or fastboot operation was performed.

## 4. Stop condition

**BLOCKED. Stop here.** The minimum unblock is publication of the four exact Window A/B artifacts at the taskbook paths (or an explicit taskbook update naming their canonical replacement paths). Once present, this review can verify only the single frozen candidate against the supplied exact target facts. No speculative payload, competing variant, boot image, device test, or next audit task is created by this report.

---
End of ROUND159 AI2 independent component review.
