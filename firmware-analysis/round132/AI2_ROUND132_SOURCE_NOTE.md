# KUnit seam v2 — source note

## Delivery identity

- Deliverable: `firmware-analysis/round132/round132-kunit-seam-v2.patch`
- Source baseline: previously accepted ROUND35S KUnit seam (`firmware-analysis/round35s/round35s-kunit-seam.patch`, source blob `dfd6594b3ec4a80f6f21b7c3b18a69cdd2bb3a26`).
- Patch SHA-256: `1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f`
- Patch size: 16797 bytes
- Patch base commit: `7578c9f3eb56ec41ac5ff9c027e16d3bd9103f51` (temporary local parent commit; not pushed)
- Patch base tree: `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`
- Reproducible base definition: fixed ACK `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` plus all 17 frozen production patches applied in the recorded ROUND35S order. This patch is relative to that resulting tree, not directly to the bare ACK commit.

## Why the option is bool

`CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST` is declared as `bool`, not `tristate`. The observer is called from the built-in regulator core (`drivers/regulator/core.c`). The observer declaration/definition and KUnit helper functions use `#ifdef CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST`. With `tristate=m`, Kconfig emits the `_MODULE` form rather than the plain macro tested by those guards, so the helper and built-in observer could be compiled inconsistently. `bool` ensures the test seam and observer are selected together as built-in code when enabled.

The Kconfig help keeps the option off by default and excludes it from `KUNIT_ALL_TESTS`; it describes isolated-test use without claiming that `default n` alone prevents explicit selection by a product configuration.

## Patch scope

Seven paths are included:
- `drivers/regulator/Kconfig`
- `drivers/regulator/Makefile`
- `drivers/regulator/core.c`
- `drivers/regulator/kunit-proxy-consumer.dtso`
- `drivers/regulator/proxy-consumer-kunit.c`
- `drivers/regulator/proxy-consumer.c`
- `include/linux/regulator/proxy-consumer.h`

The patch contains the existing KUnit test source and overlay, test-only observer/helper seams, and Kconfig/Makefile wiring. The changes in `core.c` and `proxy-consumer.c` are test-only instrumentation/helper seams guarded by the test config; no production regulator proxy-consumer decision, vote, registration, teardown or matching logic is changed. The frozen 17 production patches are not edited or included. No board DTS, PMIC data, or product `.config` is changed.

## Verification status

This is a source delivery for independent review, not a test report. No new KUnit run, host regression, product-config check, or checkpatch run was performed while preparing this v2 delivery. The prior ROUND35S report records the earlier accepted seam's UML KUnit 1/1 and host regressions, but the recipient must independently validate this exact v2 patch and its SHA-256 before treating it as verified.

**Responsibility:** implementation and source delivery by 2号 AI; independent execution by the local Agent; patch review by 1号 AI.