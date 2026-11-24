# Phase B — real DT binding validation and negative fixtures

**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Pinned source:** `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Status:** PASS — hosted run 45451513173 completed the authoritative schema and positive/negative fixture gates.

## Authoritative command path

The dedicated workflow `.github/workflows/round61-ack-ufs-validation.yml`:
- clones the fixed ACK commit into a disposable source directory;
- applies the UFS binding/driver patches, the ROUND63 PHY binding/driver patches, and performs `git diff --check`;
- installs dtschema in a Python virtual environment;
- invokes `make ARCH=arm64 dt_binding_check` with colon-separated `DT_SCHEMA_FILES` for `qcom,ufs.yaml`, `qcom,ufs-common.yaml`, and `qcom,sc8280xp-qmp-ufs-phy.yaml`;
- runs direct `dt-doc-validate` and `yamllint` for all three modified schemas;
- captures direct `dt-validate` output for the original UFS example;
- runs independent DTB fixture tests against `Documentation/devicetree/bindings/processed-schema.json`.

The kernel Makefile's `dt_binding_check` recipe can swallow some example-validation failures with `|| true`; its exit status alone is not treated as a PASS. The explicit `dt-validate` commands are the actual fixture gates.

## UFS fixtures

Generator: `tests/generate_round61_ufs_fixtures.py` (10 DTS cases: two positive, eight negative).

The workflow compiles each generated DTS with the pinned ACK `dtc` and validates:
- SM8250 with one power domain — expected PASS.
- SM8250 with two power domains — expected PASS.
- SM8250 with seven clock names — expected FAIL.
- SM8250 with nine clock names — expected FAIL.
- SM8250 with three power domains — expected FAIL.
- SM8150 with two power domains — expected FAIL.
- VDDP supply without its max-microamp property — expected FAIL.
- VCCQ-parent supply without its max-microamp property — expected FAIL.
- VDDP max-microamp set to zero — expected FAIL.
- VCCQ-parent max-microamp set to zero — expected FAIL.
- VCCQ-parent max-microamp set to zero — expected FAIL.

The SM8150 negative fixture uses its valid nine-clock/two-register layout so the expected failure isolates the non-SM8250 two-domain restriction. The SM8250 nine-clock fixture has nine clock names, including the extra `ice_core_clk`, and nine clock phandles.

ROUND32 is not applied: the fixed ACK `qcom,sc7180-ufshc.yaml` already selects `qcom,sm8250-ufshc` and defines the eight-clock SM8250 branch. Applying ROUND32 would select the same compatible a second time through `qcom,ufs.yaml`, producing duplicate schema matches. ROUND57 is not applied verbatim because it targets the wrong `qcom,ufs.yaml` schema. The actual SM8250 schema is `qcom,sc7180-ufshc.yaml`; its non-SC7180 branch requires `clock-names.minItems: 8` but does not cap the list at eight. A branch-local correction adds `maxItems: 8` to that exact branch, so the 7/9 fixtures exercise the intended cardinality. The original ROUND32/ROUND57 canonical drafts remain untouched.

## ROUND63 PHY fixtures

- no optional property — expected PASS (legacy path);
- empty boolean `vdda-phy-always-on;` — expected PASS;
- malformed cell-valued `vdda-phy-always-on = <1>;` — expected FAIL.

These are separate from the UFS fixtures and validate the optional PHY property against the same processed schema.

## Evidence publication

The workflow writes actual command output to:
`kernel-baseline/round61/hosted-ufs-validation-latest.md`

It also uploads the generated DTBs and validation logs as an Actions artifact. Its path filters exclude progress/result reports, so publishing evidence does not recursively retrigger validation.

## Current result boundary

No fixture PASS/FAIL result is asserted in this report yet. The previous hosted run `45435020774` proved the earlier UFS patch application and some schema tooling, but it predates ROUND63 integration and these explicit UFS/PHY fixture tests. Wait for the new branch-published result and fix any actual schema/test failures before marking Phase B complete.


## Hosted run 83 diagnostics and harness correction

Run `45443538190` passed Phase-A source gates and reached schema validation. The original ACK UFS example's direct `dt-validate` command returned exit code 0 while still printing `power-domains` and `unevaluatedProperties` diagnostics. Therefore a zero exit code is not a sufficient success signal for this validator version. The fixture gate now checks output content: positive fixtures must produce an empty diagnostic log; negative fixtures must produce the expected property diagnostic. The processed schema is retained as an artifact with its SHA-256 for inspection.

The first fixture compile attempt exposed a DTS syntax issue in the generator: root `interrupt-parent` was emitted after a child node. It has been moved into the root property block before all subnodes. The next hosted run will compile all ten UFS fixtures and then test the three PHY fixtures. The extracted UFS example is still compiled by dt_binding_check, but it is not passed to standalone dt-validate as a gate: the example contains external provider labels (for example &gcc) without their provider nodes, so the extracted DTB carries placeholder phandles and cannot prove provider cell counts. The direct diagnostic output is retained. The self-contained fixtures below define real provider nodes and #*-cells, and are the positive/negative schema-validation gates.


## ROUND32 superseded by the pinned ACK's existing SM8250 binding

Source inspection of the exact ACK commit showed `qcom,sc7180-ufshc.yaml` already selects `qcom,sm8250-ufshc`, defines its compatible tuple, and supplies the eight-clock SM8250 branch. The branch-local ROUND32 draft adds the same compatible to `qcom,ufs.yaml`, causing both schemas to select the same SM8250 node. The workflow now skips ROUND32 rather than introducing duplicate schema selection. The canonical ROUND32 draft remains untouched.

ROUND52-0001's four optional supply/load properties and pairing conditions have been moved from `qcom,ufs.yaml` into the shared `qcom,ufs-common.yaml` binding, because the actual SM8250 binding is `qcom,sc7180-ufshc.yaml` and it also references that common schema. This makes the properties available to both Qualcomm UFS binding families without duplicate selection. The branch-local patch still applies after ROUND36; canonical ROUND52 files remain unchanged.


## Follow-up corrections — 2026-11-25

- The hosted validator now pins `dtschema==2023.9`, the minimum declared by the immutable ACK Makefile, for deterministic compatibility with this kernel baseline.
- The SM8250 provider-backed fixtures use `#power-domain-cells = <1>` and matching `<&pdN 0>` specifiers. Zero-cell providers made the encoded power-domains arrays malformed and produced misleading cardinality errors.
- Corrected schema patch: `kernel-baseline/round61/patches/round32-corrected-sc7180-clock-names.patch`. It adds `maxItems: 8` to the non-SC7180 branch of `qcom,sc7180-ufshc.yaml`; this is the schema selected for `qcom,sm8250-ufshc` in pinned ACK. The initial patch hunk-count mismatch was fixed; real `git apply --check` is pending in run 45448394286.
- The extracted `qcom,ufs.example.dtb` standalone validation diagnostics are retained but are not used as a gate because its example has unresolved external provider phandles. `dt_binding_check` still extracts and compiles the example; the self-contained provider-backed fixtures remain the authoritative validation gate.
- Current Phase B status remains PENDING until the latest hosted run completes all UFS and PHY positive/negative cases and the kernel `dt_binding_check` command.


### ROUND36 cardinality correction discovered from processed schema

The hosted run 45448394286 successfully applied the patch series and passed all pre-schema gates, but the one-domain SM8250 fixture failed. Inspection of the retained processed-schema.json showed that dtschema 2023.9 expands maxItems: 2 without an explicit minItems into minItems: 2, maxItems: 2. This contradicted ROUND36's stated intent to allow either one or two domains. Added round61/patches/round36-corrected-power-domain-range.patch to set minItems: 1 on the shared power-domains property; the SM8250 conditional then caps it at two, while the non-SM8250 else branch caps it at one. Both UFS validation and manifest-pinned build workflows apply this correction immediately after ROUND36. Latest UFS run is pending.


### Patch order note

The shared-schema patch ROUND52-0001 replaces the common binding file as a full-file hunk. Therefore the explicit minItems: 1 correction for ROUND36 must be applied after ROUND52-0001, not before it. Both hosted workflows now use: ROUND36 → ROUND52-0001 → round36-corrected-power-domain-range.patch → round32-corrected-sc7180-clock-names.patch. The failed run 45449480649 stopped at the next ROUND52 patch because the correction had initially been applied before that replacement; the sequence has been corrected and a fresh run is pending.


### Conditional minItems correction

Run 45449803857's retained processed-schema.json confirmed that dtschema 2023.9 converts the SM8250 conditional then-branch's maxItems: 2 into minItems: 2 independently of the shared property's minItems: 1. The branch-local correction now sets minItems: 1 in both the shared power-domains property and the SM8250 then-branch, leaving the non-SM8250 else branch exactly one. This preserves the intended SM8250 cardinality range of one or two domains. A fresh hosted run is pending.


## Final hosted result — PASS (run 45451513173)

The latest pinned-source hosted run completed successfully on 2026-11-24 UTC. It fetched and verified ACK `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`, applied the ordered UFS + ROUND63 PHY + Kleaf patches using real `git apply --check` / `git apply`, passed `git diff --check`, strict checkpatch, buildifier and all 9 config-helper unit tests, then completed the authoritative `make ARCH=arm64 dt_binding_check` command with dtschema 2023.9.

The archived self-contained fixture logs establish the expected matrix:

- UFS positive: SM8250 with one power domain — empty diagnostics (PASS).
- UFS positive: SM8250 with two power domains — empty diagnostics (PASS).
- UFS negative: seven clock names, nine clock names, three power domains, SM8150 with two power domains, missing VDDP load, zero VDDP load, missing VCCQ-parent load, zero VCCQ-parent load — each rejected with the expected property diagnostic (8/8 PASS).
- PHY positive: legacy node without `vdda-phy-always-on` and node with the empty boolean property — both empty diagnostics (2/2 PASS).
- PHY negative: cell-valued `vdda-phy-always-on = <1>` — rejected as not boolean (PASS).

Artifact: `round61-ufs-phy-validation`, GitHub Actions artifact ID `14947424627`, 1,607,562 bytes. Processed-schema SHA-256: `da083e8307d1f903d5784392b3cba29542343f49964482882b84f13a478447f6`. Applied-source diff SHA-256 remains `b6897118cbef2fe36216d8fa00c22707531b7d6ba6aa5b35417c547185d54b90`.

The dt_binding_check log reports two unrelated malformed upstream YAML files ignored by the kernel schema scanner (`firmware/gunyah-cma-mem.yaml` and `iommu/pkvm,pviommu.yaml`); the modified UFS/PHY schemas and explicit fixture gates completed successfully. The upstream UFS example's standalone diagnostic log is empty in this run. This result closes Phase B for the current patch set; it does not prove board-DTS/DTB correctness or runtime regulator behavior.


## ROUND63 regulator lifetime / remove-order source review

A follow-up read of the exact pinned ACK source confirms the normal UFS consumer-first shutdown path:

- `ufs_qcom_remove()` calls `ufshcd_pltfrm_remove()`; the latter calls `ufshcd_remove()`.
- `ufshcd_remove()` reaches `ufshcd_hba_exit()`, which calls `ufshcd_variant_hba_exit()` while the UFS Host driver is still bound.
- The Qualcomm variant exit callback `ufs_qcom_exit()` calls `phy_power_off()` and `phy_exit()`; the consumer's managed PHY reference is released later during its devres teardown.
- `phy_get()` creates a `DL_FLAG_STATELESS` device link. The link gives ordering semantics but does not guarantee that manually unbinding the QMP PHY provider will first unbind every UFS consumer.
- The ROUND63 cleanup action is registered after `devm_regulator_bulk_get_const()`, so devres LIFO ordering runs the action before the managed regulator handles are released.

This supports normal consumer-first removal and regulator-handle cleanup ordering. It does **not** establish forced provider-unbind safety. Do not manually unbind the QMP PHY provider while the UFS Host remains bound; no forced-unbind test is required for initial bring-up. Runtime regulator measurements and actual PHY power-cycle/suspend-resume testing remain hardware gates.


## Re-run after validator hardening — PASS (run 45457083961)

A later hosted run repeated the full source/schema gate at head `055e4b5a51bbfd1c76a04ff15d468f9879c5a7cf` and published `hosted-ufs-validation-latest.md` with **Job status: success**.

- Exact ACK source identity verified.
- All ordered UFS, ROUND63 PHY and ROUND58 Kleaf patches applied; final diff check passed.
- Strict checkpatch passed (ROUND63 only ignores the known upstream `CAMELCASE` classification for `init_load_uA`).
- Buildifier passed.
- Updated config-helper **11-test suite passed**, including `CONFIG_BLOCK` and `CONFIG_ARM_SMMU_QCOM` missing/module rejection tests.
- `make ARCH=arm64 dt_binding_check` completed successfully with dtschema 2023.9.
- UFS fixtures: 2/2 positives clean; 8/8 negatives rejected with expected diagnostics.
- PHY fixtures: 2/2 positives clean; malformed boolean fixture rejected with expected diagnostic.
- Extracted upstream UFS example standalone validation log is empty.
- Processed schema SHA-256: `da994937d63cca2176a5065e8119be7ecd8b45c4939729f1810a8a8f5cc8dc50`.
- Applied diff SHA-256: `b6897118cbef2fe36216d8fa00c22707531b7d6ba6aa5b35417c547185d54b90`.
- Artifact: `round61-ufs-phy-validation`, ID `14951770706`.

The scanner again noted two unrelated malformed upstream YAML files that it ignored (`firmware/gunyah-cma-mem.yaml` and `iommu/pkvm,pviommu.yaml`). The modified UFS/PHY schema and explicit fixture gates passed. This re-run closes the schema/source validation for the current patch set; it does not prove final board DTS, hardware regulator behavior, or a compiled Image.
