# ROUND138 — HOS4.3 DTBO entry-2 vs entry-8 variant and live-FDT delta audit

- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel reference: ACK `android17-6.18.33_r00`, pinned `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`; R3 candidate tree `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Nature: local offline read-only comparison of already-existing binary work copies and already-collected device text captures. **No device access, no firmware extraction, no build, no source/DTS/DTBO/Kconfig/patch change, no binary upload.**
- Executor: WorkBuddy Agent (local executor). Dispatched by AI1.

**Final outcome: PASS — ENTRY2/8 STATIC COMPARISON COMPLETE.**
PASS here means the static comparison and all five evidence tasks in the taskbook were executed against the authorized corpus. It does **not** assert that the on-device `dtbo` partition equals the extracted package; that linkage remains UNKNOWN and is stated as a condition in §7.

---

## 0. Inputs actually used (identities, read-only)

| ID | Path (project-established) | Use in this round |
|---|---|---|
| E1 | `MatePad11_HOS43_LocalCheck_20261123_230849/` | HOS4.3 extracted-package workspace (11 copied files, 43-row inventory; **not re-extracted**) |
| E5 | `Agent_Round2_Report/device/` | already-collected device text/metadata (getprop, live DT listings) |
| E6 | `github_upload/round2-adb/adb_getprop_redacted.txt` | byte-identical duplicate of the E5 getprop capture (same line numbers) |
| E7 | `D:/DBY-W09_FirmwareAnalysis_round3/dtb_work/` | 9 pre-existing DTBO work copies + 4 boot FDT candidates |
| R3/R7/R8 outputs | `D:/DBY-W09_FirmwareAnalysis_round3/`, `..._round7/`, `..._round8/` | prior parser results, compared — not trusted |

All E7 files were opened `rb` only. Their mtimes are unchanged from the pre-round state (`2026-11-24 01:18:00`–`01:18:01`); no file was rewritten, renamed, repaired or re-extracted. Only the nine DTBO entries and `boot_fdt_candidate_0.dtb` were structurally parsed (`boot_fdt_candidate_1.dtb` was hashed for an identity-only cross-check and not otherwise used); no arbitrary drive or personal-directory enumeration was performed.

---

## 1. Task A — entry 2 / entry 8 / base FDT identities

### 1.1 Recomputed identity (this round, independent encoder)

| File | Size (B) | SHA-256 | mtime (local) | FDT `totalsize` | nodes parsed |
|---|---|---|---|---|---|
| `dtbo_entry_2.dtbo` | 329,240 | `0633a6fbeebbad45c0f5572faf222c779e1cd51d253a6ef8282592a730ba3c8b` | 2026-11-24 01:18:00 | 329,240 | 1,688 |
| `dtbo_entry_8.dtbo` | 329,352 | `a7946352a86ab6e47b5ee79d84e5d6c4cf4e548c96b0221cec909f32ebd9d21d` | 2026-11-24 01:18:01 | 329,352 | 1,690 |
| `boot_fdt_candidate_0.dtb` | 556,524 | `df2730f3d2e9bdabad874c3ef7399534c5c6070b046c4524224aa461ba2c70f7` | 2026-11-24 01:18:01 | 556,524 | 3,471 |

Comparison with ROUND137 Appendix A: **size and SHA-256 match for all three; identity MISMATCH = none.** `totalsize` equals file size in every case, so none of the three files carries trailing padding.

### 1.2 DTBO FDT root metadata (raw overlay root, before application)

| Property | entry 2 | entry 8 |
|---|---|---|
| `model` | `Huawei Technologies, Inc. DBY-W09` | `Huawei Technologies, Inc. DBY-W09` |
| `compatible` | `qcom,kona-qrd`, `qcom,kona`, `qcom,qrd` | identical |
| root `qcom,board-id` | **(8206, 0)** | **(8298, 0)** |
| root `qcom,msm-id` | absent | absent |
| FDT version | 17 | 17 |

**The `model` string is identical in all nine entries and in the base FDT, so `model` cannot discriminate the board variant. No variant conclusion in this report is derived from `model` or from `compatible`.**

### 1.3 DT table entry fields kept separate from overlay properties

| Field class | Value | Source |
|---|---|---|
| DT table entry `id` / `rev` | `0x00000000` / `0x00000000` for entries 0–8 | ROUND3 `device_tree_inventory.csv` + `round3_summary.json` (`"id_rev": "all 0x00000000 (parsed from DTBO entry table)"`) |
| DT table `custom[0..3]` | **unavailable** — not recorded in any already-existing parser output | — |
| Overlay-root `qcom,board-id` | entry 2 = (8206,0); entry 8 = (8298,0) | this round, direct read |
| Fragment payload `qcom,boardid` | entry 2 = u32[8,2,0,6]; entry 8 = u32[8,2,9,8] | this round, direct read |

The table `id`/`rev` are **not** board identity: all nine are zero while their board-ids differ. They are therefore reported separately and never substituted for `qcom,board-id`.

### 1.4 Decimal / hexadecimal mapping (explicit, recomputed)

| Entry | root `qcom,board-id` (decimal, authoritative) | hexadecimal | payload `qcom,boardid` digits | consistent? |
|---|---|---|---|---|
| 0 | 8200 | 0x2008 | 8,2,0,0 → 8200 | yes |
| 1 | 8296 | 0x2068 | 8,2,9,6 → 8296 | yes |
| **2** | **8206** | **0x200E** | **8,2,0,6 → 8206** | **yes** |
| 3 | 8208 | 0x2010 | 8,2,0,8 → 8208 | yes |
| 4 | 8202 | 0x200A | 8,2,0,2 → 8202 | yes |
| 5 | 8238 | 0x202E | 8,2,3,8 → 8238 | yes |
| 6 | 8302 | 0x206E | 8,3,0,2 → 8302 | yes |
| 7 | 8240 | 0x2030 | 8,2,4,0 → 8240 | yes |
| **8** | **8298** | **0x206A** | **8,2,9,8 → 8298** | **yes** |

- **8206 decimal = 0x200E** and **8298 decimal = 0x206A**: confirmed.
- 0x206E = **8302** = entry 6, not entry 2. The hexadecimal values 0x200E (entry 2) and 0x206E (entry 6) are distinct; this repeats the ROUND137 correction deliberately rather than silently.
- The payload `qcom,boardid` is sixteen bytes = four `u32` cells holding the decimal digits of the same board number, and it is internally consistent for all nine entries — an independent cross-check that entry 2 really is the 8206 variant document and entry 8 the 8298 one.

No file substitution was made or needed: no identity mismatch occurred.

---

## 2. Task B — `/rootparam` resolved across all nine entries

### 2.1 Four concepts, kept separate

1. **Literal overlay node named `/rootparam`** — a node whose path in the *raw* DTBO contains `rootparam`. Measured on the raw FDT structure, all nodes, all nine entries: **0 occurrences**.
2. **Fragment target reference** — the fragment carries `target = <0xffffffff>` (placeholder) and the overlay root node `/__fixups__` holds a property named `rootparam` whose value is `/fragment@N:target:0`. Present in **all nine**, exactly one reference each. No entry uses `target-path = "/rootparam"` (0 occurrences in all nine).
3. **Fragment `__overlay__` payload** — five variant-identity properties (see §2.2).
4. **DT table `id`/`rev`/`custom`** — all-zero id/rev, custom unavailable; independent of the overlay root `qcom,board-id`.

A placeholder phandle was never treated as a resolved target: resolution required the `__fixups__` symbol plus the base-FDT `__symbols__` entry (`rootparam → /rootparam`, base symbols = 1,753 entries, phandle index = 1,693 entries). All targets resolved; **0 unresolved, 0 no-fixup, 0 target-path** in all nine.

### 2.2 Per-entry matrix

| # | DT id/rev | overlay root `qcom,board-id` | fragments | literal `/rootparam` node | rootparam target ref | resolved vs base symbol | rootparam fragment | payload identity values | `huawei,modem_id` |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0/0 | 8200 (0x2008) | 143 | no | yes (`__fixups__` → phandle) | yes `/rootparam` | `fragment@142` | **VA** / SH0DBSLM / DBY-W09 | identical generic sentinel |
| 1 | 0/0 | 8296 (0x2068) | 145 | no | yes | yes | `fragment@143` | **VF** / SH1DBSLMA / DBY-W09 | same sentinel |
| 2 | 0/0 | **8206 (0x200E)** | **144** | no | yes | yes | `fragment@143` | **VD** / SH1DBSLM / DBY-W09 | same sentinel |
| 3 | 0/0 | 8208 (0x2010) | 143 | no | yes | yes | `fragment@142` | **VC** / SH1DBSLM / DBY-W09 | same sentinel |
| 4 | 0/0 | 8202 (0x200A) | 144 | no | yes | yes | `fragment@143` | **VB** / SH1DBSLM / DBY-W09 | same sentinel |
| 5 | 0/0 | 8238 (0x202E) | 145 | no | yes | yes | `fragment@143` | **VI** / SH1DBSLMA / DBY-W09 | same sentinel |
| 6 | 0/0 | 8302 (0x206E) | 145 | no | yes | yes | `fragment@143` | **VH** / SH1DBSLM / DBY-W09 | same sentinel |
| 7 | 0/0 | 8240 (0x2030) | 145 | no | yes | yes | `fragment@143` | **VE** / SH1DBSLM / DBY-W09 | same sentinel |
| 8 | 0/0 | **8298 (0x206A)** | **145** | no | yes | yes | `fragment@143` | **VG** / SH1DBSLM / DBY-W09 | same sentinel |

Payload field names (identical set in all nine): `qcom,boardid`, `qcom,board_name`, `qcom,product_name`, `hardware_version`, `huawei,modem_id`.
`huawei,modem_id` is the **same 8-byte generic sentinel in all nine entries** (one distinct value across the nine, equal to `u32[0xFFFFFFFF, 0]`); raw value is not reproduced beyond this sentinel form. `qcom,product_name` is `DBY-W09` in all nine, so it also cannot discriminate variants.

### 2.3 Resolution of the prior-report discrepancy (no silent overwrite)

| Report | Statement | Verdict |
|---|---|---|
| ROUND7 `dtbo_board_rootparam_matrix.csv` | `rootparam_present=False`, `rootparam_fields` empty, for all 9 | **correct for its own definition, misreadable as a conclusion**: the generator tests `any("rootparam" in n["path"].lower() for n in nodes)` (`round7/tools/Build-Round7-Inventory.py:214`), i.e. a *literal node path*. Raw overlays contain no such node (0/9, independently re-verified), so False is the right value for concept 1 — it is **not** evidence that no fragment targets `/rootparam`. |
| ROUND7 same CSV | `__symbols__`, `__fixups__`, `__local_fixups__` = False for all 9 | **invalid column** — implementation defect at `Build-Round7-Inventory.py:212`: `any(meta in e for e in props.values())` tests whether the string is a **property name** on some node, while these three are **child nodes** of the overlay root. Independent re-scan: all nine entries contain `/__symbols__`, `/__fixups__` (165–166 symbols) and `/__local_fixups__`. These three False values must not be cited as absence evidence. |
| ROUND8 | entry 8 `fragment@143` targets `/rootparam`, 145/145 resolved | **confirmed** by an independent parser: `fragment@143`, symbol `rootparam`, path `/rootparam`. |
| ROUND137 | all nine entries contain a `rootparam` overlay target | **confirmed** for all nine (concept 2), one reference each, at `fragment@142` (entries 0,3) or `fragment@143` (all others). |

Conclusion: none of the three reports is substantively wrong about entry 8; ROUND7's False column is definition-scoped for `rootparam` and defective for the three metadata columns. Both statements are recorded here rather than one being overwritten.

---

## 3. Task C — entry 2 vs entry 8 overlay delta

Method: every fragment target was resolved through base-FDT symbols to a real node path; each fragment was canonicalised as `(resolved path, sorted payload properties, overlay child nodes)` and the two entries compared both per target and as a strict multiset.

**Totals: entry 2 = 144 fragments / 73 unique targets / 0 unresolved. Entry 8 = 145 fragments / 73 unique targets / 0 unresolved. Identical target set; 142 fragments carry byte-identical payloads.**

| Class | Count | Detail |
|---|---|---|
| present in both, identical | **142 fragments** (71 targets) | includes every UFS, PMIC, regulator, RPMh/RSC, power-domain, clock, reset and interconnect touch point |
| present in both, changed | **2 targets** | `fragment@143 → /rootparam`; `fragment@76/@136 → /huawei_wifi_info` |
| present only in entry 2 | 0 targets | — |
| present only in entry 8 | 1 fragment, 0 new targets | `fragment@144 → /huawei_slpi_sensor`, an exact duplicate of entry-8 `fragment@135` (`als_para_select = old_struct`); entry 2 has only `fragment@135` |
| unresolved / unknown | 0 | all 145/144 targets resolved |

### 3.1 The two changed targets

| Target | Property | entry 2 | entry 8 |
|---|---|---|---|
| `/rootparam` | `qcom,board_name` | `DBY_W09_VD` | `DBY_W09_VG` |
| `/rootparam` | `qcom,boardid` | u32[8,2,0,6] (8206) | u32[8,2,9,8] (8298) |
| `/rootparam` | `hardware_version` | `SH1DBSLM` | `SH1DBSLM` (same) |
| `/rootparam` | `qcom,product_name` | `DBY-W09` | `DBY-W09` (same) |
| `/rootparam` | `huawei,modem_id` | same generic sentinel | same generic sentinel |
| `/huawei_wifi_info` | `wifi,pubfile_id` | `dby_lx9` | `dby_fem_lx9` |

The Wi-Fi pubfile difference is a firmware-file selector, not a UFS/PMIC property; it is recorded for completeness and is not interpreted as a hardware variant discriminator in this report.

### 3.2 UFS host / PHY (resolved, identical)

| Fragment | Resolved target | entry 2 payload | entry 8 payload |
|---|---|---|---|
| `fragment@63` | `/soc/ufsphy_mem@1d87000` | `compatible=qcom,ufs-phy-qmp-v4`, `status=ok`, `vdda-phy-supply=<placeholder phandle>`, `vdda-pll-supply=<placeholder phandle>`, `vdda-phy-always-on` (present, len 0), `vdda-phy-max-microamp=89900`, `vdda-pll-max-microamp=18800` | identical |
| `fragment@64` | `/soc/ufshc@1d84000` | `status=ok`, `vcc-supply`, `vccq-supply`, `vccq2-supply`, `vdd-hba-supply`, `qcom,vddp-ref-clk-supply`, `qcom,vccq-parent-supply` (all placeholder phandles), `vcc-voltage-level=2504000,2950000`, `vcc-max-microamp=800000`, `vccq-max-microamp=800000`, `vccq2-max-microamp=800000`, `qcom,vddp-ref-clk-max-microamp=100`, `qcom,vccq-parent-max-microamp=210000`, `vcc-low-voltage-sup` (present), `vdd-hba-fixed-regulator` (present) | identical |
| `fragment@10`, `fragment@113` | `/soc/ssphy@88e8000` | `extcon=<phandle>`; `qcom,qmp-phy-init-seq` (opaque blob, same length and bytes) | identical |

No fragment in either entry modifies UFS `clocks`, `clock-names`, `resets`, `power-domains`, `interconnects`, `phys` or `phy-names` — those remain base-tree values in both. Entry 2 therefore changes **no** UFS host/PHY property relative to entry 8.

Note: ROUND8's entry-8 UFS summary listed `vdd-hba-supply` but omitted `vdd-hba-fixed-regulator`, which is present in the raw payload (len 0). Minor omission in that report's display list; the underlying binary is unaffected and both entries carry it.

### 3.3 PMIC / regulator / RPMh / power-domain sweep

Every overlay property whose name matches `supply|regulator|power-domain|voltage|microamp|microvolt|rpmh|rsc|vdd|vcc|vdda|vddp|interconnect` was enumerated in both entries. The complete set is identical:

| Target | Relevant properties (both entries identical) |
|---|---|
| `/soc/ufsphy_mem@1d87000` | `vdda-phy-supply`, `vdda-pll-supply`, `vdda-phy-always-on`, `vdda-phy-max-microamp`, `vdda-pll-max-microamp` |
| `/soc/ufshc@1d84000` | `vdd-hba-supply`, `vdd-hba-fixed-regulator`, `vcc-supply`, `vccq-supply`, `vccq2-supply`, `vcc-voltage-level`, `vcc-low-voltage-sup`, current limits, `qcom,vddp-ref-clk-*`, `qcom,vccq-parent-*` |
| `/soc/sdhci@8804000` | `vdd-supply`, `vdd-io-supply`, `qcom,vdd-*-voltage-level`, `qcom,vdd-*-current-level` |
| `/soc` | regulator-fixed / display-regulator child nodes (`dsi_panel_pwr_supply*`, `regulator-haptics-boost`, `regulator-dbb1`, `display_gpio_regulator@1`) — added identically |
| `/huawei,lcd_panel` (`fragment@83`, `fragment@142`) | `iovcc_gpio` |
| `/huawei_hall_sensor` | `vdd-supply` |

No fragment targets an RPMh/RSC node, a `regulator-*` node, a PMIC SPMI sub-node for the purpose of changing regulators, or any `power-domains` property. The only PMIC-adjacent fragments (`fragment@0/2/4/7` → `/soc/qcom,spmi@c440000`) add `qcom,spmi-pmic` / `qcom,qpnp-revid` / `qcom,qpnp-power-on` / `qcom,spmi-temp-alarm` child nodes identically in both entries. The Huawei `power_supply`/charger targets (`/huawei_power_supply`, `/huawei_power_proxy`, `/power_thermalzone`, `/direct_charger*`) are battery/charger class nodes, not regulator providers, and are likewise identical in both entries.

**Result: entry 2 and entry 8 are functionally identical for storage rails, PMIC, regulators and power domains; their only differences are the `rootparam` identity pair and the Wi-Fi pubfile selector, plus one duplicated sensor fragment in entry 8.**

---

## 4. Task D — provenance of `ro.boot.dtbo_idx`

| Item | Value | Where |
|---|---|---|
| `ro.boot.dtbo_idx` | `[2]` | `Agent_Round2_Report/device/adb_getprop_redacted.txt` **line 753**; byte-identical duplicate `github_upload/round2-adb/adb_getprop_redacted.txt` line 753 |
| capture timestamp | `2026-11-23T22:52:16.4241436+08:00` | line 1 of the same file |
| `ro.boot.flash.locked` | `[0]` | line 755 (context only) |
| `ro.boot.verifiedbootstate` | `[orange]` | line 765 (context only) |
| `ro.boot.product.hardware.sku` | `[DBY-W09]` | line 761 |
| `ro.boot.hardware` | `[qcom]` | line 757 |
| `ro.boot.bootdevice` | `[1d84000.ufshc]` | line 750 |
| `ro.build.fingerprint` | `HUAWEI/DBY-W09/HWDBY:12/HUAWEIDBY-W09/104.3.0.196C00:user/release-keys` | line 786 |
| `ro.huawei.build.fingerprint` | same as above | line 1042 |
| `ro.build.version.incremental` | `104.3.0.196C00` | line 809 |
| `ro.build.version.emui` | `EmotionUI_15.0.0` | line 808 |
| `hw_sc.build.platform.version` | `4.3.0` | line 279 |
| `ro.build.version.sdk` | `31` | line 815 |
| boot-image (not system) fingerprint | `qti/kona/kona:11/RP1A.200720.011/huawei202408300839:user/dev-keys` | line 768 |

Sanitisation: `ro.boot.serialno` is already `[REDACTED]` in the capture; no serial, MAC, IMEI or other device-unique value is reproduced in this report.

Partition-readback status: **no dtbo-partition hash exists in the corpus.** `device/live.dtb.sha256` contains `NOT AVAILABLE: live.dtb could not be pulled read-only`, and `device/live_dtb_status.txt` records `adb pull /sys/firmware/fdt` → `Permission denied` (no FDT bytes obtained). Therefore this round **does not claim** that the on-device `dtbo` partition matches the extracted package.

Package↔build association: the E1 inventory (`package_inventory.csv`, 43 rows; `REPORT_README.txt`) contains **no build/version metadata**, and no file in the E1 workspace carries `104.3.0.196C00`. The association "E1 package == build 104.3.0.196C00" is therefore **NOT ESTABLISHED** in the existing corpus (UNKNOWN), separate from the untouched question of whether the device `dtbo` partition matches the package.

### 4.1 Live `/rootparam` property-name set (direct structural observation)

E5 `devicetree_base_redacted.txt` (`=== rootparam ===`, captured 2026-11-23T22:53:09) lists 7 property files:

`hardware_version` (stat denied), `huawei,modem_id` (8 B), `name` (10 B = "rootparam"), `phandle` (4 B), `qcom,board_name` (11 B), `qcom,boardid` (stat denied) — **`qcom,product_name` is absent.**

All nine package entries carry `qcom,product_name` in the rootparam payload. The live node therefore has a **property-name set that matches no package entry exactly**. Because values are unreadable (except lengths) and no live FDT bytes were obtained, the cause is UNKNOWN: it could be bootloader post-processing, or a device `dtbo` build different from the extracted package (consistent with `verifiedbootstate=orange`, `flash.locked=0`). This observation is recorded as DIRECT (structure), interpretation UNKNOWN; it directly limits any claim of package↔device byte identity.

`qcom,board_name` is 11 bytes = a 10-character string, which is consistent with both `DBY_W09_VD` and `DBY_W09_VG` and therefore **cannot discriminate** the two variants. `hardware_version` size is not readable and is `SH1DBSLM` in both entries anyway.

---

## 5. Task E — live reserved-memory 39 vs base 37

### 5.1 Correction of the premise

The "39" is **not a child count**. In E5 `devicetree_nodes_redacted.txt` line 69 the entry is:

```
drwxr-xr-x  39 root root  0 2026-11-23 22:50 reserved-memory
```

The second column of `ls -l` is `st_nlink`. For a directory, `st_nlink = number of child directories + 2` (`.` and the parent's entry). The correct reading is therefore **37 child directories**, and ROUND137's phrase "`reserved-memory/`: 39 child directories" (ROUND137 report line 107 and line 232) is a misreading of that column. This is recorded as a correction, not silently edited.

### 5.2 Node-by-node validation of the `st_nlink` reading

Base FDT = `boot_fdt_candidate_0.dtb` (this round's parse). Overlay-added child names = entry 2's resolved `__overlay__` child nodes (entry 8's set is identical).

| Node | live `st_nlink` | implied children (`nlink−2`) | base children | overlay-added names | union expected | match |
|---|---|---|---|---|---|---|
| `/reserved-memory` | 39 | **37** | **37** | 0 (no overlay contains a reserved-memory node or `memory-region` property — 0/9 entries) | 37 | **exact** |
| `/soc` | 527 | 525 | 498 | 28 names, 1 already in base (`spi@880000`) → +27 | 525 | **exact** |
| `/vendor` | 6 | 4 | 1 | `bt_qca6390`, `lbs`, `qcom,battery-data` (+3) | 4 | **exact** |
| `/power_thermalzone` | 3 | 1 | 0 | `sensors` (+1) | 1 | **exact** |
| `/shell_back@0` | 3 | 1 | 1 | 0 | 1 | **exact** |
| `/rootparam` | 2 | 0 | 0 children (base has only `phandle`) | — | 0 | **exact** |
| `/` (root) | not captured | — | 83 child dirs | 0 new root nodes | 83 | live root listing = 83 dirs; the live and base root-directory name sets are identical, 0 added / 0 missing |

Every node for which both a live `st_nlink` and a base-tree child count exist satisfies `nlink − 2 = children`. Entry 8's added-name multiset is identical to entry 2's for `/soc`, `/vendor` and `/power_thermalzone`, so the check cannot and does not discriminate the two entries — it validates the column semantics and the base+overlay relationship.

### 5.3 Answer to the 39-vs-37 question

**No structural delta exists.** Live `/reserved-memory` = 37 children; base FDT = 37 immediate children; overlays add none (all nine contain no `/reserved-memory` node and no `memory-region` property). ROUND24's independent count of 37 (reconciliation paragraph in `_r24/round24-hos43-reserved-memory-and-consumer-map.txt`) is confirmed, and its historical "34" is confirmed as stale.

Per-child **identity** is still unavailable: E5 captured only the parent directory listing, never the names inside `/reserved-memory`. So name-by-name comparison is NOT POSSIBLE from existing evidence — but this is an identity/values limitation, not a count discrepancy:

> **COUNT RECONCILED (37 = 37). NODE IDENTITY / VALUES UNAVAILABLE.**

---

## 6. Corrections and limitations carried forward

| # | Item | Status |
|---|---|---|
| 1 | ROUND137 "`reserved-memory` 39 child directories" | **corrected**: 39 is `st_nlink`; 37 children |
| 2 | ROUND7 `__symbols__` / `__fixups__` / `__local_fixups__` = False | **invalid** (property-vs-node test defect, `Build-Round7-Inventory.py:212`); all three nodes exist in all nine |
| 3 | ROUND7 `rootparam_present` = False | definition-scoped (literal node only); not evidence about fragment targets |
| 4 | ROUND8 entry-8 UFS display list omitted `vdd-hba-fixed-regulator` | minor display omission; binary unchanged |
| 5 | R137 entry-2 hex value | 0x200E stands; 0x206E = 8302 = entry 6 |
| 6 | live `/rootparam` lacks `qcom,product_name` | new DIRECT structural delta, cause UNKNOWN |
| 7 | device `dtbo` partition vs package `dtbo.img` | **UNKNOWN** — no readback, no hash |
| 8 | E1 package build number | **UNKNOWN** — package inventory carries no version field |
| 9 | live FDT bytes / rootparam values | **NOT FOUND** — root-only, pull denied |

---

## 7. Task F — decision and impact statement

**F1. Is entry 2 a stronger variant reference than entry 8?**
**CONDITIONAL YES.** The only direct selection evidence is `ro.boot.dtbo_idx=2` published by the bootloader for that boot. If (a) the device `dtbo` partition content equals the E1 package's `dtbo.img`, and (b) index 2 in that table denotes the same entry in that boot, then the applied DTBO is entry 2 → board-id 8206 / `DBY_W09_VD` / `SH1DBSLM`, which makes entry 2 a strictly better variant reference than entry 8. Conditions (a) and (b) are **not verified**; additionally the live `/rootparam` property set omits `qcom,product_name`, which is direct evidence that the applied overlay's payload is *not* identical to any package entry — so condition (a) is actively in doubt. Entry 8 (`DBY_W09_VG`) has never had direct device evidence; it was and remains a candidate only. Entry 8 is not "wrong", it is **unsupported**.

**F2. Does entry 2's rootparam payload match the current VG overlay?**
**No.** Mismatches: `qcom,board_name` `DBY_W09_VD` vs `DBY_W09_VG`; `qcom,boardid` 8206 vs 8298. Matches: `hardware_version = SH1DBSLM`, `qcom,product_name = DBY-W09`, `huawei,modem_id` generic sentinel. All values above are read directly from the existing entry-2 binary; no replacement value is invented.

**F3. Does entry 2 change any UFS/PMIC property relative to entry 8 that would affect the minimal storage board DTS?**
**No.** 142 of 142 relevant fragments are identical; no UFS host/PHY, regulator, RPMh/RSC, PMIC or power-domain property differs. The only differences are the `rootparam` identity pair and a Wi-Fi pubfile selector, plus a duplicated sensor fragment in entry 8. A minimal storage board DTS derived from entry 8's UFS/PMIC values is equally valid under the entry-2 hypothesis.

**F4. Is the 39-vs-37 memory-node count reconcilable?**
**Yes — it is not a real delta.** 39 is `st_nlink`; children = 37 = base count. Cross-validated on six other nodes. Child *identity* remains unavailable.

**F5. Which previous assumptions must be marked UNKNOWN / stale pending a final FDT?**
- "device variant = `DBY_W09_VG` / entry 8" → **stale / unsupported** (never direct evidence).
- "device `dtbo` partition = E1 package `dtbo.img`" → **UNKNOWN, now in doubt** (live rootparam property set differs by `qcom,product_name`).
- "E1 package == build 104.3.0.196C00" → **UNKNOWN** (no version metadata in package).
- "`dtbo_idx=2` is the vendor-default selection" → **UNKNOWN** (`flash.locked=0`, `verifiedbootstate=orange`; the capture proves the current boot only).
- final live FDT content, `/rootparam` values, live reserved-memory child identities → **UNKNOWN / NOT FOUND**.
- "`reserved-memory` has 39 children" → **stale** (see §5).
- ROUND7's three metadata columns → **stale/invalid**.

**F6. Single smallest additional evidence that would close the variant/rootparam question without a forbidden read?**
One non-privileged read of **`/sys/firmware/devicetree/base/rootparam/qcom,board_name`** in a future authorized capture. That file is world-readable in the existing listing (`-r--r--r--`, 11 bytes — E5 `devicetree_base_redacted.txt`), needs no root, no partition image, no `/sys/firmware/fdt`, and returns either `DBY_W09_VD` or `DBY_W09_VG`, which decides the variant outright. `hardware_version` (a string identical — `SH1DBSLM` — in both entries) and `qcom,boardid` (unreadable) would not add discriminating power; no local artifact in the current corpus can substitute for it.

---

## 8. Scope limits (explicit)

- No device connection, ADB, fastboot, USB, serial, shell, recovery, reboot or bootloader operation occurred.
- No ABL/`dtbo`/`boot`/`ramdisk`/`vbmeta` partition read, no permission bypass, no root, no escalation; denied paths were not retried.
- No firmware download, unpack, extraction or re-extraction; `dtbo.img`/`boot.img` were not opened — only the pre-existing `dtb_work` copies.
- No binary/FDT upload; only this sanitized Markdown.
- No source, DTS, DTBO, Kconfig, config, patch, manifest or test change; no compile/build/package/AVB/sign/flash; ROUND135/R3 Image/Kleaf/host tests were not rerun.
- All E7 files opened read-only; mtimes unchanged (`2026-11-24 01:18`).
- Values reproduced here are limited to variant-identity strings, property names, lengths, small integer cells and symbolic status; no MMIO/reserved-memory coordinates, no personal or device-unique identifiers.

## 9. Deliverable

- `firmware-analysis/round138/round138-dtbo-variant-and-live-fdt-delta-audit.md` (this file), uploaded to branch `firmware-audit-v1`, read back and byte-verified.

**Final outcome: PASS — ENTRY2/8 STATIC COMPARISON COMPLETE**, with the conditionality and UNKNOWN items listed in §6–§7 unchanged and unmitigated. No patched candidate, no source change and no device action was produced or is implied by this report.

---

## Appendix A — base FDT `/reserved-memory` immediate children (37, unit-address suffixes stripped, names only, no `reg`)

`hyp_region, xbl_aop_region, reserved-memory, res_xbl_uefi_log_region, smem_region, removed_region, pil_camera_region, pil_wlan_fw_region, pil_ipa_fw_region, pil_ipa_gsi_region, pil_gpu_region, pil_npu_region, pil_video_region, pil_cvp_region, pil_cdsp_region, pil_slpi_region, pil_adsp_region, pil_spss_region, cdsp_secure_heap, adsp_region, sdsp_region, cdsp_region, cont_splash_region, disp_rdump_region, dfps_data_region, mem_dump_region, sp_region, user_contig_region, rainbow_mem, bootfail_mem, kerneldump, qseecom_region, qseecom_ta_region, secure_display_region, cnss_wlan_region, linux,cma, mailbox_region`

(ROUND24 records that `linux,cma` and `kerneldump` are the only two of the 37 without `/aliases` entries. Unit-address suffixes are omitted here and no `reg` value is reproduced.)

## Appendix B — independent tooling used

Two stdlib-only scripts written for this round, both read-only: `_r138/fdt138.py` (independent FDT/DTBO structure decoder: header validation, node tree, property raw bytes, `__symbols__`/`__fixups__`/`__local_fixups__` as nodes) and `_r138/scan138.py` (identities, per-entry resolution, rootparam matrix, entry-2/8 delta, base reserved-memory enumeration). Neither imports the ROUND3 parser, so agreement with ROUND3/7/8 is a cross-check rather than a restatement. Neither script nor any intermediate JSON was uploaded.
