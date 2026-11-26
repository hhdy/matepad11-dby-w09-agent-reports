# ROUND155 — DTBO selection and first-boot strategy independent review

- Reviewer: AI2 (independent reviewer)
- Date: 2026-11-26
- Scope: read-only architecture, source and published-report review
- Disposition: **HARD NO-GO for flash / first boot**
- No device access, source/DTS edits, package generation, builds, flashing, reboot, recovery or boot were performed in this round.

## 0. Executive verdict

**Recommended strategy: do not try to boot the current minimal candidate by reusing stock Entry 2 or Entry 8. Keep the three-FDT boot-v2 layout as the conservative packaging hypothesis, place the candidate-specific SoC DTB in slot 0, and plan a narrowly scoped custom overlay (or a base-DTB expansion if the eventual bootloader contract permits no overlay). Do not assemble or flash a package yet.**

This is a strategy recommendation, not an authorization to implement it.

The decisive blockers are independent:

1. **Stock overlay incompatibility is demonstrated by two ROUND154 lanes.** The frozen candidate has no `/__symbols__`; adding `-@` only raises the published compatibility count to 10/166 external symbols and 57/144 fragment targets. The other 156 symbols and 87 fragment targets remain unavailable. Both lanes report `fdtoverlay` failure.
2. **The exact ABL/XBL is absent.** The observed stock boot proves that DTBO Entry 2 was applied and that the handed-off FDT was further mutated, but it does not prove whether the loader always requires an overlay, how it selects a DTB slot, how it selects DTBO index 2, or whether a no-overlay boot is accepted.
3. **The current candidate is not shown to contain the minimum hardware tree needed for a useful boot.** The stock live FDT has 4,566 nodes; the stock base has 3,471; Entry 2 adds 1,095 live-only nodes. The candidate has 905 nodes. This comparison does not prove that every stock node is required, but it does show that the candidate is not a drop-in equivalent of the stock base-plus-overlay tree.
4. **AVB cannot be treated as solved.** The root vbmeta chain has SHA256_RSA2048 descriptors for boot, ramdisk and dtbo. Any change to boot or dtbo invalidates the corresponding descriptor. No OEM signing key or tested authorized signing/restore path is available in the evidence.
5. **Full partition backup and a tested exact-stock restore path are both absent.** ROUND154 records these as FAIL. This alone blocks a first boot even if the technical DTBO questions were resolved.

The current ROUND154 state is therefore a **hard no-go for flash**. A successful DTB-only build is not a boot package, and a syntactically valid custom overlay is not evidence that the target ABL will select or apply it.

## 1. Evidence coverage and provenance

### 1.1 Inputs located and reviewed

- [ROUND154 Window A report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round154-candidate-dtbo-symbol-fixup-boot-packaging/firmware-analysis/round154/WORKBUDDY_A_ROUND154_MINIMAL_RAM_PATCH_AND_DTBO_BOOT_PACKAGE_GATE_REPORT.md)
- [ROUND154 Window B report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round154-true-independent-ram-reserved-hash/firmware-analysis/round154/WORKBUDDY_B_ROUND154_INDEPENDENT_PATCH_AND_DTBO_REPRODUCTION_REPORT.md)
- [ROUND151 live runtime/FDT report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round151-root-readonly-runtime-audit/firmware-analysis/round151/WORKBUDDY_ROUND151_ROOT_READONLY_RUNTIME_AUDIT_REPORT.md)
- [ROUND153 stock boot-chain / DTBO / memory-fixup report](https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round153-stock-boot-chain-dtbo-memory-fixup-audit/firmware-analysis/round153/WORKBUDDY_ROUND153_STOCK_BOOT_CHAIN_DTBO_MEMORY_FIXUP_AUDIT_REPORT.md)
- Pinned ACK source at commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`:
  - [scripts/Makefile.lib](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/scripts/Makefile.lib)
  - [scripts/Makefile.dtbs](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/scripts/Makefile.dtbs)
  - [scripts/dtc/libfdt/fdt_overlay.c](https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9/scripts/dtc/libfdt/fdt_overlay.c)

### 1.2 Inputs that were not available at the requested locations

The taskbook also names `kernel-baseline/round154/AI1_ROUND154_DELIVERY_REVIEW_AND_ROUND155_ACCELERATION.md`. I attempted to fetch it from both the ROUND154 AI2 review branch and the ROUND155 task branch; the path returned 404 in both places. I therefore **did not read or rely on that AI1 review**. The two ROUND154 lane reports and ROUND151/153 reports were available and reviewed.

The taskbook asks for the ROUND138 full DTBO inventory. I did not locate a ROUND138 report branch/path in the repository branch listing. ROUND153 reproduces and quantifies the relevant Entry 2/Entry 8 comparison, so I use those published ROUND153 facts as a cross-reference, not as a claim that I independently re-opened the ROUND138 raw inventory.

### 1.3 Independence limitation

Window A and Window B report separate builds/analyses. Their numerical agreement is useful corroboration. However, the raw stock `dtbo.img`, Entry 2/Entry 8 blobs, candidate DTB binaries and per-symbol/per-fragment raw evidence were not present as directly readable inputs in this review. Consequently, the exact counts below are **independently corroborated from the two published ROUND154 reports**, not re-computed by AI2 from the raw binary bytes. This distinction is deliberate.

## 2. Stock Entry 2 compatibility — verdict and mechanism

### 2.1 Published ROUND154 results

Both ROUND154 lanes report the same material result:

| Base DTB tested | External symbols resolved | Entry 2 fragment targets resolved | Apply result |
|---|---:|---:|---|
| Frozen candidate, no `-@` | 0 / 166 | 0 / 144 | `FDT_ERR_BADOFFSET`; base has no `/__symbols__` |
| Scratch candidate with `-@` | 10 / 166 | 57 / 144 | `FDT_ERR_NOTFOUND` |
| Missing after `-@` | **156 / 166** | **87 / 144** | Still cannot apply |

Window A reports Entry 2 has 144 fragments, 166 external fixup symbols and 450 fixup references. Window B independently reports 144 fragments and 166 distinct external symbols, with a corrected target/property accounting disclosed in its report. Both report a failed whole-overlay apply on the no-`-@` base and on the `-@` scratch base.

The same reports show Entry 8 does not solve this: it has 145 fragments and the same 166 external symbols; its no-`-@` and `-@` compatibility results are likewise 0/166 and 10/166.

**Finding:** the taskbook's numeric claim is supported by two separate ROUND154 reports. AI2's evidence grade is corroborated-report level, not raw-binary remeasurement.

### 2.2 Why `-@` helps but does not repair the overlay

Pinned ACK source confirms the build mechanics:

- `scripts/Makefile.lib` defines `target-stem` by stripping the target path and basename extension. For `huawei-dby-w09.dtb`, the stem is `huawei-dby-w09`.
- `scripts/Makefile.dtbs` adds `DTC_FLAGS_$(target-stem)` to the DTC command.
- The same Makefile automatically adds `-@` to a DTB that is listed as a base DTB for a Kbuild composite `*-dtbs` overlay target. A standalone board DTB that is not used as such a composite base does not receive this automatic flag from that rule.
- In the published scratch experiment, the correctly named override is therefore `DTC_FLAGS_huawei-dby-w09 := -@`; the extension-bearing variable name does not match the stem.

The pinned `scripts/dtc/libfdt/fdt_overlay.c` makes the distinction explicit:

- A fragment can target a node by phandle (`target`) or by path (`target-path`).
- For external fixups, `overlay_fixup_phandles()` looks for `/__fixups__` in the overlay and `/__symbols__` in the base.
- `overlay_fixup_phandle()` takes each fixup property name as a symbol, looks that symbol up in the base `/__symbols__`, resolves the stored path, obtains that node's phandle, and writes the phandle into the overlay's fixup location.
- The source explicitly allows an overlay with no external fixups and a base without symbols, but it cannot resolve a requested external symbol that is absent.

Thus `-@` is a symbol-export prerequisite for overlays that use external labels. It causes the compiler to emit symbol metadata for labels that actually exist in the candidate source. It **does not** synthesize vendor labels, nodes, phandles, regulators, clocks, PMIC nodes or thermal zones that the candidate does not define. This exactly explains why the scratch candidate improves from 0 to 10 resolved symbols but still fails.

### 2.3 Answer to Question 1

- No `-@`: **0/166** external symbols; **0/144** fragment targets.
- With `-@`: **10/166** symbols; **57/144** targets.
- Still absent: **156** external symbols and **87** fragment targets.
- Whole-overlay apply remains failed.

I accept these counts as corroborated by Window A and Window B. A future audit should still retain the raw binary parser output and exact artifact hashes alongside the published summary, so another reviewer can independently re-run the counts without trusting either report.

## 3. Can first boot proceed without a DTBO overlay?

### 3.1 What is proven

ROUND151 captured the live FDT for the audited HOS build. It records:

- `androidboot.dtbo_idx=2` in the live boot arguments.
- Root `qcom,board-id = <0x200e 0>`.
- `/rootparam` identifies the VD variant (`DBY_W09_VD` and boardid `<8,2,0,6>`).
- The live tree contains Entry 2's identity values; Entry 8's distinguishing identity values are absent.
- The stock base DTB plus Entry 2 accounts for the live tree's node-set and property changes as analysed in ROUND153. The live tree has 4,566 nodes; the stock base DTB #0 has 3,471 nodes; 1,095 nodes are live-only. All 3,471 base paths survive.
- ROUND153 attributes 411 of 441 shared-node property differences to overlay fragment subtrees; 30 other changes are root identity, `/chosen`, fstab status, and `/memory` changes. No Entry 2 fragment targets `/`, `/chosen`, `/memory` or `/reserved-memory`.
- The `/memory` node and `/chosen` are modified by a non-DTBO boot-chain-side layer. The actor is not identified.
- The stock `/reserved-memory` subtree is byte-identical between the stock base and live FDT. The boot chain did not populate or relocate those carveouts in the observed boot.

This proves that the observed stock boot used an overlay and a further boot-chain mutation layer. It does **not** prove that every possible candidate boot must apply a DTBO, or that the ABL rejects a no-overlay path.

### 3.2 What is not proven

There is no exact-build ABL/XBL image or bootloader trace in the reviewed inputs. Therefore the following remain unknown:

- Whether the ABL unconditionally attempts to apply the selected DTBO entry.
- Whether the DTBO index can be absent, disabled, or bypassed for a candidate package.
- Whether the loader can hand off a base DTB without an overlay.
- Whether the loader's no-overlay path still performs the required `/memory`, `/chosen`, fstab and root-identity mutations.
- Which exact subset of the stock overlay's 1,095 added nodes is required for early boot, storage, display, touch, Wi-Fi, audio, sensors and power management.

### 3.3 Strategy implication

A no-DTBO first boot is **architecturally possible in principle** only if the bootloader permits that path and the candidate base DTB itself contains every node/property needed for the target's early boot and the desired minimum hardware set. The evidence does not establish either condition for the current candidate.

The current 905-node candidate is not shown to contain the required minimum set. It is substantially smaller than the 3,471-node stock base and does not include the vendor additions present in the live tree. The fact that the stock overlay does not apply is not evidence that the overlay is optional.

**Answer to Question 2:** no evidence proves unconditional DTBO application, but no evidence authorizes omission either. A no-overlay route remains UNKNOWN and is not a safe current strategy.

## 4. Keep the four boot-chain concepts separate

### 4.1 Boot-v2 SoC DTB selection by `qcom,msm-id`

The stock Android boot-v2 image has three concatenated FDTs in its DTB region:

| Slot | SoC model | `qcom,msm-id` |
|---:|---|---|
| 0 | kona v2.1 | `<0x164 0x20001>` |
| 1 | kona v2 | `<0x164 0x20000>` |
| 2 | kona v1 | `<0x164 0x10000>` |

The candidate's `qcom,msm-id` is `<0x164 0x20001>`, matching stock slot 0 and the live FDT.

This makes the candidate a plausible match **if** the loader uses the conventional Qualcomm msm-id matching process. The actual selector code is not available. It is unknown whether the target ABL scans all concatenated FDTs, uses a fixed slot, applies additional board/revision rules, or requires another table ordering.

**Recommendation:** preserve the stock three-FDT layout and order for the first candidate package design, with the candidate-specific SoC DTB replacing slot 0 and the stock v2/v1 fallbacks retained byte-for-byte. This is the least disruptive offline packaging hypothesis, not a proven loader contract.

### 4.2 DTBO index selection

The observed `androidboot.dtbo_idx=2` is a DTBO table index. ROUND153/154 identifies that selected entry as Entry 2, with overlay root board-id `0x200e`.

This must not be conflated with:

- the SoC DTB slot number (0, 1 or 2);
- the `qcom,msm-id` pair used to identify a SoC FDT;
- the `qcom,board-id` property embedded in an overlay; or
- the DTBO container table's `id` and `rev` fields.

ROUND153 reports all nine DTBO table `id`/`rev` fields are zero, while the base SoC DTB has root `qcom,board-id = <0 0>`. The observed live overlay identity is Entry 2 / `0x200e`; Entry 8 / `0x206a` is a different variant. The evidence does not explain where the loader obtains the selection value or which code performs the selection.

**Answer to Question 3 (selection part):** retain the observed index-2 fact as an observation, not a causal explanation. Do not claim that the base DTB's `qcom,board-id` selects Entry 2.

### 4.3 External fixup resolution

The stock entries use external symbols. Their fragment targets are placeholders (`0xffffffff`) and the overlay's `/__fixups__` maps symbol names to overlay locations to patch. The base DTB must export the corresponding labels in `/__symbols__` for this fixup scheme.

The symbol table is a name-to-path mapping; the resolver then obtains the target node's phandle. A missing symbol cannot be repaired by changing the overlay's DTBO index, changing `qcom,msm-id`, or merely adding `-@`.

A custom overlay can be designed to avoid many external symbol dependencies by using `target-path` fragments and by keeping references internal to the overlay where appropriate. Any genuine reference to a node in the base still needs a stable resolution strategy and a real target node. This design choice must be tested against the actual overlay implementation used by the bootloader; ACK's libfdt implementation is a source reference, not proof that Huawei's ABL uses precisely this code path.

### 4.4 Bootargs and `/rootparam` mutation

These are separate mutations:

- The live `/rootparam` identity is consistent with the root-level properties contributed by the selected overlay. No fragment targets the root node itself; overlay-root properties are merged at the root.
- `/chosen/bootargs`, initrd start/end and KASLR seed are part of the non-fragment boot-chain mutation set. ROUND153 shows the live bootargs incorporate the boot image header cmdline and bootloader-set Android boot arguments.
- `/memory/reg` is rewritten from one zero-size tuple to three live RAM windows, and `ddr_device_type` is added, by a layer that is not the DTBO application.
- 21 fstab status properties are also rewritten outside the overlay fragments.

The actor is not proven to be ABL specifically. Do not state that ABL owns all of these operations until the exact-build ABL or a trace establishes it.

## 5. Is modifying only DTBO Entry 2 sufficient?

**No, not as a complete flashable package under the current evidence.**

### 5.1 DTBO container mechanics

The stock DTBO container has a header, an entry table, nine entry records and aligned entry payloads. Entry 2 is a slice inside the container. If a replacement Entry 2 is exactly the same byte length and all other offsets/layout fields remain valid, the container's structural header/table might remain unchanged. That does not make the modified image valid under AVB.

If the replacement entry changes size, the container must be repacked consistently: update the affected entry size and offset fields, any later offsets that move, aggregate size/total fields and alignment/padding. The complete image must be reparsed and every entry boundary verified. A byte-level replacement that ignores these fields is not acceptable.

### 5.2 AVB consequence

ROUND154 reports the root vbmeta chain has SHA256_RSA2048 descriptors covering `boot`, `ramdisk` and `dtbo`. Changing only Entry 2 changes bytes inside the DTBO partition and therefore invalidates the DTBO descriptor's expected digest. Changing the candidate DTB inside `boot.img` invalidates the boot descriptor.

Thus:

- Editing Entry 2 alone does not yield a valid signed package.
- Repacking the DTBO header/table correctly does not restore AVB validity.
- Updating a vbmeta descriptor without the required signing key does not create a valid signature.
- A changed boot image also requires its boot descriptor and authenticated chain to be regenerated.
- No unknown signature bypass, unlocked-state acceptance, or KernelSU/root-based recovery route may be assumed.

**Answer to Question 4:** an entry-only byte edit is not sufficient. At minimum, all affected container metadata must be correct; and the AVB descriptor/vbmeta chain must be validly regenerated and signed. With no OEM signing key or demonstrated authorized alternative, this is a hard package blocker. Do not disable AVB or infer a bypass.

## 6. Candidate-specific overlay versus expanding the base DTB

### 6.1 Candidate-specific minimal overlay

A custom overlay can preserve a clean separation between the SoC base tree and device/variant-specific additions. It is the preferred *design direction* if the exact loader is confirmed to apply a DTBO and the signing/packaging path is solved.

Criteria for accepting this approach:

1. The exact target ABL's DTBO index selection and apply contract is known.
2. The overlay is generated against the candidate base tree, not pruned mechanically from stock Entry 2.
3. Every fragment target exists. Prefer `target-path` where it avoids unnecessary external label dependencies.
4. Any external fixup references resolve to real exported base labels; any overlay-local phandle references are correctly represented.
5. The overlay provides the minimum required vendor/device nodes and properties, including dependencies between regulators, clocks, resets, pinctrl, interconnects, PMIC, storage, display and input devices.
6. The merged tree is compared structurally against the live stock tree, with explicit allowlists for intentional omissions and changes.
7. The exact DTBO container is reparsed after packing and the AVB chain is validly signed.

Risks:
- The current candidate lacks 156 of 166 stock Entry 2 external symbols even after `-@`; the missing symbols include hardware/vendor-specific areas. A small overlay cannot simply assume those targets exist.
- A `target-path` fragment can avoid a label lookup but cannot create a missing parent node or satisfy a missing dependency.
- Root-level identity, `/chosen`, memory map and reserved-memory semantics must not be delegated to the overlay when the observed stock chain changes them separately.
- Duplicate or conflicting phandles, regulator consumers, clock/reset references, interconnect paths and power-domain relationships can yield a tree that parses but does not boot.
- A valid `fdtoverlay` result only proves host-side libfdt merge success, not ABL acceptance or hardware correctness.

### 6.2 Expanding the base DTB

Putting more of the minimum hardware tree directly into the candidate base DTB reduces dependence on external symbols for those nodes and makes a no-overlay route more plausible if the loader permits it.

Criteria for accepting this approach:

1. A documented minimum-node/dependency set is derived from the live FDT and driver probe dependencies.
2. The candidate base contains every required node and dependency with valid addresses, interrupts, clocks, resets, regulators, pinctrl, interconnect and phandle relationships.
3. Boot-chain-owned properties (`/memory`, `/chosen`, fstab mutations and any root identity) are explicitly handled and not assumed to be supplied by DTBO.
4. Any overlay still applied by the bootloader is compatible with the expanded base; duplicate-node merges and property overrides are tested.
5. The resulting DTB is validated against the exact ABL selector and the final AVB packaging/signing contract.

Risks:
- A large base-tree reconstruction increases the surface for incorrect phandles, missing dependencies, conflicting providers and accidental changes to generic SM8250 nodes.
- Copying the entire live FDT into the base is not automatically correct: the live tree includes runtime/boot-chain mutations and possibly generated values whose provenance is unknown.
- Adding stock labels does not automatically reproduce vendor initialization or bootloader behavior.
- If the ABL unconditionally applies Entry 2, a full base expansion still leaves the stock overlay incompatibility problem unless the overlay is also made compatible or replaced.
- If a no-overlay path is attempted without exact ABL evidence, a technically complete DTB may still never be selected or handed off.

### 6.3 Recommendation

Use a **hybrid in design, not in a live package**:

- Make the candidate base DTB self-sufficient for the minimum SoC and early-boot dependencies that can be established from source and live-tree evidence.
- Use a candidate-specific custom overlay only for the remaining device/variant layer if the exact ABL contract confirms it is needed.
- Do not preserve stock Entry 2 or Entry 8 as-is.
- Do not prune stock Entry 2 and assume the remaining fragments are valid.
- Do not choose a no-overlay package until the ABL's behavior and minimum-node coverage are proven.

This is smaller and more auditable than blindly rebuilding the full 3,471-node stock base or the 4,566-node live tree, while avoiding the unsupported assumption that the current 905-node candidate is sufficient.

## 7. Package option matrix

| Option | Technical assessment | Evidence classification | Recommendation |
|---|---|---|---|
| Three concatenated FDTs; candidate at slot 0 matching `0x164/0x20001`; retain stock slots 1/2 | Preserves the stock slot count/order and candidate's msm-id match. Does not prove the ABL selector or overlay compatibility. | **Plausible / selector UNKNOWN** | Best conservative packaging hypothesis for offline design only |
| One-FDT slot | Could work only if the loader accepts a single FDT and selects it without depending on the stock concatenation layout. No evidence establishes this. | **UNKNOWN / unsupported** | Do not choose |
| No DTBO | Stock live boot did apply Entry 2. The loader's no-overlay behavior is unknown; the current candidate's minimum hardware coverage is unproven. | **UNKNOWN; current candidate not demonstrated sufficient** | Do not choose now |
| Custom DTBO | Necessary if the selected overlay mechanism is required, because stock Entry 2/8 cannot resolve against the current candidate. Requires a candidate-specific dependency/fixup design and AVB signing. | **Design direction plausible; implementation and loader acceptance UNKNOWN** | Preferred conditional overlay strategy, not yet packageable |
| Reuse stock Entry 2 unchanged | 0/166 fixups on current base; only 10/166 with `-@`; apply fails. | **Disproven for current candidate in tested host libfdt path** | Reject |
| Reuse stock Entry 8 unchanged | Same symbol deficit and no compatibility advantage; it is also the wrong observed variant for the captured VD boot. | **Disproven for current candidate in tested host libfdt path; wrong variant for observed boot** | Reject |

## 8. Smallest next experiment that closes the most important unknown

**Acquire and inspect the exact-build ABL image offline.** This is the highest-value next step because it can close several questions at once without writing to the tablet.

Required identity:
- ABL extracted from the exact HOS 4.3.0.196(C00E100) firmware package matching the captured device build, or a previously acquired exact-build ABL artifact with a trustworthy hash/provenance chain.
- Do not substitute an ABL from another Huawei model, another HOS build, another board variant or a generic SM8250 reference.

Minimal analysis:
1. Hash and identify the ABL artifact; document package/build provenance.
2. Search and, where possible, disassemble the code paths that parse the boot-v2 concatenated DTB list and compare `qcom,msm-id`.
3. Locate the DTBO index selection path and determine whether `androidboot.dtbo_idx` is an input, output, or both.
4. Determine whether overlay application is unconditional, optional, or conditional on metadata; identify how `__fixups__` are resolved.
5. Locate rootparam and memory-map mutation routines and distinguish code evidence from mere strings.
6. Publish exact offsets/symbols/disassembly excerpts and a confidence grade; strings alone are not proof of control flow.

If the exact-build ABL cannot be obtained from the existing offline firmware package, record that absence and stop. Do not replace this experiment with a device write or a guess based on another bootloader.

A parallel host-only follow-up after the ABL contract is known would be to create a tiny custom overlay using `target-path` and no external base labels, apply it to a copy of the candidate DTB with the pinned ACK `fdtoverlay`, and verify the merged tree. That test validates overlay syntax/merge mechanics only; it cannot establish the ABL selector or bootability.

## 9. Offline, ABL-dependent and device-only gates

### 9.1 Offline-testable now

- Reparse and hash the existing boot-v2 image and all three FDTs.
- Reparse the DTBO container and each entry, including offsets, lengths, alignment and root metadata.
- Re-run external-symbol and fragment-target resolution against the candidate DTB once the exact binaries are staged as read-only inputs.
- Test `-@` symbol export and custom overlay merging with pinned ACK libfdt.
- Compare base/candidate/merged/live FDT node and property sets, with an explicit required-node dependency matrix.
- Validate RAM tuple arithmetic, reserved-memory intervals and phandle graph.
- Validate boot-v2 header fields and container boundaries after any offline repack.
- Recompute all affected image hashes and verify AVB descriptor consistency/signatures if and only if the legitimate signing material is available.

### 9.2 Requires exact-build ABL or equivalent bootloader trace

- Whether the loader scans the three FDTs or selects a fixed slot.
- Whether it selects by `qcom,msm-id`, and how fallback/revision matching works.
- How the loader selects DTBO index 2 and what metadata it compares.
- Whether it always applies the selected overlay or supports a no-overlay path.
- Which component applies external fixups.
- Which component mutates `/rootparam`, `/chosen`, `/memory`, `ddr_device_type` and fstab properties.

### 9.3 Only a controlled device boot can determine

- Whether the bootloader accepts and hands off the proposed signed package on the actual DBY-W09.
- Whether the kernel reaches early userspace and whether storage, display, touch, Wi-Fi, audio, thermal and power-management dependencies work at runtime.
- Whether the real RAM map, carveouts, DMA pools, secure-world reservations and runtime firmware interactions behave correctly.
- Whether suspend/resume, reboot and recovery paths work on the target hardware.

A device boot is a later, separately authorized stage. It is not authorized by this review.

## 10. What must be backed up and verified before any write

Before any future flash/write authorization, the evidence package must contain:

1. **A complete raw backup of every partition that may be affected or required for recovery**, not merely the 15 boot-family payload images. Include boot, dtbo, vbmeta and all chained vbmeta partitions, plus relevant bootloader/metadata partitions such as abl/xbl and partition metadata where available. Record exact partition names, sizes and slot suffixes.
2. A cryptographic hash (preferably SHA-256) for every raw backup, plus a second independent read/hash or equivalent verification that the backup bytes are complete and stable.
3. A complete GPT/partition map and current slot/boot-control metadata, including any boot-success/rollback counters relevant to the platform.
4. The exact stock firmware package and its hashes, with a documented mapping from package images to on-device partition targets.
5. A proven, authorized route to restore the exact original stock state. The route must be rehearsed on offline images and its practical availability on this device must be established before any write. A recovery image existing in a package is not proof that restoration works.
6. A record of AVB chain relationships, descriptor digests, rollback-index constraints and signing-key provenance. Do not write a package whose chain cannot be authenticated under the actual device policy.
7. A user-data preservation plan and explicit acceptance of data-loss risk. Do not assume that restoring boot-family partitions alone is enough to recover all device state.

ROUND154 reports that only 15 boot-family payload images are present, 86 by-name partitions were visible but their sizes were denied, no complete per-partition backup/hash set exists, and no exact-stock restore rehearsal exists. These are not paperwork gaps; they are hard recovery blockers.

## 11. Ranked blockers and required exit criteria

| Rank | Blocker | Current status | Exit evidence |
|---:|---|---|---|
| 1 | Exact-build ABL selector / overlay / memory-fixup contract | **UNKNOWN** | Exact ABL static analysis or equivalent exact-build trace |
| 2 | Stock Entry 2/8 incompatible with current candidate | **FAIL** | Candidate-specific overlay/base design with complete host-side fixup and merge tests |
| 3 | Minimum required base-tree coverage | **UNKNOWN / not demonstrated** | Dependency matrix from live tree + source, then validated merged DTB |
| 4 | AVB signing and authenticated package path | **BLOCKED** | Valid signed descriptors/chain under actual device policy; no assumed bypass |
| 5 | Full backup and exact-stock restore route | **FAIL** | Complete hashed backup plus proven restore procedure |
| 6 | Three-FDT / DTBO package selector semantics | **PARTIAL** | Exact ABL analysis; retain conservative stock shape until resolved |
| 7 | Device runtime acceptance | **NOT RUN / NOT AUTHORIZED** | Separate first-boot gate after all prior blockers close |

### Final verdict

- **Current ROUND154: hard no-go for flash and first boot.**
- Best next action: exact-build ABL offline acquisition and static analysis.
- Best future design direction: self-sufficient minimum base DTB plus a small candidate-specific overlay only if the ABL contract requires it; preserve the stock three-FDT layout as the conservative initial packaging hypothesis.
- Stock Entry 2/Entry 8 are not compatible with the present candidate in the tested host libfdt path.
- No first-boot, flash, fastboot, recovery, partition-write, source-edit or build authorization is granted by this report.

**STOP — ROUND155 review complete.**
