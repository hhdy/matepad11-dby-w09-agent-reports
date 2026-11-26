# AI1 ROUND141 Independent Review and ROUND142 Disposition

- Reviewer: AI1 (ChatGPT)
- Date: 2026-11-26
- Reviewed executor: 2号 AI (independent AI collaborator; not 2号 Agent and not WorkBuddy Agent)
- Report: firmware-analysis/round141/AI2_ROUND141_CANDIDATE_PREBOOT_ARCHITECTURE_RISK_REVIEW.md
- Branch: ai2/round141-candidate-preboot-risk-review
- Report blob: f2333fe1b8f7202ec671174b93df2e68ca760863
- Candidate tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- Fixed ACK: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9

## 1. AI1 disposition

**ACCEPTED WITH ONE TERMINOLOGY CORRECTION AND ONE EVIDENCE-BOUNDARY QUALIFICATION.**

2号 AI's main architecture conclusions are supported by the fixed ACK source and accepted ROUND135–ROUND140 artifacts. In particular, the report correctly keeps physical PMIC inputs, runtime MMCX/MX behavior, final post-ABL memory, actual ABL policy, AVB trust verification and device recovery blocked.

The conclusion **NOT READY — additional offline evidence is required** is accepted. First device boot remains BLOCKED / NOT AUTHORIZED.

## 2. Accepted technical findings

### 2.1 UFS driver consumers

The following mapping is accepted within the inspected candidate and HOS4.3 KONA v2.1 evidence:

- PHY vdda-phy → PM8150 L5, vdda-pll → PM8150 L9; fixed ACK's SM8250 QMP UFS PHY bulk-regulator table consumes these names and enables them before PHY clocks.
- Host vcc → L17, vccq → L6, vccq2 → S4; fixed ACK UFS platform/core paths parse and operate these regulator names.
- Candidate qcom,vddp-ref-clk-supply → L6 is consumed by frozen candidate patch 06 through devm_regulator_get("qcom,vddp-ref-clk"), regulator_set_load() and regulator_enable(). This is candidate-only behavior, not unpatched ACK behavior.
- Candidate qcom,vccq-parent-supply → S8 has no consumer in the inspected candidate evidence. Its presence in DT alone does not enable S8 or create a dependency.
- The candidate omits HOS4.3 vdd-hba-supply → ufs_phy_gdsc and expresses the GDSC through the host power-domains list. The fixed ACK missing-vdd-hba path is non-fatal and treats it as absent/assumed enabled at the regulator-parser level. It does not prove hardware-equivalent sequencing.

The report correctly states that static consumer links do not prove the physical upstream input of any rail, successful runtime enable, or UFS link startup.

### 2.2 MMCX / MX / GDSC

Direct fixed ACK source confirms:
- generic dev_pm_domain_attach_list() attaches each declared domain by index and creates supplier device links;
- PD_FLAG_DEV_LINK_ON adds DL_FLAG_RPM_ACTIVE;
- candidate patch 5 attaches both ordered UFS host domains and maps the UFS OPP's single required_dev slot to index 0 / MMCX;
- SM8250's RPMHPD_MMCX table entry selects the plain mmcx descriptor with no .parent;
- a separate mmcx_w_cx_parent descriptor exists but is not selected for SM8250;
- CX is separately mapped to cx_w_mx_parent.

Therefore the candidate's static dual-domain attachment is real, but the selected SM8250 MMCX descriptor does not propagate an MX vote through a parent pointer. This remains a runtime/hardware compatibility blocker, not a source-level defect proven by this review.

### 2.3 Memory and reservation gates

Accept the exact ACK behavior:
- early_init_dt_scan_memory() decodes memory tuples and skips a tuple if size == 0;
- early_init_dt_scan_nodes() calls the memory scan before usable-memory-range and KHO checks;
- the candidate's zero-size /memory tuple therefore contributes no usable RAM through that tuple.

The candidate's 18 reserved-memory children and vendor FDT #0's 37 children are different device-tree artifacts. The count difference alone is not evidence that the candidate is defective, but no per-node range, ownership or consumer equivalence is established. Do not copy all 37 vendor reservations blindly.

The minimum sufficient memory evidence remains the final post-ABL FDT handed to Linux, including usable /memory/reg tuples, every relevant reserved-memory reg/flag and consumer relation, and the actual handoff route.

### 2.4 Image reproducibility and fetch-policy assessment

Accept:
- Image size matches across ROUND135 and ROUND140; Image digest differs.
- A per-build generated module-signing certificate is a sound explanation for at least part of the Image digest change.
- The BTF delta is reported with byte-level attribution, but no exact BTFGen/pahole version, binary identity and generation command were retained in the report. Its general reproducibility status remains PARTIAL / UNRESOLVED.
- The R3 prior claim that the differing Image was caused by embedded staging paths is not supported by the ROUND140 report's byte-level comparison.
- ROUND140's external Kleaf repository fetch statement is insufficient to prove either cache-only access or a prohibited payload download. The correct status remains UNRESOLVED, not silently COMPLIANT.

No rebuild, dependency fetch, signing operation or access to another Agent's private workspace is authorized to resolve these questions.

## 3. Required terminology correction — Device Tree node availability is not regulator enablement

ROUND140 §7.1 reports provider status as "absent → enabled". This wording is ambiguous and must not be repeated as evidence that the electrical regulator output is on.

Correct interpretation:
- absent status means the Device Tree node is available by the standard OF availability convention (it is not marked disabled);
- it does not establish that the regulator hardware is enabled, has a valid upstream input, has received an RPMh request, or is supplying voltage.

Accordingly, use wording such as "DT node available (status property omitted); runtime regulator enable UNKNOWN". This correction applies to all six UFS rail provider nodes, including S8. The report's overall UNKNOWN / BLOCKED conclusions already preserve runtime uncertainty, so this is a terminology correction, not a change to its final gate matrix.

## 4. Evidence-boundary qualification

The report properly distinguishes direct fixed-ACK source inspection from candidate facts inherited from ROUND140. The exact candidate qcom,vddp-ref-clk-supply consumer was identified by ROUND140 as patch 06, but ROUND141 itself relies on that report/patch record rather than publishing a new candidate tree checkout. Treat it as candidate patch/report-confirmed; do not describe it as independently rebuilt or re-read from a new candidate worktree in ROUND141.

The report's source references and file:line claims for fixed ACK are consistent with source excerpts independently inspected by AI1:
- drivers/base/power/common.c:193-275
- include/linux/pm_domain.h:20-48
- drivers/pmdomain/qcom/rpmhpd.c:125-153, 465-482
- drivers/of/fdt.c:1034-1072, 1246-1274
- drivers/ufs/host/ufshcd-pltfrm.c:175-195
- drivers/ufs/core/ufshcd.c:9499-9612, 10027-10084
- drivers/phy/qualcomm/phy-qcom-qmp-ufs.c:1208-1211, 1832-1854, 1894-1907, 2126-2130

## 5. Accepted first-boot matrix

| Gate | AI1 disposition |
|---|---|
| 23-patch candidate identity | PASS |
| Independent source / Kleaf / DTB reproduction | PASS with Image digest qualification |
| UFS consumer/provider/driver links | CONDITIONAL — static, with candidate patch 06 and inert S8 parent property distinguished |
| Physical PMIC inputs L5/L6/L9/L17/S4/S8 | BLOCKED |
| S8 effective consumer and enable sequence | BLOCKED |
| MMCX/MX runtime vote equivalence | BLOCKED |
| Final post-ABL FDT / usable RAM | BLOCKED |
| Reserved-memory ranges and ownership | BLOCKED |
| Device DTBO partition identity / selected entry | CONDITIONAL |
| ABL boot-v2 / DTB / independent ramdisk policy | BLOCKED |
| AVB trust verification / footer provenance | BLOCKED |
| Device-matched backups / tested HOS4.3 recovery | BLOCKED |
| First device boot | NOT AUTHORIZED |

## 6. ROUND142 disposition

ROUND141 does not identify a proven source-level defect requiring an immediate patch change. Its remaining offline-verifiable uncertainty is narrowly defined:
1. BTFGen/pahole exact tool identity and BTF generation command from existing ROUND140 logs;
2. exact Bazel/Kleaf external repository fetch/cache details from existing ROUND140 logs;
3. candidate patch/source readback for the VDDP REF_CLK consumer and proof that no candidate consumer exists for qcom,vccq-parent-supply;
4. correct interpretation of omitted provider status properties.

These items are assigned to 2号 Agent in ROUND142 because it executed ROUND140 and is the proper owner of its own local build logs. This does not authorize WorkBuddy Agent or AI2 to access 2号 Agent's private workspace.

ROUND142 must be read-only, use only artifacts already produced by ROUND140 in its own round directory, perform no build or network access, and stop after uploading one sanitized addendum. If the logs do not exist, report NOT FOUND and do not recreate them.

Physical PMIC parent topology, final ABL FDT, ABL partition policy, runtime MMCX/MX votes, device-matched backup and HOS4.3 recovery route cannot be closed by another report-only local log audit. Those require authoritative vendor board documentation or a separately user-authorized and reviewed device evidence collection. No such device access is authorized here.

## 7. Final disposition

**ROUND141 ACCEPTED — NOT READY. ROUND142 MAY PROCEED AS A BOUNDED EXISTING-ARTIFACT PROVENANCE ADDENDUM.**

No source-level defect is declared solely from the current evidence. The 23-patch candidate remains unchanged. First real-device boot remains BLOCKED / NOT AUTHORIZED.

— END OF AI1 REVIEW —
