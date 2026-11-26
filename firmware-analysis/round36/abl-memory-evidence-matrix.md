# ROUND36 — ABL / FDT / EFI / DTB-DTBO memory-handoff evidence matrix

**Workstream:** A (ABL final memory handoff)
**Type:** read-only evidence audit. No code, no DTS, no build, no device access, no firmware re-extraction.
**Branch:** `firmware-audit-v1`

**Pinned evidence trees**

| Tree | Repo / ref | Commit |
|---|---|---|
| Report corpus | `hhdy/matepad11-dby-w09-agent-reports` `firmware-audit-v1` | `be4f5178c41b4a26c5bc5f5658244e3470d82151` |
| Stage A corpus | `hhdy/matepad11-dby-w09-agent-reports` `ai-parallel/stagea-port-until-boot` | `f0b00e38c8222be14adfb21f122db7f8cac94c14` |
| ACK source reference | `android17-6.18.33_r00` | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` |

All paths below are relative to their tree. Line numbers are 1-based on the pinned commit.

**Legend — grade**

| Grade | Meaning (taskbook §证据等级) |
|---|---|
| `A — Direct` | DBY-W09 hardware-revision-specific ABL handoff dump / final FDT / EFI map, or schematic / board power-tree original |
| `B — Corroborating` | ABL log, DTB/DTBO, board design note or verified measurement that matches this device exactly |
| `C — Software-only` | DTS, driver, binding, Kconfig, public reference-platform source |
| `D — Inference` | Derived from node names, reference models, software requests or common platform structure. **D never closes the Phase E gate** |

**Legend — status**: `PROVEN` / `PARTIAL` / `MISSING` / `CONFLICT`.

---

## 0. Three-layer separation (the rule this matrix enforces)

The taskbook (§允许范围, §验收标准) requires the three layers below to stay separate. Every row states which layer it belongs to. No row carries a value from a lower layer into a higher one.

| Layer | Artifact | What it can prove | What it cannot prove |
|---|---|---|---|
| L1 Source DTS | `dts/dby-w09-ack18-board.dts.draft`, ACK `arch/arm64/boot/dts/qcom/sm8250*.dtsi` | intent of a text source | nothing about the shipped device |
| L2 Static DTB/DTBO | stock base DTB inside the HOS4.3 boot image (`boot_fdt_candidate_0.dtb`, totalsize 556524 B, `firmware-analysis/round7/dby_w09_hw_matrix.txt:6`), 9 stock DTBO entries (`dtbo.img`, 25 165 824 B, `firmware-analysis/round19/round19_hos43_boot_ramdisk_avb_dtbo_audit.txt:108`) | the pre-ABL template and the overlay inputs | **not** the post-ABL tree handed to Linux |
| L3 Final FDT / EFI map | `/sys/firmware/fdt` (800316 B, mode `-r--------`), live `/proc/device-tree` | the actual handoff | — (this layer is what Phase E needs) |

The ROUND19 finding that the stock base DTB `/memory` `reg` is `0x0 0x0 0x0 0x0` (`round19…txt:46`, `:624`) is an **L2** fact. It is a template placeholder, not a handoff value. ROUND64 restates this at `firmware-analysis/round64/round64-dby-w09-hos43-final-memory-and-pm8150-input-evidence.md:23`.

---

## 1. RAM banks / root cell configuration

| ID | Fact | Value established | Source (tree:path:line) | Layer | Grade | Status |
|---|---|---|---|---|---|---|
| A-01 | Final FDT root `#address-cells` exists | property present, length **4 B** (i.e. exactly one 32-bit cell holding the count) | report:`round2-adb/devicetree_nodes_redacted.txt:6` | L3 | B | PARTIAL |
| A-02 | Final FDT root `#size-cells` exists | property present, length **4 B** | report:`round2-adb/devicetree_nodes_redacted.txt:7` | L3 | B | PARTIAL |
| A-03 | Numeric value of `#address-cells` / `#size-cells` | **unread** — `cat` of every root property returned `Permission denied` | report:`round2-adb/devicetree_base_redacted.txt:15-22` (compatible), `:23-30` (`#address-cells`), `:31-38` (`#size-cells`) | L3 | — | MISSING |
| A-04 | RAM bank base/size tuples | **not established.** The live `/memory/reg` is **48 B**; its cell decomposition depends on A-03, which is unread. 48 B = 3×16 B *if* the root were `#address-cells=<2>`/`#size-cells=<2>`, or 6×8 B *if* it were `<1>`/`<1>`. **No bank count, base or size is asserted in this report.** | report:`round2-adb/devicetree_base_redacted.txt:68` | L3 | B (length only) | MISSING (values) |
| A-05 | Static base DTB `/memory/reg` | `0x0 0x0 0x0 0x0` — all-zero placeholder, 16 B ("the node is present but carries no usable range") | report:`round19…txt:46`, `:624`, `:636-637` | L2 | B | PROVEN (L2 only) |
| A-06 | L2 placeholder ≠ L3 live node | live `reg` is 48 B, static placeholder is 16 B — the two cannot be the same property value | report:`round2-adb/devicetree_base_redacted.txt:68` vs `round19…txt:624` | L2 vs L3 | B | PROVEN |
| A-07 | Cause of the 16 B → 48 B change | **not established.** Candidate explanations (ABL `AddMemMap()` rewrite per ROUND42 §4; a different DTB source than the extracted boot-image DTB; post-handoff tree mutation) are all `D` and must not be selected | stagea:`kernel-baseline/round42/hos43-memory-handoff-sm8250-abl-fdt-prerequisite.md:94-101` (mechanism *exists* in a same-SoC-class reference), `:105-115` | — | D | MISSING |
| A-08 | `linux,usable-memory` anywhere in the stock base DTB | 0 occurrences | report:`round19…txt:681` | L2 | B | PROVEN (absence, L2) |

**Structural observations on the live root (grade B, no values):**

- `/memory` exists as a node in the live tree: `drwxr-xr-x 2 root root 0 … memory` — `report:round2-adb/devicetree_nodes_redacted.txt:57`.
- its properties are `ddr_device_type` (4 B), `device_type` (7 B), `name` (7 B), `reg` (48 B) — `report:round2-adb/devicetree_base_redacted.txt:63-68`.
- `ddr_device_type` is a vendor property; its value is unread. It is recorded here as *presence only*; no DDR type is asserted.
- root `/model` is 34 B in the live tree (`report:round2-adb/devicetree_nodes_redacted.txt:59`) while the offline template's `/model` string is `"Qualcomm Technologies, Inc. kona v2.1 SoC"` (`firmware-analysis/round7/dtb_property_inventory.csv`, first data row, column `value_redacted`), which is 42 B with terminator. Different lengths ⇒ the live `/model` is not the offline template's `/model`. Board identity value remains unread; this does **not** identify the board revision.

---

## 2. Firmware / secure / hypervisor carveouts

| ID | Fact | Value established | Source | Layer | Grade | Status |
|---|---|---|---|---|---|---|
| A-09 | Carveout node count, base tree | **37** direct children of `/reserved-memory`; 35 have an `/aliases` entry, `kerneldump` and `linux,cma` have none | report:`firmware-analysis/round24/round24-hos43-reserved-memory-and-consumer-map.txt:31-46` | L2 | B | PROVEN |
| A-10 | Carveout node count, live tree | `reserved-memory` directory has `st_nlink` **39** ⇒ **37 subdirectories** — independent live corroboration of A-09 | report:`round2-adb/devicetree_nodes_redacted.txt:69` | L3 | B | PROVEN |
| A-11 | Count reported elsewhere as 34 | `round64…md:24` and stagea:`kernel-baseline/round61/phase-e-board-dts-memory-power-gates.md:32` state 34. Reproduced cause: `firmware-analysis/round7/dtb_property_inventory.csv` yields **34 unique direct-child paths** under `/reserved-memory` across 279 rows — a column-scope artifact, already documented at `round24…txt:31-46`; the CSV row count above (279 rows, 34 unique direct-child paths) was re-derived this round with an independent parser | as cited | L2 | B | CONFLICT (explained, see §5) |
| A-12 | Per-node `reg` base/size | **not published.** ROUND24 states physical addresses are not published; no committed report carries a base or size for any of the 37 nodes | report:`round24…txt:16`; stagea:`round61…md:12` ("Physical addresses are not published") | L2 | — | MISSING |
| A-13 | Per-node attributes (`no-map`, `reusable`, `alloc-ranges`, `shared-dma-pool`, resize strings) | published per node, e.g. `#31 kerneldump` zero-reg placeholder + resize string; `#35 cnss_wlan_region` reusable,alloc-ranges; `#36 linux,cma` reusable,linux,cma-default; `#37 mailbox_region` no-map,alloc-ranges | report:`round24…txt:55`, `:89-104` | L2 | B | PROVEN |
| A-14 | Stock DTBOs touching carveouts | none — 9 entries, 0 `/reserved-memory` nodes, 0 `memory-region` properties, 0 `device_type="memory"` | report:`round24…txt:44-46`, `:211-212`; report:`round19…txt:51-52`, `:679-690` | L2 | B | PROVEN (absence) |
| A-15 | HOS vs ACK sm8250 fixed carveout intervals | ACK `sm8250.dtsi` has 18 immediate children, all with a fixed `reg` and `no-map`; **17** match a HOS fixed interval exactly; **1** is ACK_ONLY (`cdsp_secure_heap`, HOS has the same node name with **no** fixed `reg`); **7** HOS fixed nodes are HOS_ONLY | report:`firmware-analysis/round26/round26-sm8250-vs-hos43-reserved-memory-interval-audit.txt:44-45`, `:84-91`, `:96-133`, `:184-192` | L2 vs C | B (interval comparison only; bases still unpublished) | PROVEN (comparison), PARTIAL (values) |
| A-16 | Carveout ranges in the final FDT | unread — `reserved-memory` contents of the live tree were never dumped | report:`round2-adb/devicetree_nodes_redacted.txt:69` (directory only) | L3 | — | MISSING |

---

## 3. `memory-region` consumers

| ID | Fact | Value established | Source | Layer | Grade | Status |
|---|---|---|---|---|---|---|
| A-17 | Consumer reference count, base tree | 45 `memory-region` hits, of which **31** resolve to a true reserved region | report:`round24…txt:147` | L2 | B | PROVEN |
| A-18 | Named consumer → region edges | e.g. `cnss_pci` → `cnss_wlan_region` (#35); `qcom,msm-audio-apr/voice-mhi-audio` → `mailbox_region` (#37); `spf_core_platform/voice-mhi-audio-ar…` → `mailbox_region` (#37) | report:`round24…txt:185-189` | L2 | B | PROVEN |
| A-19 | Regions with no consumer property | `cont_splash_region`, `disp_rdump_region`, `bootfail_mem`, `kerneldump`, `rainbow_mem`, `linux,cma` — absence of a consumer is explicitly **not** evidence of being unused | report:`round24…txt:206-210` | L2 | B | PROVEN |
| A-20 | Consumer edges in the final FDT | unread | — | L3 | — | MISSING |

---

## 4. EFI memory map and kernel entry classification

| ID | Fact | Value established | Source | Layer | Grade | Status |
|---|---|---|---|---|---|---|
| A-21 | EFI memory descriptors for this device | **none exist in the corpus.** No EFI map capture of any kind | report:`round64…md:31` (Path B: no `linux,uefi-system-table` capture, no UEFI mmap descriptors) | L3 | — | MISSING |
| A-22 | `/chosen` contents in the stock base DTB | `bootargs = "rcupdate.rcu_expedited=1 rcu_nocbs=0-7 kpti=off"` only; **no** `linux,uefi-system-table`, **no** `linux,uefi-mmap-*` | report:`round19…txt:47-49`, `:627-629` | L2 | B | PROVEN |
| A-23 | `/chosen` contents in the live tree | exactly 5 entries: `bootargs` (1507 B), `kaslr-seed` (8 B), `linux,initrd-end` (8 B), `linux,initrd-start` (8 B), `name` (7 B). **No `linux,uefi-*` entry of any kind** | report:`round2-adb/devicetree_nodes_redacted.txt:113-119` | L3 | B | PROVEN (live absence) |
| A-24 | What A-23 implies for Path B | an EFI-stub entry writes `linux,uefi-system-table` + `linux,uefi-mmap-start/size/desc-size/desc-ver` into `/chosen` (`stagea:round43…md:65-72`). Their live absence is negative evidence **against** an EFI-stub handoff — but it is a directory listing of `/proc/device-tree`, so it is corroborating (B), not a byte-level dump of the handed-off blob | stagea:`kernel-baseline/round43/ack-6.18.33-fdt-memory-scan-classic-vs-efi-handoff.md:65-72` | L3 | B | PARTIAL |
| A-25 | Kernel entry classification (classic ARM64 Image vs Linux EFI stub) | **UNKNOWN.** ROUND43: "the actual Huawei kernel entry path has not been directly inspected"; ROUND20: layer 3 (`efi_stub_entry` reached?) and layer 4 (`/chosen` carries complete `linux,uefi-*`) are both UNKNOWN | stagea:`round43…md:109`; report:`firmware-analysis/round20/round20_efi_stub_memory_handoff_and_boot_payload_compatibility.txt:433`, `:439-441` | — | — | MISSING |
| A-26 | Consequence for the classic route | with an all-zero `/memory` and no EFI, `arm64_memblock_init()` performs no `memblock_add`; memblock stays empty. Nothing in the stock base DTB can populate RAM | report:`round20…txt:502-512` | C | C | PROVEN (kernel semantics) |
| A-27 | Consequence for the EFI route | `efi_init()` runs before `arm64_memblock_init()` and `memblock_remove(0, PHYS_ADDR_MAX)` discards DT-derived memblocks — but only if the stub was actually entered | report:`round20…txt:516-560` | C | C | PROVEN (kernel semantics) |

A-26/A-27 are kernel-source facts, not device facts. They define *which* handoff the device must be using; they do not say which one it uses.

---

## 5. ABL artifact, DTB/DTBO selection, boot chain

| ID | Fact | Value established | Source | Layer | Grade | Status |
|---|---|---|---|---|---|---|
| A-28 | `/sys/firmware/fdt` exists on the live device | **800316 B**, mode `-r--------`, owner root — not readable by the shell user | report:`round2-adb/devicetree_nodes_redacted.txt:3`; `report:round2-adb/live_dtb_status.txt:1-3` | L3 | B | PROVEN (existence + size) |
| A-29 | Attempted capture of that blob | `adb: error: failed to stat remote object '/sys/firmware/fdt': Permission denied` (captured 2026-11-23T22:52:24+08:00) | report:`round2-adb/live_dtb_status.txt:1-3` | L3 | B | PROVEN (failure) |
| A-30 | Any other post-ABL capture in the corpus | **none.** ROUND64 states no other authorized local artifact is a post-ABL capture | report:`round64…md:10`, `:20` | L3 | B | PROVEN (absence) |
| A-31 | ABL partition on the device | `abl -> /dev/block/sde6` present in the live by-name table (captured 2026-11-23T01:20) | report:`round2-adb/partition_names_redacted.txt:5` | L3 | B | PROVEN (existence) |
| A-32 | ABL binary bytes in the corpus | **none.** The offline HOS4.3 payload has 43 entries including `xbl.img` (4 018 176 B) and `xbl_config.img` (4 325 376 B) but **no** `abl.img` / `abl.elf`; no local ABL copy exists | report:`round19…txt:122-126` | L1/L2 | B | MISSING |
| A-33 | A-31 vs A-32 are not a conflict | they are different inventories: A-31 is the **live `/dev/block/by-name`** table; A-32 is the **offline update-package payload**. The ABL artifact exists on the device and was never dumped | as cited | — | B | PROVEN |
| A-34 | Other relevant live partition symlinks | `boot -> /dev/block/sde9`, `dtbo -> /dev/block/sde13`, `xbl -> /dev/block/sdb1`, `xbl_config -> /dev/block/sdb2` | report:`round2-adb/partition_names_redacted.txt:9`, `:21`, `:87-88` | L3 | B | PROVEN |
| A-35 | Number and identity of DTBO entries in the image | 9 entries (`dtbo_entry_0..8`), Android DTBO table with AVB footer, `dtbo.img` = 25 165 824 B; board-ids 8200/8296/8206/8208/8202/8238/8302/8240/8298; nine hardware variants VA..VI distinguished by `board-id`, `board_name`, `hardware_version` | report:`round19…txt:108`, `:54-56`; `firmware-analysis/round7/dby_w09_hw_matrix.txt:9` | L2 | B | PROVEN |
| A-36 | Which DTBO entry the ABL actually selected on this unit | **not established.** No ABL log, no post-composition tree. The live `qcom,board-id` is 8 B on disk but its value was unread | report:`round2-adb/devicetree_nodes_redacted.txt:66` (size only); `round2-adb/devicetree_base_redacted.txt:55-62` (read denied) | L3 | — | MISSING |
| A-37 | Boot-image handoff parameters | kernel 22 264 379 B @ `0x00008000`; ramdisk 519 986 B @ `0x02000000`; tags `0x00000100` (low 16 bits only, recorded as-is); `dtb address 0x0000000001F00000`; header v2; no `recovery_dtbo` in `boot.img` | report:`round19…txt:147-156`, `:154` | L2 | B | PROVEN |
| A-38 | ABL memory-node prerequisite in a same-SoC-class reference | FreeABL SM8250 `UpdateDeviceTree()` calls `FdtPathOffset(fdt,"/memory")` and returns `EFI_NOT_FOUND` if it fails; it does **not** create a missing `/memory`. `AddMemMap()` rewrites the **existing** `/memory/reg` from `EFI_RAMPARTITION_PROTOCOL`; `REMOVE_CARVEOUT_REGION` is optional and only consumes already-`no-map` regions | stagea:`round42…md:44-48`, `:94-101`, `:105-115` | C (public reference) | C | PROVEN (reference only) |
| A-39 | Does A-38 apply to Huawei HOS4.3? | **unknown.** "not evidence that Huawei HOS4.3 uses the identical source revision, build flags, or DTB selection policy" | stagea:`round42…md:60`; `round61…md:22` | — | D | MISSING |

---

## 6. Summary

| Status | IDs |
|---|---|
| PROVEN | A-05 (L2 only), A-06, A-08, A-09, A-10, A-13, A-14, A-15 (comparison), A-17, A-18, A-19, A-22, A-23, A-26, A-27, A-28, A-29, A-30, A-31, A-33, A-34, A-35, A-37, A-38 (C) |
| PARTIAL | A-01, A-02, A-15 (values), A-24 |
| MISSING | A-03, A-04, A-07, A-12, A-16, A-20, A-21, A-25, A-32, A-36, A-39 |
| CONFLICT | A-11 (resolved: counting scope, not hardware) |

**Direct evidence for the ABL→Linux memory handoff does not exist in the corpus.** The only artifact that could supply it — the 800316-byte `/sys/firmware/fdt` blob, or equivalently the live `/proc/device-tree/{memory,reserved-memory,chosen}` property values — was never successfully read (A-29). Every populated memory value in this matrix would have to come from L3, and L3 is empty except for node names, property names and byte lengths.

Therefore: **a final memory-safety review cannot be completed from the current corpus**, and Phase E workstream A remains **`BLOCKED — direct evidence absent`**.
