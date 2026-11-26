# ROUND36 — PM8150 L5 / L9 software description vs physical supply topology

**Workstream:** B (DBY-W09 mainboard PM8150 L5/L9 physical input topology)
**Type:** read-only evidence audit. No code, no DTS, no build, no device access.
**Branch:** `firmware-audit-v1`

**Pinned evidence trees**

| Tree | Repo / ref | Commit |
|---|---|---|
| Report corpus | `hhdy/matepad11-dby-w09-agent-reports` `firmware-audit-v1` | `be4f5178c41b4a26c5bc5f5658244e3470d82151` |
| Stage A corpus | `hhdy/matepad11-dby-w09-agent-reports` `ai-parallel/stagea-port-until-boot` | `f0b00e38c8222be14adfb21f122db7f8cac94c14` |
| ACK source reference | `android17-6.18.33_r00` | `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` |

Grades and statuses use the same legend as `abl-memory-evidence-matrix.md` §0.

---

## 0. The one distinction this matrix enforces

The taskbook forbids treating a `*-supply` declaration, a regulator node name, a software proxy-vote or a reference-platform design as physical-wiring proof. Concretely, four different kinds of edge exist in this data and **none of them is a board-level electrical edge**:

| Kind | Example in this corpus | What it actually means | Why it is not a physical parent |
|---|---|---|---|
| Driver-table input name | `RPMH_VREG("ldo5","ldo%s5",&pmic5_nldo,"vdd-l3-l4-l5-l18")` — ACK `drivers/regulator/qcom-rpmh-regulator.c:995` | the regulator core will look up a DT property named `vdd-l3-l4-l5-l18-supply` **on the PM8150 provider node** | it names a *property expected in DT*; the property is optional and absent here, and even its name only expresses a PMIC-internal rail grouping, never a board net |
| Binding permission | `vdd-l3-l4-l5-l18-supply: true` — ACK `Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml:289` | the property is *allowed* on `qcom,pm8150-rpmh-regulators` | `required:` lists only `compatible` and `qcom,pmic-id` (`…yaml:136-138`); allowed ≠ present, and permitted ⊆ proven |
| Vendor ARC parent edge | 4 × `*-parent-supply` in `/soc/rsc@18200000`, e.g. `pm8150_s3_level-parent-supply → regulator-pm8150a-s3-level` — report:`firmware-analysis/round11/round11_pmic_parent_supply_findings.txt:38-52` | voltage-level dependency between ARC accelerator groups | targets are voltage-*level* nodes, not supplies; ACK does not even bind `qcom,rpmh-arc-regulator` (stagea:`round21…md:31-34`) |
| Vendor proxy vote | 6 × `proxy-supply`, incl. `rpmh-regulator-ldoa5 → regulator-pm8150-l5` — `round11…txt:54-64` | a temporary boot-time consumer vote on a rail (`qcom,proxy-consumer-current/enable`) | proves a software request, not an electrical input |

The board-level question — *what copper feeds L5 and L9* — is answered by none of the four.

---

## 1. Provider identity (shared by L5 and L9)

| ID | Fact | Value | Source | Grade | Status |
|---|---|---|---|---|---|
| B-01 | PM8150 L5 node in the HOS4.3 base FDT | group `/soc/rsc@18200000/rpmh-regulator-ldoa5`, `compatible = "qcom,rpmh-vrm-regulator"`, `qcom,resource-name = "ldoa5"`, child `/…/regulator-pm8150-l5`, `regulator-name = "pm8150_l5"` | report:`firmware-analysis/round13/round13_pm8150_mode_drms_findings.txt:137-143` | B | PROVEN |
| B-02 | PM8150 L9 node in the HOS4.3 base FDT | group `/soc/rsc@18200000/rpmh-regulator-ldoa9`, same compatible, `qcom,resource-name = "ldoa9"`, child `/…/regulator-pm8150-l9`, `regulator-name = "pm8150_l9"` | `round13…txt:196-202` | B | PROVEN |
| B-03 | `qcom,pmic-id` in the HOS4.3 base FDT | **0 nodes in the entire base FDT** — provider identity is anchored only on group compatible + resource-name + child regulator-name | `round13…txt:97-99` | B | PROVEN |
| B-04 | Binding conformance note | the ACK binding *requires* `qcom,pmic-id` (`…yaml:136-138`), which the HOS tree does not carry; the review-only board draft supplies `qcom,pmic-id = "a"` (stagea:`dts/dby-w09-ack18-board.dts.draft:163`). Any future board DTS must keep it, and its correctness is a board-identity question, not a supply question | as cited | C | PARTIAL |
| B-05 | Stock DTBO influence on these rails | none — all 9 entries: fragment "none", target "none", overlay action NONE, and no entry contains `rpmh-regulator`, a regulator node name, or any audited mode property | `round13…txt:21-23`, `:130`, `:163`, `:189`, `:216` | B | PROVEN (absence) |

---

## 2. L5 — UFS QMP VDDA-PHY, 0.88 V

### 2.1 Software description (all C / B, none physical)

| ID | Fact | Value | Source | Grade | Status |
|---|---|---|---|---|---|
| B-06 | Chip-internal regulator type | `qcom,regulator-type = "pmic5-ldo"` | `round13…txt:145` | B | PROVEN |
| B-07 | Mode set | `qcom,supported-modes = <2 4>` (raw, ordered) | `round13…txt:146` | B | PROVEN (raw values only) |
| B-08 | Mode-switch current threshold | `qcom,mode-threshold-currents = <0 30000>` µA — this is the **HPM/LPM switch threshold**, not a load capability rating | `round13…txt:147` | B | PROVEN (semantics: threshold only) |
| B-09 | Output voltage | `regulator-min/max-microvolt = 880000 / 880000`, `qcom,init-voltage = 880000` | `round13…txt:150-151` | B | PROVEN |
| B-10 | Init mode / set | `qcom,init-mode = 4`, `qcom,set = 3` (raw; symbolic meaning **not** mapped, and deliberately not guessed) | `round13…txt:152-153`; unmapped-semantics statement `round13…txt:107-108` | B | PROVEN (raw) / UNKNOWN (semantics) |
| B-11 | Proxy vote | group `proxy-supply = phandle 124` → its own child node; child `qcom,proxy-consumer-current = 100000` µA, `qcom,proxy-consumer-enable` present (zero-length) | `round13…txt:148-149`, `:154-155` | B | PROVEN (software request only) |
| B-12 | Sibling rail copies in the same group | `regulator-pm8150-l5-ao` (`init-mode 2`, `set 1`, 880000 µV); `regulator-pm8150-l5-so` (`init-mode 2`, `set 2`, `init-enable 0`, 880000 µV) | `round13…txt:158-162` | B | PROVEN |
| B-13 | ACK driver input name for L5 | `"vdd-l3-l4-l5-l18"`, hardware data `pmic5_nldo` | ACK `drivers/regulator/qcom-rpmh-regulator.c:995` (table `pm8150_vreg_data`, `:980-1010`) | C | PROVEN (software expectation) |
| B-14 | Where the driver consumes it | `vreg->rdesc.supply_name = rpmh_data->supply_name;` | ACK `…/qcom-rpmh-regulator.c:447` | C | PROVEN |
| B-15 | Binding permission for that name | `vdd-l3-l4-l5-l18-supply: true` under the `qcom,pm8150-rpmh-regulators` branch | ACK `…/qcom,rpmh-regulator.yaml:282`, `:289` | C | PROVEN (optional) |
| B-16 | UFS consumer mapping | `vdda-phy-supply = <&vreg_l5a_0p88>`, `vdda-phy-max-microamp = <89900>` | stagea:`dts/dby-w09-ack18-board.dts.draft:285-286`; rationale `round21…md:56` | C | PROVEN (consumer→output) |

### 2.2 Physical topology (what Phase E actually needs)

| ID | Fact | Value | Source | Grade | Status |
|---|---|---|---|---|---|
| B-17 | L5 **input** parent rail, named in any board-specific source | **none found.** No schematic, PMIC power tree, BOM or PCB net list for DBY-W09 exists in the authorized corpus | report:`firmware-analysis/round64/round64-dby-w09-hos43-final-memory-and-pm8150-input-evidence.md:37`, `:40-42`; stagea:`kernel-baseline/round61/phase-e-board-dts-memory-power-gates.md:43-45` | — | MISSING |
| B-18 | Explicit input-parent property in the HOS base FDT | **0 hits** for `vdd-s1..s10-supply`, `vin-supply`, `vph-pwr-supply` across the whole base FDT (whole-FDT property-name scan on a fully parsed 3281-property tree — a verified NOT_FOUND, not an inference) | `round11…txt:74-79` | B | PROVEN (absence) |
| B-19 | `vin-supply` / `vph-pwr-supply` | 0 hits | `round11…txt:76-77` | B | PROVEN (absence) |
| B-20 | Upstream-named regulator mode/DRMS properties as a cross-check on scan completeness | 0 hits for `regulator-initial-mode`, `regulator-allowed-modes`, `regulator-allow-set-load`, `regulator-system-load`, and 0 for the three `regulator-state-*` child nodes — consistent with B-18 being a real absence in this vendor tree, not a parse failure | `round13…txt:77-88` | B | PROVEN |
| B-21 | L5 input voltage | **unknown.** The 880000 µV in the DTS is the L5 **output**; no source states the input | — | — | MISSING |
| B-22 | L5 input current capability / continuous rating | **unknown.** `qcom,mode-threshold-currents = <0 30000>` is a mode-switch threshold (B-08); `qcom,proxy-consumer-current = 100000` is a *request* (B-11); neither is a capability rating | as cited | — | MISSING |
| B-23 | L5 power-up sequencing / dependency order | **unknown.** `qcom,init-mode = 4` and `qcom,set = 3` are raw vendor values with unmapped semantics | `round13…txt:152-153` | — | MISSING |
| B-24 | Board hardware revision that any future schematic must match | **UNKNOWN** — "Board DBY-W09 identified; specific board hardware revision UNKNOWN" | `round64…md:37` | — | MISSING |
| B-25 | Whether a same-name reference-platform design exists | yes, but reference designs are grade **C** and "must not be upgraded to this unit's physical fact" | taskbook §工作流 B.3; `round64…md:10` (HOS4.2 public reference is not an acceptable substitute) | D | MISSING |

---

## 3. L9 — UFS QMP VDDA-PLL, 1.2 V

| ID | Fact | Value | Source | Grade | Status |
|---|---|---|---|---|---|
| B-26 | Chip-internal regulator type | `qcom,regulator-type = "pmic5-ldo"` | `round13…txt:204` | B | PROVEN |
| B-27 | Mode set | `qcom,supported-modes = <2 4>` | `round13…txt:205` | B | PROVEN (raw) |
| B-28 | Mode-switch threshold | `qcom,mode-threshold-currents = <0 30000>` µA | `round13…txt:206` | B | PROVEN (threshold only) |
| B-29 | Output voltage | `regulator-min/max-microvolt = 1200000 / 1200000`, `qcom,init-voltage = 1200000` | `round13…txt:208-209` | B | PROVEN |
| B-30 | Init mode / set | `qcom,init-mode = 4`, `qcom,set = 3` (raw) | `round13…txt:210-211` | B | PROVEN (raw) / UNKNOWN (semantics) |
| B-31 | Proxy vote | group `proxy-supply = phandle 125` → its own child; child `qcom,proxy-consumer-current = 100000` µA, `qcom,proxy-consumer-enable` present | `round13…txt:207`, `:212-213` | B | PROVEN (software request only) |
| B-32 | ACK driver input name for L9 | `"vdd-l6-l9"`, hardware data `pmic5_nldo` — **L9 shares its driver-level input name with L6**, which is *not* a claim about copper | ACK `…/qcom-rpmh-regulator.c:999`; L6 at `:996` | C | PROVEN (software expectation) |
| B-33 | Binding permission for that name | `vdd-l6-l9-supply: true` under `qcom,pm8150-rpmh-regulators` | ACK `…/qcom,rpmh-regulator.yaml:290` | C | PROVEN (optional) |
| B-34 | UFS consumer mapping | `vdda-pll-supply = <&vreg_l9a_1p2>`, `vdda-pll-max-microamp = <18800>` | stagea:`dts/…draft:288-289`; `round21…md:57` | C | PROVEN (consumer→output) |
| B-35 | L9 **input** parent rail | **none found** — same absence as B-17 | `round64…md:37`, `:40-42` | — | MISSING |
| B-36 | L9 input voltage | **unknown** (1200000 µV is the output) | — | — | MISSING |
| B-37 | L9 input current capability | **unknown** (B-28 and B-31 are not ratings) | — | — | MISSING |
| B-38 | L9 power-up sequencing | **unknown** (raw `init-mode 4`) | `round13…txt:210` | — | MISSING |

---

## 4. Why "it probes successfully" is not evidence

This is the trap the taskbook names explicitly (§明确禁止 last two bullets; §工作流 B.2 last bullet). The ACK regulator core will silently substitute a dummy regulator, so a board DTS without any `vdd-l*-supply` phandle **will still probe**:

| ID | Fact | Value | Source | Grade | Status |
|---|---|---|---|---|---|
| B-39 | Dummy substitution is automatic whenever a DT is populated | `have_full_constraints()` returns `has_full_constraints \|\| of_have_populated_dt()` | ACK `drivers/regulator/core.c:114-117` | C | PROVEN |
| B-40 | Provider-side fallback path | on `regulator_dev_lookup(rdev->supply_name)` failure and full constraints, `r = dummy_regulator_rdev` instead of failing | ACK `core.c:2070-2091` | C | PROVEN |
| B-41 | Consumer-side fallback path and its stated assumption | `NORMAL_GET` → `rdev = dummy_regulator_rdev;` and the in-tree comment: *"Assume that a regulator is physically present and enabled, even if it isn't hooked up, and just provide a dummy."* | ACK `core.c:2227-2238` (comment `:2229-2233`, warning `:2237`) | C | PROVEN |
| B-42 | Therefore | successful probe of L5/L9 proves **only** that the software graph was satisfied by a dummy; it proves nothing about the presence, voltage or enable state of any physical rail | `round21…md:38-45`; `round61…md:41` | C | PROVEN |

B-39…B-42 are the reason the corpus cannot be "made consistent" by a build that boots.

---

## 5. Negative-finding register (searched, with the search that makes the absence meaningful)

Every row below is a *verified* NOT_FOUND, i.e. a scan that demonstrably parsed the whole tree and then found nothing. This is the distinction the taskbook demands between "searched, not found" and "proven absent in the inspected scope".

| ID | Probe | Result | Scan scope / completeness proof | Source | Grade |
|---|---|---|---|---|---|
| B-43 | `vdd-s1-supply` … `vdd-s10-supply` | 0 hits | whole-base-FDT property-name scan after a full parse: totalsize 556524, 3471 nodes, 3281 property paths, 0 structure errors, phandle index 1693 | `round11…txt:16-17`, `:74-75`, `:78-79` | B |
| B-44 | `vin-supply` | 0 hits | same scan | `round11…txt:76-77` | B |
| B-45 | `vph-pwr-supply` | 0 hits | same scan | `round11…txt:76-77` | B |
| B-46 | property names containing `supply` / `vin` / `parent` in `/soc/rsc@18200000` | exactly 10: 4 `*-parent-supply` + 6 `proxy-supply`, enumerated | 109 property paths in the rsc subtree | `round11…txt:22-24`, `:38-64` | B |
| B-47 | `regulator-initial-mode`, `regulator-allowed-modes`, `regulator-allow-set-load`, `regulator-system-load`, `regulator-state-{standby,mem,disk}` | 0 hits each | global scan of all 3281 property-bearing paths | `round13…txt:77-88` | B |
| B-48 | `qcom,pmic-id` | 0 nodes | whole base FDT | `round13…txt:97-99` | B |
| B-49 | Any DTBO adding a regulator/provider node | 0 | all 9 entries, whole-overlay level, 4 independent probes (node name, regulator name, mode property, fragment target) | `round13…txt:67-70`, `:21-23` | B |
| B-50 | Board-specific schematic / PMIC power tree / PCB net list | 0 artifacts | "No schematic/power-tree source present" | `round64…md:37`, `:40-42` | B (absence in corpus) |

---

## 6. Summary

| Status | IDs |
|---|---|
| PROVEN (software layer only) | B-01…B-05, B-06…B-16, B-26…B-34, B-39…B-42, B-43…B-50 |
| PARTIAL | B-04 |
| MISSING | B-17, B-21, B-22, B-23, B-24, B-25, B-35, B-36, B-37, B-38 |
| CONFLICT | none |

**Separated by layer:**

- *Chip-internal regulator type and output behaviour* — PROVEN at grade B/C. L5 and L9 are `pmic5-ldo` (nldo in the ACK table), fixed 0.88 V and 1.20 V respectively, with a vendor raw `init-mode 4` and a 100 mA proxy request.
- *PMIC-internal input grouping* — PROVEN at grade **C only**. The ACK driver expects the L5 input property to be shared by L3/L4/L5/L18 and the L9 input to be shared with L6. This is a software naming convention; it does not name a net, a voltage or a source.
- *Board physical input of L5 and L9* — **MISSING at every grade above D.** No schematic, no power tree, no BOM, no rail measurement, no input-supply property, no board revision binding.

Therefore Phase E workstream B remains **`BLOCKED — direct evidence absent`**, and the L5/L9 physical input parent must stay unspecified in `dts/dby-w09-ack18-board.dts.draft` exactly as it is today (`round21…md:62-67`; `round61…md:41`).
