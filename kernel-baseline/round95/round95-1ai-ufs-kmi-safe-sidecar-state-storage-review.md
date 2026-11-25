# ROUND95 — 1号 AI KMI review: preserve UFS exported structures and use the existing OEM data slot for sidecar state

**Date:** 2026-11-25  
**Research owner:** 1号 AI（ChatGPT）  
**Implementation owner:** 2号 AI（independent development AI）  
**Test executor:** testing Agent only, under a separate AGENT_TEST_TASK.md  
**Pinned baseline:** ACK android17-6.18.33_r00 / 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Related records:** ROUND84, ROUND88, ROUND90, ROUND91, ROUND93, ROUND94

## 1. Executive result

A direct inspection of the pinned GKI ABI metadata confirms two UFS structures are on exported Qualcomm KMI interfaces:

1. **ufshcd_pltfrm_init** is in **gki/aarch64/symbols/qcom**. Its tracked ABI signature takes a pointer to **const struct ufs_hba_variant_ops**. The tracked structure is 280 bytes and has no Android KABI reserve member in its source definition. Appending a parse callback would change this public structure layout.
2. **ufshcd_populate_vreg** is also in the Qualcomm KMI symbol list. Its tracked ABI signature exposes an output pointer to **struct ufs_vreg**. The tracked structure is 24 bytes and has no KABI reserve member. Adding min/max voltage or state fields there would change a structure exposed through an exported KMI helper.

**Do not add fields to struct ufs_hba_variant_ops or struct ufs_vreg for this feature without a deliberate KMI break approval.**

A promising ABI-preserving alternative already exists in the pinned baseline: **struct ufs_hba** ends with **ANDROID_OEM_DATA(1)**. That is an existing 64-bit OEM-reserved slot included in the baseline ABI. On the 64-bit GKI target, **CONFIG_ANDROID_VENDOR_OEM_DATA** has Kconfig **default y**. An OEM-specific, devm-managed sidecar pointer could be stored in this slot without changing the **struct ufs_hba** size/layout. The sidecar can hold the VCC min/max request and per-rail voltage/load/pending-cleanup state needed by ROUND84–ROUND94.

This is a design candidate for 2号 AI to evaluate, not an implementation authorization. Before using the slot, verify the final .config enables the option and perform a direct local search to ensure no existing project/OEM code already consumes android_oem_data1 for struct ufs_hba.

## 2. Exact pinned GKI ABI evidence

### 2.1 Qualcomm KMI symbol list

Source: [gki/aarch64/symbols/qcom](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/gki/aarch64/symbols/qcom).

The pinned Qualcomm partner list contains both:
- ufshcd_pltfrm_init
- ufshcd_populate_vreg

The same list also contains UFS core helper symbols and the regulator consumer API used by this integration. These are not merely arbitrary internal functions omitted from the partner KMI list.

### 2.2 ufshcd_pltfrm_init exposes ufs_hba_variant_ops

Source: [gki/aarch64/abi.stg](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/gki/aarch64/abi.stg).

The pinned ABI graph records:
- ELF symbol **ufshcd_pltfrm_init**, CRC **0x329a6dc6**, function type ID **0x928794d5**.
- That function type's second parameter is a pointer to a const-qualified **struct ufs_hba_variant_ops**.
- The ABI graph records **struct ufs_hba_variant_ops** as 280 bytes with 34 member IDs.

The corresponding fixed source declaration is in [include/ufs/ufshcd.h](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/ufs/ufshcd.h):

    int ufshcd_pltfrm_init(struct platform_device *pdev,
                           const struct ufs_hba_variant_ops *vops);

The current struct ufs_hba_variant_ops definition has no trailing ANDROID_KABI_RESERVE() slot. Adding one callback pointer changes the structure shape and therefore changes the type reachable from a Qualcomm KMI symbol. Treat it as an ABI change, not as a harmless source-only extension.

### 2.3 ufshcd_populate_vreg exposes struct ufs_vreg

Pinned gki/aarch64/abi.stg records:
- ELF symbol **ufshcd_populate_vreg**, CRC **0x88e6faae**, function type ID **0x9decf8e9**.
- Its third parameter resolves through pointer references to **struct ufs_vreg**.
- The ABI graph records **struct ufs_vreg** as 24 bytes with five member IDs.

The source declaration is in [drivers/ufs/host/ufshcd-pltfrm.h](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.h), and the structure definition is in [include/ufs/ufs.h](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/ufs/ufs.h).

Current struct ufs_vreg fields are regulator handle, name, always-on flag, enabled flag and max_uA. It has no KABI reserve. Adding min/max voltage or vote-state fields changes a public output type reachable through the exported helper. Keep it unchanged for this feature unless a KMI change is explicitly approved.

### 2.4 Allowed-break list does not pre-approve these changes

Source: [gki/aarch64/abi.stg.allowed_breaks](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/gki/aarch64/abi.stg.allowed_breaks).

The pinned allowed-break file lists several approved type differences, including a UFS TX equalization type change, but it does not list ufs_hba_variant_ops or ufs_vreg. There is no evidence in this file that a change to either structure is already approved.

## 3. Existing OEM-reserved storage in struct ufs_hba

Pinned source: [include/ufs/ufshcd.h](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/ufs/ufshcd.h).

The fixed structure ends with:

    struct ufshcd_tx_eq_params tx_eq_params[UFS_HS_GEAR_MAX];
    ANDROID_OEM_DATA(1);

Pinned [include/linux/android_vendor.h](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/include/linux/android_vendor.h) defines, when CONFIG_ANDROID_VENDOR_OEM_DATA is enabled:

    #define ANDROID_OEM_DATA(n) u64 android_oem_data##n

The pinned [drivers/android/Kconfig](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/android/Kconfig) defines CONFIG_ANDROID_VENDOR_OEM_DATA, depends on 64-bit, and has default y. It is not explicitly listed in the pinned arch/arm64/configs/gki_defconfig; final local .config must still be checked to confirm the Kconfig default was not overridden.

The pinned ABI graph records struct ufs_hba as 5,552 bytes. Within the struct_union entry for ufs_hba itself, the final member ID is 0xd671c9db; the corresponding ABI member record identifies it as android_oem_data1, type u64, at bit offset 44,352 (byte offset 5,544). It occupies the final 8 bytes of this exact structure (5,544 + 8 = 5,552). This is an already-existing slot, not a same-named field inferred from another structure.

Official Android guidance explains that OEMs should use ANDROID_OEM_DATA() for OEM-specific data and should not appropriate ANDROID_VENDOR_DATA(), which is reserved for vendor-specific use: [Android GKI kernel coding guidance](https://source.android.com/docs/core/architecture/kernel/kernel-code).

## 4. ABI-preserving sidecar design candidate

If 2号 AI confirms the OEM slot is unused for this UFS HBA in the project and enables the Kconfig option in the actual final config, a small sidecar can avoid growing the KMI-visible UFS structures:

1. In the existing early ufshcd_parse_regulator_info(hba) stage (ROUND88/91), allocate a devm-managed private state object only when vcc-voltage-level is present.
2. Validate exactly two u32 values, min_uV > 0, min_uV <= max_uV, and a real VCC supply descriptor.
3. Store the sidecar pointer in the existing hba->android_oem_data1 slot. Keep the pointer representation explicit and 64-bit-only; verify the config symbol before referencing the member.
4. The sidecar can hold the parsed VCC interval plus the distinct state required by ROUND84/89/90/93: current voltage-request state, per-rail DRMS load state and pending cleanup status. Do not duplicate the already-existing regulator enable reference unnecessarily.
5. Make the private UFS core helpers that apply VCC voltage / DRMS votes able to access the HBA sidecar. Their current ufshcd_config_vreg / ufshcd_enable_vreg / ufshcd_disable_vreg helpers are static/internal, so a private helper-signature change can be considered without extending the exported UFS variant-ops ABI.
6. Keep the exported ufshcd_populate_vreg() and struct ufs_vreg layout unchanged, and keep struct ufs_hba_variant_ops layout unchanged.
7. Leave the slot zero when the property is absent. Initialize it explicitly and clear it before any teardown path if the object lifetime can outlast the HBA's managed state.

The sidecar is OEM-specific state and must not become a general vendor data channel. A source-level inventory fetched every C/H file under the pinned `drivers/ufs/core` and `drivers/ufs/host` directories (44 files total) and searched for `android_oem_data`, `ANDROID_OEM_DATA`, `android_vendor_data`, and `ANDROID_VENDOR_DATA`; no existing use was found in the upstream UFS core/host source tree. This narrows the in-tree collision risk, but it does not cover the project’s complete local checkout, device/OEM downstream additions, generated source, or external modules. 2号 AI must still run a direct search in its complete integration worktree and any OEM extension source before adopting the slot.

### 4.1 Why this fits the current port

- The board property is Huawei/DBY-W09-specific and is not a generic regulator property.
- It is parsed early before the first regulator enable.
- The runtime UFS core can retrieve the state by HBA without modifying exported helper object layouts.
- The sidecar carries state separately from struct ufs_vreg, so DRMS, voltage request and enable reference are not conflated.
- The fixed slot is already present in the pinned ABI. Using it does not append fields or alter struct ufs_hba byte size.

This is a candidate, not a claim that it is already implemented or validated.

## 4.2 Sidecar allocation lifetime and teardown order

A second fixed-source check confirms that the proposed `devm_kzalloc()` sidecar can fit the existing HBA/devres lifetime, provided it is allocated during the early regulator parser and accessed through the HBA directly.

Pinned sources:
- [drivers/ufs/core/ufshcd-priv.h](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd-priv.h)
- [drivers/ufs/core/ufshcd.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/core/ufshcd.c)
- [drivers/ufs/host/ufshcd-pltfrm.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/ufs/host/ufshcd-pltfrm.c)
- [drivers/scsi/hosts.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/drivers/scsi/hosts.c)

Exact order:
1. `ufshcd_pltfrm_init()` calls `ufshcd_alloc_host(dev, &hba)` before it sets vops or parses regulators.
2. `ufshcd_alloc_host()` calls `scsi_host_alloc(..., sizeof(struct ufs_hba_priv))`; `scsi_host_alloc()` allocates the Scsi_Host plus private bytes with `kzalloc()`.
3. `struct ufs_hba_priv` is `{ struct ufs_hba hba; bool zwor_sup; }`, and `shost_priv(host)` points at that first `hba` member. Therefore the existing `android_oem_data1` u64 slot starts zeroed with the host private allocation.
4. Still inside `ufshcd_alloc_host()`, `devm_add_action_or_reset(dev, ufshcd_devres_release, host)` registers the host-release action.
5. Only after that does `ufshcd_pltfrm_init()` call `ufshcd_parse_regulator_info(hba)`. A sidecar allocated there with `devm_kzalloc()` is registered later than the host-release action.
6. During normal removal, `ufshcd_pltfrm_remove()` explicitly calls `ufshcd_remove(hba)` before returning to platform-device devres release. `ufshcd_remove()` / `ufshcd_hba_exit()` performs final `ufshcd_setup_vreg(hba, false)` while the HBA and sidecar are still alive.
7. When device devres is finally released, entries are released in reverse registration order: the later sidecar allocation is freed before the earlier `ufshcd_devres_release(host)` action releases the Scsi_Host/HBA private allocation.

This ordering is compatible with a devm-managed sidecar allocated during `ufshcd_parse_regulator_info()`: it remains alive throughout `ufshcd_remove()` and final regulator cleanup, then is freed before the HBA private memory. On a probe failure after parsing but before successful initialization, the same reverse order frees the sidecar before the HBA-host allocation.

Important access rule: the early parser runs before `ufshcd_init()` calls `dev_set_drvdata(dev, hba)`. It already has the `hba` pointer as an argument, so set/read the sidecar through `hba->android_oem_data1`; do not depend on `dev_get_drvdata()` being populated at parse time.

This validates devres ordering only. It does **not** establish that the OEM slot is unused by another downstream consumer, that the final `.config` enables `CONFIG_ANDROID_VENDOR_OEM_DATA`, or that the resulting patch passes Kleaf ABI validation. Those remain mandatory checks before adoption.

## 5. Implementation checks required before adoption

2号 AI should verify:
1. Final target .config has CONFIG_ANDROID_VENDOR_OEM_DATA=y.
2. struct ufs_hba::android_oem_data1 has no existing consumer in the complete local source/workspace or device OEM integration branch.
3. Any pointer stored in the u64 slot is initialized/cleared safely and obeys managed lifetime ordering.
4. No second UFS vendor/variant path uses the Huawei sidecar unless its property/binding supports it.
5. All voltage/load/enable-reference states and cleanup conditions from ROUND84–ROUND94 are represented.
6. Run the pinned Kleaf ABI check/update/diff against the exact ACK baseline; do not rely on the static graph alone to claim a KMI PASS.
7. Keep ufs_hba_variant_ops, ufs_vreg, ufs_vreg_info, and ufshcd_populate_vreg() layout/signature unchanged.
8. Run source build, dt_binding_check and later test-agent validation only after the implementation is ready.

## 6. Role and scope boundary

**This is a [1号 AI read-only KMI review] for 2号 AI.**
- 1号 AI: pinned KMI/ABI evidence analysis and design recommendation.
- 2号 AI: owns the actual implementation and KMI/build integration.
- Testing Agent: test executor only, under a separate AGENT_TEST_TASK.md.
- The user is not asked to run commands.

No source, header, DTS, binding, patch, configuration, 2号 AI branch, protected branch or PR was modified. No ABI checker, patch apply, compiler, dt-schema test, or device operation was run.

**Final status:** adding fields to ufs_hba_variant_ops or ufs_vreg would affect structures exposed by Qualcomm KMI symbols. The existing ufs_hba::android_oem_data1 OEM reserve is a promising fixed-size location for a devm-managed sidecar, subject to final config and existing-consumer checks. ROUND27 schema remains NOT CLEAN until 2号 AI implements and tests the complete UFS driver/binding and independent root/rootparam fixes.