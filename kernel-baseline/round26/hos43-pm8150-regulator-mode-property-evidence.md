# ROUND26 — HOS4.3 PM8150 regulator mode/DRMS property evidence boundary

Date: 2026-11-24

Status: source-side review of ROUND7 sanitized inventory and same-device public DTS. A targeted local-only property verification is queued as ROUND13, to run only after the current ROUND12 AVB task. No new local FDT parse was performed in this review.

## 1. What ROUND7 does and does not prove

The published ROUND7 dtb_property_inventory.csv contains PM8150 regulator-name and min/max-microvolt rows for the deterministic base-FDT candidate and two valid alternate candidates. It does not contain any rows for:
- regulator-initial-mode;
- regulator-allow-set-load;
- regulator-allowed-modes;
- regulator-boot-on;
- regulator-always-on.

The inventory is filtered by category/property scope. Therefore zero rows for these properties is NOT evidence that they are absent from the full base FDT or DTBO entry 8. ROUND9's UFS supply report resolves the voltage rails and consumer load values, but likewise does not record mode/DRMS provider constraints.

## 2. Why this matters for ACK PM8150 L5/L6/L9

ACK android17-6.18 PM8150 L5/L6/L9 use PMIC5 NLDO hardware data with rpmh_regulator_vrm_drms_ops and hpm_min_load_uA=30000. The implementation chooses NORMAL/HPM when aggregate load is >=30mA and IDLE/LPM below it, but only if the regulator constraints allow DRMS mode changes and list allowed modes.

Without regulator-allow-set-load, regulator core's drms_uA_update() treats DRMS as not allowed and returns success without a hardware mode update. With no regulator-allowed-modes, a DRMS-capable driver also cannot make a valid transition. Therefore these DTS constraints are meaningful hardware policy, not harmless annotations.

The current board DTS had copied LPM/HPM allowed modes and allow-set-load from the public same-device reference pattern on other PM8150L rails. That was not proven for HOS4.3 PM8150 L5/L6/L9. In particular, if L9's QMP PLL load is only 18.8mA, a speculative DRMS enable could select LPM under the ACK 30mA threshold, which may not preserve the HOS PLL power mode.

## 3. Conservative first-storage draft correction

The board DTS draft now:
- retains the HOS4.3-confirmed PM8150 output voltages and UFS load requests;
- removes unverified regulator-allow-set-load and regulator-allowed-modes from PM8150 L5/L6/L9;
- retains HPM as the provisional initial mode for S4/L5/L6/L9/L17 based on the same-device public Linux HOS4.2 structural reference;
- clearly labels the HPM initial-mode values as a cross-reference assumption, not an HOS4.3 local fact;
- leaves S8 initial mode unspecified because neither HOS4.3 property evidence nor an exact HOS4.3 mode read is available.

With those constraints, L6's UFS VCCQ and VDDP regulator_set_load calls remain API-level votes but are not expected to change mode in this conservative draft. The provider starts in the provisional HPM mode. A future confirmed HOS4.3 DRMS configuration can re-enable dynamic mode transitions after ROUND13.

## 4. ROUND13 — queued read-only local verification

After ROUND12 AVB metadata inspection is complete, the next local Agent task will inspect only the original HOS4.3 base FDT and stock DTBO entry 8 provider/overlay properties for:
- regulator-initial-mode;
- regulator-allow-set-load;
- regulator-allowed-modes;
- regulator-boot-on;
- regulator-always-on;
- regulator-system-load (if present).

Target regulator nodes: PM8150 S4/L5/L6/L9/L17 and PM8150A S8. The result must distinguish base-FDT properties from entry8 overlay additions and resolve phandles only where needed.

Use only the previously reviewed ROUND3 parser and already-existing ROUND3 local work copies. No re-extraction, no new parser, no install, no WSL, no security-policy changes, no device connection, no image writes, no compile. If the source copies or parser are unavailable, report BLOCKED. Only a short sanitized text report may be uploaded; no binaries or full paths/hashes.

Do not run ROUND13 concurrently with ROUND12. ROUND12 remains the sole active Agent task until its report is uploaded.

## 5. References

- ROUND7 local inventory: firmware-analysis/round7/dtb_property_inventory.csv on firmware-audit-v1.
- Same-device public Linux 7.0 structural cross-reference (explicit HPM initial modes; PMIC provider layout): https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts
- ACK PM8150 regulator provider ops and 30mA threshold: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/qcom-rpmh-regulator.c
- ACK regulator core DRMS constraint/aggregation: https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/regulator/core.c

## 6. Verification status

| Item | Status |
|---|---|
| HOS4.3 regulator names/output voltage ranges | LOCAL INVENTORY / ROUND9 EVIDENCE |
| HOS4.3 original initial-mode/DRMS properties | UNKNOWN; not present in filtered report scope |
| Same-device HOS4.2 HPM initial-mode pattern | PUBLIC SOURCE REVIEWED |
| ACK LDO DRMS threshold and mode policy | SOURCE REVIEWED |
| Current draft removes unverified DRMS permission on L5/L6/L9 | UPDATED |
| ROUND13 exact local base-FDT + DTBO property inspection | QUEUED AFTER ROUND12 |
| DTS schema / Kconfig / build / runtime | NOT_RUN |

