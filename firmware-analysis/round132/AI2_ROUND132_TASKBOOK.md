# AI2-ROUND132 — KUnit test option linkage correction

- **任务归属 / 实现责任：2号 AI 专属。**
- **代码实现者：2号 AI。**
- **测试执行者：用户本地 WorkBuddy Agent，只负责按本任务书验证，不编写/修复内核代码。**
- **独立审查者：1号 AI（ChatGPT）。**
- 这是 ROUND35R 的 test-only follow-up，不是新的产品内核补丁，不修改冻结的 17-patch Stage A series。
- 固定 ACK：`8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`。
- 固定 17-patch manifest：`kernel-baseline/round61/round32-stagea-series.txt`，blob `9a93b7e3a500d807533517a92b98fe244b2ea456`。
- AI2 implementation base: `ai-parallel/stagea-port-until-boot@f0b00e38c8222be14adfb21f122db7f8cac94c14`.
- AI2 isolated task branch: `ai2/round132-kunit-option-bool`, created from the exact base above. Do not commit this test-only seam into the frozen production patch series.

## 1. Why this task exists

ROUND35R successfully generated and ran the independent UML KUnit seam using:

`CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST=y`

However, the patch declares that option as Kconfig `tristate`, while the KUnit-only helpers and core unregister observer are guarded with:

`#ifdef CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST`

For tristate `m`, Kconfig exposes `CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST_MODULE` instead, so those built-in APIs/observer are omitted while the test object may still be selected as a module. The passing `=y` run does not test that invalid state.

Because `drivers/regulator/core.c` is built into regulator core and calls the observer, a module-only observer is not a viable design. The preferred correction is changing the test-only Kconfig option from `tristate` to `bool`, with dependencies continuing to require KUnit, the production proxy consumer, OF and OF overlay.

## 2. Required AI2 implementation

1. Start from the exact AI2 base commit above in the isolated branch.
2. Recreate the exact ACK + frozen 17-patch applied tree using the manifest, then apply the accepted ROUND35R seam patch:
   - seam source SHA-256: `14c62ec878e701a10e6eef211704262300e2ac742286c18f1e5c7496eaeb9049`.
3. Change only the Kconfig test option type from `tristate` to `bool`, unless an additional strictly necessary Kconfig constraint is demonstrated and documented. Do not change any production proxy-consumer logic, 17-patch production patch, device DTS, product config or product target.
4. Export a new seam-v2 patch relative to the precise 17-patch-applied base. It must include the full accepted ROUND35R seam plus the Kconfig correction and must not duplicate any of the 17 production patches.
5. Add a short source note explaining why bool is required: core's observer is compiled into built-in regulator core, so test config and observer must be built in together.
6. Keep the implementation on `ai2/round132-kunit-option-bool`; do not merge/cherry-pick into the Stage A 17-patch series or AI1 branch.

## 3. Agent validation (test-only; wait for AI2 source artifact)

After 2号 AI uploads the exact seam-v2 patch and its hash/source note, the Agent shall:

1. Create two new disposable worktrees from the fixed ACK. Never reuse ROUND35 or ROUND35R workspaces.
2. Apply the 17 production patches in manifest order, checking each patch identity, `git apply --check`, `git apply`, and `git diff --check`.
3. Apply seam-v2 in a second clean tree; require `git apply --check` and `git apply` success with zero fuzz. Record offsets if any.
4. Inspect Kconfig's resolved type: it must be `bool`, not `tristate`. Confirm the generated KUnit `.config` has `CONFIG_REGULATOR_PROXY_CONSUMER_KUNIT_TEST=y`; confirm the resulting built tree contains the observer and KUnit helper symbols.
5. Re-run the same UML KUnit suite. Preserve the actual KUnit command, generated `.config` hash, full TAP output and exit code. Require the suite to run and pass 1/1.
6. Re-run host regression suites 38/38 and 83/83 using the exact committed host harness from the AI2 base.
7. Verify product `.config` SHA-256 remains `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15` and the KUnit option remains absent from product config.
8. Run `git diff --check` and `checkpatch.pl --strict`; disclose missing SPDX checker dependencies without hiding errors.
9. Restore/remove only the disposable worktrees and files created by this task. Do not delete any previous worktree, build tree or artifact.
10. Upload a single result report plus seam-v2 and exact logs to `firmware-analysis/round132/` on `firmware-audit-v1`. No source code is to be edited by the Agent.

## 4. Safety and stop boundary

- No tablet connection of any kind: no USB, ADB, fastboot, recovery, serial or device interface.
- No HOS4.3 firmware access, extraction, upload or editing.
- No product Image build; no boot.img, DTB/DTBO, ramdisk, vbmeta, AVB/footer or flash package.
- No product defconfig, Kleaf target, DTS, binding, PMIC, voltage, supply-parent, ARC/VRM or memory map changes.
- Frozen 17-patch production series remains unchanged.
- This round only repairs the KUnit test option linkage. It does not authorize ROUND133 or any Phase E/F/G work.
- Agent stops immediately after publishing its report. 1号 AI reviews the evidence before any next task.

## 5. Expected deliverables

AI2 implementation branch:
- `firmware-analysis/round132/round132-kunit-seam-v2.patch`
- `firmware-analysis/round132/AI2_ROUND132_SOURCE_NOTE.md`

Agent report branch `firmware-audit-v1`:
- `firmware-analysis/round132/TEST_AGENT_ROUND132_REPORT.txt`
- `firmware-analysis/round132/round132-apply-check.log`
- `firmware-analysis/round132/round132-kunit-final-TAP.log`
- `firmware-analysis/round132/round132-checkpatch.log`
- `firmware-analysis/round132/round132-config-and-host-regression.log`

Do not write PASS unless the new exact seam-v2 patch is the one applied and the one that produces the reported TAP log.
