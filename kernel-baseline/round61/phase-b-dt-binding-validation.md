# Phase B — real DT binding validation and negative fixtures

**Date:** 2026-11-25  
**Branch:** `ai-parallel/stagea-port-until-boot`  
**Pinned source:** `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Status:** TESTS WIRED INTO HOSTED RUNNER; RESULTS PENDING. Do not mark Phase B PASS until the branch-published hosted log proves every expected result.

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
