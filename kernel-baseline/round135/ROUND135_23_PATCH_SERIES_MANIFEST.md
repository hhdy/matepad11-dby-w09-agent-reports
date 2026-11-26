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
| 22 | `kernel-baseline/round135/series/22-round135-huawei-dby-w09-real-dts.patch` | `ab0108364c835d87ac35ca670347d9d0001a821d` | new real-path DBY-W09 board DTS (DTS file only) |
| 23 | `kernel-baseline/round135/series/23-round135-huawei-dby-w09-dtb-makefile.patch` | `ceb72ed206d97beb2c2fa8558cb120ee186cb685` | qcom Makefile DTB target entry (TAB-exact hunk) |

All four ROUND130 source blobs (18–21) are byte-identical copies of the accepted candidate inputs. The frozen 17-patch series already contains the complete SM8250 UFS dual-GenPD / required-OPP implementation in patch 5 (`round33-checkpatch-clean.patch`). A separate ROUND45 driver patch was compared against patch 5 and its diff body differed only by one whitespace alignment character; re-applying it as patch 23 would duplicate the driver implementation and fail on the already-added include hunk. Therefore the duplicate driver patch is intentionally excluded, and patch 23 is now a separate qcom Makefile DTB target entry.

## 3. ROUND135 board-DTS integration

Patch 22 creates:
- Kernel source path: `arch/arm64/boot/dts/qcom/huawei-dby-w09.dts`
- Source file Git blob on this branch: `58293f7a62a50f8109886c92ce4b9cd14d7980e2`
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

The `ufs_mem_phy` node is not changed; it retains its GCC `UFS_PHY_GDSC` domain. Patch 22 creates the board DTS at the real kernel source path. Patch 23 adds `huawei-dby-w09.dtb` to the qcom Makefile. This is the first candidate that places the board file at a real kernel DTS path rather than the old repository-only `.dts.draft` path.

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


## 6. ROUND135 patch-22 remediation (2026-11-26)

The first Agent pass correctly blocked at patch 22 because the qcom Makefile hunk used spaces where the pinned ACK file uses a TAB before `+=`. Patch 22 has been regenerated against the manifest-pinned ACK Makefile using TABs in both context and inserted lines. The board DTS has also been synchronized with the latest reviewed main-branch evidence: `vdda-phy-always-on` is retained; obsolete PHY `*-max-microamp` properties are omitted because the pinned SM8250 QMP UFS regulator list already supplies those loads; memory comments now state that the included `sm8250.dtsi` supplies a bootloader-filled zero-size `/memory` node and HOS4.3 has 37 reserved-memory children. The dual-domain Host order remains MMCX index 0, GCC UFS_PHY_GDSC index 1. This is a candidate correction only; it is not yet revalidated by Agent.


## 7. ROUND135 patch-series deduplication (2026-11-26)

A source diff comparison found that frozen patch 5 (`round33-checkpatch-clean.patch`) already contains the complete ROUND45 SM8250 UFS dual-GenPD / required-OPP implementation. The original patch 23 (`23-round135-ufs-dual-genpd-driver.patch`) had the same diff body except for one alignment whitespace character; when ordered after frozen patch 5, its include hunk would be a duplicate and cannot apply.

To preserve an honest 23-patch manifest without duplicate implementation:
- patch 22 now contains only the new real-path board DTS file;
- patch 23 now contains only the TAB-exact qcom Makefile DTB target entry;
- the duplicate ROUND45 driver patch is removed from this series; its implementation is already carried by frozen patch 5.

The corrected series still contains 17 frozen patches + 4 ROUND130 patches + 2 independent DTS/Makefile integration patches = 23 ordered patch inputs.


## 8. ROUND135 R2 result-tree identity — pinned for R3 (2026-11-26)

R2 completed the exact identity/apply preflight in two independent clean Git trees. The Agent's result and raw evidence are preserved under `firmware-audit-v1:firmware-analysis/round135/r2-preflight/`:

- Final report: `ROUND135_R2_PREFLIGHT_FINAL_REPORT.txt`, blob `2d8b006482b4542e6018e27afbe8b4d8fbeed5d8`.
- Tree A raw log: blob `6fe70593091d0aaed0478b8b5bb100d1479c1b7f`.
- Tree B raw log: blob `87c7119c687448b1f1336f120a437ec15d8bba6d`.
- Tree equivalence / offsets: blob `1a191291963d0e78c2138332fb639e5232d9d687`.
- Upload/readback: blob `f03511589fba658a503fcb11efb6365396ff8a42`.

Both trees independently produced the frozen 17-patch intermediate tree `77e2b2b1515b3813f7538aedffe4c5a4e90edb57`, then the same full 23-patch content tree:

**Pinned expected ROUND135 R3 content Tree SHA: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.**

This is the expected Git content-tree identity after all 23 manifest inputs are applied. It is not a commit SHA, kernel Image SHA, proof of source compilation, or proof of device boot. R3 must independently rebuild the tree from the exact ACK base and 23 immutable inputs and stop before any build/test if the resulting tree differs.

The controlled offsets accepted as the predeclared R2 pattern are:
- patch 16: H1=-25, H2=-2, H3=+2;
- patch 17: H1=+1, H2=-2;
- patch 20 (ROUND128 V2): H3=-19.

All were reproduced identically in both R2 trees, with successful check/apply/diff-check, no fuzz, no rejects, no context relaxation and no fallback applier. Other patches emitted no offset line from the primary `git apply` applier. This does not permit suppressing or rewriting offset diagnostics in R3.

Frozen-manifest note: Tree A's log records an older local snapshot blob `96b52a4fdbc1f63023ec1fbfc9aec12b8176cfdb`; the authoritative frozen GitHub manifest remains `9a93b7e3a500d807533517a92b98fe244b2ea456`. The two snapshots differ only in the trailing status annotations on patch 16 and 17; patch paths, source blobs, SHA-256 values and order match. The R2 report preserves this disclosure. Do not call the two manifest blobs byte-identical.

R3 authorization is limited to reconstructing this exact content tree, then performing the schema/DTB/Kconfig/object/Image/Host validation specified by the dedicated R3 taskbook. R3 must not change any patch or DTS to make a test pass. The known memory/ABL handoff, PM8150 physical input topology, ARC/MMCX equivalence, AVB/DTBO/ramdisk and hardware-startup blockers remain open.
