# ROUND139 — WorkBuddy Agent taskbook: HOS4.3 PMIC/UFS and boot/AVB static evidence closeout

- Executor: WorkBuddy Agent (local executor only; not AI2)
- Dispatched by: AI1 (ChatGPT)
- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Kernel: ACK android17-6.18.33_r00, pinned commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Candidate tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- Mode: offline, read-only, existing artifacts only
- Purpose: advance the two unclosed first-boot tracks identified by ROUND136 as B/C/D. This task does not authorize a device test or boot package build.

## 0. Role and execution order

This is a WorkBuddy Agent task, not an AI2 task. It may be executed after ROUND138 has finished if the local workspace is busy; it must not modify or overlap any source changes (none are authorized). ROUND138 remains the authority for entry-2/entry-8 DTBO variant comparison and the 39-vs-37 reserved-memory name reconciliation.

Use only already-existing local extracted HOS4.3 package files, decompiled FDT/DTBO work copies, parser outputs, existing device text captures, and existing reports cited below. Do not re-extract firmware to recover missing inputs. If a named input is absent, mark that subtask BLOCKED rather than searching arbitrary drives.

## 1. Authorized evidence set

Use only the already-identified workspace and evidence:
- ROUND137 E1: existing HOS4.3 extracted-package workspace <workspace>/MatePad11_HOS43_LocalCheck_20261123_230849;
- ROUND137 E5: existing device text/metadata under <workspace>/Agent_Round2_Report/device;
- ROUND137 E7: existing FDT/DTBO work copies under <round3-work>/dtb_work;
- existing parser outputs such as logs/boot_headers.json, logs/ramdisk_inventory.json, logs/dtbo_audit.json, if present;
- existing reports: ROUND13 PM8150 mode/DRMS census, ROUND21 UFS/PMIC overlay audit, ROUND24 reserved-memory audit, ROUND51 UFS/PM8150L regulator findings (if present), ROUND64 final-FDT/PM8150 input-parent evidence, ROUND136 AI2 audit, ROUND137 AI1 review, and the completed ROUND138 report if available.

Do not enumerate arbitrary personal directories. Do not search cloud drives or download anything.

## 2. Workstream B — PM8150 / PM8150L physical input topology

### B1. Re-establish exact UFS rail consumers
From the existing HOS4.3 base FDT and all nine existing DTBOs:
- resolve the UFS host at /soc/ufshc@1d84000 and UFS PHY at /soc/ufsphy_mem@1d87000 through phandles/symbols;
- enumerate each supply property and its resolved regulator provider;
- identify whether existing evidence maps UFS consumers to PM8150 L5/L6/L9/L17/S4 and PM8150L S8;
- report base-tree and overlay changes separately. If ROUND138 provides entry-2/entry-8 deltas, cite those rather than duplicating or overriding them.

### B2. Search only explicit physical-parent evidence
For the identified rails and provider nodes, inspect only existing decompiled files/parser outputs for:
- vin-supply, vdd-s*-supply, vph-pwr-supply, and other explicit input-supply properties;
- regulator parent phandles and resolved parent-node paths;
- regulator constraints, voltage/current ranges, operating modes and status;
- provenance and meaning of qcom,regulator-type, qcom,supported-modes and vendor current-threshold properties.

Keep three concepts separate:
1. physical electrical input parent;
2. Qualcomm RPMh/ARC corner or level relationship;
3. proxy/consumer-side supply dependency.

A missing physical parent must remain UNKNOWN. Do not convert ARC edges or qcom,vccq-parent-supply into an electrical vin-supply. Do not invent vph_pwr, vdd-s1..s10, fixed regulators, voltages or current limits.

### B3. UFS performance-domain evidence
Record existing HOS4.3 UFS host/PHY references to:
- power-domains, operating-points-v2, required-opps, interconnects, clocks and resets;
- any RPMh power-domain provider/corner values and consumer-to-domain association;
- any existing CMD DB, ARC or proxy relationship evidence already captured in the local corpus.

Compare with pinned ACK behavior:
- SM8250 RPMHPD_MMCX selects the plain MMCX descriptor with no parent pointer;
- the CX descriptor may have a parent pointer to MX, but that does not make MMCX inherit MX;
- fixed ACK UFS host code does not consume downstream qcom,vccq-parent-supply as a physical-parent mechanism.

Do not claim runtime corner equivalence from matching numeric corner labels. Do not infer actual runtime RPMh votes from static DTS alone.

### B4. Required output
Produce:
- UFS consumer → supply → regulator-provider table;
- physical parent findings per rail with DIRECT / CONDITIONAL / UNKNOWN / NOT FOUND labels;
- UFS OPP/domain/ICC dependency table;
- exact differences between HOS4.3 static declarations and pinned ACK support;
- smallest missing authoritative artifact for each unresolved rail/corner question.

Explicitly reconcile ROUND64's result that no board-specific schematic/power tree or explicit physical input parent was present in the inspected corpus. Do not repeat ROUND64 as a new successful discovery.

## 3. Workstream D — boot-v2 / independent ramdisk / DTBO / AVB / recovery evidence

### D1. Existing boot-layout artifacts
Using only existing extracted files and parser outputs:
- verify the already-recorded boot header version, page size, kernel/ramdisk/DTB section offsets and sizes;
- verify independent ramdisk.img header/version/size and distinguish it from the boot-v2 embedded stock ramdisk;
- verify DTBO container version, entry count and table metadata;
- retain original inventory and hashes as evidence; do not alter any image.

Do not assume the same-device HOS4.2 Linux 7.0 project's repack strategy is the HOS4.3 ABL contract. It is a reference only.

### D2. AVB chain and anomaly
Using an already-installed parser/tool only (do not install tools):
- inspect existing vbmeta*.img metadata and report which descriptors/chains cover boot, ramdisk, dtbo and other relevant partitions;
- report algorithm, rollback-index location/value presence, public-key metadata presence, descriptor types and referenced partition names, but do not publish key material or sensitive signing data;
- independently check the recorded vbmeta_cust.img size/footer/descriptor anomaly against the existing file and parser output;
- distinguish malformed file, truncated extraction, parser interpretation issue and unresolved state. Do not select an explanation without direct evidence.

No signing, verification-key substitution, vbmeta regeneration, disable-verity changes, footer repair, descriptor editing or image patching is allowed.

### D3. ABL and partition-consumption limits
State separately what is and is not known about:
- whether HOS4.3 ABL accepts a replacement boot-v2 DTB;
- whether it consumes the independent ramdisk partition as expected;
- which exact DTBO entry is selected;
- whether it applies a /rootparam overlay and how;
- whether boot preserves or replaces the embedded stock ramdisk.

The actual ABL binary/version is not in the known corpus. Do not substitute XBL/TZ/UEFI Secure App for ABL. Cite ROUND137 and ROUND138 evidence and keep unresolved ABL policy items UNKNOWN.

### D4. Recovery / reversibility
From existing evidence only, inventory:
- original partition backup images already available;
- known partition sizes and image hashes;
- documented recovery/restore route, if any;
- existing evidence about fastboot boot refusal or recovery entry.

Do not test a recovery route. Distinguish “documented by a same-device public HOS4.2 project” from “verified on this HOS4.3 tablet.” If no tested HOS4.3 recovery route and no complete original-partition backup set exist, mark recovery readiness BLOCKED.

### D5. Required output
Produce a boot/ramdisk/DTBO/AVB matrix with DIRECT / CONDITIONAL / UNKNOWN / NOT FOUND labels; a partition-backup inventory; vbmeta_cust anomaly analysis; and the smallest evidence needed to prove a reversible HOS4.3 test route.

## 4. Strict prohibitions

- No device connection, ADB, fastboot, recovery, USB, serial, reboot or bootloader interaction.
- No ABL partition access, no /sys/firmware/fdt retry, no permission bypass, root or privilege escalation.
- No new firmware download, extraction or re-extraction.
- No raw firmware/binary/key/signature/digest upload; only sanitized Markdown and optional safe text metadata.
- No source, DTS, DTBO, Kconfig, config, patch, manifest or branch changes outside this report.
- No compilation, build, boot-image packaging, signing, AVB operation, flashing or partition write.
- No rerunning ROUND135/R3 or changing the pinned 23-patch candidate.
- Do not declare first-boot readiness from static inspection.

## 5. Output, upload and stop

Create:
firmware-analysis/round139/round139-hos43-pmic-ufs-and-boot-avb-static-evidence-audit.md

The report must contain:
- input inventory and hashes of text artifacts only where safe;
- separate B and D workstream outcomes;
- exact paths/properties supporting each DIRECT claim;
- explicit UNKNOWN / NOT FOUND statements;
- reused evidence references and any inconsistencies;
- a concise “what this round actually closed” versus “what still needs an authoritative external artifact or explicit user-authorized device evidence” section;
- final outcome:
  - PASS — STATIC EVIDENCE INVENTORY COMPLETE
  - PARTIAL — STATIC INVENTORY COMPLETE WITH INPUT LIMITATIONS
  - BLOCKED — REQUIRED EXISTING ARTIFACTS MISSING

Upload only this sanitized Markdown report to firmware-analysis/round139/ on the existing firmware-audit-v1 branch. Read it back and verify byte identity. Then stop. No follow-on task, device test, package, build or flash is authorized by this taskbook.
