# AI1 ROUND157 Delivery Review and ROUND158 Rootparam / Fastboot Gate Plan

- Reviewer: 1号 AI (ChatGPT)
- Date: 2026-11-27
- Target: Huawei MatePad 11 (2021), DBY-W09, HOS 4.3.0.196 (C00E100), SM8250
- Candidate: ACK android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- This review uses published reports and existing target-device read-only captures. No device operation occurred in this review.

## 1. ROUND157 evidence verified

### 1.1 Exact source identity

- Frozen 23-patch source tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b.
- RAM/comment patched source tree: c56d93eafa35057d65176db6594d67d5144868a0.
- Window A patch commit: 491d0cbffb4d16e2840c1788674e6a05b26e88a2.
- RAM DTS patch SHA-256: 047a0af868fcdfceac0b0bb30360dbc9587530c0cedb38e4e6b940fa923afda1, 4919 B.
- Window A and Window B independently verified the 23 patch identities/replay and reconstructed the exact same post-RAM source tree.
- Candidate DTB: 108,680 B, SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60.

### 1.2 Window A — primary build and ABL supplement

Report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round157-primary-build-abl-final-proof/firmware-analysis/round157/WORKBUDDY_A_ROUND157_PRIMARY_KERNEL_BUILD_AND_ABL_FINAL_PROOF_REPORT.md

Blob: 73cdb334a9f0ecc42f02242892809bc6e4bc1853.

- Formal Kleaf command tools/bazel build //common:dby_w09 --jobs=2 exited RC=1.
- First real failure was an OOM kill of pahole during BTF generation; host dmesg recorded about 5.26 GB anonymous RSS for pahole. It is classified as environmental memory exhaustion, not a source compile failure.
- No full-build Image/vmlinux/System.map or packaged DTB was produced by Window A. No retry was launched, following the taskbook.
- A separate same-source/same-config/same-toolchain Kbuild DTB rebuild succeeded: 108,680 B / SHA 9d0d7600…fed60, byte-identical to the frozen R154 DTB.
- DTB static structure: one memory node, 3 candidate tuples, 18 reserved-memory children, 905 nodes, 239 phandles, UFS host/PHY supply/clock/reset/power-domain/OPP/interconnect closure intact, /chosen empty.

ABL supplement:
- The /memory/reg routine constructs a property through a custom allocated FDT/property builder and copies 4-byte cells; it is not a direct call to stock libfdt fdt_setprop or fdt_appendprop. The higher-level distinction between replacing an existing property and appending/rebuilding within the full tree remains unresolved.
- Overlay error returns are non-fatal to the traced caller, but whether a later fragment error can leave earlier fragment mutations in the base FDT is not proven. Do not rely on a stock Entry 2 application failing harmlessly.
- AVB path includes unlocked continuation, public-key validation callback and Huawei TA digest post-processing. Exact top-level signature/rollback/descriptor-skip order in Huawei ABL remains partly unresolved. No unconditional AVB bypass is established.

Patch:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round157-primary-build-abl-final-proof/firmware-analysis/round157/AI1_R157_RAM_DTS_PATCH.patch

### 1.3 Window B — independent successful full build

Report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round157-independent-build-repro/firmware-analysis/round157/WORKBUDDY_B_ROUND157_INDEPENDENT_KERNEL_BUILD_REPRODUCTION_REPORT.md

Blob: 11a7476f06f611c0046afdd8a604c1b0b06c3070.

- Independently reconstructed the exact source tree c56d93ea…, using the archived RAM DTS patch / its exact published diff.
- Fresh Kleaf build tools/bazel build //common:dby_w09 --jobs=2 completed RC=0, 775 actions, 625.011 s.
- Kleaf .config SHA-256 0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15, identical to ROUND140 Kleaf config.
- Outputs:
  - Image: 44,820,992 B / SHA-256 f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21
  - vmlinux: 230,259,072 B / SHA-256 d47e9a71d58747afa69468fa5afea3c06775fb32b7b144c0c6df796b7eb543e8
  - System.map: 7,611,571 B / SHA-256 7f01a12037a367466b8d2bad83ce1e0df191e3137ae81c08367fb16102705f44
  - Module.symvers: 0 B; modules archive: 67 B containing only the empty root entry. No loadable modules were produced.
- Kleaf did not expose a named DTB output. A separate Kbuild DTB was built from the same source and copied build config, then matched the expected 108,680 B / 9d0d7600…fed60 exactly. This must not be described as a DTB directly emitted by the Kleaf target.
- Image hash differences from ROUND140 are attributed by Window B to generated signing-certificate material and BTF nondeterminism; .debug_info was identical. Image hash is not a cross-build identity gate.
- UFS closure and reserved-memory structure passed. dtbs_check was not run.

### 1.4 Corrected provenance note

The ROUND157 AI2 report originally said the named AI1 ROUND156 integration review was unavailable. This was a branch/path lookup miss, not a missing file. The report exists at:

https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round156/AI1_ROUND156_DELIVERY_REVIEW_AND_ROUND157_PLAN.md

Blob: 67176e659d56c1f88acead8debce1730d3a0913b.

The ROUND157 AI2 report remains useful for its conservative ABL/AVB/restoration boundaries, but its missing-input statement is corrected.

## 2. Newly surfaced same-model public evidence: rootparam and fastboot boot

Two public DBY-W09 Linux projects report an important boot gate:
- One describes an HOS boot-v2 flow in which the DTBO selected/applied by ABL must populate /rootparam with board identity; the author reports that otherwise ABL returns the tablet to fastboot, and that fastboot boot is refused.
- Its public rootparam example uses board ID 0x206a and fields qcom,boardid, qcom,board_name, qcom,product_name, hardware_version, and huawei,modem_id.
- A second public project describes a 6 GB DBY-W09 running HOS 4.2.0.213 and Linux 7.0.14, also referencing board-id 0x206a and many vendor-only DTBO symbols.

References:
- https://github.com/svesnav/linux-dby-w09
- https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso
- https://github.com/svesnav/linux-dby-w09/blob/main/pack_dtbo.py
- https://github.com/Anglerfish314/matepad11-dby-w09-kubuntu

These public values are not transferable without target-specific proof. The public evidence describes HOS4.2.0.213 / 6 GB / board-id 0x206a. This project has direct HOS4.3.0.196(C00E100) captures, approximately 12 GB-class live RAM windows, and live androidboot.dtbo_idx=2 corresponding to Entry 2 / board-id 0x200e; Entry 8 / 0x206a was not the selected live entry.

Evidence hierarchy for this project:
1. Exact target-device HOS4.3 capture and exact ABL binary.
2. Independent reports from this target's capture.
3. Same-model but different-firmware public projects.
4. General inference.

Therefore:
- /rootparam is now a priority first-boot gate to resolve.
- Do not simply inject public HOS4.2 values or force board-id 0x206a.
- Do not continue the old “stock Entry 2 will fail harmlessly” hypothesis.
- Exact HOS4.3 ABL must determine required rootparam content and DTBO selection metadata.
- Fastboot temporary-boot refusal is a lead only until the exact HOS4.3 ABL command dispatcher is checked.

## 3. Integrated ROUND157 decisions

| Activity | Decision | Conditions / rationale |
|---|---|---|
| Offline full kernel build | GO — build gate passed | Window B produced a fresh RC=0 Kleaf build from exact source/config. Window A OOM does not invalidate the independent successful build. Keep the OOM cause recorded. |
| Offline DTB/rootparam/DTBO prototypes | GO — host-only experiments | It is safe to inspect candidate /rootparam, create clearly labelled 0x200e/0x206a variants, validate Android DT table headers and fdtoverlay on host. These are not device-ready artifacts. |
| Integrated boot-v2 boot.img + DTBO package | NO-GO | Required rootparam and target selector contract are unresolved; ABL overlay failure may partially mutate base FDT; final RAM behavior and /chosen handoff are unvalidated; AVB/TZ/Huawei TA digest acceptance is not demonstrated. |
| Temporary boot | NO-GO / exact support unknown | Public same-model project reports fastboot boot refusal, but target HOS4.3 ABL command registration/dispatch must be checked before concluding this device behaves identically. No fastboot session is authorized. |
| Partition write | HARD NO-GO | Device is A-only; required chain backups are incomplete (vbmeta_odm, eng_vendor, eng_system, version not captured); no full GPT geometry/rollback metadata; no proven restore mode or restore rehearsal; no explicit write authorization. |

No boot package, signing, temporary boot, partition write, flash, or reboot occurred in ROUND157.

## 4. ROUND158 — focused tasks issued

The next round is deliberately limited to resolving the exact HOS4.3 /rootparam / DTBO / fastboot contract and validating host-only DTBO prototypes. Do not reopen ARC/proxy/display work.

### WorkBuddy Window A — exact HOS4.3 ABL

Branch: workbuddy/round158-exact-hos43-rootparam-abl

Taskbook:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round158-exact-hos43-rootparam-abl/firmware-analysis/round158/WORKBUDDY_A_ROUND158_EXACT_HOS43_ROOTPARAM_DTBO_AND_FASTBOOT_BOOT_AUDIT_TASKBOOK.md

Start prompt:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round158-exact-hos43-rootparam-abl/firmware-analysis/round158/START_PROMPT_WORKBUDDY_A_ROUND158_EXACT_HOS43_ROOTPARAM_DTBO_AND_FASTBOOT_BOOT_AUDIT.md

Assignment: use only Window A's existing HOS4.3 ABL and already captured stock boot-chain evidence. Resolve rootparam required fields/failure behavior, Entry2 0x200e vs Entry8 0x206a selection, DTBO header/selection expectations, and whether fastboot boot is supported. Also finish only the narrow RAM property-builder and overlay-failure gaps where practical. No device interaction.

### WorkBuddy Window B — independent candidate/DTBO experiments

Branch: agent2/round158-independent-rootparam-dtbo

Taskbook:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round158-independent-rootparam-dtbo/firmware-analysis/round158/WORKBUDDY_B_ROUND158_INDEPENDENT_ROOTPARAM_DTBO_VARIANT_AND_CONTAINER_AUDIT_TASKBOOK.md

Start prompt:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round158-independent-rootparam-dtbo/firmware-analysis/round158/START_PROMPT_WORKBUDDY_B_ROUND158_INDEPENDENT_ROOTPARAM_DTBO_VARIANT_AND_CONTAINER_AUDIT.md

Assignment: independently inspect the candidate rootparam node/symbols, create host-only target-path and phandle overlay prototypes, clearly separate 0x200e vs 0x206a experiments, validate Android DTBO table container parsing/roundtrip, and resolve the empty modules artifact/config question. No device interaction or source/config edits.

### 2号 AI — independent integrated review

Branch: ai2/round158-independent-rootparam-bootgate

Taskbook:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round158-independent-rootparam-bootgate/firmware-analysis/round158/AI2_ROUND158_INDEPENDENT_ROOTPARAM_AND_FASTBOOT_BOOT_GATE_REVIEW_TASKBOOK.md

Start prompt:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round158-independent-rootparam-bootgate/firmware-analysis/round158/START_PROMPT_AI2_ROUND158_INDEPENDENT_ROOTPARAM_AND_FASTBOOT_BOOT_GATE_REVIEW.md

Assignment: correct the prior Round157 report's path omission, independently compare exact HOS4.3 capture with public HOS4.2 examples, and give separate decisions for offline experiments, boot package, temporary boot and partition write. No device/build/write operations.

## 5. ROUND158 completion gate

Do not proceed to a device boot or package-write plan until:
1. Exact HOS4.3 ABL rootparam requirement and selector inputs are explained from the captured binary.
2. A candidate DTBO container's header/entry values are proven to match that HOS4.3 selector contract.
3. Stock DTBO failure/partial mutation risk is avoided by a deliberate compatible overlay path, not assumed harmless.
4. Candidate /chosen handoff and runtime RAM expectations are explicitly documented.
5. AVB/TZ/Huawei TA authorization and a viable restore route are established or an alternative safe test mechanism is demonstrated.

The public HOS4.2 board-id 0x206a overlay is a reference implementation only, not the chosen configuration for this HOS4.3 device.

## 6. Stop conditions

- No new device/ADB/root/fastboot access in ROUND158.
- No partition reads/writes, flash, reboot, recovery, temporary boot.
- No boot.img or flashable DTBO/vbmeta package.
- No AVB key extraction, signature manipulation, flags or bypass.
- No unauthorized device write.

ROUND157 final disposition: kernel build gate passed; integrated boot package / temporary boot / partition write remain blocked. ROUND158 proceeds as offline target-specific boot-chain research and disposable host-only experiments.

— END —
