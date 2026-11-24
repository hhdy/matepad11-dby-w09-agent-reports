# ROUND54 — Independent UFS patch-series review

**Status:** REVIEW COMPLETE — ONE SCHEMA FINDING; NO FULL-TREE OR HARDWARE VALIDATION  
**Dedicated branch:** `ai-parallel/round54-ufs-review`  
**Fixed ACK:** `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Verdict:** `PASS WITH NON-BLOCKING FINDINGS`

## 1. Reviewed revisions and exact blob identities

Latest `main` snapshot was used for the canonical artifacts. Upstream source files were fetched at the immutable ACK commit above.

| Artifact | Blob SHA reviewed | Status |
|---|---|---|
| `kernel-baseline/round32/0001-dt-bindings-ufs-add-sm8250-compatible.patch.draft` | `efe2d932da34716c631de22d89aba19730cc7f50` | Reviewed; P3 finding |
| `kernel-baseline/round36/0001-dt-bindings-ufs-allow-sm8250-dual-power-domains.patch.draft` | `dad87ef8dfefee6141b8a7949982c007c4a03b4a` | Reviewed |
| `kernel-baseline/round37/0001-dby-w09-ufs-host-dual-genpd-dts.patch.draft` | `486654c8d0b1b785190253270f5e83f796f07362` | Reviewed |
| `kernel-baseline/round33/0001-scsi-ufs-qcom-sm8250-dual-genpd-required-opp.patch.draft` | `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5` | Reviewed |
| `kernel-baseline/round52/0001-dt-bindings-ufs-vddp-vccq-parent-supplies.patch.draft` | `c0ac84067a900022a077c748b7abb10345f1295f` | Reviewed |
| `kernel-baseline/round52/0002-ufs-qcom-sm8250-vddp-refclk-managed-lifecycle.patch.draft` | `fb34fbc9701bc7e7b56bb9078ee98c0cdd8caf78` | Reviewed |
| `dts/dby-w09-ack18-board.dts.draft` | `dd9035083458ea6ccdb5fdd852b7a1860509fbaf` | Reviewed as review-only draft |
| `kernel-baseline/round38/ufs-dual-genpd-patch-series-manifest.md` | `3b6a07c2c29b07f3e95af6d342f84117ecb993c9` | Context reviewed |
| `kernel-baseline/round45/ack-ufs-dual-genpd-all-opp-validation.md` | `02c1086fb2b7dac575b9ade13d7174725ce93bc8` | Context reviewed |
| `kernel-baseline/round49/ack-ufs-vddp-vccq-parent-devres-lifecycle-redesign.md` | `fc8558e520792ffd2c1aa3a735dcc5fb26909254` | Context reviewed |
| `kernel-baseline/round52/round52-storage-first-ufs-vddp-integration-and-binding-closure.md` | `acd35ab048a437e03957cf6a7f5ffd2c82885378` | Context reviewed |
| `kernel-baseline/round53/ack-storage-first-kconfig-fragment-static-closure.md` | `b471500b33e987453e4492c80113457f8a34e92e` | Read for context only; ROUND53 not duplicated |
| `dts/README.md` | `0dd09332079adde6945176a65d280bfae4a3f93e` | Context reviewed |

Pinned ACK source blobs examined:

| ACK source path | Blob SHA |
|---|---|
| `Documentation/devicetree/bindings/ufs/qcom,ufs.yaml` | `1dd41f6d5258014d59c8c8005bc54f7994351a52` |
| `Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml` | `962dffcd28b44b3489be5615c75e7270a0c45dc4` |
| `arch/arm64/boot/dts/qcom/sm8250.dtsi` | `adf6b49b52c48ca05ed6d0c1251f97ace664ef9d` |
| `drivers/ufs/host/ufs-qcom.c` | `a80c6998406dbc88c25dbd9977699ba481207efe` |
| `drivers/ufs/host/ufs-qcom.h` | `5f979daabd5323184eeee137cc8ecc076193979e` |
| `drivers/ufs/core/ufshcd.c` | `2cf7aa8e0a9472f9024d4251ac2f9d7da830e219` |
| `drivers/ufs/host/ufshcd-pltfrm.c` | `5ac7afe759346debfc2910fb219d8e491ba08b64` |
| `drivers/regulator/core.c` | `39d317ad73a33c4aa27e179cc436d8bf4daf5bcc` |
| `drivers/regulator/devres.c` | `2cf03042fddf4263d05c95e29dd534003fb8246c` |
| `drivers/base/dd.c` | `2996f4c667c42f7915260339ca588cda8e5b391a` |
| `drivers/base/devres.c` | `9893d656302d9795911b7e524f300999c395fef4` |
| `drivers/opp/of.c` | `505d79821584e28f454dae673cf85078762b2ec7` |
| `drivers/opp/core.c` | `157c84b689feba9ae2c446083e42de63e94a38a6` |

## 2. Executive verdict

The ROUND33 two-domain/required-OPP design and ROUND52 VDDP supply lifecycle are internally consistent with the inspected pinned ACK call paths at source-review level. I did not find a proven P1/P2 driver-lifecycle defect in the reviewed drafts.

One concrete, non-blocking schema gap remains in ROUND32: the SM8250 branch fixes the number of clocks at eight and enumerates eight names, but does not constrain the number of `clock-names` entries. The inherited common schema allows 7–9 names. An isolated candidate adds the matching exact-count constraint.

This is not a build or integration approval. The canonical drafts remain drafts and all full-tree / schema / DTB / build / boot gates remain open.

## 3. Findings

| ID | Severity | File / function / lines | Finding | Evidence | Consequence | Proposed fix |
|---|---|---|---|---|---|---|
| R54-001 | P3 | ROUND32 patch; `Documentation/devicetree/bindings/ufs/qcom,ufs.yaml`, new SM8250 conditional branch | The SM8250 branch constrains `clocks` to exactly 8 but leaves `clock-names` length unconstrained. | ROUND32 adds eight positional `clock-names.items` values but no `minItems`/`maxItems`. Pinned `qcom,ufs-common.yaml` lines 15–19 sets common `clock-names` to 7..9. JSON Schema tuple-style `items` does not by itself prohibit additional array entries. The actual SM8250 DTSI has eight clocks and eight names. | The binding can accept an SM8250 node with 7 or 9 `clock-names` entries even though the branch describes an eight-clock controller. This weakens validation and can let a malformed board DTS pass schema review. | Add `minItems: 8` and `maxItems: 8` under the SM8250-specific `clock-names` property. Candidate: `ai-parallel/round54/candidates/0001-qcom-ufs-sm8250-clock-names-exact-count.patch`. |

No other confirmed defect is reported. In particular, I did not find evidence to change the ROUND33 required-OPP mapping or the ROUND52 VDDP acquisition order based on the pinned source inspected.

## 4. Call paths and lifecycle evidence

### ROUND52 VDDP regulator

Pinned source evidence:

- `drivers/regulator/devres.c` lines 17–40: `devm_regulator_get()` registers a managed release which calls `regulator_put()`.
- `drivers/regulator/core.c` lines 2444–2474: `regulator_put()` requires prior enable/disable balance; `_regulator_put()` warns if `enable_count` remains nonzero.
- `drivers/ufs/host/ufs-qcom.c` lines 1504–1604: `ufs_qcom_init()` allocates `ufs_qcom_host` with devm, binds it to the HBA, initializes PHY/ICE state, and calls `ufs_qcom_setup_clocks()` after ICE initialization. ROUND52 inserts VDDP get/load/enable before that clock/PHY setup point.
- `drivers/ufs/core/ufshcd.c` lines 10716–10732: `ufshcd_remove()` stops the HBA and calls `ufshcd_hba_exit()`; the latter invokes variant exit before generic regulator and clock teardown.
- `drivers/ufs/host/ufshcd-pltfrm.c` lines 709–719: normal platform remove calls `ufshcd_remove()`; driver-core devres release follows the remove callback.
- `drivers/base/devres.c` lines 511 onward: `devres_release_all()` releases the device's managed resources after detach. `drivers/base/dd.c` `really_probe()` error cleanup also releases probe-time devres on failed probe.

Path assessment:

1. **Successful probe:** platform probe allocates the HBA; Qualcomm variant init allocates the host; the VDDP handle is acquired; the cleanup action is registered after the managed regulator get; load is set; regulator is enabled; then the PHY/clock setup proceeds. Flags are set only after the corresponding operation succeeds.
2. **Missing supply property:** helper returns without acquiring VDDP; this is intentionally optional.
3. **Present but malformed/missing load property:** u32 read fails or zero is rejected before regulator enable.
4. **Regulator provider unavailable:** `devm_regulator_get()` error, including `-EPROBE_DEFER`, is propagated. No cleanup action has been registered yet.
5. **Load-setting failure:** the already-registered action runs during probe unwind; both flags remain false, so no disable is attempted.
6. **Enable failure:** load flag is true but enabled flag is false; cleanup clears the load without issuing a disable.
7. **Later HBA initialization failure:** the action remains registered; HBA unwind/variant exit runs before device devres release, then the action cleans VDDP while the host/HBA managed allocations are still earlier in the devres stack.
8. **Normal remove:** `ufshcd_remove()` completes HBA/variant teardown and generic VCCQ shutdown before devres cleanup reaches the VDDP action; managed regulator put is later than the action because the action is registered after the get.

The action's `host->hba->dev` access is consistent with the observed devres registration order: the VDDP action is added after the HBA and host allocations, so LIFO cleanup reaches it before those earlier managed allocations are released.

**Failure limitation:** if `regulator_disable()` itself fails, the callback logs and returns; the subsequent managed `regulator_put()` is still required by devres. The regulator core explicitly warns if an enable count remains. This is a hardware/provider disable failure, not evidence that normal cleanup ordering is wrong. Do not add `regulator_force_disable()` for a shared L6 rail as a speculative workaround.

### ROUND33 GenPD / required-OPP

- The helper is called in `ufs_qcom_probe()` before `ufshcd_pltfrm_init()`, so the required-device mapping is installed before the generic UFS OPP table is parsed/initialized.
- It preserves the one-domain and no-domain path; the two-domain path fails closed unless index 0 is `qcom,sm8250-rpmhpd` / `RPMHPD_MMCX` and index 1 is `qcom,gcc-sm8250` / `UFS_PHY_GDSC`.
- It validates each available UFS OPP child, requires exactly one `required-opps` reference, checks the target's parent table and provider, and compares the target table node with the provider's advertised `operating-points-v2` node.
- Explicit OF-node references acquired by `of_parse_phandle()` / `of_get_parent()` are put on the success and error paths. The OPP-table iterator drops the current child on its error exit and the table reference is put at the common exit.
- `devm_pm_domain_attach_list()` and `devm_pm_opp_set_config()` are used before generic platform initialization. The OPP configuration token is managed by the OPP core; the attached-domain resources are managed by the device. Probe failure therefore unwinds those later registrations before earlier host/HBA resources.

No source-level defect was confirmed in these checks. Runtime provider readiness, actual deferred-probe behavior under the final DT, and domain transition semantics still require a real integrated build/device test.

## 5. Binding and DTS review

### ROUND32 + ROUND36 + ROUND52-0001

- ROUND32 adds `qcom,sm8250-ufshc` to the UFS binding selection and compatible enum, and gives it an eight-clock, one-register conditional.
- The ROUND32 conditional's eight clock names match the pinned SM8250 DTSI list: `core_clk`, `bus_aggr_clk`, `iface_clk`, `core_clk_unipro`, `ref_clk`, `tx_lane0_sync_clk`, `rx_lane0_sync_clk`, `rx_lane1_sync_clk`. The missing exact count is R54-001.
- ROUND36 raises the common `power-domains` ceiling to two and applies a compatible-scoped maximum of two for SM8250 and one for other Qualcomm UFS compatibles. This retains one-domain SM8250 compatibility.
- ROUND52-0001 documents both new supply properties as phandles and both maximum-load values as positive uint32 values. Its conditionals require the max-load property when the corresponding supply property exists. No incorrect type or property spelling was found.
- The binding has `unevaluatedProperties: false`; explicitly documenting the downstream Qualcomm supply extensions is necessary and ROUND52 does so.

### Board DTS

Pinned `arch/arm64/boot/dts/qcom/sm8250.dtsi` lines 2507–2589 establish:

- The inherited UFS Host has one `power-domains = <&gcc UFS_PHY_GDSC>` entry.
- It has exactly eight clock names and eight clock phandles.
- Its two available UFS OPP entries each point through one `required-opps` phandle to RPMhPD OPP levels.
- The `ufs_mem_phy` node is a separate node; in this source excerpt it carries its clocks and reset reference, not a separate `power-domains` property. ROUND37 changes the UFS Host's domain list, preserving GCC UFS_PHY_GDSC as index 1 and adding MMCX at index 0.
- The current main-branch board `.dts.draft` itself still has only the supply/status overlay and does not contain the ROUND37 dual-domain delta. The ROUND37 patch targets that review-only draft as a separate delta.

The board draft maps VDDP to PM8150 L6 with `qcom,vddp-ref-clk-max-microamp = <100>`; the unit is microamps and the same 100µA value is corroborated in the reviewed ROUND49 public KONA reference and ROUND52 design note. S8/VCCQ-parent remains declared as topology metadata but is intentionally not acquired or enabled by the ROUND52 driver. The draft preserves the documented RET policy and does not add an S8 enable vote.

**Integration boundary:** `dts/dby-w09-ack18-board.dts.draft` is not in an actual ACK DTS source path. ROUND37 is a draft delta against that file, not a compiled board DTS.

## 6. Candidate fix

Created only on the dedicated ROUND54 branch:

- `ai-parallel/round54/candidates/0001-qcom-ufs-sm8250-clock-names-exact-count.patch`
- Current candidate blob SHA: `6f3715c8b068556baf2993477c2387df98f8a574`
- Intended order: apply after ROUND32 adds the SM8250 conditional to `qcom,ufs.yaml`.
- Change: add `minItems: 8` and `maxItems: 8` to that branch's `clock-names`.
- This is an isolated candidate only. Canonical ROUND32 and later artifacts were not modified.

No real `git apply --check`, `dt_binding_check`, `dtbs_check`, YAML/schema validation, or full-tree patch application was executed for this candidate. It is a source-reviewed proposed correction, not a tested patch.

## 7. Not reviewed / blocked / not run

- No full ACK worktree was assembled; no full-series `git apply` or `git apply --check`.
- No `checkpatch.pl`, `dt_binding_check`, `dtbs_check`, `dtc`, Kconfig resolution, Kleaf/Bazel build, kernel image, DTB/DTBO build, or boot test.
- No actual DBY-W09 access, unlock, root, flash, partition write, or hardware test.
- ROUND53 Kconfig closure was read only for context; its scope was not repeated.
- No claim is made that any patch is buildable, schema-valid, bootable, or hardware-correct.

## 8. Completion handoff

- **Final branch:** `ai-parallel/round54-ufs-review`
- **Report path:** `ai-parallel/round54/ROUND54_REVIEW.md`
- **Verdict:** `PASS WITH NON-BLOCKING FINDINGS`
- **Finding:** one P3 schema exact-count gap in ROUND32 `clock-names`.
- **Candidate:** `ai-parallel/round54/candidates/0001-qcom-ufs-sm8250-clock-names-exact-count.patch`
- **Primary AI follow-up:** review R54-001 and decide whether to adopt the candidate into the canonical patch series. All integration/build/device gates remain outstanding.
