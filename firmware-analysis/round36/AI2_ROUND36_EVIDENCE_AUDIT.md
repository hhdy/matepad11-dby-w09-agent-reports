# AI2-ROUND36 — Phase E evidence audit: ABL memory handoff and PM8150 L5/L9 physical supply

**Task owner:** 2号 AI
**Branch:** `firmware-audit-v1`
**Date:** 2026-11-26
**Type:** read-only evidence audit. No code, no DTS, no build, no firmware upload, no device access.

**Pinned inputs**

| Input | Identity |
|---|---|
| Report corpus | `hhdy/matepad11-dby-w09-agent-reports` `firmware-audit-v1` @ `be4f5178c41b4a26c5bc5f5658244e3470d82151` |
| Stage A corpus | same repo, `ai-parallel/stagea-port-until-boot` @ `f0b00e38c8222be14adfb21f122db7f8cac94c14` |
| ACK source reference | `android17-6.18.33_r00` @ `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` |
| Taskbook | `firmware-analysis/round36/AI2_ROUND36_TASKBOOK.md` |

---

## 0. Verdict

### 中文结论

两个工作流的结论都是 **`BLOCKED — direct evidence absent`**，且原因不同、不可互相替代：

- **工作流 A（ABL 内存交接）**：`/sys/firmware/fdt` 是设备上唯一可能的交接后制品（800316 B，`-r--------`），历史抓取因权限失败，从未成功取回；离线 base DTB 是 ABL 之前的模板（`/memory/reg` 全零）。本轮新增两项**结构性**旁证（B 级，仅长度/节点名，无任何数值）：live 树 `/memory/reg` 为 48 B 而离线模板为 16 B，说明两者不是同一个属性值；live `reserved-memory` 目录 `st_nlink=39` ⇒ 37 个子节点，独立印证 ROUND24 的 37 并解释 ROUND64/ROUND61 的 34 来自 ROUND7 CSV 的口径。**但 RAM bank 的 base/size、carveout 区间、EFI memory descriptor、ABL 实际选中的 DTBO、内核进入方式五项全部 `MISSING`**，本轮不给出任何数值。
- **工作流 B（PM8150 L5/L9 供电）**：软件层（芯片内部 regulator 类型、输出电压、原始 `init-mode`、proxy 请求）证据充分；**物理层（输入端 parent rail、输入电压、电流能力、上电时序、板级 revision）全部 `MISSING`**。全 FDT 扫描 0 命中 `vdd-s*-supply`/`vin-supply`/`vph-pwr-supply`，0 命中 `qcom,pmic-id`，9 个 DTBO 均不改这些 rail。ACK 驱动表的 `vdd-l3-l4-l5-l18` / `vdd-l6-l9` 只是**软件属性名**，且该属性在 binding 中为可选、在本机 DT 中不存在。

Phase E/F 维持 **BLOCKED**，Phase G 维持 **NOT RUN**。本轮未猜测任何数值，未修改任何生产代码/DTS/Kconfig/defconfig，未上传固件，未接触设备。

### Verdict table

| Workstream | Verdict | Decisive reason | Matrix |
|---|---|---|---|
| A — ABL final memory handoff | **`BLOCKED — direct evidence absent`** | No post-ABL capture exists. The only candidate (`/sys/firmware/fdt`) was never read: `adb: error: failed to stat remote object '/sys/firmware/fdt': Permission denied` (`round2-adb/live_dtb_status.txt:1-3`). The offline base DTB is an L2 template whose `/memory/reg` is all-zero (`round19…txt:46`, `:624`). | `abl-memory-evidence-matrix.md` |
| B — PM8150 L5/L9 physical input | **`BLOCKED — direct evidence absent`** | No board-specific schematic, PMIC power tree, BOM or rail measurement exists in the corpus (`round64…md:37`, `:40-42`); the HOS base FDT carries no input-supply property (`round11…txt:74-79`); board revision is UNKNOWN. | `pm8150-physical-topology-matrix.md` |

### Classification counts

| Workstream | Rows | PROVEN | PARTIAL | MISSING | CONFLICT |
|---|---|---|---|---|---|
| A | 39 | 23 | 4 (incl. `A-15`, split: interval comparison proven, addresses missing) | 11 | 1 (`A-11`, explained) |
| B | 50 | 39 | 1 (`B-04`) | 10 | 0 |

**Zero `A — Direct` rows exist for either workstream.** The highest grade actually reached is `B` (corroborating: live directory metadata, static-artifact parses, verified whole-tree absence scans) and `C` (ACK driver/binding/kernel-source semantics). This is the precise sense in which the evidence is *absent* rather than merely *thin*: Phase E needs `A`, and the corpus contains no `A` artifact at all.

---

## 1. How the taskbook was interpreted

The taskbook (`§目标`) asks a narrow question: *can the existing corpus prove these two hardware facts; if not, exactly which original evidence is missing?* It explicitly forbids filling the gap (`§明确禁止` bullets 6–8) and forbids treating `*-supply` declarations, regulator node names, software proxy-votes or reference-platform designs as board-wiring proof (`§明确禁止` bullet 7).

Accordingly this round:

- searched both branches for existing ABL / boot-chain / FDT / EFI / reserved-memory / DTB-DTBO / boot-path reports;
- recorded, for every candidate fact, the **layer** (source DTS / static DTB / final FDT) and the **grade** (A/B/C/D);
- marked every row `PROVEN` / `PARTIAL` / `MISSING` / `CONFLICT` with a `path:line` citation;
- produced an evidence request list split into documents the user can supply and artifacts that require device or hardware access.

It did **not** attempt to close either gap.

---

## 2. Corpus actually inspected

Read-only; each file's SHA-256 and blob SHA are in `source-hashes.txt`.

| Document | What it contributed | Highest grade used |
|---|---|---|
| `firmware-analysis/round64/round64-…-final-memory-and-pm8150-input-evidence.md` | prior BLOCKED verdict on both outputs; the authoritative statement of what is *not* available | B |
| `firmware-analysis/round24/round24-hos43-reserved-memory-and-consumer-map.txt` | 37-child inventory, attributes, consumer map, 34-vs-37 reconciliation | B |
| `firmware-analysis/round26/round26-sm8250-vs-hos43-reserved-memory-interval-audit.txt` | ACK 18 / 17 EXACT / 1 ACK_ONLY / 7 HOS_ONLY interval comparison | B |
| `firmware-analysis/round19/round19_hos43_boot_ramdisk_avb_dtbo_audit.txt` | zero `/memory` reg, chosen contents, 9-DTBO non-interference, ABL artifact triage, boot-header fields | B |
| `firmware-analysis/round20/round20_efi_stub_memory_handoff_and_boot_payload_compatibility.txt` | kernel-side: classic vs EFI-stub memblock construction; layers 3–4 UNKNOWN | C |
| `firmware-analysis/round11/round11_pmic_parent_supply_findings.txt` | verified NOT_FOUND scans; the 4 ARC parent edges and 6 proxy edges | B |
| `firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt` | L5/L9/S4/L6/L17 rail-by-rail raw values; 0-hit census | B |
| `firmware-analysis/round7/dby_w09_hw_matrix.txt`, `dtb_property_inventory.csv`, `dtbo_board_rootparam_matrix.csv` | DTBO board-id list; property inventory (re-counted this round: 34 unique reserved-memory paths, 0 `/memory` rows) | B |
| `round2-adb/live_dtb_status.txt`, `devicetree_nodes_redacted.txt`, `devicetree_base_redacted.txt`, `partition_names_redacted.txt` | the only live-device observations: sizes, directory listings, `st_nlink`, denied reads, partition symlinks | B |
| `stagea:kernel-baseline/round19/…handoff-review.md` | `/memory` handoff review | B |
| `stagea:kernel-baseline/round21/ack-pm8150-vrm-parent-supply-gap.md` | ACK supply_name table; dummy-regulator semantics | C |
| `stagea:kernel-baseline/round42/hos43-memory-handoff-sm8250-abl-fdt-prerequisite.md` | pinned FreeABL SM8250 `UpdateDeviceTree()` `/memory` precondition; `AddMemMap()`; `REMOVE_CARVEOUT_REGION` | C |
| `stagea:kernel-baseline/round43/ack-6.18.33-fdt-memory-scan-classic-vs-efi-handoff.md` | EFI-stub writes `/chosen/linux,uefi-*`; does not synthesize `/memory`; entry-path table | C |
| `stagea:kernel-baseline/round61/phase-e-board-dts-memory-power-gates.md` | the Phase E gate definition and required-evidence list | — |
| `stagea:dts/dby-w09-ack18-board.dts.draft` | current consumer→output mapping and its explicit do-not list | C |
| ACK `drivers/regulator/qcom-rpmh-regulator.c`, `drivers/regulator/core.c`, `Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml` | driver input names, dummy fallback, binding optionality | C |

---

## 3. Workstream A — what is proven and what is not

**Proven (B):** the carveout *inventory* and *attributes*; the fact that no stock DTBO touches memory, `/chosen`, `/reserved-memory` or fstab; the fact that the offline base DTB has an all-zero `/memory/reg`; the fact that a post-ABL blob exists on the device at 800316 B and that reading it failed; the ACK/HOS interval correspondence at 17/18 nodes; the live tree's structural shape.

**Not proven (MISSING):** every populated number.

| Missing | Why it blocks |
|---|---|
| RAM bank base/size (`A-04`) | cannot reconcile any reserved range against usable RAM |
| Per-carveout `reg` (`A-12`, `A-16`) | cannot prove a carveout is inside RAM rather than outside it |
| EFI descriptors (`A-21`) | closes Path B entirely |
| Kernel entry classification (`A-25`) | without it, Path A (classic FDT) and Path B (EFI stub) cannot be discriminated, and the two require different verification |
| Selected DTBO entry (`A-36`) | the board variant (VA–VI) determines which overlay's nodes are in the final tree |
| ABL bytes (`A-32`) | cannot verify that ABL's own memory mutation ran, only that *something* populated `/memory` |

### 3.1 Two new structural observations this round (B, no values)

1. **Live `/memory/reg` is 48 B while the offline template's is 16 B** (`round2-adb/devicetree_base_redacted.txt:68` vs `round19…txt:624`). The two are therefore not the same property value — the offline blob is demonstrably not what the kernel is running with. This is the first *direct* (if value-free) confirmation of the layer separation this whole audit depends on. **The cause is not established**: the ABL `AddMemMap()` rewrite (a same-SoC-class mechanism only — `stagea:round42…md:94-101`), a DTB source other than the extracted boot-image DTB, and post-handoff mutation are all `D` and none is selected. The cell count could not be read, so **no bank count, base or size is asserted anywhere in this report**.
2. **Live `reserved-memory` has `st_nlink` 39 ⇒ 37 subdirectories** (`round2-adb/devicetree_nodes_redacted.txt:69`), independently corroborating ROUND24's 37 and resolving the 34-vs-37 discrepancy (see §5).

### 3.2 What would settle A

One artifact: the 800316-byte blob (request `D-1`), or — if privilege is limited — the ~15 targeted property reads (request `D-2`). One boot log settles the entry-path sub-question (`D-4`).

---

## 4. Workstream B — what is proven and what is not

**Proven (B/C):** L5 and L9 exist, are `pmic5-ldo` (ACK table: `pmic5_nldo`), output 880000 µV / 1200000 µV fixed, carry vendor `qcom,init-mode = 4` and `qcom,set = 3` (raw, semantics unmapped), and each has a 100000 µA proxy-consumer request. Both are UFS QMP PHY rails. The ACK driver expects input property names `vdd-l3-l4-l5-l18` and `vdd-l6-l9`; the binding permits but never requires them. The dummy-regulator path explains why a board DTS without them still probes.

**Not proven (MISSING):** the physical input parent, input voltage, current capability, sequencing, and even the board revision a schematic would have to match.

The chain `pmic5-ldo` → `"vdd-l6-l9"` → *where the copper goes* breaks at step 3, and no artifact in the corpus supplies it. The four edge types that look like candidate evidence (driver input name, binding permission, ARC `*-parent-supply`, `proxy-supply`) are each disqualified in `pm8150-physical-topology-matrix.md` §0, with the ACK source line that shows why.

### 4.1 The dummy-regulator trap, stated once

`have_full_constraints()` returns true whenever a DT is populated (`core.c:114-117`), so an unmatched `supply_name` resolves to `dummy_regulator_rdev` (`core.c:2070-2091`) and, on the consumer side, the in-tree comment states the assumption outright: *"Assume that a regulator is physically present and enabled, even if it isn't hooked up, and just provide a dummy."* (`core.c:2229-2233`). Therefore **a successful boot is not evidence of a physical rail**, and no future "it works" observation may be used to close this gate.

---

## 5. Conflict / discrepancy register

| # | Discrepancy | Where it appears | Resolution | Carry forward |
|---|---|---|---|---|
| 1 | `reserved-memory` child count **34** vs **37** | 34: `round64…md:24`, `stagea:round61…md:12`, `:32`. 37: `round24…txt:31-46` | Not a hardware conflict — a counting-scope difference. `firmware-analysis/round7/dtb_property_inventory.csv` yields **34 unique direct-child paths** under `/reserved-memory` across 279 rows (re-counted this round with an independent parser), while the full dtc dump yields 37. Live corroboration: `reserved-memory` `st_nlink` 39 ⇒ 37 subdirectories (`round2-adb/devicetree_nodes_redacted.txt:69`) | **37** is the correct child count for both the static and the live tree. ROUND64/ROUND61's 34 should be read as "the ROUND7 CSV figure". No numeric consequence: addresses remain unpublished either way |
| 2 | `abl` **absent** from the offline payload vs **present** on the device | absent: `round19…txt:122-126` (43 package entries, `xbl.img`/`xbl_config.img`, no `abl.img`/`abl.elf`). present: `round2-adb/partition_names_redacted.txt:5` (`abl -> /dev/block/sde6`) | Not a conflict — two different inventories (offline update-package payload vs live `/dev/block/by-name`). Both statements are true | The ABL binary **exists on the device and was never dumped**; there is no offline copy. Recorded as `A-31`/`A-32`/`A-33` |
| 3 | Offline `/memory/reg` (16 B, all zero) vs live `/memory/reg` (48 B) | `round19…txt:624` vs `round2-adb/devicetree_base_redacted.txt:68` | Not a conflict — a layer difference (L2 template vs L3 live tree). It is in fact positive evidence that the layers must be kept separate | Values remain `MISSING`; cause is `D` and unasserted |
| 4 | ROUND7 CSV records `__symbols__`/`__fixups__` as absent for all 9 DTBO entries, while ROUND8/ROUND13 resolve entry 8 through a real `__fixups__` node | `round13…txt:50-56` | Already documented as a ROUND7 column-scope artifact in ROUND13 §1.6; not re-litigated here | Not material to ROUND36 (no memory/power content in those columns) |

Only entry 1 changes a number anyone might cite; entries 2–4 are recorded so that a future reader does not mistake a scope difference for a contradiction.

---

## 6. What this round adds beyond ROUND64

ROUND64 already returned `BLOCKED` for both outputs. This round does not overturn that; it adds:

1. a row-level matrix with `path:line` citations and explicit grades, so each gap is individually checkable rather than asserted in prose;
2. two new live-device structural observations (§3.1) that strengthen the layer separation without supplying values;
3. resolution of the 34-vs-37 discrepancy with a reproducible re-count and an independent live corroboration (§5.1);
4. separation of the "ABL absent offline" and "ABL present on device" statements, which previously read as a contradiction (§5.2);
5. an explicit disproof of the "it boots, therefore the rails are fine" argument, anchored in `core.c:2229-2233` (§4.1);
6. a prioritized, admissibility-checked evidence request list, split by who can produce each artifact (`missing-evidence-request.md`).

---

## 7. Non-actions (explicit)

- No firmware download, extraction, unpacking or analysis of any previously unauthorized image.
- No device connection, no ADB/fastboot/recovery/root, no partition read or write, no reboot, unlock, temporary boot or flash.
- No DTS/DTBO, boot/vendor_boot/init_boot, vbmeta, AVB/footer, ramdisk or flash-package generation, modification or packaging.
- No product Image build; no change to the 17 frozen production patches, Kconfig, defconfig, Kleaf targets or Stage A sources.
- No guessed RAM address, reserved-memory range, EFI descriptor, ABL DTB/DTBO selection, PM8150 parent, input voltage, load capability or PMIC connection.
- No absence turned into "the hardware does not have it", and no substitute value created.
- The two audit worktrees were used read-only; the only writes were the five files of this round under `firmware-analysis/round36/`.

---

## 8. Acceptance self-check against the taskbook

| Criterion (`§验收标准`) | How it is met | Where |
|---|---|---|
| ABL and PM8150 audited separately, neither substituting for the other | two independent matrices, disjoint ID spaces (`A-*` / `B-*`), separate verdicts | this file §0; both matrices |
| Every key fact carries a grade, a status and a source identity | every table row has `Grade` + `Status` + `path:line` | all matrices |
| Final ABL FDT kept distinct from static DTS/DTB | explicit three-layer section; every row tagged L1/L2/L3; §5 row 3 | `abl-memory-evidence-matrix.md` §0 |
| Physical wiring kept distinct from software regulator description | explicit four-edge-type disqualification table; the dummy-regulator section | `pm8150-physical-topology-matrix.md` §0, §4 |
| No guessed values, no production change, no firmware upload, no device action, no packaging | §7 above; §12 of the matrix cross-references | this file §7 |
| Missing material listed as a minimal next request, and Phase E not declared unblocked | 9 prioritized requests split U/D, each with accepted/rejected forms and the IDs it closes; explicit BLOCKED restatement | `missing-evidence-request.md`; below §9 |
| Report cites exact paths, commits, line numbers/node names and evidence hashes | `source-hashes.txt` registers every cited file with branch, commit, Git blob SHA and SHA-256 | `source-hashes.txt` |

---

## 9. Phase status

| Phase | Status | Note |
|---|---|---|
| E — board DTS / memory / power | **BLOCKED** (both workstreams) | unchanged by this round; requires an `A`-grade artifact |
| F | **BLOCKED** | unchanged |
| G | **NOT RUN** | unchanged |

Nothing in this round authorizes a board DTS migration, a `dtbs_check` run, a boot attempt, or ROUND37. Per the taskbook's stop rule, this audit stops here and awaits 2号 AI's independent review.

---

## Appendix — deliverables of this round

| File | Content |
|---|---|
| `AI2_ROUND36_EVIDENCE_AUDIT.md` | this report: verdict, method, corpus, findings, conflict register, acceptance self-check |
| `abl-memory-evidence-matrix.md` | workstream A: 39 rows over 6 sections, layered and graded |
| `pm8150-physical-topology-matrix.md` | workstream B: 50 rows, with the four-edge-type disqualification and the negative-finding register |
| `missing-evidence-request.md` | 9 prioritized requests (4 document / 5 device-hardware), each with accepted and rejected forms and the IDs it closes |
| `source-hashes.txt` | path, branch, commit, Git blob SHA, SHA-256, byte size and line count for every cited file |
