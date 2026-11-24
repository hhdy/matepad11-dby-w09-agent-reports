# DBY-W09 ACK 6.18 DTS draft

This directory contains a **review-only source draft** for the initial DBY-W09 board DTS and its minimal ABL rootparam overlay.

Files:
- `dby-w09-ack18-board.dts.draft` — minimal SM8250 board identity + PM8150 UFS rails + UFS/QMP enablement.
- `dby-w09-ack18-rootparam.dtso.draft` — separate minimal DBY-W09 board identity overlay.

## Important integration rule

Do **not** apply the stock HOS4.3 DTBO entry 8 to this minimal base. ROUND8 resolved 145 stock fragments targeting many nodes absent from this minimal DTS. The source reference for the minimal one-fragment ABL rootparam overlay is the same-device svesnav project:
https://github.com/svesnav/linux-dby-w09/blob/main/dby-w09-rootparam.dtso

The current overlay omits `huawei,modem_id` pending review of whether ABL requires that property and what safe value/source is appropriate. Therefore this overlay is not yet a boot-ready replacement.

## Current limits

- No source sync, dtc invocation, dt-schema validation, compile, boot-image packing or hardware test has been done.
- PMIC input topology (`vph_pwr` / `apps_rsc`) is provisional and must be reconciled with the exact HOS4.3 PMIC facts and ACK binding.
- No UART console, reserved-memory, panel, THP, WLAN, BT, audio, camera, USB-C or DP nodes are enabled.
- Panel `ACTIVE_PROFILE=UNKNOWN`.
- The stock HOS4.3 ramdisk remains unread (ROUND10 BLOCKED); module ordering is unknown.
- These files use the suffix `.draft` deliberately. Do not rename them into build input or flash them.

## Source and evidence basis

- Google ACK `android17-6.18` SM8250 DTSI.
- Local ROUND9 UFS regulator closure.
- Local ROUND8 overlay target map and /rootparam identity.
- Public same-device Linux DTS / rootparam overlay, used as cross-reference, not copied as a complete Android/ACK solution.
