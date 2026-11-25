# ROUND135 — pinned 23-patch integration series

- Owner: 1号 AI (ChatGPT)
- Branch: `ai1/round130-stagea-ufs-lifecycle-integration`
- Fixed source: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9` (`android17-6.18.33_r00`)
- Frozen Stage A 17-patch manifest: `ai-parallel/stagea-port-until-boot:kernel-baseline/round61/round32-stagea-series.txt`
- Frozen manifest Git blob: `9a93b7e3a500d807533517a92b98fe244b2ea456`
- Series rule: items 1–17 are immutable; items 18–21 are exact AI1 ROUND130 candidates already accepted as a buildable Stage A candidate series; items 22–23 are the ROUND135 integration candidates. No cherry-pick, merge, or protected branch update is authorized.

## 1. Immutable frozen base

Apply the exact 17 patches in the manifest above in manifest order. Verify every source Git blob and SHA-256 against the original manifest before applying. The original manifest is the authority for all 17 filenames, blob IDs and SHA-256 values; do not regenerate, reorder, substitute or edit it.

The exact frozen series was independently replayed in two fresh trees for ROUND132 and produced content tree `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`. This is a cross-check value, not permission to skip any input verification.

## 2. AI1 candidate extensions (18–23)

| Index | Patch file on this branch | Git blob | Source identity / role |
|---:|---|---|---|
| 18 | `kernel-baseline/round135/series/18-round120-ufs-per-hba-async-join.patch` | `f604c8672fcbc98f3e9645f5e8888c8a34b1c11e` | exact ROUND120 candidate; original source blob preserved |
| 19 | `kernel-baseline/round135/series/19-round122-ufs-regulator-load-first.patch` | `64dd2ad9022251e2411a1a745aeb920a0badfa85` | exact ROUND122 candidate; original source blob preserved |
| 20 | `kernel-baseline/round135/series/20-round128-qmp-ufs-dual-rail-v2.patch` | `22ccec1cabf2d78e61442d19219985135f8341e7` | exact ROUND128 V2 candidate; original source blob preserved |
| 21 | `kernel-baseline/round135/series/21-round126-proxy-consumer-load-first.patch` | `c180dbf458403d68b2c32c1d54776a7559e7e5db` | exact ROUND126 candidate; original source blob preserved |
| 22 | `kernel-baseline/round135/series/22-round135-huawei-dby-w09-real-dts.patch` | `d303439a9fde864ea765f59ef0888ada3f20468c` | new real-path board DTS plus qcom Makefile DTB entry |
| 23 | `kernel-baseline/round135/series/23-round135-ufs-dual-genpd-driver.patch` | `2bf34810b15fd3fef8b1033d9b6ceb884b77fbb5` | exact ROUND45 dual-GenPD / required-OPP driver candidate |

All four ROUND130 source blobs (18–21) are byte-identical copies of the accepted candidate inputs. Patch 23 is a byte-identical copy of the fixed-ACK source-reviewed ROUND45 driver patch.

## 3. ROUND135 board-DTS integration

Patch 22 creates:
- Kernel source path: `arch/arm64/boot/dts/qcom/huawei-dby-w09.dts`
- Source file Git blob on this branch: `f51c5691d2955909149ba8f76d0b99dcf671e36f`
- Base board-DTS source: `dts/dby-w09-ack18-board.dts.draft`, blob `dd9035083458ea6ccdb5fdd852b7a1860509fbaf`
- Fixed ACK qcom Makefile source: `arch/arm64/boot/dts/qcom/Makefile`, blob `296688f7cb26550f75bce65826f234bc24110356`

It adds the binding macro includes:
```dts
#include <dt-bindings/clock/qcom,gcc-sm8250.h>
#include <dt-bindings/power/qcom,rpmhpd.h>
```

And changes the UFS Host domain array to the required ordered pair:
```dts
&ufs_mem_hc {
    power-domains = <&rpmhpd RPMHPD_MMCX>,
                    <&gcc UFS_PHY_GDSC>;
    /* all previously reviewed board rails/status remain */
};
```

The `ufs_mem_phy` node is not changed; it retains its GCC `UFS_PHY_GDSC` domain. Patch 22 adds `huawei-dby-w09.dtb` to the qcom Makefile. This is the first candidate that places the board file at a real kernel DTS path rather than the old repository-only `.dts.draft` path.

## 4. Explicit acceptance boundaries

This manifest defines a **disposable validation candidate**, not a production-ready boot image.

- The board DTS still contains a bootloader-filled memory placeholder. Do not invent RAM ranges or adapt another unit's memory size.
- PM8150 physical input-parent rails are not proven. Do not add synthetic regulator parents, dummy fixed regulators, or guessed voltages.
- MMCX-to-MX ARC/corner propagation remains unresolved; the dual-GenPD wiring does not claim to implement ARC semantics.
- ABL final memory/FDT/EFI handoff, reserved-memory ownership, AVB/footer provenance, boot-v2 ramdisk path and final selected DTBO remain separate blocked gates.
- The known undocumented `huawei,dby-w09` board-compatible schema warning is not permission to weaken schemas or modify unrelated Qualcomm compatible bindings. Record any diagnostics exactly.
- No device connection, ADB, fastboot, recovery, serial, boot, flash, partition read/write or firmware extraction is included.
- Do not merge this branch into `main`, `ai-parallel/stagea-port-until-boot`, `ack18-dby-w09-dts-draft`, or any PR.

## 5. Required independent validation

The ROUND135 Agent taskbook on this branch is the operational authority. It requires exact identity checks for all 23 patches, clean application with all offsets transparently reported, dt-schema and DTB inspection, Kconfig resolution, target-object compilation, and a full `//common:dby_w09` candidate build. No validation result is implied by this manifest.
