# ROUND67 — HOS4.3 DBY-W09 rootparam-only DTBO candidate evidence reconciliation

**Date:** 2026-11-25  
**Owner:** Primary AI, report-to-source reconciliation  
**Scope:** existing ROUND19 HOS4.3 DTBO audit plus the already-referenced public same-device Linux rootparam overlay. No local firmware re-extraction, no DTS edit, no DTBO compilation, no device.

## 1. Executive result

The HOS4.3 stock DTBO entries all populate the same base `/rootparam` node shape with five properties. The nine entries differ in board-variant identity values and a small number of product-specific fragments; they do not differ in the rootparam node structure. The project should therefore use a **minimal rootparam-only overlay**, not copy the 143–145-fragment stock DTBO onto the minimal ACK base DTS.

The public same-device Linux reference `svesnav/linux-dby-w09/dby-w09-rootparam.dtso` describes precisely this design and records that Huawei ABL refused a DTBO entry that did not populate `/rootparam` like stock overlay 8 (found by bisection in that project). Its variant data is VG / board-id 0x206a. ROUND19's independent HOS4.3 DTBO inventory contains a matching entry 8:
- header board-id `0x206a 0x00`;
- variant VG / `DBY_W09_VG`;
- `hardware_version = "SH1DBSLM"`;
- `qcom,boardid = <0x08 0x02 0x09 0x08>`;
- `product_name = "DBY-W09"`;
- `huawei,modem_id` sentinel in every entry.

This is a strong **VG candidate**, not proof that this particular tablet's ABL selects entry 8. Other DBY-W09 variant ids exist. Do not silently promote VG to the runtime selection without same-device/same-boot evidence.

## 2. Exact HOS4.3 rootparam findings from ROUND19

Source report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/firmware-audit-v1/firmware-analysis/round19/round19_hos43_boot_ramdisk_avb_dtbo_audit.txt

- Base FDT has a root `/rootparam` node with phandle only and no properties.
- Every one of the nine DTBO entries has exactly one fragment targeting `&rootparam`.
- That fragment writes the same five property names:
  `qcom,boardid`, `qcom,board_name`, `qcom,product_name`, `hardware_version`, `huawei,modem_id`.
- `qcom,product_name` is `"DBY-W09"` in all nine.
- `huawei,modem_id` uses the same opaque phandle-plus-zero sentinel in all nine.
- The board-id / board_name / hardware_version / qcom,boardid tuple distinguish the variants:
  - 0x2008 VA / DBY_W09_VA / SH0DBSLM
  - 0x2068 VF / DBY_W09_VF / SH1DBSLMA
  - 0x200e VD / DBY_W09_VD / SH1DBSLM
  - 0x2010 VC / DBY_W09_VC / SH1DBSLM
  - 0x200a VB / DBY_W09_VB / SH1DBSLM
  - 0x202e VI / DBY_W09_VI / SH1DBSLMA
  - 0x206e VH / DBY_W09_VH / SH1DBSLM
  - 0x2030 VE / DBY_W09_VE / SH1DBSLM
  - 0x206a VG / DBY_W09_VG / SH1DBSLM

The stock entries have 143–145 fragments. Their other fragments target many Huawei/vendor-only storage, panel, camera, Wi-Fi/BT, audio, PMIC, USB and display nodes that are absent from the minimal ACK board DTS. Applying a full stock entry to that minimal DTS is therefore not a valid substitution for a rootparam-only overlay.

## 3. Public same-device overlay cross-reference

Public file:
https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso

The file has:
- root `model = "Huawei MatePad 11 (2021) DBY-W09"`;
- root `compatible = "huawei,dby-w09", "qcom,sm8250"`;
- root `qcom,board-id = <0x206a 0>`;
- a single fragment targeting `<&rootparam>`;
- the VG rootparam values listed in section 2, including `huawei,modem_id = <0xffffffff 0x00>`.

Its own comment says ABL copies the root compatible/identity properties into the base FDT and the overlay should preserve `qcom,sm8250` because msm-mdss obtains UBWC configuration from the machine compatible. It further says ABL rejected a DTBO entry that failed to fill `/rootparam` like stock overlay 8, found by bisection.

This is a same-device public Linux reference, not the private Android 17 DerpFest implementation and not proof for the exact HOS4.3 ABL binary. Its structural values are independently corroborated by the local HOS4.3 ROUND19 table for entry 8, but its ABL behavior narrative remains a cross-reference.

## 4. Current project gap and safe next action

The current main branch `dts/` directory contains:
- `dby-w09-ack18-board.dts.draft`;
- `README.md`.

Although the README documents a separate `dby-w09-ack18-rootparam.dtso.draft`, that file is not currently present in the main-branch directory listing. No rootparam overlay artifact has yet been compiled.

Safe next sequence:
1. Use ROUND22's local report to establish the available rootparam draft/work-copy state and reconcile its source blob.
2. Create or restore a **VG-only candidate** overlay only if the device variant is confirmed as VG or explicitly maintain separate candidates for the other variants.
3. Validate that the overlay contains only the root properties and the one `rootparam` fragment; do not include the other stock 142–144 fragments.
4. Compile with dtc `-@` and inspect the DTBO header/entry metadata in a temporary directory.
5. Validate the final ABL DTBO selection contract separately; a successful dtc compile does not prove ABL selection or rootparam acceptance.

No candidate was created in this round because the runtime variant is unknown.

## 5. Status

- HOS4.3 rootparam property names and nine variant values: PASS from ROUND19.
- VG 0x206a candidate matches the public same-device overlay values: PASS as a cross-reference.
- Actual selected runtime variant: UNKNOWN.
- Main-branch rootparam overlay file: NOT PRESENT in current directory listing.
- dtc/DTBO compile of the project rootparam overlay: NOT RUN.
- ABL acceptance on current HOS4.3 build: NOT RUN.
- No source/DTS/DTBO/firmware/device changes.
