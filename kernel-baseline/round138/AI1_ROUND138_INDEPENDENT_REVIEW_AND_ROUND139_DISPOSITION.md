# AI1 ROUND138 Independent Review and ROUND139 Disposition

- Reviewer: AI1 (ChatGPT)
- Date: 2026-11-26
- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel: ACK android17-6.18.33_r00, pinned 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Candidate tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- Agent report reviewed: firmware-analysis/round138/round138-dtbo-variant-and-live-fdt-delta-audit.md
- Agent branch: firmware-audit-v1
- Report blob: 2d712e01f96b724058122118122de2b9c10557dd

## 1. Overall review result

**ACCEPTED — PASS for the scoped static comparison.**

The report provides a coherent independent comparison of the pre-existing DTBO binary work copies and E5 text captures. It does not claim the current device DTBO partition is byte-identical to the extracted HOS4.3 package, does not claim the extracted package belongs to build 104.3.0.196C00, and does not claim to have read the final post-ABL FDT. Those limitations are material and correctly preserved.

This acceptance is limited to static evidence comparison. It is not ABL validation, final-FDT validation, electrical topology proof, runtime UFS validation, boot-package validation, or first-boot authorization.

## 2. Accepted findings

### 2.1 Entry 2 / entry 8 identity

- Entry 2 file identity matches ROUND137: 329,240 bytes, SHA-256 0633a6fbeebbad45c0f5572faf222c779e1cd51d253a6ef8282592a730ba3c8b.
- Entry 8 file identity matches ROUND137: 329,352 bytes, SHA-256 a7946352a86ab6e47b5ee79d84e5d6c4cf4e548c96b0221cec909f32ebd9d21d.
- Base FDT candidate 0 identity also matches ROUND137.
- Entry 2 raw overlay identity is VD / board-id 8206 / 0x200E; entry 8 is VG / board-id 8298 / 0x206A.
- The DT table id/rev values are all zero and must not be mistaken for board identity.

Disposition: **entry 2 is the stronger current variant reference only conditionally**, because the device boot property capture says ro.boot.dtbo_idx=2, but the on-device dtbo partition and package-to-build identity remain unverified. Entry 8/VG is unsupported as the current device variant and the previous VG assumption is stale.

### 2.2 /rootparam semantics and ROUND7/8/137 discrepancy

Accepted distinctions:
1. No raw overlay contains a literal /rootparam node.
2. Every one of the nine overlays contains one __fixups__ reference for the base-tree symbol rootparam.
3. Each such fragment target resolves against the base FDT symbol to /rootparam.
4. The fragment payload carries the variant identity fields.
5. DT table id/rev/custom fields are separate and are not a substitute for board identity.

ROUND7 rootparam_present=False is correct only for its literal-node-path test; it did not test whether a fragment targeted the base rootparam node. ROUND7's three metadata booleans for __symbols__, __fixups__, and __local_fixups__ are invalid because the implementation tested property names where these are overlay-root child nodes. ROUND8 entry-8 fragment@143 target resolution is confirmed. ROUND137's all-nine target statement is confirmed.

No report was silently overwritten; the semantics are now explicitly reconciled.

### 2.3 Entry 2 and entry 8 UFS / PMIC overlay equivalence

Accepted:
- 144 fragments in entry 2 and 145 in entry 8; all targets resolved.
- The entries have the same 73-target set.
- All UFS, regulator, PMIC, RPMh/RSC and power-domain relevant payloads are identical.
- The sole additional entry-8 fragment is a duplicate sensor fragment, not an additional hardware target.
- The material differences are the two rootparam variant identity fields and the Wi-Fi pubfile selector.

Disposition: the entry-2 vs entry-8 variant ambiguity does **not** change the current minimal storage DTS's static UFS/PMIC property basis. This does not prove the static UFS supplies have physical input parents or that runtime MMCX/MX votes are sufficient.

### 2.4 ro.boot.dtbo_idx provenance and live rootparam limitation

Accepted direct capture:
- ro.boot.dtbo_idx=2 at E5 adb_getprop_redacted.txt line 753;
- capture timestamp 2026-11-23T22:52:16.4241436+08:00;
- flash.locked=0 and verifiedbootstate=orange appear in the same capture as context.

Unresolved:
- no on-device dtbo partition hash/readback exists;
- E1 package inventory does not associate the extracted package with build 104.3.0.196C00;
- live rootparam property-name listing lacks qcom,product_name although each static package entry contains it;
- live rootparam values and final FDT bytes remain unavailable.

The absence of qcom,product_name is a direct structural delta. Its cause is UNKNOWN; it is not by itself proof of which ABL transformation or DTBO package produced the live node.

The report identifies /sys/firmware/devicetree/base/rootparam/qcom,board_name as a potentially non-privileged discriminator. This is a useful narrow evidence candidate, but **it is still a new device read**. No Agent may connect to the tablet or collect it until the user is explicitly informed and authorizes that device-access step. Do not silently bundle it into ROUND139.

### 2.5 Reserved-memory count correction

Accepted correction:
- E5's ls -l second column 39 is directory st_nlink, not the number of child directories.
- For kernfs directories, the pinned ACK implementation explicitly sets link count to kn->dir.subdirs + 2 in fs/kernfs/inode.c::kernfs_refresh_inode(). Source: https://github.com/aosp-mirror/kernel_common/blob/8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a/fs/kernfs/inode.c
- Therefore st_nlink=39 corresponds to 37 child directories under this kernfs interpretation.
- ROUND24 independently enumerated 37 base /reserved-memory direct children.
- ROUND138 reports all 9 DTBOs add no /reserved-memory node and no memory-region property.

Disposition: the earlier ROUND137 statement "39 child directories" is corrected and must no longer be repeated. The count is reconciled as 37 vs 37. However, the actual reserved-memory child-name/value listing in the live tree and the final post-ABL RAM reg tuples remain unavailable. Matching the count does not prove matching reservation ranges or memory handoff.

The pinned ACK source provides the exact kernfs rule used for the interpretation. Because the E5 listing came from the stock HOS4.3 device environment, retain this as an implementation-semantics interpretation unless the stock kernel source/build identity is independently pinned; the count is nevertheless strongly reconciled by the captured st_nlink and independent base-FDT enumeration.

## 3. Corrections to project state

Update these items across future reports:
- "Current variant is VG / entry 8" → stale / unsupported.
- "Current variant is VD / entry 2" → conditional, supported by dtbo_idx=2 but not proved against the on-device partition.
- "E1 package matches build 104.3.0.196C00" → UNKNOWN.
- "Live reserved-memory has 39 children" → incorrect; report 37 implied children from st_nlink=39.
- "There is a 39-vs-37 reserved-memory structural delta" → resolved as no count delta; live child identities and values remain unavailable.
- "Entry2-vs-entry8 UFS/PMIC variant delta blocks the minimal storage DTS" → no longer a blocker; their relevant static payloads are identical.
- "Final FDT / ABL RAM handoff is closed" → still BLOCKED. Neither exact memory tuples nor the actual ABL entry route are established.

## 4. Updated first-boot gate matrix

| Gate | Updated status | Reason |
|---|---|---|
| ROUND135 R3 Image / DTB / Kleaf offline validation | PASS — BUILD/DTB INTEGRATION ONLY | Already accepted; no rebuild needed |
| Entry2/8 DTBO static identity and overlay comparison | PASS — STATIC COMPARISON | ROUND138 accepted |
| Current hardware variant | CONDITIONAL / PARTIAL | dtbo_idx=2 points to entry2 only if on-device DTBO table matches E1 |
| rootparam payload on live device | UNKNOWN | qcom,product_name absent; values/FDT not readable |
| Reserved-memory child count | RECONCILED: 37 | st_nlink 39 implies 37; ROUND24 base has 37 |
| Final ABL FDT / RAM tuples / entry route | BLOCKED | No final post-ABL FDT bytes or entry-route trace |
| PMIC physical input-parent topology | BLOCKED | ROUND64 found no authoritative board-specific power tree or explicit parents in the inspected corpus |
| UFS runtime MMCX/MX / CMD DB vote equivalence | BLOCKED | Static overlay equality does not prove runtime vote propagation |
| boot-v2 / independent ramdisk / DTBO / AVB / recovery route | BLOCKED | ABL contract and verified reversible HOS4.3 recovery route remain unproven |
| First real-device boot | NOT AUTHORIZED / NOT RUN | Required gates and reversible recovery still unresolved |

## 5. ROUND139 execution disposition

ROUND139 already exists on the AI1 branch as:
- firmware-analysis/round139/AGENT_TASKBOOK_HOS43_PMIC_UFS_AND_BOOT_AVB_AUDIT.md
- firmware-analysis/round139/START_PROMPT_HOS43_PMIC_UFS_AND_BOOT_AVB_AUDIT.md

Proceed with ROUND139 now that ROUND138 is complete. WorkBuddy Agent must use ROUND138's accepted results rather than redoing DTBO entry-2/entry-8 or the reserved-memory count:
- entry-2/entry-8 UFS/PMIC overlay property deltas = none;
- current variant = conditional entry2 reference;
- live rootparam qcom,product_name property absent, cause unknown;
- reserved-memory count = 37, not 39.

ROUND139 remains offline/read-only only. The new qcom,board_name read suggested in ROUND138 is not included in this authorization. No device access, ADB/fastboot, root, FDT retry, build, packaging, AVB modification or flashing is authorized.

## 6. Final AI1 disposition

**ROUND138 ACCEPTED. ROUND139 MAY PROCEED.**

This closes the static DTBO-variant comparison and corrects the reserved-memory count interpretation. It does not close the final memory handoff, PMIC power-parent, UFS runtime performance-domain, boot/AVB/recovery or first-boot gates.
