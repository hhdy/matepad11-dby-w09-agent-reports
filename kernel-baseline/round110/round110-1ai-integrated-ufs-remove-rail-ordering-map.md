# ROUND110 — 1号 AI integrated UFS remove/rail ordering map for Stage A

**Date:** 2026-11-25  
**Owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Pinned ACK:** `android17-6.18.33_r00` / `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`  
**Inputs:** ROUND90, ROUND96, ROUND97–102, ROUND105, ROUND107–109 and exact pinned UFS/regulator/PHY sources.  
**Boundary:** source/design review only; no driver, binding, DTS or AI2 branch changes.

## 1. Integrated shutdown order

The required consumer-first Stage-A UFS shutdown order is:

1. **Join the UFS-owned async scan** at the beginning of `ufshcd_remove()`, before any HBA state teardown.
2. Perform the ordinary UFS host remove sequence: SCSI host removal, IRQ disable and HBA stop.
3. Enter `ufshcd_hba_exit()`; the variant exit runs before generic UFS supply teardown.
4. Qualcomm `ufs_qcom_exit()` powers off/exits the QMP PHY. QMP sets PHY hardware power-down, disables clocks, drops the L9 PLL load/reference when possible, and sets the retained L5 PHY load to zero while keeping its one retained enable reference.
5. Generic UFS rail shutdown then processes VCC/L17, VCCQ/L6 and VCCQ2/S4. The VCC and VCCQ DRMS load requests must be set to zero **before** their regulator enable references are disabled. This avoids regulator-core post-decrement DRMS errors.
6. Generic HBA/device rails and clocks are shut down. VCCQ/L6 is now off as a UFS consumer, but the separate VDDP/REF_CLK L6 consumer remains enabled at 100µA.
7. `ufshcd_remove()` returns. Device devres release runs the later-registered VDDP custom action before the managed VDDP regulator put. The action must set its 100µA load to zero first, then disable its reference.
8. The generic HBA private-wrapper/host allocation are released in their registered devres order.
9. The QMP PHY provider has its own device lifetime. When that provider is eventually removed after the UFS consumer is gone, its custom action drains any remaining L5/L9 references before the managed regulator bulk handles are put.

The provider PHY link is stateless. This ordering describes normal UFS consumer-first removal; it does not authorize manually unbinding the QMP provider while a UFS consumer remains bound.

## 2. Shared L6 constraint

L6 is shared by:
- generic UFS VCCQ consumer (800mA active vote);
- Qualcomm VDDP/REF_CLK consumer (100µA vote).

The required order is therefore strict:

- QMP PHY shutdown happens first, but QMP uses L5/L9; it does not disable the VDDP L6 consumer.
- Generic UFS VCCQ load-zero and disable happen next; L6 may remain enabled at 100µA because VDDP is still active.
- VDDP load-zero and disable happen only in the later custom devres action.

Do not combine the VDDP cleanup into `ufs_qcom_exit()` or disable L6 from inside the QMP PHY path. The generic UFS VCCQ owner and Qualcomm VDDP owner are separate regulator handles with distinct lifetimes.

## 3. State objects are separate

The implementation must keep three independent state domains:

1. **UFS generic HBA-private state** — VCC voltage request, generic VCC/VCCQ/VCCQ2 load requests, and their consumer enable-reference state. This state belongs in the existing private `struct ufs_hba_priv` wrapper (ROUND102), not in a separate devm sidecar allocation. It must be reachable from every private UFS regulator helper, including runtime PM transitions.
2. **Qualcomm `ufs_qcom_host` state** — independent VDDP/REF_CLK regulator handle, its stored load request and its enable reference. This is not the generic UFS HBA-private state.
3. **QMP `struct qmp_ufs` state** — retained L5 enable, L5 stored load state, and trailing L9 enable/load state. This belongs to the PHY provider and is cleaned by the QMP provider own devres action.

Do not collapse these into one boolean or assume that the HBA sidecar owns QMP/VDDP handles.

## 4. Cross-layer acceptance conditions

A source-complete result must prove all of the following in the final integrated branch:

- The UFS-owned async callback has completed before `ufshcd_remove()` touches the HBA or starts any rail teardown.
- The normal HBA remove order invokes variant exit before generic VCC/VCCQ shutdown.
- The QMP provider L5 retained enable and L9 state remain balanced through successful and partially failed power cycles.
- Generic VCC/L17 and VCCQ/L6 requests are load-zero-before-disable and keep voltage-request state separate from enable/load state.
- Generic VCCQ L6 shutdown does not consume or disable VDDP independent L6 reference.
- VDDP L6 cleanup is load-zero-before-disable after generic VCCQ shutdown.
- VDDP and QMP custom devres actions run before their corresponding managed regulator handles are put.
- The embedded `ufs_hba_priv` state remains alive with the Scsi_Host/HBA private allocation through the async join and all synchronous UFS rail helpers; it is released only by the existing host devres/scsi_host_put lifetime.
- The absent HOS4.3 ARC/proxy 100mA temporary votes on L5/L9 remain an explicit parity gap. They must not be represented as physical parent links or permanent always-on constraints.
- No result is promoted to Phase E/F/G without their separate FDT/boot-chain/device evidence gates.

## 5. Source anchors

- [UFS async scan scheduling and callback](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)
- [UFS host remove and HBA exit ordering](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)
- [Qualcomm UFS variant exit](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufs-qcom.c)
- [UFS VCC/VCCQ/VCCQ2 regulator helpers](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)
- [Regulator load/disable semantics](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/core.c)
- [Managed regulator devres release](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/regulator/devres.c)

## 6. Status

This map is a source-based integration contract for 2号 AI. It does not mean the current AI2 branch has implemented these changes. The latest reviewed AI2 branch snapshot still predates the ROUND30 implementation task and must be rechecked before any implementation verdict. No code, config, patch series, DTS or build output was changed by this report.


## 7. ROUND102 private-wrapper correction

ROUND102 supersedes the earlier ROUND95 OEM-slot-plus-devm-sidecar design for the generic UFS VCC state. The exact fixed ACK already has `struct ufs_hba_priv { struct ufs_hba hba; bool zwor_sup; }`, allocated by `ufshcd_alloc_host()` as SCSI host-private storage. The preferred generic UFS private state is embedded there. This avoids modifying public `struct ufs_hba`, avoids using `android_oem_data1`, avoids `CONFIG_ANDROID_VENDOR_OEM_DATA` dependence, and avoids a separate sidecar release action.

Accordingly, the generic HBA-private state in this map is **not** a separate devm allocation and has no independent devres release step. It remains alive as part of the Scsi_Host private area until the existing host-release action calls `scsi_host_put()`. ROUND108's per-HBA registered async-domain join must complete before `ufshcd_remove()` begins teardown, ensuring that callback can no longer access the embedded state before final host release.

The Qualcomm VDDP `ufs_qcom_host` allocation and the QMP PHY `struct qmp_ufs` provider state remain distinct objects with their own devres lifetimes.
