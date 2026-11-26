# ROUND154 — WorkBuddy Window A: minimal RAM patch + DTBO / boot-v2 package gate

- **Executor:** WorkBuddy Window A (1号 Agent).
- The other local executor is WorkBuddy Window B (2号 Agent). Both are WorkBuddy chat windows; do not confuse product identity with task-role identity.
- Device: Huawei MatePad 11 (2021), DBY-W09 / HWDBY / KONA / SM8250.
- Base: ACK `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`; accepted pre-change tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`.
- Task type: local source edit in a **new reversible worktree/branch**, scratch DTB build and static package compatibility tests. No full kernel build yet. No device.

## 1. Purpose

ROUND153 confirms a device-specific three-window RAM map, but also discovers two packaging risks:
- the live HOS boot uses DTBO Entry 2 (`0x200e`), not the candidate comment's Entry 8 (`0x206a`);
- the candidate DTB currently has no exported `rootparam` symbol/phandle, while stock overlays use external `rootparam` fixups. The complete Entry 2 fixup set must be tested against the candidate—not assumed compatible.

The aim is to produce the smallest candidate DTB that can be packaged coherently for the first boot, without adding unrelated hardware features.

## 2. Inputs and workspace restrictions

Use only:
- Window A's own existing canonical candidate source workspace and existing WorkBuddy firmware extraction workspace;
- published ROUND138, ROUND151, ROUND153 reports;
- public/pinned ACK sources.

Do not enter Window B's workspace or use its private logs. If the canonical source tree cannot be located or does not match the pinned 23-patch tree, stop and report the exact mismatch. Do not overwrite the frozen ROUND140/ROUND151 artifacts. Create a new worktree or copy for this round.

## 3. Required task A — minimal RAM-only DTS correction

On the new worktree, change the existing `/memory@80000000` node's `reg` property from one zero-size tuple to exactly these three 2-address-cell / 2-size-cell tuples:

```dts
memory@80000000 {
    reg = <0x0 0x80000000 0x0 0x39900000>,
          <0x0 0xc0000000 0x0 0xc0000000>,
          <0x2 0x00000000 0x2 0x00000000>;
};
```

No second `device_type = "memory"` node. Do not change any of the 18 `/reserved-memory` entries or their properties. Retain the 70 MiB `cdsp_secure_heap` provisionally.

Keep the root `qcom,board-id = <0 0>` unchanged. Correct stale comments only:
- do not claim selection by `0x206a`;
- state the captured stock boot used `dtbo_idx=2` / Entry 2 / `0x200e`, while the mechanism selecting the index remains unknown;
- do not assert ABL is the memory mutator: stock boot-chain mutation is proven, exact component unknown;
- update the comment that says final RAM tuple is still unknown, because the candidate DTS now explicitly declares it.

Provide exact patch diff, new source tree SHA, patch SHA, and note every changed file.

## 4. Required task B — compile and validate candidate DTB in scratch

Build only the affected DTB target, not the full kernel Image. Record exact command, toolchain, environment and full logs. Inspect the resulting DTB bytes and prove:
- exactly one root node with `device_type = "memory"`;
- its `reg` has 12 cells with exactly the tuples above;
- no arithmetic gaps were accidentally filled; base order and 64-bit high cells correct;
- all 18 reserved-memory intervals exactly match the frozen candidate and lie within RAM window 1;
- no other DTS/property changed.
Do not use a previous output DTB as proof of the new source.

## 5. Required task C — stock Entry 2 / Entry 8 compatibility against candidate

Use the stock DTBO extracted by Window A in its own firmware workspace. The live device evidence is Entry 2 / `dtbo_idx=2`; Entry 8 is not the live overlay on the captured unit.

1. Parse all 144 Entry 2 fragments and every external fixup symbol, resolving against the candidate DTB built in Task B.
2. Determine which fragment targets / symbols are absent from the candidate. Distinguish absent labels from absent target nodes.
3. In a scratch-only build, test candidate source with `rootparam: rootparam { ... } ` label exported using `dtc -@` / the actual kernel DTC flag mechanism. Do not modify the accepted source patch with this experiment.
4. Re-test the entire Entry 2 overlay after the experiment. `rootparam` resolving alone is insufficient. Record every unresolved symbol/target and exact apply error.
5. Test whether Entry 8 has the same compatibility result; do not spend time restating its known differences.
6. Decide among: stock Entry 2 can apply; stock Entry 2 cannot apply and a minimal custom overlay is needed; or the device boot chain / selected overlay mechanism remains unknown. Do not invent a target-path or selector contract.
7. Keep original stock DTBO bytes untouched.

No speculative ARC/proxy additions. No flash or device operation.

## 6. Required task D — boot-v2 / DTB container packaging contract

From the existing stock boot image and actual project build/package scripts, determine:
- stock boot image header version, DTB slot offset/size/address and the 3 concatenated FDT sizes/order;
- how the loader selects the SoC DTB by `qcom,msm-id`, and whether a single candidate DTB can satisfy that selection;
- whether the separate DTBO partition is applied to the DTB in `boot.img`, and what metadata/board-id the package needs;
- exact candidate output expected in `boot.img`: one FDT vs three concatenated FDTs, correct header `dtb_size` and `dtb_addr`, and whether stock vendor_boot/ramdisk must remain byte-identical;
- hashes and provenance of existing artifacts. If the bootloader selector/ABL path cannot be proven, say UNKNOWN and identify the single evidence needed.

Do not create or flash a boot image yet.

## 7. Required task E — pre-boot security/recovery checklist from existing evidence

Using only existing reports/artifact metadata, mark each:
- AVB/vbmeta chain and footer anomaly understood;
- boot/vendor_boot/init_boot/DTBO partition roles and exact install target known;
- full required partition backup already exists and hashes verified;
- tested route to exact stock state available.
Do not read any device partition. Do not turn a checklist item into PASS without evidence.

## 8. Deliverables and stop

Publish sanitized report:
`firmware-analysis/round154/WORKBUDDY_A_ROUND154_MINIMAL_RAM_PATCH_AND_DTBO_BOOT_PACKAGE_GATE_REPORT.md`

Publish reversible patch separately in the project's source repository/branch; do not put full source files or private/raw firmware in this report repository. Include source branch/commit/tree SHA and exact patch path/commit.

Read back the uploaded report and verify blob SHA/content. Stop after reporting blockers and exact next action. **No full kernel/Image build, no ADB, no partition read/write, no flash, no reboot, no fastboot, no recovery, no candidate boot.**