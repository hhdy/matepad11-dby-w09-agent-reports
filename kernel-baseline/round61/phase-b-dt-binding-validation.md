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

ROUND57 is not applied as a separate patch: ROUND32's SM8250 `clock-names.items` list contains exactly eight const entries, and the fixed ACK dt-schema meta-schema rejects redundant `minItems/maxItems` beside that fixed tuple. The 7/9 fixtures test the actual accepted cardinality directly.

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
