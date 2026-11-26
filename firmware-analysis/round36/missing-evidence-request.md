# ROUND36 — Minimal evidence request to unblock Phase E

**Purpose.** Convert the two `BLOCKED — direct evidence absent` findings (`abl-memory-evidence-matrix.md`, `pm8150-physical-topology-matrix.md`) into the smallest possible set of concrete requests. Each request states *what artifact*, *why it is the minimum*, *what form is acceptable*, *what will be rejected*, and *which matrix IDs it closes*.

**Rules that apply to every request below**

1. Requests are split into **U** (the user can supply a document) and **D** (must be produced from the device or a hardware experiment). Every **D** request currently requires device access, which this round's taskbook forbids (`§明确禁止`). They are listed for a future authorized round only.
2. **No request asks for another HOS4.3 firmware upload.** That avenue is exhausted: the HOS4.3 base FDT has already been fully parsed (556524 B, 3471 nodes, 3281 property paths, 0 structure errors) and contains **0** `vdd-s1..s10-supply`, **0** `vin-supply`, **0** `vph-pwr-supply` and **0** `qcom,pmic-id` (`round11…txt:16-17`, `:74-79`; `round13…txt:97-99`). Re-uploading the same packages cannot produce what they do not contain.
3. No request may be satisfied by a reference-design value, a same-name property from another SM8250 product, an inference from a node name, a proxy-vote, or a boot that succeeds via the dummy-regulator path (`core.c:2229-2233`).
4. Every artifact must arrive with: capture command, capture timestamp, byte size, and SHA-256. An artifact without provenance is `D`, not `A`.

---

## Part U — documents the user can supply

### U-1 · Board hardware revision identity

| Field | Content |
|---|---|
| Artifact | A statement (or a label photo / service document) mapping this physical unit to a board revision: `hardware_version` / `board-id` variant (the nine stock variants are distinguished by `board-id`, `board_name`, `hardware_version` — `round19…txt:54-56`; the nine board-ids are 8200/8296/8206/8208/8202/8238/8302/8240/8298 per `firmware-analysis/round7/dby_w09_hw_matrix.txt:9`), or the schematic revision printed on the PCB |
| Why minimum | `round64…md:37` records "specific board hardware revision UNKNOWN". Every U-2/U-3/U-4 artifact is only admissible if it is bound to the revision of *this* unit. Without U-1, U-2 cannot be graded `A` |
| Accepted form | text + optional label photo; a service-manual revision page |
| Rejected | "DBY-W09" alone (model, not revision); a revision inferred from firmware strings |
| Closes | enables `A` grading of U-2…U-4 |

### U-2 · Board schematic pages covering the PMIC rails of interest

| Field | Content |
|---|---|
| Artifact | Schematic sheet(s) for the revision from U-1 showing: PM8150 (a) L5, L6, L9, L17 and S4, and PM8150L (c) S8; each rail's **pin/ball designation**, its **net name**, and the **upstream net / source component** feeding it, plus the input decoupling and any series element |
| Why minimum | This is the only artifact class that turns "the ACK driver expects a property called `vdd-l3-l4-l5-l18-supply`" into "the copper feeding L5 is net X from source Y". Nothing in the corpus contains it (`round64…md:37`, `:40-42`). It closes the largest cluster of `MISSING` rows in one artifact |
| Accepted form | PDF / PNG of the schematic sheet with the net names legible; a net-list extract naming the same nets; a hand-drawn but source-identified page |
| Rejected | A reference-design or Qualcomm公版 schematic for a different product; a schematic without rail/pin mapping; an OCR summary with no sheet reference |
| Closes | `B-17`, `B-21`, `B-22`, `B-23`, `B-35`, `B-36`, `B-37`, `B-38`, and (with U-1) `B-24` |

### U-3 · PMIC power tree / power-up sequencing table for this board

| Field | Content |
|---|---|
| Artifact | The board's power-tree or sequencing document: rail hierarchy, source of each PMIC input (e.g. which buck or which always-on source feeds the L3/L4/L5/L18 group and the L6/L9 group), and the power-up order with any dependency constraints |
| Why minimum | `qcom,init-mode = 4` and `qcom,set = 3` are raw vendor values whose symbolic meaning is explicitly unmapped (`round13…txt:107-108`, `:152-153`, `:210-211`). Only a board/PMIC document resolves them, and only such a document proves the L5/L9 power-up dependency order |
| Accepted form | PDF / table; a PMIC datasheet section **only if** combined with a board document that says which rail group this board uses |
| Rejected | A generic PM8150 datasheet alone (chip-level, not board-level); a sequencing order inferred from `init-mode` numbers |
| Closes | `B-23`, `B-38`, and corroborates `B-17`, `B-35` |

### U-4 · Existing rail measurement record (if any)

| Field | Content |
|---|---|
| Artifact | Any prior measurement of the L5 and L9 **input** nets: nominal voltage, tolerance, measured value, load condition, instrument, date |
| Why minimum | If such a record already exists, it upgrades `B-21`, `B-22`, `B-36`, `B-37` to `B` without any new hardware work |
| Accepted form | measurement table with instrument and date |
| Rejected | a value copied from a reference design; "3.7 V because VPH_PWR" |
| Closes | `B-21`, `B-22`, `B-36`, `B-37` (partially) |

---

## Part D — artifacts that must come from the device or a hardware experiment

> All of Part D requires device access and is **out of scope for this round**. Listed so a future authorized round has an exact, minimal work list.

### D-1 · Privileged read of the final FDT blob — **highest value, single artifact**

| Field | Content |
|---|---|
| Artifact | The 800316-byte `/sys/firmware/fdt` blob, copied read-only off the running device with sufficient privilege, unmodified. Mode today is `-r--------` owned by root (`round2-adb/devicetree_nodes_redacted.txt:3`), and the earlier attempt failed with `adb: error: failed to stat remote object '/sys/firmware/fdt': Permission denied` (`round2-adb/live_dtb_status.txt:1-3`) |
| Why minimum | It is the **only** candidate post-ABL artifact on the device, and one read closes nearly the whole workstream A gap. Nothing else in the corpus is a post-ABL capture (`round64…md:10`, `:20`, `:30`) |
| Accepted form | raw binary + `sha256sum` + `stat` output + the exact capture command + the privilege used. Structural redaction of *addresses* is acceptable if the redaction is described (e.g. "all `reg` values replaced by `0xADDR_REDACTED`, length preserved") — **length-preserving redaction keeps every row in this matrix auditable** |
| Rejected | a re-serialized / re-compiled DTB; a `dtc` round-trip without the original blob; a screenshot of `/proc/device-tree`; a blob from a different unit or a different firmware version |
| Closes | `A-03`, `A-04`, `A-16`, `A-20`, `A-36`, and upgrades `A-01`, `A-02`, `A-15`, `A-24` from `PARTIAL` to `PROVEN`; also supplies the live `/chosen` values behind `A-23` and the live root `/model`, `qcom,board-id` behind U-1 |

### D-2 · Fallback: targeted property reads (if D-1 is refused but some privilege exists)

| Field | Content |
|---|---|
| Artifact | Read-only `cat` / `od` of exactly these files, values and lengths both preserved:<br>`/proc/device-tree/#address-cells`, `/proc/device-tree/#size-cells`, `/proc/device-tree/memory/reg`, `/proc/device-tree/memory/ddr_device_type`, `/proc/device-tree/memory/device_type`, `/proc/device-tree/qcom,board-id`, `/proc/device-tree/qcom,msm-id`, `/proc/device-tree/model`, `/proc/device-tree/rootparam/qcom,boardid`, `/proc/device-tree/rootparam/hardware_version`, `/proc/device-tree/chosen/bootargs`, and `reg` + each of `no-map` / `reusable` / `status` for every child of `/proc/device-tree/reserved-memory/` |
| Why minimum | These are exactly the rows of `abl-memory-evidence-matrix.md` that are `MISSING`. Reads are tiny (the largest is the 1507-byte `bootargs`), so this is a far cheaper authorization than D-1, at the cost of not capturing ABL's exact byte layout |
| Accepted form | one text transcript per property with byte count; `od -An -tx1` for binary properties |
| Rejected | a hand-transcribed value without a length; decimal-only values for `reg` (cell boundaries become unrecoverable) |
| Closes | `A-03`, `A-04`, `A-16`, `A-36`; corroborates `A-23` |

### D-3 · Read-only dump of the `abl` partition (optional, lower value)

| Field | Content |
|---|---|
| Artifact | The `abl` partition (`/dev/block/sde6`, `round2-adb/partition_names_redacted.txt:5`), read-only, size unknown |
| Why optional | A binary ABL would allow string/source-line correlation with the FreeABL reference (`stagea:round42…md:44-48`) and would confirm or refute the `/memory`-must-exist precondition. But it is a *large* artifact and D-1/D-2 answer the memory question more directly. Request it only if the ABL's own memory-mutation logic must be proven, not merely its result |
| Accepted form | image + SHA-256 + size + read command; region-of-interest excerpts with offsets are acceptable if the extraction is reproducible |
| Rejected | a patched or re-signed ABL; an ABL from another unit |
| Closes | `A-32`, and gives `B`-grade corroboration for `A-07` / `A-38` / `A-39` |

### D-4 · Early-boot log showing the entry path and the memory handoff

| Field | Content |
|---|---|
| Artifact | The kernel boot log from the first ~2 s: the ARM64 banner, any `EFI stub` / `efi:` lines, `Memory:` and the `memblock` reserved-region dump, `On node … totalpages`, and any `Unable to handle` / early mapping messages |
| Why minimum | The taskbook requires the *actual* entry classification (`round61…md:30-31`), which is currently `MISSING` (`A-25`). A boot log distinguishes classic Image entry from EFI-stub entry far more cheaply than reverse-engineering the ABL |
| Accepted form | full untruncated `dmesg` from boot, or the pstore/console log; timestamps preserved |
| Rejected | a log from a different kernel; a log with the `memblock`/`Memory:` lines removed; a log whose provenance (build id) is unstated |
| Closes | `A-25`, and upgrades `A-24` from `PARTIAL` to `PROVEN` |

### D-5 · Hardware measurement of the L5 / L9 input nets

| Field | Content |
|---|---|
| Artifact | In-circuit measurement: DC voltage of each input net at idle and under UFS load; continuity from each PMIC pin/ball to the named upstream net; if a current probe is available, the drawn current at the L5/L9 inputs |
| Why minimum | If no schematic exists, measurement is the only remaining route to a physical fact. It is grade `B` (verified measurement on this device), which the taskbook explicitly admits |
| Accepted form | measurement table + instrument + test points + date; photos of probe placement |
| Rejected | a value derived from `qcom,proxy-consumer-current` (a software request); a value derived from a reference design |
| Closes | `B-17`, `B-21`, `B-22`, `B-35`, `B-36`, `B-37` |

---

## Priority

| Rank | Request | Type | Artifacts | IDs closed | Note |
|---|---|---|---|---|---|
| 1 | **D-1** final FDT blob | device | 1 | 6 closed + 4 upgraded (+ U-1 input) | highest value per unit of effort; the only true `A`-grade artifact obtainable |
| 2 | **U-2** schematic sheets | document | 1–3 pages | 8 | the only route to a physical supply fact without hardware work |
| 3 | **U-1** board revision | document | 1 | enables U-2…U-4 grading | must precede or accompany U-2 |
| 4 | **D-4** boot log | device | 1 | 1 closed + 1 upgraded | cheap; settles the entry-path question |
| 5 | **U-3** PMIC power tree | document | 1 | 2 (+2 corroborated) | needed for sequencing, not for parent identity |
| 6 | **D-2** targeted reads | device | ~15 tiny files | 4 closed | only if D-1 is refused |
| 7 | **U-4** existing measurements | document | 1 | 4 partial | free if it exists |
| 8 | **D-3** ABL partition | device | 1 (large) | 1 + corroboration | only if ABL logic itself must be proven |
| 9 | **D-5** new measurements | hardware | 1 session | 6 | last resort when no schematic exists |

**Minimum viable pair to unblock both workstreams:** `D-1` + `U-2` (with `U-1`). `D-1` alone unblocks workstream A; `U-2` alone unblocks workstream B.

---

## Explicit non-requests

The following will **not** be requested, and must not be offered as substitutes:

1. **A re-upload of the HOS4.3 packages.** Already fully parsed; the properties sought are absent, not unexamined.
2. **A same-device public Linux 7.0 / HOS4.2 DTS.** Grade `C`; it is where the untrustworthy `vph_pwr = 3.7 V` and `vdd-s*-supply` guesses come from.
3. **A "just tell me the RAM ranges" answer without an artifact.** Unfalsifiable; grade `D`; cannot close the gate.
4. **A translation of the 4 ARC `*-parent-supply` edges or the 6 `proxy-supply` edges into electrical parents.** Explicitly forbidden (`round11…txt:54-58`, `round21…md:31-34`, `round61…md:41`).
5. **A board DTS that boots.** A boot proves the dummy-regulator path was taken (`core.c:2229-2233`), not that any rail exists.
6. **Any redaction that destroys structure.** Address-only redaction is fine; deleting `reg` length, node names, or attributes makes the artifact unusable.

---

## Status after this request list

Phase E remains **BLOCKED** on both workstreams. This document does not change the Phase E/F status, does not authorize any device operation, and does not authorize Phase G. It becomes actionable only when 2号 AI reviews it and the user chooses to seek the artifacts above.
