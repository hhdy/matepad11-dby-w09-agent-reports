# NEXT TASK — Exact c56d93ea ACK Android 17 Entry/Alignment Audit (Read-only)

- Executor: WorkBuddy Window B / source-workspace owner with access to the completed ROUND157 independent build workspace.
- Reviewer: AI2.
- Target: Huawei MatePad 11 DBY-W09 VD; ACK android17-6.18.33_r00; Huawei ABL boot-v2 direct-partition path.
- Scope: inspect the actual frozen ROUND157 candidate tree and the exact successful ROUND157 build configuration, not a public upstream mirror.
- This task is read-only. Do not edit source, rebuild, package, sign, connect to device, or write partitions.

## 1. Why this task exists

AI2's previous report AI2_DIRECT_ABL_ACK_ANDROID17_ENTRY_ALIGNMENT_REVIEW.md examined fixed upstream commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9. It found no upstream direct dependency between Image header text_offset and PI relocation / runtime PHYS_OFFSET, but it explicitly did not inspect the exact ROUND157 patched tree.

ROUND157 reports identify the exact candidate:
- ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- 23-patch tree before RAM DTS change: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- RAM-patched candidate tree: c56d93eafa35057d65176db6594d67d5144868a0
- RAM patch commit: 491d0cbffb4d16e2840c1788674e6a05b26e88a2
- Successful independent build workspace reported: /home/kerneldev/work/matepad11/r157-windowB/a30build/common
- Independent build config SHA-256: 0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15
- Normalized olddefconfig config SHA-256: efb663e9c792840e2cfbbc03e115996bb486aefe964b448c1717828c55bf042f
- Successful Image SHA-256: f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21
- Successful Image size: 44,820,992 bytes.

Published evidence:
- AI1 ROUND156 plan: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round156/AI1_ROUND156_DELIVERY_REVIEW_AND_ROUND157_PLAN.md
- Window A ROUND157 report: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round157-primary-build-abl-final-proof/firmware-analysis/round157/WORKBUDDY_A_ROUND157_PRIMARY_KERNEL_BUILD_AND_ABL_FINAL_PROOF_REPORT.md
- Window B ROUND157 report: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round157-independent-build-repro/firmware-analysis/round157/WORKBUDDY_B_ROUND157_INDEPENDENT_KERNEL_BUILD_REPRODUCTION_REPORT.md
- ADAPT02 ABL alignment report: https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/direct-abl-partition-adapt02/firmware-analysis/boot-v2/direct-abl-partition-adapt02/abl_imagegz_alignment_analysis.md

## 2. Exact source inspection required

Use the local source workspace whose tree hash is exactly c56d93eafa35057d65176db6594d67d5144868a0. Verify with git rev-parse HEAD^{tree} before reading. If unavailable or mismatch, STOP and report the exact observed tree; do not silently switch to upstream or another workspace.

Read and record exact source lines / blob hashes for:

1. arch/arm64/kernel/head.S
   - Image header fields: code0, code1, text_offset, image_size, flags, magic, PE header offset.
   - primary_entry, __primary_switch, setting of kimage_voffset, entry ABI comments and register handling.
2. arch/arm64/include/asm/memory.h, arch/arm64/include/asm/page.h, and all definitions/references of PHYS_OFFSET, __PHYS_OFFSET, memstart_addr, kimage_voffset.
3. arch/arm64/kernel/pi/map_kernel.c, relocate.c, PI Makefile and relevant linker script:
   - runtime _text / physical placement calculations;
   - MIN_KIMG_ALIGN, CONFIG_RANDOMIZE_BASE, CONFIG_RELOCATABLE, CONFIG_RELR;
   - RELA/RELR relocation inputs and assumptions;
   - any code or assembly that reads Image header text_offset.
4. The exact final .config from the successful ROUND157 build:
   - report values for CONFIG_RELOCATABLE, CONFIG_RELR, CONFIG_RANDOMIZE_BASE, CONFIG_ARM64_4K_PAGES, CONFIG_ARM64_16K_PAGES, CONFIG_ARM64_64K_PAGES, CONFIG_ARM64_VA_BITS_*, CONFIG_EFI, CONFIG_UNMAP_KERNEL_AT_EL0, and relevant boot/EFI options.
   - Provide the config path, size, SHA-256, and prove it matches the published successful build.
5. Search the entire candidate source tree for text_offset, TEXT_OFFSET, MIN_KIMG_ALIGN, __PHYS_OFFSET, PHYS_OFFSET, kimage_voffset; list all relevant hits and classify whether they read/write the Image header field or only use runtime symbols.

## 3. Required analysis

A. Determine whether a header-only change from text_offset=0 to 0x80000 remains source-consistent in the exact c56 tree. Do not assume upstream result transfers to patched tree.

B. Determine whether the exact config enables PI relocation and/or RELR, and whether the actual built Image contains relocation metadata consistent with the source/config. This is inspection only; do not patch or rebuild.

C. Derive the exact ABL alignment condition using ADAPT02's proven destination formula:
- ABL writes raw Image and gzip output to ImageBuffer + 0x80000.
- ImageBuffer comes from AllocatePages(AllocateAnyPages, EfiBootServicesData, EFI_SIZE_TO_PAGES(size)).
- Only 4 KiB page granularity is established; no 2 MiB guarantee or second relocation has been found.
- Current ACK text_offset=0 requires ImageBuffer_phys mod 0x200000 = 0x180000.
- Candidate text_offset=0x80000 would require ImageBuffer_phys mod 0x200000 = 0.

Explain clearly why changing the header does or does not solve the runtime placement requirement. Do not claim that EFI page allocation is 2MiB aligned without exact evidence.

D. Inspect the actual Image artifact header at byte offsets and confirm text_offset, image_size, flags, magic, PE header pointer. Compare the artifact hash/size with ROUND157 report.

E. State whether the next engineering step should be:
- header-only source adaptation;
- ABL allocation alignment change (not authorized in this task);
- kernel placement/early-entry adaptation;
- or STOP pending runtime allocator evidence.

No source modification is authorized in this task.

## 4. Deliverable

Publish:
firmware-analysis/boot-v2/direct-abl-ack-entry-review/WORKBUDDY_C56_EXACT_TREE_ENTRY_ALIGNMENT_AUDIT.md

Include:
- exact tree/config/Image identity;
- line-numbered source excerpts and blob hashes;
- config option table;
- Image header field dump;
- complete symbol/header-read search hits;
- ABL formula comparison;
- PASS / FAIL / UNKNOWN gate table;
- explicit recommendation and unresolved evidence.

Read the published report back from GitHub and verify the blob/content. Then STOP.

## 5. Prohibitions

- No source edits, cherry-picks, patch creation or patch application.
- No kernel build or DTB build.
- No boot.img, Image.gz, DTBO or vbmeta construction.
- No signing, key handling, AVB flag change or bypass.
- No ADB, root, fastboot, recovery, UART, device connection, partition read/write, flash or reboot.
- Do not use Window A's private workspace/logs; use only the executor's own exact c56 source/build workspace.
- Do not infer device runtime ImageBuffer address from a static ABL allocation call.

STOP after the read-only exact-tree report.
