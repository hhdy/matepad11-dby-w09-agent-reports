# ROUND154 — WorkBuddy Window A: minimal RAM patch + DTBO / boot-v2 package gate

**Executor:** WorkBuddy Window A (1号 Agent). Window B (2号 Agent) is a separate chat task context; no Window B workspace or private log was used.

**Mode:** local source edit in a new reversible branch/worktree + scratch DTB builds + offline static/package tests. **No full kernel/Image build. No ADB, device access, partition read/write, flash, reboot, fastboot, recovery or candidate boot.**

**Overall verdict:** source patch and DTB build **PASS**; stock-overlay compatibility **FAIL (cannot apply)**; boot-v2 packaging contract **PARTIAL / selector UNKNOWN**; pre-boot safety checklist **NOT AUTHORIZED**. No boot image was created.

---

## 1. Verdict summary

| Task | Result | Hard number | Blocker |
|---|---|---|---|
| A — minimal RAM-only DTS correction | **PASS** | 1 file changed, +32/−15; new source tree `c56d93eafa35057d65176db6594d67d5144868a0` | — |
| B — scratch DTB build + byte-level validation | **PASS** | 108 680 B / sha256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60`; exactly 1 tree difference from frozen candidate DTB | — |
| C — stock Entry 2 / Entry 8 against candidate | **FAIL — cannot apply** | accepted base: 0/166 external fixups, 0/144 fragment targets; `-@` scratch base: 10/166, 57/144; `fdtoverlay` `FDT_ERR_BADOFFSET` → `FDT_ERR_NOTFOUND` | 156 absent labels; 87 absent fragment targets (Entry 2) |
| D — boot-v2 / DTB container contract | **PARTIAL** | header v2, `dtb_size=1 664 243`, `dtb_addr=0x1f00000`, 3 FDTs + 173 B tail | bootloader DTB selector / DTBO entry selector not evidenced (no ABL artifact) |
| E — pre-boot safety/recovery checklist | **NOT AUTHORIZED** | backup and tested stock-restore route absent | 2 of 4 items FAIL, 1 PARTIAL, 1 PASS |

---

## 2. Inputs, identity and workspace restrictions

### 2.1 Source identity

| Item | Value |
|---|---|
| Pinned ACK | `android17-6.18.33_r00`, commit `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9`, root tree `790a68ae6d4f4ac51ab2d88977b6fd5c031473b7` |
| Frozen candidate (23 patches) | `afe9517f8062b96bfeb5b4dd5714942861e6a44b` — reproduced independently in this round |
| New local source branch | `r154-minram`, base commit `0c5c84b5c89d32068af4ba0bd4a3032090cafbd9`, patch commit `491d0cbffb4d16e2840c1788674e6a05b26e88a2` |
| Source workspace (new, this round) | `/home/kerneldev/work/matepad11/r154-windowA/{base,out-dtb,out-dtb-at,scratch-at,evidence,logs}` |
| Source provenance | New `git init` + `fetch --depth=1 file://…/round140-agent2/tree HEAD`, shallow history disclosed; source repo read-only; 23 patches `01.patch`…`23.patch` sha256-verified against `identity.json` (23/23 MATCH, 23/23 `git apply --index` rc=0) |

No ROUND140/ROUND151 artifact was overwritten. No raw firmware or private log is embedded in this report.

### 2.2 Offline firmware artifacts (previously extracted, hashes recomputed)

| Artifact | Bytes | SHA-256 | Role |
|---|---:|---|---|
| `dtbo.img` | 25 165 824 | `51a5d7b81bc149765c1b4038e9aba5917392cd7370e029ea9f1b2933a8970c0c` | stock DTBO container, 9 entries; **not modified** |
| `entry2.dtbo` | 329 240 | `0633a6fbeebbad45c0f5572faf222c779e1cd51d253a6ef8282592a730ba3c8b` | live-selected entry (`dtbo_idx=2`, board-id `0x200e`) |
| `entry8.dtbo` | 329 352 | `a7946352a86ab6e47b5ee79d84e5d6c4cf4e548c96b0221cec909f32ebd9d21d` | non-live entry (board-id `0x206a`) |
| `boot.img` | 100 663 296 | `027f88fd6f318523925ca27a4d681d17a9bbca904b0c471ccc05e651d3da19b8` | stock boot v2 with 3 appended FDTs |

---

## 3. Task A — minimal RAM-only DTS correction

### 3.1 Where the node actually lives

The board file `arch/arm64/boot/dts/qcom/huawei-dby-w09.dts` has **no** `/memory` node. The single node is inherited from `arch/arm64/boot/dts/qcom/sm8250.dtsi:683-687`:

```dts
memory@80000000 {
        device_type = "memory";
        /* We expect the bootloader to fill in the size */
        reg = <0x0 0x80000000 0x0 0x0>;
};
```

`sm8250.dtsi:771-866` holds exactly **18** `/reserved-memory` children, including `cdsp_secure_heap: memory@8bf00000` at `:862`. Those files/properties were not touched.

**Implementation choice:** override the *same* node in the board root (`/ { memory@80000000 { reg = …; }; };`). DTS merges a same-name child under the same parent, so this replaces the inherited `reg` and keeps one `device_type = "memory"` node. Editing the shared `sm8250.dtsi` would change every other board and is deliberately avoided. Task B proves the compiled result has exactly one memory node.

### 3.2 Exact patch

```diff
+	memory@80000000 {
+		reg = <0x0 0x80000000 0x0 0x39900000>,
+		      <0x0 0xc0000000 0x0 0xc0000000>,
+		      <0x2 0x00000000 0x2 0x00000000>;
+	};
```

Windows: `0x80000000 + 0x39900000 = 0xB9900000` (921 MiB), `0xC0000000 + 0xC0000000 = 0x1_8000_0000` (3072 MiB), `0x2_0000_0000 + 0x2_0000_0000 = 0x4_0000_0000` (8192 MiB); total 12 185 MiB. No arithmetic gap was inserted: the 921 MiB window ends at `0xB9900000` and the next begins at `0xC0000000`, matching ROUND153's live FDT exactly (the 7 MiB spacing is a genuine HOS carveout gap, not a rounded fill).

### 3.3 Stale comments corrected (4 sites)

| File:line (before) | Old claim | New claim |
|---|---|---|
| `huawei-dby-w09.dts:13-16` | entry 8 `0x206a` selected; ABL pairing asserted | captured boot used `dtbo_idx=2` / Entry 2 / `0x200e`; selecting mechanism **UNKNOWN**; mutating component **UNKNOWN**; neither stock entry assumed compatible |
| `huawei-dby-w09.dts:35-36` | DTBO "selected by board-id 0x206a and fills /rootparam for Huawei ABL" | board-id `<0 0>` kept; `0x206a` claim withdrawn; selection mechanism UNKNOWN |
| `huawei-dby-w09.dts:311-316` | "final ABL-provided RAM tuple … remain UNKNOWN" | same node overridden; final tuple now explicit; 18 reserved-memory entries + 70 MiB `cdsp_secure_heap` untouched |
| `huawei-dby-w09.dts:328-332` | "ABL may populate … dynamically" | stock boot-chain mutation proven; attribution to ABL specifically **not proven** |

`qcom,board-id = <0 0>` and `qcom,msm-id = <QCOM_ID_SM8250 0x20001>` unchanged. No ARC/proxy/regulator property changed.

### 3.4 Artifact identity

| Item | Value |
|---|---|
| Changed files (exactly 1) | `arch/arm64/boot/dts/qcom/huawei-dby-w09.dts` |
| Diffstat | `1 file changed, 32 insertions(+), 15 deletions(-)`; `git diff --check` rc=0 |
| DTS blob before → after | `58293f7a62a50f8109886c92ce4b9cd14d7980e2` → `f9cc42ff621f6fe02ef22981eab9fbc9cb170aa8` |
| DTS file sha256 (after) | `df0fc83c2ab8a294aa78601f4deaa21bf992eb2999484e26e608a8eac6436521` |
| New source tree | `c56d93eafa35057d65176db6594d67d5144868a0` |
| Patch file | `r154-minimal-ram-only.patch` (`git format-patch -1 --stdout`), 4 919 B, sha256 `047a0af868fcdfceac0b0bb30360dbc9587530c0cedb38e4e6b940fa923afda1` |

---

## 4. Task B — scratch DTB build and validation

### 4.1 Exact build

```bash
CLANG=/home/kerneldev/work/matepad11/ack-6.18.33-a30/prebuilts/clang/host/linux-x86/clang-r584948c/bin
PATH=$CLANG:$PATH make -C <r154-windowA/base> ARCH=arm64 O=<r154-windowA/out-dtb> LLVM=1 \
      qcom/huawei-dby-w09.dtb
```

- Toolchain: Android clang r584948c, `clang version 22.0.1`; `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`; GNU Make 4.3; in-tree dtc built by kbuild.
- `.config` copied from ROUND140 `out-dtb/.config` (sha256 `efb663e9c792840e2cfbbc03e115996bb486aefe964b448c1717828c55bf042f`, already `olddefconfig`-processed), byte-identical to the product config used for the frozen candidate DTB.
- **Only** the DTB target was built; no `Image`, no modules, no full kernel build. `BUILD_RC=0`.
- Actual `cmd_dtc` line (from `.huawei-dby-w09.dtb.cmd`): `clang -E … -D__DTS__ … ; ./scripts/dtc/dtc -o … -b 0 … -Wno-simple_bus_reg -d …` — note **no `-@`** in the accepted configuration.

### 4.2 Byte-level proof

| Check | Result |
|---|---|
| New DTB | 108 680 B, sha256 `9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60` |
| Frozen candidate DTB (ROUND140) | 108 648 B, sha256 `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e` |
| Size delta | **+32 B**, exactly `48 − 16` for `reg` |
| Node / property counts | 905 nodes, 3 443 properties — identical to frozen DTB |
| Root cells | `#address-cells = <2>`, `#size-cells = <2>` |
| `device_type = "memory"` nodes | **exactly 1**, path `/memory@80000000` |
| `reg` | 48 B / 12 cells, byte-for-byte the three required tuples |
| `/reserved-memory` | 18 children, every path and every property byte-identical to frozen candidate; all 18 intervals lie inside window 1 (`0x80000000`–`0xB9900000`) |
| Full-node/property diff vs frozen DTB | **1 difference**: `/memory@80000000:reg`; 0 added/removed nodes, 0 other changed properties |

No previous output DTB was used as proof of the new source: the DTB above was rebuilt from source tree `c56d93ea…` in a newly created `O=` directory.

---

## 5. Task C — stock Entry 2 / Entry 8 compatibility against the candidate

### 5.1 Overlay structure actually observed

| Entry | Fragments | `__fixups__` properties | Fixup references | Unique external symbols | root `qcom,board-id` |
|---|---:|---:|---:|---:|---|
| Entry 2 (live) | **144** | 166 | 450 | 166 | `<0x200e 0x0>` |
| Entry 8 (non-live) | **145** | 166 | 451 | 166 | `<0x206a 0x0>` |

All fragments use `target = <0xffffffff>` and resolve through the overlay's `/__fixups__` node (key = symbol, value = `/fragment@N:target:0`). There is **no** `target-path` fragment in either entry. Values in `__fixups__` are **symbol names**, not paths — they must be resolved through the base DTB's `/__symbols__` table (the same correction made in ROUND153).

### 5.2 The kernel's real `-@` mechanism

- `scripts/Makefile.lib:19`: `target-stem = $(basename $(patsubst $(obj)/%,%,$@))` → for this target the stem is `huawei-dby-w09` (**without** `.dtb`).
- `scripts/Makefile.dtbs:112`: `DTC_FLAGS += $(DTC_FLAGS_$(target-stem))`.
- `scripts/Makefile.dtbs:11,115`: `base-dtb-y` is derived from `multi-dtb-y`, and a base DTB listed there also gets `-@`.
- `CONFIG_OF_OVERLAY` is **not set** in the product `.config` — DTBO application is a boot-chain concern, not a Linux kernel overlay-fs concern.

Scratch experiment (`/home/kerneldev/work/matepad11/r154-windowA/scratch-at`, detached worktree of patch commit `491d0cb`, **accepted source patch untouched**): appended one line to `arch/arm64/boot/dts/qcom/Makefile`:

```make
DTC_FLAGS_huawei-dby-w09 := -@
```

Resulting `-@` DTB: 145 881 B, sha256 `235663547667c06871c1f2b7a2977395905e0f49ed4b6b543602477316e35ef7`, `/__symbols__` 514 entries, `rootparam = "/rootparam"`. `cmd_dtc` now contains `-@`.

### 5.3 Compatibility results

| Base | Entry 2 symbols resolved | Entry 2 fragment targets resolved | `fdtoverlay` result |
|---|---:|---:|---|
| **B1** = accepted DTB, no `-@` (`9d0d7600…`) | 0/166 | 0/144 | rc=1, `FDT_ERR_BADOFFSET`; stderr: `base blob does not have a '/__symbols__' node, make sure you have compiled the base blob with '-@' option` |
| **B2** = scratch `-@` DTB (`23566354…`) | **10/166** (156 absent labels) | **57/144** (87 targets absent) | rc=1, `FDT_ERR_NOTFOUND` |

For Entry 8 the numbers are 0/166 and 0/145 (B1), then **10/166** and **57/145** (B2), with the same two exact apply errors. Entry 8 therefore gives no compatibility advantage.

Additional discriminators:

- `label-present-but-target-path-absent = 0` in both bases: every failure is an **absent label in the base symbol table**, not a dangling path stored in the base.
- `rootparam` **does** resolve in B2 (`/rootparam` exists), yet the full overlay still fails — confirming that exporting `rootparam` alone is insufficient.
- The first unresolved external fixup in fragment order on B2 is `/fragment@0/__overlay__/qcom,pm8150@0/clock-controller@5b00:clocks:0` → symbol `clock_rpmh` (absent from the candidate's 514 symbols). The first absent fragment target is `fragment@1` → `thermal_zones`.
- Full per-symbol and per-fragment status for all 166 symbols × 4 combinations and all 144/145 fragments is in `evidence/C-overlay-full-detail.txt` (1 254 lines).
- Stock DTBO bytes were never modified; entry hashes in §2.2 still match.

### 5.4 Decision

**Stock Entry 2 cannot apply to the candidate DTB, and a minimal custom overlay is required** — but it must be authored against the candidate's own 514 symbols / 905 nodes; it cannot be derived by pruning stock Entry 2 without supplying missing vendor nodes. Separately, **which component selects `dtbo_idx=2` remains UNKNOWN**. No target-path or selector contract was invented.

---

## 6. Task D — boot-v2 / DTB container packaging contract

### 6.1 Stock header (independently re-parsed this round)

| Field | Value |
|---|---|
| Magic / header version | `ANDROID!` / **v2** |
| `header_size` / `page_size` | `1660` / `4096` (offsets `1644` / `36-39`) |
| `kernel_size` / `ramdisk_size` / `second_size` | 22 264 379 / 519 986 / 0 |
| `recovery_dtbo_size` / offset | 0 / 0 |
| `dtb_size` / `dtb_addr` | **1 664 243** / **0x1f00000** (offsets `1648` / `1652`, little-endian) |
| DTB region start | `0x15bc000` = `page + pages(kernel) + pages(ramdisk) + pages(second) + pages(recovery_dtbo)` |

### 6.2 DTB slot contents

| # | File offset | Size | `/model` | `qcom,msm-id` | sha256 (first 16) |
|---|---:|---:|---|---|---|
| 0 | `0x15bc000` | 556 524 | kona **v2.1** | `<0x164 0x20001>` | `df2730f3d2e9bdab` |
| 1 | `0x1643dec` | 556 520 | kona **v2** | `<0x164 0x20000>` | `f3dcba83e73f4d86` |
| 2 | `0x16cbbd4` | 551 026 | kona **v1** | `<0x164 0x10000>` | `6cda673986bf814c` |

Zero gaps; 173 trailing bytes complete the declared `dtb_size`. All three carry `qcom,board-id = <0 0>`, 4-cell all-zero `/memory.reg`, and 37 `/reserved-memory` children. (A naive magic scan also finds a 173-byte FDT-looking tail; the validated count is **three** complete FDTs, as in ROUND153.)

### 6.3 msm-id selection and what the candidate can satisfy

- The candidate declares `qcom,msm-id = <0x164 0x20001>` — **identical to stock slot 0 (kona v2.1)** and to the live FDT's msm-id.
- Therefore one candidate FDT *can* satisfy a first-match `qcom,msm-id = 0x164/0x20001` selector by value.
- **But the selector itself is not evidenced.** No ABL/XBL image exists in this workspace; the ACK tree has no boot-packaging script, no `mkbootimg`, and no non-DTS code that reads `qcom,msm-id` (only `include/dt-bindings/arm/qcom,ids.h:12` documents the older convention). Whether the loader scans all three FDTs, uses a fixed slot, or requires a specific concatenation order is **UNKNOWN**.
- All nine DTBO table `id`/`rev` values are 0; overlays carry no `qcom,msm-id`; base board-id is `<0 0>`; live selected entry is `0x200e`. A board-id comparison against the base DTB cannot produce the observed selection. **The single missing evidence is this build's ABL (or an equivalent bootloader trace).**

### 6.4 DTBO → boot.img DTB relationship

ROUND153 established that the live tree = stock base DTB #0 + Entry 2 fragments + non-DTBO mutations (bootargs/initrd/kaslr, 21 fstab `status` rewrites, `/memory` 4→12 cells plus `ddr_device_type`); no fragment touches `/`, `/chosen`, `/memory` or `/reserved-memory`. So the DTBO **is** applied to the DTB that came from `boot.img`, but the applying component and entry-selection metadata are UNKNOWN. A candidate package cannot rely on the DTBO to supply `/memory`, `/chosen` or carveouts.

### 6.5 Expected candidate boot.img shape

No boot-image repack script exists in the source workspace and no candidate boot image was created. The conservative shape that preserves stock selection inputs is:

| Variant | FDTs in slot | `dtb_size` (with 173 B tail) | `dtb_addr` |
|---|---|---:|---|
| Accepted DTB (no `-@`), replacing slot 0 only | 3 (candidate + stock v2 + stock v1, stock order kept) | **1 216 399** | `0x1f00000` (unchanged) |
| `-@` scratch DTB replacing slot 0 | 3 | 1 253 600 | `0x1f00000` |
| Single candidate FDT | 1 | 108 680 or 108 853 (with tail) | unknown policy |

A one-FDT slot is **not** justified by available evidence. Note that replacing a 556 524-B vendor template with a 108 680-B minimal candidate removes ~4/5 of the nodes the stock overlay expects (§5), so packaging cannot substitute for overlay compatibility work.

### 6.6 Roles, provenance and immutability

- No `vendor_boot` / `init_boot` partition exists in the captured `by-name` farm or in the 15-image payload set (ROUND149 §9, ROUND64 §1). Roles are: `boot` (kernel+ramdisk+DTB), separate `ramdisk`, `dtbo`, and `vbmeta*`; exact targets on this unit are `boot=sde9`, `dtbo=sde13`, `vbmeta=sde12` (A-only, no slot suffix).
- Root `vbmeta` chain descriptors cover `boot`, `ramdisk`, `dtbo` (SHA256_RSA2048). Any repack invalidates the `boot` hash descriptor unless vbmeta is regenerated; no signing/verification route was tested. **Stock embedded ramdisk (519 986 B) and the separate `ramdisk.img` (payload 2 097 152 B / raw 1 325 056 B) must remain byte-identical unless a signed repack is explicitly authorized.**
- Hashes of all 15 payload images are recorded in ROUND64 §2, cross-checked against AVB footer original-image-sizes; no image was modified.

---

## 7. Task E — pre-boot security/recovery checklist (existing evidence only)

| # | Item | Status | Evidence / limit |
|---|---|---|---|
| 1 | AVB/vbmeta chain and footer anomaly understood | **PARTIAL** | AOSP `avbtool 1.4.0` `info_image` (ROUND64): 14/15 images carry footers; root vbmeta chains `boot`, `ramdisk`, `dtbo`; `vbmeta_cust.img` footer points to a 1 344-B `Algorithm: NONE` blob at offset 10 375 168, outside the 1 MiB file — documented, not explained away. No key/signature verification, no acceptance claim. |
| 2 | `boot` / `vendor_boot` / `init_boot` / DTBO roles and exact install target known | **PASS (roles + targets)** | `boot=sde9`, `dtbo=sde13`, `vbmeta=sde12`; A-only; no `vendor_boot`/`init_boot` in by-name or payloads (ROUND149, ROUND64). Loader-side selection policy still UNKNOWN (§6.3). |
| 3 | Full required partition backup exists and hashes verified | **FAIL** | Only 15 boot-family payload images are present; 86 `by-name` partitions visible, sizes DENIED; ROUND149 U-7 explicitly defers a backup plan. No full backup, no per-partition hash set. |
| 4 | Tested route to exact stock state available | **FAIL** | No flash/restore rehearsal, no recovered stock-state hash comparison, no authorized recovery path in the corpus. `recovery.img == erecovery.img` byte-identically, but that is metadata, not a tested restore. |

**First boot remains NOT AUTHORIZED.** Rows 1, 3 and 4 independently block it; PASS on row 2 does not close any gate.

---

## 8. Pitfalls and corrections in this round

1. **Wrong make target on first build.** `make … arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb` fails with `No rule to make target 'arch/arm64/boot/dts/arch/arm64/boot/dts/qcom/…'`; the correct target relative to `arch/arm64/boot/dts` is `qcom/huawei-dby-w09.dtb`. The first failed log was overwritten by the clean rebuild; `B1-dtb-build.log` is the successful rebuild, and the failure is recorded here verbatim rather than hidden.
2. **`-@` variable name.** `DTC_FLAGS_huawei-dby-w09.dtb := -@` silently produces a byte-identical DTB with no `-@`; `target-stem` drops the extension (`scripts/Makefile.lib:19`). Correct variable: `DTC_FLAGS_huawei-dby-w09`.
3. **Fixup parsing direction.** Fixup entries are keyed by symbol name with values `path:prop:offset`; deriving symbols from the trailing colon yields offsets (`0`, `4`, …). Correct accounting is 166 symbols, not 23.
4. **Big-endian vs little-endian header.** Android boot v2 header fields here are little-endian with vendor offsets (`header_size@1644`, `dtb_size@1648`, `dtb_addr@1652`); a big-endian read produces nonsense (`dtb_size = 4 083 423 488`).
5. **False fourth FDT.** The 173-B tail contains an FDT-shaped prefix; validate `version`, `last_comp` and a plausible `totalsize` before counting DTBs.
6. **`fdtoverlay` message is diagnostic, not a full inventory.** `FDT_ERR_NOTFOUND` reports only the first failure; the complete unresolved-symbol/fragment list is produced statically (§5.3).

---

## 9. Blockers and exact next action

1. **No ABL/XBL artifact for this build** — the only evidence that can turn "some boot-chain layer" into a code path and explain `dtbo_idx=2` selection. Required before any packaging claim.
2. **No tested stock restore and no full partition backup** — hard stop for any candidate boot.
3. **Overlay contract absent** — a minimal custom DTBO must be authored against the candidate's symbol table; this round does not invent target paths or a selector convention.
4. **Packaging policy absent** — one-FDT vs three-FDT slot and whether the loader requires specific `dtb_addr`/order need bootloader evidence (same blocker as 1).

**Next action (no boot):** obtain the ABL image for this build, then re-run §6 selector analysis; separately author a minimal candidate-scoped overlay and re-run the `fdtoverlay` test from §5 before any boot-image repack is discussed.

---

## 10. Evidence index (local, unsanitized paths; no raw firmware uploaded)

| File | Contents |
|---|---|
| `r154/evidence/A0-setup-and-apply.log` | source identity, 23/23 patch sha256, apply rc, tree hashes |
| `r154/evidence/taskA-diff.txt`, `taskA-identity.txt` | exact patch diff, `git diff --check`, commit/tree/blob/patch hashes |
| `r154/evidence/r154-minimal-ram-only.patch` | the reversible patch (4 919 B) |
| `r154/evidence/B1-dtb-build.log` | exact DTB build command, toolchain, full log |
| `r154/evidence/B2-dtb-validation.txt` | DTB structural validation and full-tree diff |
| `r154/evidence/C1-scratch-at-build.log` | `-@` scratch build and actual `cmd_dtc` |
| `r154/evidence/C-overlay-compatibility.txt` | 4 base/entry compatibility results and exact apply stderr |
| `r154/evidence/C-overlay-full-detail.txt` | every external symbol and every fragment target × 4 combinations |
| `r154/evidence/D1-boot-header-parse.txt` | boot v2 header, DTB slot offsets/sizes/msm-ids/hashes |
| `r154/evidence/SHA256SUMS.txt` | hashes of all evidence files above |

Local scripts: `r154/{setup_base.sh,taskA_edit.py,taskA_diff.sh,taskA_commit.sh,taskB_build.sh,validate_dtb.py,taskC_scratch_build.sh,taskC_analyze.py,parse_boot.py,collect_evidence.sh}`.

**Stop.** No full kernel build, no ADB/device operation, no partition access, no flash/reboot/fastboot/recovery, no candidate boot image, and no further round was started.
