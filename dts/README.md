# DBY-W09 ACK 6.18 DTS draft

This directory contains a **review-only source draft** for the initial DBY-W09 board DTS and its minimal ABL rootparam overlay.

Files:
- `dby-w09-ack18-board.dts.draft` — minimal SM8250 board identity + HOS4.3 PM8150 UFS rails + UFS/QMP enablement.
- `dby-w09-ack18-rootparam.dtso.draft` — separate minimal DBY-W09 board identity overlay, including the stock `huawei,modem_id` sentinel.
- `../config/dby-w09-ack18-storage-first.fragment.draft` — built-in UFS/QMP/RPMh clock/regulator/SM8250 GCC/interconnect/SMMU Kconfig fragment for the first storage milestone.
- `../patches/ufs-qcom-vccq-parent.patch.draft` — legacy protected-branch sketch; **do not apply as-is**. ROUND49 found it enables both supplies and releases them too early; a replacement design is documented on main but has not been applied to the protected branch.

## Important integration rule

Do **not** apply the stock HOS4.3 DTBO entry 8 to this minimal base. ROUND8 resolved 145 stock fragments targeting many nodes absent from this minimal DTS. Use a separately built and ABL-validated minimal DBY-W09 overlay.

The local ROUND7 DTBO inventory shows that all nine stock entries carry the same generic `huawei,modem_id = <0xffffffff 0>` sentinel. The same-device Linux reference preserves that field in its minimal overlay:
https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso

The draft now preserves that known stock value. This is stronger evidence than omitting it, but it does **not** prove that a newly packed DTBO header / entry table is accepted by the user's current ABL.

## Current limits

- ROUND11 is complete; its sanitized findings are documented in ROUND16/21/22/23. ROUND23 adds the PM8150L S8 UFS VCCQ-parent consumer rail; ROUND24 corrects VDDP placement and documents PM8150 L6 aggregate DRMS; ROUND25 confirms UFS core sequencing and how its VCCQ vote interacts with the two Host-level vendor supplies. ROUND12 has now uploaded a BLOCKED result because no trusted installed AVB inspector was available; AVB footer/vbmeta descriptor coverage remains UNKNOWN. The firmware-analysis ROUND13 read-only task is complete and uploaded at `firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt` on `firmware-audit-v1`; its HOS4.3 mode/DRMS metadata is translated into the main-branch review draft by ROUND48/51. ROUND51 corrects S8 to preserve HOS initial RET (the prior AUTO fallback was based on a load request ACK cannot act upon) and leaves S8 enable state UNKNOWN. The older protected ACK driver patch sketch is stale and unsafe to apply as-is; ROUND49/51 record the corrected lifecycle design on main, but no replacement driver patch has been applied or compiled. ROUND21 records the remaining ACK PM8150 VRM parent-supply gap and the regulator-core dummy fallback semantics. ROUND17 records the ACK GENI UART/console distinction and why both candidate UART nodes remain disabled. ROUND19 records the HOS4.3 memory/reserved-memory audit and the still-unresolved ABL memory injection boundary. ROUND20 documents Android first-stage module loading and dynamic/EROFS mount requirements. No source sync, dtc invocation, dt-schema validation, Kconfig resolution, compile, boot-image packing or hardware test has been done.
- PM8150 UFS supply map now includes a separate UFS VCCQ parent rail: HOS4.3 `qcom,vccq-parent-supply` resolves to PM8150A S8 (1.2–1.4 V, max 210 mA); ROUND7 finds the same S8 node in all three valid boot-FDT candidates. ROUND13 establishes HOS4.3 S8 supported modes RET/AUTO, initial RET and 200mA threshold; this is static FDT metadata, not a runtime mode read. Same-device public Linux DTS maps legacy `pm8150a_s8` to PM8150L S8 / `pmic-id = c` / `smps8`. The ACK board draft now defines that PM8150L S8 output and preserves the UFS consumer property. It deliberately does not add `vdd-s8-supply`, a guessed parent input or HOS4.2-only minimum voltage/mode values. See ROUND23.
- Both `qcom,vccq-parent-supply` and `qcom,vddp-ref-clk-supply` are UFS Host consumer extensions, not PMIC input-supply properties. VDDP maps to PM8150 L6 (1.2V, 100µA), is acquired and enabled as an independent regulator consumer, and should be released only after generic UFS VCCQ has shut down. KONA's VCCQ-parent/S8 path is load-only and does not call regulator_enable/disable; the generic regulator core only triggers DRMS updates for an enabled consumer handle, so the KONA 210mA vote is not proof of an effective mode transition. Fixed ACK S8 has no get_optimum_mode/set_load callbacks, so its 210mA set_load request is a no-op. ROUND51 supersedes ROUND49's tentative S8 cleanup recommendation: the initial ACK UFS patch should omit the S8 get/load/enable/disable path entirely, not register an empty deferred cleanup action. Do not force-enable S8; runtime enable state is UNKNOWN. VDDP/L6 still uses deferred devm cleanup after ufshcd_remove() completes. The old protected patch sketch is stale/unsafe; no replacement has been applied.
- ROUND11's initial HOS4.3 base-FDT scan identified four internal ARC `*-parent-supply` edges; ROUND14 later confirmed a fifth edge from the MX MMCX-supply child to a CX MMCX-supply child. The proven minimum is now five, but the complete parent-edge total remains UNKNOWN because ROUND14 did not re-scan the full graph. ROUND11 also identified six ARC proxy-supply links. The inspected base-FDT scope found no `vdd-s1..s10` / `vin` / `vph-pwr` properties. ACK's PM8150 VRM driver assigns internal `supply_name` values to S4/L5/L6/L9/L17 and S8. On populated DT, regulator core can use a dummy parent if no matching real supply is found; that assumes the physical rail already exists and is enabled, it does not prove the electrical path. Do not restore HOS4.2 public-reference `vph_pwr=3.7 V` or invent a PMIC input.
- SPMI PMIC GPIO/PON/arbiter nodes are intentionally absent from this minimal UFS-only base.
- ARC/proxy are not enabled in this UFS-first DTS: ACK's upstream RPMh regulator has VRM/XOB only; the older vendor ARC driver is a porting reference, not code that can be copied without adapting Command DB/RPMh APIs. ACK has no equivalent generic proxy-consumer helper. ROUND14 confirms MMCX ALL's proxy-supply resolves to its own ALL child with proxy-consumer-enable and voltage <384 65535> (TURBO..MAX), a temporary boot request in public KONA; flags for the other proxy-supply links remain unverified. Do not convert this to regulator-always-on or permanent system-load.
- No UART console, reserved-memory, panel, THP, WLAN, BT, audio, camera, USB-C or DP nodes are enabled. ACK maps uart2 to the GENI debug-console path (ttyMSM / earlycon) and uart6 to the regular GENI UART path (ttyHS); the same-device Linux reference uses uart6 with a Bluetooth child. Do not assume serial0=uart6 makes it ttyMSM0 under ACK 6.18. The HOS androidboot.console=ttyMSM0 property is not by itself a proven ACK console-to-pin mapping.
- ROUND7 HOS4.3 base-FDT inventory has no /memory or device_type node, but it has 34 reserved-memory children across boot/security handoff, firmware carveouts, reusable pools and crash/log areas. The public HOS4.2-based Linux DTS has no explicit /memory node either and only four reserved-memory children. ABL may inject usable RAM metadata, but this is not established for the ACK replacement DTB. Do not copy HOS4.2 splash/DFPS addresses or omit all HOS4.3 carveouts on the assumption that ABL will preserve them. See ROUND19; memory/reserved-memory handoff remains a pre-build gate.
- Public same-device Linux 7.0 source documents ABL v2 boot plus a separate ramdisk partition and a /rootparam-only DTBO requirement. Local ROUND2 confirms matching image file sizes (boot 96 MiB, ramdisk 2 MiB, dtbo 24 MiB), but HOS4.3 AVB footer / vbmeta descriptor coverage has not yet been inspected. ROUND12's sanitized AVB metadata report is uploaded but BLOCKED at the trusted-tool gate; footer and vbmeta descriptor coverage remain UNKNOWN.
- Panel `ACTIVE_PROFILE=UNKNOWN`.
- The stock HOS4.3 ramdisk remains unread (ROUND10 BLOCKED); whether its ABL-combined initramfs exposes Android's /lib/modules/<release>/modules.load and depmod files is unknown. Android first-stage can load UFS modules before mounting logical partitions, but this legacy boot/ramdisk combination has not been proven compatible; the storage-first config conservatively keeps UFS built-in.
- ROUND20 adds CONFIG_BLK_DEV_DM=y because Android first-stage maps dynamic logical partitions with dm-linear (built into dm-mod; no CONFIG_DM_LINEAR symbol exists), and CONFIG_EROFS_FS=y is currently a configuration proposal only; EROFS filesystem/content identification remains BLOCKED and is not treated as a completed audit. DM_VERITY / FEC stay pending ROUND12 AVB descriptors and ramdisk fstab; EXT4/F2FS stay pending exact filesystem identification.
- These files use the suffix `.draft` deliberately. Do not rename them into build input or flash them.

## Source and evidence basis

- Google ACK `android17-6.18` SM8250 DTSI: UFS host, QMP PHY, GCC GDSC, RPMh XO clock and RPMh OPP references, IOMMU and interconnect topology.
- ACK does not use the legacy vendor qcom,rpmh-arc-regulator graph in its upstream PMIC regulator driver. Its SM8250 power-level representation uses the SoC rpmhpd provider and OPP table. The upstream SM8250 RPMhPD domain descriptor does not mirror every HOS4.3 MMCX ARC edge, so full corner equivalence remains a later subsystem validation item.
- Local ROUND7/ROUND9 HOS4.3 facts: stock DTBO rootparam values and UFS rail closure.
- Local ROUND8 overlay target map: stock entry 8 has 145 fragments and is incompatible with a minimal ACK base.
- Public same-device Linux DTS / rootparam overlay, used as a cross-reference only, not copied as a complete Android/ACK solution.

## ROUND13 / ROUND48 regulator mode update (2026-11-24)

ROUND13 confirms HOS4.3 uses vendor properties, not the upstream `regulator-*` mode names. Vendor values are interpreted using the public Qualcomm SM8250 KONA header/driver: PASS=0, RET=1, LPM=2, AUTO=3, HPM=4. The fixed ACK header uses RET=0, LPM=1, AUTO=2, HPM=3, so the board DTS uses ACK symbolic values instead of raw HOS integers.

Current `dby-w09-ack18-board.dts.draft` proposal:
- S4: no forced mode; local HOS4.3 has no mode metadata.
- L5/L9: HPM initial, LPM/HPM allowed, DRMS enabled, but no synthetic `regulator-system-load`. Public KONA proxy-consumer code removes the boot-time 100mA proxy request at `late_initcall_sync`; ACK has no equivalent temporary proxy helper, so this remains a boot-handoff gap.
- L6/L17: LPM initial, LPM/HPM allowed, DRMS enabled.
- S8: ROUND13/14 report RET/AUTO, initial RET, 200mA threshold, and no static init-enable/boot-on/always-on property. ACK HFSMPS510 has no DRMS load callback and the UFS 210mA load-only request is a no-op; the draft now preserves initial RET, does not force enable, and leaves runtime enable state UNKNOWN.

ROUND13 report: [round13_pm8150_mode_drms_findings.txt](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt)

ROUND48 design report (including proxy lifecycle correction): [ack-hos43-pmic5-mode-enum-translation-and-dts-decision.md](../kernel-baseline/round48/ack-hos43-pmic5-mode-enum-translation-and-dts-decision.md)

The nine stock DTBO entries do not target the relevant RSC regulator subtree, but entry selection remains UNKNOWN; do not call the proposed rail settings effective post-overlay values. Full-tree DTS compile/schema/build/boot checks remain NOT_RUN. EROFS, AVB and ramdisk gates remain BLOCKED.

## ROUND49 / ROUND50 updates (2026-11-24)

- [ROUND49 UFS VDDP/VCCQ-parent lifecycle redesign](../kernel-baseline/round49/ack-ufs-vddp-vccq-parent-devres-lifecycle-redesign.md): public KONA uses VDDP enable/disable but VCCQ-parent load-only; fixed ACK generic teardown order allows deferred devm cleanup after generic VCCQ shutdown. The load-only parent request is not proven effective without that consumer's enable reference; ACK S8 has no DRMS callback.
- [ROUND50 MMCX→MX ARC parent semantics](../kernel-baseline/round50/ack-sm8250-mmcx-mx-arc-parent-semantics-and-remaining-local-gate.md): public KONA has separate MMCX ALL/AO parent targets and ARC min-dropout propagation; fixed ACK SM8250 RPMHPD has no MMCX parent. ROUND14 has now filled the corner/dropout/proxy values; ROUND51 explains why the corner vocabulary matches but the full GenPD/ARC graph does not.
- [ROUND51 ROUND14 ARC value semantics, parent-edge reconciliation and S8 policy](../kernel-baseline/round51/round14-arc-value-semantics-proxy-vote-and-round11-edge-reconciliation.md): confirms 0xffffffff behaves as signed -1 in the KONA ARC parent request path, reconciles at least five known parent edges, identifies the MMCX ALL TURBO..MAX temporary proxy request, and corrects S8 to RET initial with no guessed enable.
- ROUND14 local task is COMPLETE and uploaded to firmware-audit-v1. No new local task is active. No new local FDT parse was performed.
- Do not modify the protected DTS branch or PR #1. ROUND49/50/51 are source-review/design reports; no full-tree apply, dtc/schema, Kconfig, build, boot, or runtime trace has been run.


### ROUND52 — storage-first UFS optional supply implementation drafts

- ROUND52 adds explicit qcom,ufs.yaml definitions for qcom VDDP REF_CLK and VCCQ-parent consumer properties.
- The first ACK UFS driver draft consumes VDDP/L6 only: set the DTS load, enable before PHY power-up, and defer disable + load-clear until after ufshcd_remove() has shut down generic UFS VCCQ.
- S8/VCCQ-parent is not acquired or voted by the first ACK driver patch. ACK HFSMPS510 has no DRMS callback and HOS4.3 has no static enable declaration in the inspected scope; runtime rail enable remains UNKNOWN. Do not force enable.
- Artifacts: kernel-baseline/round52/round52-storage-first-ufs-vddp-integration-and-binding-closure.md and the two 0001/0002 patch drafts. Hunk counts/context were source-reviewed; full-tree apply, checkpatch, dt-schema and build remain NOT_RUN.


### ROUND52 final ordered source-context simulation

The intended patch order is recorded in kernel-baseline/round38/ufs-dual-genpd-patch-series-manifest.md. A source-backed in-memory simulation matched all 15 hunks across ROUND32, ROUND36, ROUND52-0001, ROUND37, ROUND33 and ROUND52-0002 in dependency order. This did not modify the protected branch and is not equivalent to git apply in a full kernel worktree. Full-tree apply, checkpatch, schema validation, dtc/dtbs_check and Kleaf build remain NOT_RUN.


## ROUND63 — UFS PHY vdda-phy always-on compatibility

The HOS4.3 DTBO inventory reports `vdda-phy-always-on` on the UFS PHY node. ACK 6.18.33's QMP UFS PHY currently bulk-disables both PHY supplies on `power_off` and its schema does not declare this property. The ROUND63 driver/binding candidates on main preserve the policy by retaining one consumer enable reference for `vdda-phy`, toggling its load vote between the pinned SM8250 init load and zero, and releasing the retained enable only on provider removal. Nodes without the property retain the original bulk behavior.

The board DTS draft now declares `vdda-phy-always-on`. It no longer duplicates `vdda-phy-max-microamp=89900` / `vdda-pll-max-microamp=18800`: ACK's pinned `sm8250_ufsphy_vreg_l[]` already sets these exact values. The properties are not accepted by the current QMP UFS PHY binding and are not read by the ACK driver. The stock HOS DTBO entry 8 also contains them, but this project must not apply that 145-fragment stock entry to the minimal ACK base; the planned minimal DTBO is rootparam-only.

**Still a candidate only:** the driver and binding patches have not been full-tree applied, checkpatch/schema checked, compiled or hardware-tested. See `kernel-baseline/round63/round63-ufs-phy-always-on-lifecycle-compatibility.md`. The board DTS remains `.draft`, not a source-tree build input.


## 2026-11-25 — Superseding current evidence snapshot (ROUND18–ROUND21)

The historical notes above are retained as design history. Where they conflict with this section or the linked ROUND19–ROUND21 reports, the later inspected evidence below is authoritative.

### Confirmed corrections and current status

- **Base /memory:** the HOS4.3 base FDT does contain `/memory` with `device_type = "memory"`; its `reg` is `<0 0 0 0>` (all-zero placeholder). Do not say the node is absent. Do not infer RAM ranges or carveouts. The final ABL-to-Linux handoff remains unknown.
- **First-stage /dev:** ROUND21 statically traced the exact HOS4.3 `/init`. It mounts tmpfs on `/dev`, creates initial character nodes with `mknod()`, and uses netlink uevents/sysfs coldboot for devices. `CONFIG_TMPFS=y` is required; `CONFIG_DEVTMPFS` and `CONFIG_DEVTMPFS_MOUNT` are not required by this exact first stage.
- **UFS pinctrl:** the stock HOS TLMM compatible is `qcom,kona-pinctrl`; the pinned ACK SM8250 pinctrl driver matches `qcom,sm8250-pinctrl`. Enabling `PINCTRL_MSM/PINCTRL_SM8250` alone will not bind the HOS node. The pinned ACK UFS Host driver does not select HOS's custom `dev-reset-assert/deassert` states; it uses GCC `core_reset` and the optional device-reset GPIO is absent in the base DTB. Do not add a compatible override without a separately reviewed decision.
- **Nine stock DTBOs:** all nine carry byte-identical UFS PHY/Host fragments and UFS fixups, but no UFS dual-GenPD array. They also all write five `/rootparam` properties. Variant 8 / board-id `0x206a` is the VG candidate only; runtime variant selection is not proven.
- **UFS dual GenPD:** the ROUND18 Image includes the ROUND33 helper. The current board DTS draft still inherits only one GCC UFS GDSC domain. To activate UFS OPP routing, the next ACK DTS candidate must add exactly two Host domains in order: MMCX / RPMHPD index 0, then GCC UFS_PHY_GDSC index 1. See [ROUND37 delta](../kernel-baseline/round37/dby-w09-ufs-dual-genpd-board-dts-delta.md) and [ROUND65 audit](../kernel-baseline/round65/round65-ufs-dual-genpd-dts-opp-routing-audit.md). Keep the PHY's own GCC GDSC attachment.
- **Do not copy HOS `vdd-hba-supply`:** the stock UFS overlay points this at a GDSC node. ACK exposes GDSC as GenPD, not as a regulator. ACK UFS core would try a normal regulator get if `vdd-hba-supply` is present and may defer. The current board draft's omission is deliberate. See [ROUND64 source review](../kernel-baseline/round64/round64-ufs-hba-gdsc-regulator-source-review.md).
- **VDDP and always-on PHY rail:** ROUND18 includes the VDDP ref-clock lifecycle patch and QMP `vdda-phy-always-on` patch/binding. The board draft's VDDP/L6 and PHY always-on properties are consumed by that patched Image. The UFS VCCQ-parent/S8 property is retained as topology metadata, but the initial ACK driver does not acquire or vote S8; do not assume S8 enable state.
- **PM8150 input parents:** the pinned ACK RPMh binding does not require every PM8150 `vdd-*-supply` property, and regulator core may use a dummy parent on DT boot when no regulator is found. That fallback assumes the physical rail exists and is already enabled; it is not evidence of the board's electrical topology. Do not invent `vph_pwr`, `vdd-s*` parents or voltages. See [ROUND66 source review](../kernel-baseline/round66/round66-pm8150-rpmh-parent-supply-dummy-fallback-audit.md).
- **EFI and memory:** ROUND20 proves the built Image has a real PE/COFF EFI entry and ACK can rebuild memblock from UEFI metadata. It does not prove ABL invokes EFI. Ordinary ARM64 entry can also use the kernel EFI memory path if ABL supplies the full metadata. If EFI Stub starts without the platform DTB configuration table, it can generate an empty DTB and lose `/firmware/android/fstab`.
- **Boot-v2 / AVB:** ROUND20 compression figures prove capacity only. They do not create a boot image or preserve AVB. ROUND19 AVB metadata remains preliminary because no independent trusted implementation cross-check has closed all descriptor inconsistencies.

### Actual files currently present in this directory

As of the current main branch listing, `dts/` contains:
- `dby-w09-ack18-board.dts.draft`;
- `README.md`.

The README historically names `dby-w09-ack18-rootparam.dtso.draft`, but that file is **not currently present in the main-branch directory listing**. Do not assume it exists. ROUND19 provides the exact nine variant property values; a minimal overlay must be created/validated separately and must not apply the full 143–145-fragment HOS stock DTBO to the minimal ACK base.

### Next validation boundary

ROUND22 is the active local audit for exact ACK DTS includes/labels, temporary syntax-only DTB compilation, UFS property-to-driver contract, PM8150 input parent software/electrical distinction, and correction of this historical /memory wording. No board DTB has yet passed a full pinned-source build. The board file remains `.draft`, not a build input. Stage A remains unaccepted until a real 6.18.33 kernel boots on DBY-W09 and storage/essential hardware are evidenced.


## ROUND64 evidence update — final FDT and AVB metadata

The local Agent tried to retrieve /sys/firmware/fdt in ROUND2 and received Permission denied; the local hash sidecar says the live FDT is unavailable. No final ABL-to-Linux RAM map or final reserved-memory layout is available. The inspected base FDT's zeroed /memory/reg is a pre-ABL template value only. Do not invent RAM or carveout tuples.

The PM8150 physical input-parent topology remains unresolved because the authorized HOS4.3 corpus has no board-specific schematic/power tree or explicit physical vdd-s* / vin / vph-pwr mapping.

ROUND64 Phase F used the pre-existing AOSP avbtool 1.4.0 from the pinned ACK source tree in read-only info_image mode. It confirms AVB footers and descriptor/chain targets for boot, standalone ramdisk and dtbo; root vbmeta links those images. This is metadata inventory, not signature verification. The vbmeta_cust.img footer points beyond the 1 MiB file to an empty Algorithm NONE object, so cust coverage remains UNKNOWN. The selected HOS4.3 DTBO remains UNKNOWN. Do not package a candidate, reuse modified stock footer/hash metadata, assume ABL accepts an unverified payload, or assume a RAM-only boot is possible.

Reports:
- [ROUND64 Phase E](../firmware-analysis/round64/round64-dby-w09-hos43-final-memory-and-pm8150-input-evidence.md)
- [ROUND64 Phase F](../firmware-analysis/round64/round64-dby-w09-hos43-bootv2-ramdisk-dtbo-avb-evidence.md)

The source/Image build milestone remains complete; board DTB and boot-package gates are not complete.


## VG rootparam overlay candidate restored (2026-11-25)

The main branch now contains `dby-w09-ack18-rootparam.dtso.draft`. It is a **VG / 0x206a candidate only**, restored from the exact HOS4.3 ROUND19 entry-8 rootparam values and cross-checked against the public same-device rootparam-only source. It is not proof that the user's actual ABL selects VG. It has not been compiled with `dtc -@`, inserted into a DTBO table or accepted by HOS4.3 ABL. Keep the other eight variants available as evidence; do not silently mark VG as the selected runtime overlay.


## Board DTS rev2 integration candidate

A separate file, `dby-w09-ack18-board.dts.rev2.candidate`, now contains the ROUND37 two-domain UFS Host property (MMCX index 0, GCC UFS_PHY_GDSC index 1), the two power/clock binding headers, and corrected zeroed /memory-placeholder documentation. The original `.draft` remains unchanged for comparison.

The rev2 candidate is not compiled or schema-validated and is not an input to the current Image build. Do not promote it until ROUND22's source/contract report and full pinned-ACK dtc/schema checks pass. Final ABL memory/reserved-memory and physical PM8150 input-parent gates remain BLOCKED.


## ROUND68 — Kleaf DTB/DTBO pipeline

The source/API design note is [ROUND68](../kernel-baseline/round68/round68-kleaf-dtb-dtbo-build-graph.md). It distinguishes base dtb(), overlay dtbo(), composite resolution via dtb_composite(), and DTBO partition packaging via Kleaf dtbo_image(). Do not confuse dtb_image() with DTBO partition packaging. Base DTB needs generate_symbols=True for the rootparam overlay.

The HOS4.3 DTBO table header metadata is separate from compiling overlay DTS: stock page_size is 4096; entry 8 candidate is id 0x206a / rev 0. Any future package must set and verify dt_table_entry metadata separately, and the actual device variant must be confirmed first. This is not a package-ready result.


## ROUND22 / ROUND23 status

ROUND22 proved the original one-domain board DTS draft compiles from a byte-identical temporary copy: cpp and dtc 1.7.0 both exit 0; 32 warnings are inherited from pinned sm8250.dtsi and none originate in the draft. This did not test the newer rev2 candidate or rootparam overlay.

ROUND22 also clarified:
- qcom,vddp-ref-clk has a real patched ACK UFS Host consumer;
- qcom,vccq-parent-supply is schema-only metadata with no runtime consumer in the current Image;
- vdd-hba-to-GDSC is not an ACK regulator supply and remains absent;
- one-domain UFS DTS does not activate the ROUND33 MMCX required-opps mapping;
- PM8150 physical input parents remain unknown despite schema optionality and dummy regulator fallback.

ROUND23 now checks the current board rev2 candidate plus the restored VG-only rootparam overlay with temporary cpp/dtc compilation and fdtoverlay composite application. It is not a Kleaf target, DTBO partition package or ABL selection test.


ROUND68 package-layout detail: at the pinned ACK common commit, arch/arm64/boot/dts/qcom has no BUILD.bazel (516 entries); arch/arm64/boot/dts also has no BUILD.bazel. A future Kleaf target therefore requires a new BUILD package and explicit dtc include dependency; no qcom Bazel target currently exists.


## ROUND70 — DTBO table ID is not the root overlay board-id

A public same-device Linux reference (based on an earlier HOS generation) keeps the base DTS board-id at 0, uses 0x206a in the rootparam overlay, but packages a one-entry DTBO table with id=0/rev=0/page_size=4096. This shows table entry metadata and the overlay's root qcom,board-id are separate layers. It does **not** prove the HOS4.3 ABL accepts the same one-entry wildcard/default table. The exact replacement table id/rev policy remains UNKNOWN. Do not generate dtbo.img until that contract is evidenced.

See [ROUND70](../kernel-baseline/round70/round70-dby-w09-dtbo-table-id-selection-ambiguity.md).

## ROUND71 — same-device boot packaging reference

The public same-device Linux 7.0 reference confirms boot v2 + separate header-v0 ramdisk + rootparam-only DTBO and states its ABL refuses RAM boot. Its repack script hard-codes 24,412,160 B stock boot payload and keeps stock footer bytes when replacing payload. HOS4.3 here measures 24,457,216 B and has explicit root-vbmeta hash coverage for boot/ramdisk/dtbo; the public constants and retained-footer behavior must not be copied or assumed valid. See [ROUND71](../kernel-baseline/round71/round71-same-device-boot-packaging-structure-cross-reference.md).