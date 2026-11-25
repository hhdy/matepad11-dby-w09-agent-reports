
# ROUND68 — Kleaf DTB / DTBO build graph and DTBO table metadata design

**Date:** 2026-11-25  
**Owner:** Primary AI, pinned build-system and Android DTBO format source review  
**Baseline:** ACK android17-6.18.33_r00, commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a  
**Status:** RULE/API DESIGN REVIEW PASS; no BUILD.bazel target, DTB, DTBO or dtbo.img created.

## 1. Executive result

The eventual DBY-W09 device-tree pipeline has four distinct outputs/stages:

1. Kleaf rules_devicetree dtb() compiles the minimal ACK board DTS into a base DTB.
2. dtbo() compiles the separate rootparam-only DTSO into a relocatable DTBO.
3. dtb_composite() applies that overlay to the base DTB in a build/test graph, proving symbol/fixup references resolve. This is a static overlay test, not a test of Huawei ABL selection or live fixup behavior.
4. Kleaf dtbo_image() packages raw overlay(s) into the DT table format used by a DTBO partition. It is not interchangeable with dtb_image(), which concatenates DTB blobs for embedding into a boot/vendor_boot image.

The AOSP DTBO table header and entries carry their own fields: id, rev, and custom0..custom3. These are independent from simply placing a qcom,board-id property in the root of the overlay. The HOS4.3 stock image uses a 4096-byte DT table page size, nine entries, 32-byte table entries, and entry 8 / VG has board-id 0x206a with revision 0. A candidate dtbo image must explicitly use the matching table entry metadata and page size; otherwise the raw overlay can compile but the ABL may not select it.

No source build rule has yet been authored, and no DTB/DTBO compiled. This note defines the next safe build graph only.

## 2. Pinned Kleaf ruleset contract

The current manifest branch's Kleaf devicetree guidance documents that rules_devicetree is the ruleset for .dtb, .dtbo and composite DTBs. It is imported via Bzlmod in the Kleaf module.

Rule shapes from the ruleset's public documentation:
- dtb() loads from @rules_devicetree//devicetree:dtb.bzl. It expects exactly one .dts in srcs; generate_symbols=True adds -@ so overlays can resolve base labels.
- dtbo() loads from @rules_devicetree//devicetree:dtbo.bzl. It expects exactly one .dtso; it has no generate_symbols attribute.
- dtb_composite() loads from @rules_devicetree//devicetree:dtb_composite.bzl and applies overlay(s) to a base DTB using fdtoverlay.
- devicetree_library() can provide .dtsi/.h inputs and include directories for trees in other packages.

For source includes:
- Kleaf's devicetree guidance says //common:dtc_includes_aarch64 can be placed in the rule's deps when the source uses kernel .dtsi or binding headers.
- The ruleset's documentation distinguishes same-package includes (listed in srcs) from includes in another directory (provided by a devicetree_library dependency with includes). Do not guess include search paths.
- dtcopts are supported by dtb() / dtbo(); the ruleset documentation says explicit alignment should be used when creating blobs intended for mkdtimg. Use the exact AOSP-compatible alignment after ROUND22 reports the installed dtc/rule toolchain.

API references:
- Kleaf devicetree docs: https://android.git.googlesource.com/kernel/build/+/refs/heads/main-kernel-2026/kleaf/docs/devicetree.md
- Kleaf kernel API: https://android.git.googlesource.com/kernel/build/+/refs/heads/main-kernel-2026/kleaf/docs/api_reference/kernel.md
- rules_devicetree build guide: https://github.com/bazel-contrib/rules_devicetree/blob/main/docs/building.md
- rules_devicetree smoke test: https://github.com/bazel-contrib/rules_devicetree/blob/main/e2e/smoke/BUILD

The exact rules_devicetree version and resolved toolchain in the user's synced manifest workspace must still be confirmed before writing a real BUILD.bazel target. Do not infer a rule API version from current upstream HEAD alone.

## 3. Proposed DBY-W09 build graph (design only)

Illustrative target graph:

- Base DTB: dtb(name="dby_w09_board_dtb", srcs=["dby-w09-ack18-board.dts"], deps=["//common:dtc_includes_aarch64"], generate_symbols=True)
- Rootparam DTBO: dtbo(name="dby_w09_rootparam_dtbo", srcs=["dby-w09-ack18-rootparam.dtso"], deps=["//common:dtc_includes_aarch64"])
- Overlay resolution test: dtb_composite(name="dby_w09_composite_check", base=":dby_w09_board_dtb", overlays=[":dby_w09_rootparam_dtbo"])
- DTBO partition image: Kleaf dtbo_image(name="dby_w09_dtbo_partition", srcs=[":dby_w09_rootparam_dtbo"], config_file="dby-w09-dtboimg.cfg")

This is illustrative only. Exact load labels, dependency visibility, dtc preprocessing, toolchain and dtbo_image availability must be confirmed against the actual synced Kleaf workspace and exact ACK source tree before committing a BUILD file.

Important graph rules:
- The base DTB must be compiled with symbols because the rootparam overlay uses target = <&rootparam>.
- The composite target is a structural application test of the rootparam overlay to the candidate base; it must not be mistaken for ABL runtime selection.
- The rootparam overlay is separate from the base board DTS. Do not merge the overlay into the base and also package it separately.
- Do not apply the 143–145-fragment stock HOS DTBO to this minimal ACK board source.
- No dtb_image() is needed merely to produce the stock DTBO partition. HOS4.3 uses Android header v2 with embedded DTB in boot plus separate DTBO partition and separate ramdisk; confirm the actual candidate boot-v2 layout separately.

## 4. DTBO table metadata is a separate mandatory gate

AOSP DTBO partition documentation specifies a table header and one dt_table_entry per overlay. For each entry, mkdtimg accepts id, rev, and custom0..custom3.

The cfg_create config-file syntax supports global options such as page_size=4096 and per-entry options below each raw DTBO path. Alternatively, mkdtimg create accepts them inline. mkdtimg dump prints the emitted header and entry metadata.

The ROUND64 HOS4.3 inventory establishes the stock table:
- magic 0xD7B7AB1E;
- version 0;
- page_size 4096;
- 9 entries;
- entry size 32;
- entries offset 32;
- total_size 2,963,810.
ROUND19 records entry 8 as board-id 0x206a / revision 0, VG. The user's actual selected entry is still unknown.

For the current VG-only candidate, a future candidate config could structurally specify one entry with page_size=4096, id=0x206a and rev=0. This is **not** a recommendation to package a one-entry VG-only DTBO now. It is only an example showing that table id/revision/page-size are explicit. Before any package, the actual unit's hardware variant and the expected full DTBO table entry selection contract must be known. A single candidate entry must not be mistaken for a proven replacement of the nine-entry stock table.

The root DTS overlay may itself carry qcom,board-id = <0x206a 0>, but this does not remove the separate table entry metadata requirement. Keep both layers consistent.

AOSP references:
- DTB and DTBO partitions: https://source.android.com/docs/core/architecture/dto/partitions
- AOSP libufdt mkdtimg format: https://android.googlesource.com/platform/system/libufdt/+/show/master/utils/README.md

## 5. Immediate next sequence

After ROUND22's local source/DTB readiness report is received:

1. Compare its results against the main board draft, rootparam candidate and board rev2 candidate.
2. If syntax is ready, use a disposable copy of the rev2 board source in the exact pinned ACK tree and run dtc/schema checks; do not mutate the review files or protected branch.
3. Compile the rootparam candidate separately with the real base symbol export and confirm __fixups__ / __symbols__ resolve via a dtb_composite() validation target.
4. Inspect the composite tree and assert:
   - only intended rootparam properties added;
   - UFS Host power-domains order is MMCX index 0 and GCC GDSC index 1;
   - UFS PHY retains GCC GDSC;
   - Host has no HOS-only vdd-hba-supply pointing to GDSC;
   - UFS supply properties and always-on PHY rail match the exact built driver patches.
5. Only after the final ABL memory and reserved-memory handoff and PM8150 electrical parent evidence are closed may the generated DTB/DTBO become package candidates.
6. A package path must independently reproduce the stock DTBO table metadata or obtain the exact expected replacement table contract; dtc success is not enough.

## 6. Evidence boundaries

- Current Kleaf docs and rules_devicetree public API reviewed: PASS.
- Exact synced rules_devicetree module version and repository revision in the user's ROUND18 local workspace: NOT VERIFIED in this review.
- Actual dtb() / dtbo() / dtb_composite() rules executed: NOT RUN.
- Board rev2 DTB compiled: NOT RUN.
- Rootparam DTBO compiled: NOT RUN.
- Composite DTB created: NOT RUN.
- dtbo_image() or mkdtimg run: NOT RUN.
- Actual DTBO table accepted by HOS4.3 ABL: UNKNOWN.
- Final RAM/PMIC data, AVB signing, boot package and device startup: BLOCKED / NOT RUN.

No BUILD.bazel target, source, DTS, DTBO, config, image, branch-protected artifact or device was changed.


## Addendum — actual pinned ACK DTS package layout

At the exact common source commit, a GitHub tree check found 516 entries under arch/arm64/boot/dts/qcom and no BUILD/BUILD.bazel file; arch/arm64/boot/dts has 40 entries and no BUILD file either. There is no existing qcom Bazel package to extend. A later Kleaf integration must create a new BUILD.bazel package at the selected DTS source path or a dedicated build package, load rules_devicetree and Kleaf dtbo_image, and depend on //common:dtc_includes_aarch64. The exact source tree itself remains untouched.


## Correction from ROUND70 — no dt_table_entry id is selected yet

The illustrative cfg_create snippet above using id=0x206a is withdrawn as a specific recommendation. The public same-device Linux reference (earlier HOS generation) has base board-id 0/0, overlay-root board-id 0x206a/0, but its pack_dtbo.py writes a one-entry Android DT table with id=0/rev=0/page_size=4096. Its README describes ABL acceptance as dependent on the rootparam payload.

This proves table metadata and overlay root identity are separate. It does not prove HOS4.3 accepts the same single-entry id=0 package. The replacement table id/rev policy for current HOS4.3 remains UNKNOWN. Do not package or prescribe table metadata; see ROUND70.

## 2026-11-25 — ROUND72 exact Kleaf DTS include dependency design

At the pinned ACK root BUILD.bazel lines 1874–1897, public //common:dtc_includes_aarch64 covers arm64 include-prefixes and depends on the private dt-bindings header library. It does not contain arch/arm64/boot/dts/qcom/sm8250.dtsi.

The exact qcom source directory currently has no BUILD.bazel. When creating a disposable qcom Bazel package, the simplest rule is to list both the new board dts and same-directory sm8250.dtsi in dtb(srcs=[...]), and add //common:dtc_includes_aarch64 in deps for dt-bindings headers. The rootparam dtso is built separately with dtbo(); dtb_composite() applies it to the symbol-generating base DTB. A distinct dtbo_image() target must wait for HOS4.3 DT table ID/rev selection policy.

The rules_devicetree docs explicitly permit same-directory dtsi files in dtb srcs; different-directory includes instead require devicetree_library(). Exact ruleset module version in local Bzlmod still needs checking before implementing BUILD.bazel.

Detailed note: kernel-baseline/round72/round72-kleaf-qcom-dts-include-dependency-design.md.