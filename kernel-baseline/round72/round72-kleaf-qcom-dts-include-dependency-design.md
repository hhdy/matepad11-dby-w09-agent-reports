# ROUND72 — exact Kleaf source dependency contract for the DBY-W09 qcom DTS package

Date: 2026-11-25
Baseline: ACK android17-6.18.33_r00 / common 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
Status: source/API design check PASS; no BUILD.bazel added, no Bazel target run.

## 1. Executive result

The exact pinned ACK root BUILD.bazel declares public target //common:dtc_includes_aarch64. Its devicetree_library includes only scripts/dtc/include-prefixes/arm64 headers and dtsi files and depends on the dt-bindings library. The dt-bindings library includes scripts/dtc/include-prefixes/dt-bindings headers plus include/linux/kconfig.h. This resolves angle-bracket dt-binding includes used by the DBY-W09 sources.

The board DTS includes sm8250.dtsi by local quoted include. That file lives in arch/arm64/boot/dts/qcom and is not part of //common:dtc_includes_aarch64. The exact qcom source directory has no BUILD.bazel today. Therefore, after creating a BUILD package at qcom, the simplest rule is:
- Put the board DTS and rootparam DTSO source files in the same qcom package as sm8250.dtsi during source-tree integration.
- Declare the base DTS and sm8250.dtsi together in dtb(srcs=); rules_devicetree explicitly supports same-directory dtsi and h files in srcs.
- Put //common:dtc_includes_aarch64 in deps to expose dt-binding headers.
- Compile the rootparam DTSO with dtbo(srcs=[...]).
- Use dtb_composite() with a base dtb that has generate_symbols=True to test symbol/fixup application.

This avoids expecting dtc_includes_aarch64 to contain qcom/sm8250.dtsi.

## 2. Exact pinned ACK root BUILD targets

File: BUILD.bazel at ACK common commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a.

At lines 1874–1886 it defines private devicetree_library :dt-bindings:
- hdrs: glob of scripts/dtc/include-prefixes/dt-bindings/**/*.h plus include/linux/kconfig.h;
- includes: include and scripts/dtc/include-prefixes.

At lines 1888–1897 it defines public devicetree_library :dtc_includes_aarch64:
- hdrs: glob of scripts/dtc/include-prefixes/arm64/**/*.h and *.dtsi;
- includes: scripts/dtc/include-prefixes;
- deps: [':dt-bindings'].

## 3. Exact source tree and package boundary

At the pinned ACK commit, arch/arm64/boot/dts/qcom has 516 entries and no BUILD or BUILD.bazel; arch/arm64/boot/dts has 40 entries and no BUILD or BUILD.bazel. sm8250.dtsi exists in qcom and its own include list consists of dt-bindings headers; it does not include another SoC dtsi.

If a new BUILD.bazel is placed in arch/arm64/boot/dts/qcom, that path becomes a Bazel package. DBY-W09 sources in the project repo's separate dts/ directory must be staged into that package in a disposable ACK worktree before the target can compile.

## 4. Proposed qcom BUILD graph (design only)

load('@rules_devicetree//devicetree:dtb.bzl', 'dtb')
load('@rules_devicetree//devicetree:dtbo.bzl', 'dtbo')
load('@rules_devicetree//devicetree:dtb_composite.bzl', 'dtb_composite')

dtb(
    name = 'dby_w09_board_dtb',
    srcs = ['dby-w09-ack18-board.dts', 'sm8250.dtsi'],
    deps = ['//common:dtc_includes_aarch64'],
    generate_symbols = True,
)

dtbo(
    name = 'dby_w09_rootparam_dtbo',
    srcs = ['dby-w09-ack18-rootparam.dtso'],
    deps = ['//common:dtc_includes_aarch64'],
)

dtb_composite(
    name = 'dby_w09_rootparam_composite_check',
    base = ':dby_w09_board_dtb',
    overlays = [':dby_w09_rootparam_dtbo'],
)

The graph is illustrative only. It is a compile/fixup test, not a DTBO partition image. Kleaf dtbo_image is a distinct rule and must not be wired until the HOS4.3 DT table id/rev selection contract is known.

Why this graph:
- dtb() permits exactly one dts plus same-directory dtsi and h files in srcs.
- Different-directory includes require a devicetree_library() dependency.
- //common:dtc_includes_aarch64 provides the common dt-bindings includes.
- The base must use generate_symbols=True because the overlay targets &rootparam.
- dtb_composite() invokes fdtoverlay to test the symbol/fixup application.

## 5. Rule names and table packaging

The concrete rules_devicetree rule is dtb_composite(), loaded from dtb_composite.bzl. Kleaf overview docs have described the concept as composite_dtb(), but the ruleset build guide/API uses dtb_composite().

Kleaf kernel.bzl separately exposes dtbo_image(name, srcs, out, config_file, opts, tool). It builds the Android DT table image, not the raw dtbo(). The dtbo_image config/table metadata remains blocked by ROUND70 HOS4.3 selection ambiguity.

## 6. Status

- Exact //common:dtc_includes_aarch64 target and contents: PASS.
- Exact sm8250.dtsi same-directory include dependency: PASS.
- Exact qcom Bazel package existence: no package currently exists.
- Proposed base dtb + rootparam dtbo + dtb_composite graph: design PASS.
- Exact rules_devicetree module version in the ROUND18 local workspace: not yet checked from local Bzlmod resolution.
- BUILD.bazel created: NO.
- Actual Bazel dtb/dtbo/composite target executed: NOT RUN.
- DTBO table metadata/packaging: UNKNOWN / NOT RUN.
- Final ABL memory/PMIC/AVB gates: remain open.

No source, BUILD, DTS, DTBO, config, Image, protected branch or device was modified.