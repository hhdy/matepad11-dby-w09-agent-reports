# ROUND147 — 2号 Agent read-only inventory: ARC providers in the existing ROUND140 candidate DTB

**Executor:** 2号 Agent (the local agent that produced the ROUND140 candidate build). Not 2号 AI, not WorkBuddy Agent.
**Scope:** inventory of `qcom,rpmh-arc-regulator` groups, their children / `*-parent-supply` / proxy relations, and the PM8150 / PM8150L per-PMIC provider groups, in the **already-built** ROUND140 candidate DTB.
**Nothing was rebuilt.** No source, DTS, patch, config, or binary was modified. No device was touched.

**Result in one line:** the candidate DTB contains **zero** `qcom,rpmh-arc-regulator` nodes, **zero** `mmcx.lvl` / `mx.lvl` / `cx.lvl` resource strings, and exactly **two** per-PMIC VRM provider groups (PM8150 = 5 rails, PM8150L = 1 rail) with **seven** `-supply` consumer edges, all of them on the UFS host and UFS PHY. The absence is **documented as deliberate** in the candidate's own board DTS (`huawei-dby-w09.dts:86-161`), not an artifact of the build.

---

## 0. Evidence labelling used in this report

| Label | Meaning |
|---|---|
| **A** | Direct byte-level observation in the candidate DTB (or a byte-level property of a file whose hash is recorded here) |
| **B** | Corroborated by an independent local artifact (pinned-tree source, driver source, ROUND140 log) — still local, still read-only |
| **C** | Software-only / documentation-level statement (report text, comments) |
| **D** | Inference — **not used** for any power or runtime claim in this report |

An observation is never promoted to "the device is powered" or "the runtime vote is X". Those remain outside this round.

---

## 1. Artifact identity and provenance

| Field | Value | Label |
|---|---|---|
| Path | `/home/kerneldev/work/matepad11/round140-agent2/out-dtb/arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb` | A |
| Size | `108648` bytes — equals the taskbook's expected size | A |
| SHA256 | `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e` — equals the taskbook and START_PROMPT value **exactly** | A |
| mtime | `2026-11-26 20:25:31.023677907 +0800` | A |
| Ambiguity | exactly **one** `*.dtb` exists anywhere under `out-dtb` — no candidate confusion | A |

Provenance to the ROUND140 build, read from the retained log (not reconstructed):

| Log line | Content |
|---|---|
| `logs/stage-b4-dtb-build-and-structure.log:56` | `DTC     arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb` |
| `:63-64` | `dtb_path=` / `dtb_realpath=` → the same absolute path inspected here |
| `:65` | `dtb_size=108648 expected_size=108648 match=YES` |
| `:66` | `dtb_sha256=cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e` |
| `:67-68` | `expected_sha256=cab82fe3901dbb40…` → `DTB_SHA_MATCH=NO` |
| `:86` | `dtc_used=…/out-dtb/scripts/dtc/dtc` (tree dtc `1.7.2-g52f07dcc`) |

Line `:66` is the value produced by the build at 20:25 and it is **identical** to the hash of the file on disk now. Lines `:67-68` are the pre-existing transcription defect already registered as **D-1** in the ROUND140 report (positions 11–12 `db`/`bd` transposed in the *recorded expected* value); it does **not** affect the artifact. No rebuild occurred between the build and this inspection (DTB mtime 20:25:31, inspection 21:38; no newer build output exists).

**Inspection tools:** host `/usr/bin/dtc` `1.7.0` (read-only `-I dtb -O dts` to `/tmp`), `fdtdump`, and a purpose-written FDT struct-block parser that reads the binary directly. The decompile emitted 32 pre-existing base-tree warnings (30 × `unique_unit_address`, 2 × `avoid_unnecessary_addr_size`) — recorded, not fixed, and unrelated to ARC.

**Parser validation (anti-false-negative control).** A negative result is only worth its instrumentation, so the parser was reconciled against two independent representations before its "zero" was accepted:

| Quantity | Value | Cross-check |
|---|---|---|
| nodes | `905` | text `{` count = 905, `};` count = 905 → **exact** |
| properties | `3443` | `3285` lines of the form `name = value;` **plus** `158` valueless boolean properties (`bias-disable` 32, `no-map` 18, `ranges` 10, `interrupt-controller` 9, …) → `3285 + 158 = 3443`, delta **0** |
| phandles | `239`, **no duplicates** | every `-supply` target resolved, `0` unresolved |

The 158-boolean term is exactly the reconciliation of the naive text count; the parser is therefore neither dropping nor inventing nodes.

---

## 2. Headline: `qcom,rpmh-arc-regulator` groups in the candidate = 0

| Check | Result | Label |
|---|---|---|
| Nodes with `compatible` containing `qcom,rpmh-arc-regulator` | **0** | A |
| Bookkeeping tables required by taskbook §4 (per-group path / `status` / `qcom,resource-name` / children / `*-parent-supply` / proxy) | **N/A — no group exists**, so the tables are empty by construction, not omitted | A |
| Nodes named `rpmh-regulator-*` (any suffix) | **0** | A |
| Nodes named `rpmh-regulator-mmcxlvl` / `-mxlvl` / `-cxlvl` | **0 / 0 / 0** | A |
| Occurrences of the byte string `mmcx.lvl` / `mx.lvl` / `cx.lvl` | **0 / 0 / 0** | A |
| Occurrences of the substring `mmcx` (any context) | **0** | A |
| Occurrences of the substring `arc` **and** `ARC` in the entire 108 648-byte blob | **0 / 0** | A |
| Nodes with `qcom,proxy-consumer-enable` | **0** | A |
| Nodes with `qcom,resource-name` (the ARC/VRM corner-identity property) | **0** | A |
| Property names containing `arc` | **0** (`cache-level`, `next-level-cache`, `opp-level`, `vcc-voltage-level` are the only `*level*` names) | A |

Three independent instruments agree on the zero (taskbook §2 / §6):

| Instrument | `rpmh-arc` | `mmcx` | `regulator-name` | `regulators-0` |
|---|---|---|---|---|
| FDT struct-block parser | 0 (0 nodes) | 0 | 6 | 1 |
| `dtc` decompiled text + `grep -c` | 0 | 0 | 6 | 1 |
| `fdtdump` output + `grep -c` | 0 | 0 | 6 | 1 |

Positive controls in the same run (`regulator-name` = 6, `regulators-0` = 1, `rpmhpd` = 1) confirm the searches were capable of finding hits.

**Statement of scope (deliberately narrow):** *the compiled candidate DTB declares no ARC provider group.* This says nothing by itself about whether a kernel would boot; §6 records the actual reason the nodes are absent.

---

## 3. PM8150 / PM8150L per-PMIC provider groups (taskbook §5)

Both live under `&apps_rsc`, i.e. `/soc@0/rsc@18200000`, which is the `qcom,rpmh-rsc` node — its only other children are `clock-controller`, `power-controller`, `bcm-voter`, `regulators-0`, `regulators-1`.

| Group | Full path | `compatible` | `qcom,pmic-id` | `status` | phandle | children |
|---|---|---|---|---|---|---|
| PM8150 | `/soc@0/rsc@18200000/regulators-0` | `qcom,pm8150-rpmh-regulators` | `"a"` | **absent** | **none** | 5 |
| PM8150L | `/soc@0/rsc@18200000/regulators-1` | `qcom,pm8150l-rpmh-regulators` | `"c"` | **absent** | **none** | 1 |

Authored at `huawei-dby-w09.dts:163` and `:231` respectively.

**Neither provider group carries a `phandle`.** That is structurally significant: nothing in this DTB can reference a *group* node, so no corner-vote consumer edge into the provider group exists at all. Only individual rails are referenced (§4).

Child rails — observations only (raw values converted mechanically, not by hand):

| `regulator-name` | child node | min µV | max µV | `regulator-initial-mode` | `regulator-allowed-modes` | `status` | DTS |
|---|---|---|---|---|---|---|---|
| `pm8150_s4` | `smps4` | 1 800 000 | 1 920 000 | *(absent)* | *(absent)* | absent | `:168-173` |
| `pm8150_l5` | `ldo5` | 880 000 | 880 000 | 3 = HPM | 1, 3 = LPM, HPM | absent | `:176-184` |
| `pm8150_l6` | `ldo6` | 1 200 000 | 1 200 000 | 1 = LPM | 1, 3 | absent | `:187-195` |
| `pm8150_l9` | `ldo9` | 1 200 000 | 1 200 000 | 3 = HPM | 1, 3 | absent | `:198-206` |
| `pm8150_l17` | `ldo17` | 2 496 000 | 3 008 000 | 1 = LPM | 1, 3 | absent | `:209-217` |
| `pm8150l_s8` | `smps8` | 1 200 000 | 1 400 000 | 0 = RET | 0, 2 = RET, AUTO | absent | `:235-242` |

Mode integers map to `RPMH_REGULATOR_MODE_RET/LPM/AUTO/HPM = 0/1/2/3` per `include/dt-bindings/regulator/qcom,rpmh-regulator.h:31-34` (**B**).

No rail carries `regulator-always-on`, `regulator-boot-on`, `qcom,init-enable`, `regulator-allow-set-load` on S4, or any `vin-*`/`vdd-s*-supply` property. **An absent `status` means the node is available by OF default convention — it is not evidence of a powered rail or of a runtime enable vote.**

---

## 4. Every `-supply` edge in the candidate (taskbook §4/§6, strict form)

Filtering by property type (names ending in `-supply`, which the regulator/PHY bindings define as phandle-typed) yields **7 edges, 0 unresolved**:

| Consumer | Property | Cells | Resolved provider |
|---|---|---|---|
| `/soc@0/ufshc@1d84000` | `vcc-supply` | `<0x5d>` | `…/regulators-0/ldo17` (`pm8150_l17`) |
| `/soc@0/ufshc@1d84000` | `vccq-supply` | `<0x5e>` | `…/regulators-0/ldo6` (`pm8150_l6`) |
| `/soc@0/ufshc@1d84000` | `qcom,vddp-ref-clk-supply` | `<0x5e>` | `…/regulators-0/ldo6` (`pm8150_l6`) |
| `/soc@0/ufshc@1d84000` | `vccq2-supply` | `<0x60>` | `…/regulators-0/smps4` (`pm8150_s4`) |
| `/soc@0/ufshc@1d84000` | `qcom,vccq-parent-supply` | `<0x5f>` | `…/regulators-1/smps8` (`pm8150l_s8`) |
| `/soc@0/phy@1d87000` | `vdda-phy-supply` | `<0x63>` | `…/regulators-0/ldo5` (`pm8150_l5`) |
| `/soc@0/phy@1d87000` | `vdda-pll-supply` | `<0x64>` | `…/regulators-0/ldo9` (`pm8150_l9`) |

- **`vin-supply` occurrences: 0.**
- **`*-parent-supply` occurrences: 1** — only `qcom,vccq-parent-supply` above. There is **no** provider-child ARC parent edge, because there is no ARC provider-child edge to begin with.
- Rail-side inbound count: `ldo6` 2, and `ldo17` / `smps4` / `ldo5` / `ldo9` / `smps8` 1 each. Every rail except `ldo6` has exactly one consumer; no rail is orphaned and none is multiply loaded by other subsystems.

> Measurement note, recorded so that a later round does not inherit an inflated table: a naive "which properties contain this phandle number" scan reports false positives, because clock specifier indices, interrupt numbers and `reg` cell values collide numerically with phandle values (e.g. `clocks = <0x30 0x63>`, `reg = <… 0x60>`, `qcom,vddp-ref-clk-max-microamp = <0x64>` where `0x64` is *100*, a current in µA, not phandle 0x64). Only `-supply`-typed names are counted above; the corrected strict result is 7, not the 20+ the naive scan printed.

### 4.1 How the UFS corner requirement is expressed instead of ARC

| Property on `/soc@0/ufshc@1d84000` | Value | Resolves to |
|---|---|---|
| `status` | `"okay"` | — |
| `power-domains` | `<0x34 0x06>, <0x30 0x04>` | `/soc@0/rsc@18200000/power-controller` (`qcom,sm8250-rpmhpd`) domain 6 = MMCX; `/soc@0/clock-controller@100000` (`qcom,gcc-sm8250`) domain 4 = UFS PHY GDSC |
| `operating-points-v2` | `<0x5c>` | its own `/soc@0/ufshc@1d84000/opp-table` |
| `opp-37500000` → `required-opps` | `<0x29>` | `…/power-controller/opp-table/opp3`, `opp-level = <0x40>` (64) |
| `opp-300000000` → `required-opps` | `<0x61>` | `…/power-controller/opp-table/opp6`, `opp-level = <0x100>` (256) |

So the corner relationship is carried by **rpmhpd GenPD performance levels via `required-opps`**, not by ARC regulator groups. Whether a GenPD corner is equivalent to the vendor's ARC child-supply graph is **NOT established here and is not claimed** — the board DTS itself declines that equivalence (`:114-121`, `:153-154`).

---

## 5. The two per-PMIC groups are VRM rails, not ARC providers

`regulators-0` / `regulators-1` are `qcom,pm8150*-rpmh-regulators` — the **VRM/XOB** provider family. The pinned ACK driver matches exactly this family and nothing else (**B**):

| Check | Result | Reference |
|---|---|---|
| `rpmh_regulator_match_table[]` entries | only `qcom,pmXXXX-rpmh-regulators` strings | `drivers/regulator/qcom-rpmh-regulator.c:1607-1631` (PM8005/PM8009/PM8009-1/PM8010/PM8150/PM8150L/…) |
| Regulator types modelled | `VRM` and `XOB` only | same file `:31-32`, `.regulator_type` fields `:625-896` |
| Literal `rpmh-arc` in the driver | **0** | `:0` hits in `qcom-rpmh-regulator.c` |
| Literal `rpmh-arc` anywhere under `drivers/regulator/` | **0** | whole-directory grep |

This independently reproduces ROUND146's statement ("the pinned ACK RPMh regulator driver has no `qcom,rpmh-arc-regulator` match") from my own tree, read-only (**B**). It is a statement about driver match, not about electrical behaviour.

---

## 6. Why the ARC nodes are absent — the candidate source says so itself

The candidate's own board DTS documents the omission, so the zero in §2 is a **deliberate modelling decision**, not a build accident. Quoted verbatim from `/home/kerneldev/work/matepad11/round140-agent2/tree/arch/arm64/boot/dts/qcom/huawei-dby-w09.dts` (comment block `:86-161`, immediately preceding `&apps_rsc {` at `:162`):

- `:108-112` — "ACK's upstream qcom-rpmh-regulator binding/driver handles PMIC VRM/XOB regulators, **not** the vendor `qcom,rpmh-arc-regulator` provider. SM8250's upstream SoC DTSI instead exposes rpmhpd performance levels/OPPs; the UFS OPP table uses `required-opps` against that provider. **Keep this board file on that upstream model and do not copy vendor ARC nodes/properties.**"
- `:149-151` — "ACK android17-6.18 qcom-rpmh-regulator only matches VRM/XOB, so these ARC child nodes **must remain disabled/absent** until an ARC-capable driver is deliberately ported and reviewed."
- `:139-141` — "Do not add vph_pwr=3.7 V, vdd-s\*-supply, fake fixed regulators or ARC properties as a substitute. Treat the missing physical input network as a power-tree validation gate before any boot test."
- `:153-154` — "The SoC rpmhpd/OPP provider remains a separate system performance-domain mechanism, **not a one-to-one substitute**."

Two mechanical confirmations that the omission is total, not partial (**A**/**B**):

| Cross-check | Result |
|---|---|
| `delete-node` / `delete-property` in the board DTS | **0 occurrences** — nothing was deleted at build time |
| `rpmh-arc` literal in the board DTS | 1 occurrence, and it is **inside a comment** (`:109`) |
| `mmcx` in the board DTS | 4 occurrences, **all inside comments** (`:94-97`) — none survive into the DTB, consistent with §2's `mmcx` = 0 |
| `sm8250.dtsi` rpmh-regulator / ARC nodes | **0** — the SoC dtsi contributes no provider group at all; the two groups exist only because the board file authored them |

Consequence for reading §2: the candidate does not "lose" ARC nodes during compilation; they were never authored. The vendor corner graph is replaced by the upstream `rpmhpd` + `required-opps` model (§4.1).

---

## 7. Comparison with ROUND139's HOS4.3 facts (taskbook §8)

ROUND139 (public report, read from a **pre-existing local copy** — no network fetch) records for the vendor FDT:

| ROUND139 statement | Line |
|---|---|
| 7 ARC groups — `mxlvl` (`mx.lvl`), `cxlvl` (`cx.lvl`), `mmcxlvl` (`mmcx.lvl`), `lmx.lvl`, `lcx.lvl`, `gfx.lvl`, `ebi.lvl` — all `compatible = "qcom,rpmh-arc-regulator"`, inside 47 `rpmh-regulator-*` provider groups / 105 nodes under that prefix | `:177` |
| 5 ARC provider-child `*-parent-supply` edges (CX ALL→MX ALL, CX AO→MX AO, MMCX ALL→MX MMCX-supply ALL, MMCX AO→MX AO, MX MMCX-supply→CX MMCX-supply) | `:151-155`, `:157` |
| 8 self-referential `proxy-supply` occurrences; `qcom,proxy-consumer-enable` on those plus two SoC nodes | `:161` |
| `qcom,rpmh-arc-regulator` count in ACK = 0/0 | `:200` |

Side-by-side with the candidate:

| Quantity | HOS4.3 vendor FDT (ROUND139) | ROUND140 candidate DTB (this round) |
|---|---|---|
| ARC provider groups | 7 | **0** |
| ARC provider-child parent edges | 5 | **0** |
| `rpmh-regulator-*` provider groups | 47 (105 nodes) | **0** |
| per-PMIC VRM provider groups | many | **2** (PM8150, PM8150L) |
| rails declared | many | **6** |
| `proxy-supply` occurrences | 8 | **0** |
| `qcom,proxy-consumer-enable` | 8 + 2 SoC nodes | **0** |
| `qcom,resource-name` | present on ARC/VRM groups | **0** |
| `vin-supply` / `vph-pwr-supply` / `vdd-s*-supply` | 0 in the inspected base-FDT scope | 0 |

The two artifacts are therefore **structurally disjoint** with respect to the ARC layer: the vendor graph is present in HOS, and absent by design in the candidate. This is the narrow evidence gap the round was opened to close.

**One cross-reference, stated precisely to avoid re-litigating a settled point:** ROUND139 `:189` says no code path in the *pinned* tree reads `qcom,vccq-parent-supply` or `qcom,vddp-ref-clk-supply`. That remains true of the unpatched stock ACK. The candidate tree additionally carries a `qcom,vddp-ref-clk` consumer introduced by frozen patch 06 (`drivers/ufs/host/ufs-qcom.c:1525`, guard `:1531-1534`), as recorded in the ROUND140/ROUND142 reports. Both statements hold in their own scope; the candidate DTB's `<0x5e>` on that property (§4) is a live edge **in the candidate**, and whether it is a *correct* electrical statement is outside this round.

---

## 8. Observations vs interpretations vs unknowns (taskbook §7)

**Observations (A — bytes in the artifact):**
1. Exactly two `qcom,pm8150*-rpmh-regulators` provider groups, at `regulators-0` (PM8150, id `"a"`, 5 rails) and `regulators-1` (PM8150L, id `"c"`, 1 rail); neither carries a phandle.
2. Zero `qcom,rpmh-arc-regulator` nodes; zero `mmcx`/`mx.lvl`/`cx.lvl` strings; zero `rpmh-regulator-*` node names; zero `qcom,resource-name`; zero `proxy-supply`; zero `qcom,proxy-consumer-enable`.
3. Seven `-supply` edges, all on `ufshc@1d84000` (5) and `phy@1d87000` (2); zero `vin-supply`; one `*-parent-supply` (`qcom,vccq-parent-supply` → `smps8`).
4. UFS host status `"okay"`; `power-domains` → rpmhpd MMCX (6) + GCC UFS PHY GDSC (4); two OPPs whose `required-opps` target rpmhpd `opp3` (level 64) and `opp6` (level 256).

**Interpretations (B/C — supported, explicitly not byte-level):**
5. The candidate expresses UFS corner requirements through the upstream `rpmhpd` GenPD/OPP model instead of ARC regulators, and its source says this is intentional (§6).
6. The pinned ACK RPMh regulator driver could not bind any ARC provider even if one were present (driver-level fact, §5).

**Unknowns (explicitly NOT established this round):**
7. Whether the rpmhpd/OPP corner model is electrically or functionally equivalent to the vendor ARC child-supply graph — **UNKNOWN**, and the board DTS itself declines to claim it (`:114-121`).
8. Runtime RPMh votes, actual rail enable states, and the physical input parents of the six rails — **UNKNOWN** (unchanged from ROUND139/ROUND140/ROUND142).
9. Whether removing the ARC layer would cause a boot failure — **UNKNOWN and not inferred**. A missing DT node is not a boot verdict.

---

## 9. What this round does NOT establish

This is a static inventory of an already-built artifact. It does **not** authorize a first boot, and it does **not** resolve: physical PMIC input networks, the final ABL RAM/FDT handoff, runtime RPMh/ARC votes, DTBO selection, AVB/verification state, recovery viability, or any electrical measurement. No claim here upgrades a hardware gate.

---

## 10. Method compliance, deviations, and self-corrections

**Compliance.** No build, `make`, `bazel`, compilation or test was run. No tablet/ADB/fastboot/recovery/UART/partition access. No source, DTS, patch, Kconfig, config, or binary was modified; the only writes were a decompiled text dump and scripts under `/tmp` outside any workspace artifact path. No files were deleted or cleaned. No other agent's workspace was read — every path used is under `/home/kerneldev/work/matepad11/round140-agent2/`.

**Deviations, disclosed rather than smoothed over:**

| # | Deviation | Why it happened | Effect |
|---|---|---|---|
| V-1 | The `AGENT_TASKBOOK_AGENT2_CANDIDATE_DTB_ARC_NODE_INVENTORY.md` URL in the START_PROMPT returns **404**. The taskbook was located with **three read-only GitHub contents-API requests** (one per candidate ref) on `firmware-analysis/round147`, which showed the taskbook is actually committed at the deliverable path (§V-2). | The documented filename does not exist; the round could not start otherwise. | Metadata-only HTTPS requests; no artifact, tarball or binary was fetched. Disclosed because the taskbook says "no network fetches or downloads"; the branch fetch/upload/readback required by the deliverable is separately authorized. |
| V-2 | The taskbook currently **occupies the deliverable path**. It was committed as `6e49682` ("ROUND147 taskbook: …"), blob `7e16bd33`, 4 761 B. Uploading this report to the required path therefore replaces that file. | The deliverable path is fixed by the taskbook; I do not get to relocate it. | Nothing is lost: the taskbook remains retrievable at `6e49682:firmware-analysis/round147/AGENT2_ROUND147_CANDIDATE_DTB_ARC_NODE_INVENTORY.md`. **AI1 should rename one of the two files**, since the collision will otherwise recur every round. |
| V-3 | My first reverse-reference scan reported ~20 phandle "references" per rail. | Numeric collision between phandle values and clock indices / interrupt numbers / `reg` cells / a µA constant (`0x64` = 100). | Corrected to a `-supply`-typed strict census (7 edges) before anything was written; the false-positive mechanism is recorded in §4 so it is not inherited. |
| V-4 | Decompilation used host `dtc 1.7.0`, while the ROUND140 DTB was produced by tree `dtc 1.7.2-g52f07dcc`. | The host binary is the inspector available outside the tree; using the tree's dtc would have meant touching build outputs. | Inspection only; the artifact hash is unchanged and all structural facts were cross-checked with a second tool (`fdtdump`) and a direct binary parser. |

**Self-corrections made before writing (both recorded rather than quietly fixed):**
- A naive property-count comparison (`3285` text lines vs `3443` parsed) initially looked like a parser defect. It is not: the difference is exactly the 158 valueless boolean properties, delta 0 (§1). Had this not been reconciled, the "zero ARC" claim would have rested on an unvalidated parser.
- The taskbook's own bookkeeping tables (§4) cannot be filled. Rather than emit empty rows that could later be mistaken for "checked and found empty per group", §2 states plainly that the tables are **N/A by construction**.

---

## 11. Artifact record

| Field | Value |
|---|---|
| Report path | `firmware-analysis/round147/AGENT2_ROUND147_CANDIDATE_DTB_ARC_NODE_INVENTORY.md` |
| Branch | `agent2/round147-candidate-arc-node-inventory` |
| Inspected artifact | `…/round140-agent2/out-dtb/arch/arm64/boot/dts/qcom/huawei-dby-w09.dtb`, 108 648 B, `cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e` |
| Inspection outputs (outside the repo) | `/tmp/r147/candidate.dts`, `/tmp/r147/fdtdump.txt`, `/tmp/r147/dtc-warnings.log` |
| Scripts | `/mnt/d/workbuddy/2026-11-25-22-04-11/r147/{fdt_inv.py,s1_identity.sh,s2_decompile.sh,s3_controls.sh,s4_reconcile.sh,s5_source.sh,s6_context.sh,s7_lines.sh,s8_prov.sh,s9_refs.sh,s10_strict.sh}` |

The commit SHA, blob SHA, byte size and readback result for this file are recorded in the ROUND147 delivery message to AI1. They are deliberately not embedded here: writing a blob's own digest into the blob changes the digest.
