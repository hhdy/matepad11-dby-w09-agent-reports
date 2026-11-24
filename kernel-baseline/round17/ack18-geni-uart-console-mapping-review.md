# ROUND17 — ACK 6.18 GENI UART / console mapping review

Date: 2026-11-24

Status: public ACK source review and DTS/config comment correction only. No HOS4.3 runtime access, no DTB extraction, no dtc, no schema validation, no Kconfig resolution, no build, no device test.

## 1. Existing HOS4.3 boot evidence

ROUND10's sanitized boot-cmdline report lists the keys androidboot.console and earlycon. The report records only property keys and intentionally omits values. It does not establish:
- a kernel console= argument;
- the stdout-path target used by OF earlycon;
- which physical UART pins are routed to a debug header or to the Bluetooth controller;
- whether the vendor ttyMSM0 is backed by the same GENI node used by the public Linux 7.0 port.

The key androidboot.console=ttyMSM0 is an Android boot property and must not be conflated with a proven upstream Linux console=ttyMSM0 setting. earlycon without a verified matching debug-UART OF node/route is insufficient to select a board UART.

## 2. Exact ACK android17-6.18 SM8250 DTSI nodes

The pinned ACK branch defines two distinct UART node types under qupv3_id_0:

| Label | Compatible | Register block | Default pinctrl | Upstream role |
|---|---|---:|---|---|
| uart2 | qcom,geni-debug-uart | 0x00988000 | qup_uart2_default (GPIO117/118) | dedicated GENI debug-console / earlycon candidate |
| uart6 | qcom,geni-uart | 0x00998000 | qup_uart6_default (GPIO16–19) | regular GENI UART, possible Bluetooth serdev endpoint |

Both nodes and the parent qupv3_id_0 wrapper are disabled in the SoC DTSI by default. Both UART children also reference RPMh CX performance domain, the QUP OPP table and interconnects.

Source:
https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/arch/arm64/boot/dts/qcom/sm8250.dtsi

## 3. Exact ACK GENI serial driver naming and matching

The pinned ACK qcom_geni_serial.c has separate console and regular UART drivers:

- qcom,geni-debug-uart selects the console path; its UART driver name is ttyMSM, and it is the compatible used by OF_EARLYCON_DECLARE(qcom_geni, ...).
- qcom,geni-uart selects the regular UART path; its UART driver name is ttyHS.
- The probe obtains a serial alias ID from the device tree, but the alias only provides the line number within that driver's own namespace. It does not change a normal qcom,geni-uart node into the debug-console driver.

Kconfig:
- QCOM_GENI_SE — common GENI Serial Engine wrapper support.
- SERIAL_QCOM_GENI — normal GENI UART driver; depends on QCOM_GENI_SE.
- SERIAL_QCOM_GENI_CONSOLE — console and earlycon support; depends on SERIAL_QCOM_GENI and selects SERIAL_CORE_CONSOLE / SERIAL_EARLYCON.

Sources:
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/tty/serial/qcom_geni_serial.c
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/tty/serial/Kconfig
- https://github.com/aosp-mirror/kernel_common/blob/android17-6.18/drivers/soc/qcom/Kconfig

Consequently, the same-device Linux reference's serial0=uart6 does not prove uart6 becomes ttyMSM0 under ACK 6.18: it is an ordinary qcom,geni-uart, whose driver namespace is ttyHS. The public same-device DTS also attaches a Bluetooth child beneath uart6, reinforcing that this node must not be casually repurposed as the kernel debug console.

Same-device public cross-reference:
https://github.com/svesnav/linux-dby-w09/blob/main/sm8250-huawei-dby-w09.dts

## 4. Storage-first DTS decision

The minimal ACK board DTS continues to leave all UART nodes disabled:
- Do not enable uart6 as the console based only on androidboot.console=ttyMSM0.
- Do not enable uart2 until its physical GPIO117/118 routing and intended board use are corroborated against HOS4.3 evidence.
- Do not add serial0=uart6 as a shortcut for ttyMSM0.
- Do not attach Bluetooth to UART6 until the actual HOS4.3 Bluetooth UART mapping, chipset/firmware requirements and userspace contract are confirmed.

When a console path is justified later, evaluate uart2 (debug UART) and add the GENI wrapper, pinctrl and required clock/RPMhPD/interconnect dependencies together. The Kconfig candidates are QCOM_GENI_SE=y, SERIAL_QCOM_GENI=y, and SERIAL_QCOM_GENI_CONSOLE=y, subject to the exact pinned Kconfig resolution.

For the first internal-UFS enumeration milestone, these UART/console options remain deferred and are not added to the storage-first fragment.

## 5. Updated draft files

Branch ack18-dby-w09-dts-draft:
- dts/dby-w09-ack18-board.dts.draft — now distinguishes uart2 debug console from regular uart6; neither is enabled.
- config/dby-w09-ack18-storage-first.fragment.draft — records the Kconfig candidates as a deferred feature rather than making them part of storage-first.
- dts/README.md — documents the ACK ttyMSM / ttyHS distinction and the unresolved physical mapping.

Main branch:
- ROUND17 added.
- ROUND16 / ROUND13 / ROUND14 and the project entry point link to this review.
- No local Agent task is issued by this source-only review.

## 6. Verification state

| Check | Status |
|---|---|
| ROUND10 HOS4.3 boot property key inventory reviewed | COMPLETE (keys only; no ramdisk) |
| ACK uart2 debug-UART node / GPIO117–118 source review | COMPLETE |
| ACK uart6 regular GENI-UART node / GPIO16–19 source review | COMPLETE |
| ACK driver ttyMSM vs ttyHS / earlycon match table | COMPLETE |
| Same-device Linux 7.0 uart6 Bluetooth-child reference | SOURCE REVIEWED |
| HOS4.3 physical UART pin function / debug header route | UNKNOWN |
| HOS4.3 Bluetooth UART path exact mapping | UNKNOWN |
| HOS androidboot.console / earlycon to ACK OF node equivalence | NOT_ESTABLISHED |
| UART/console DTS node enablement | NOT_RUN / DEFERRED |
| Kconfig resolution / compile / boot | NOT_RUN |

## 7. Next engineering step

Continue GPT-side review of the remaining storage-first DTS/Kconfig details and the legacy boot packaging path. No local Agent task is required for this source-only decision. Revisit UART only after a genuinely new HOS4.3 or board-routing fact is available; do not rerun existing FDT work simply to reproduce ROUND11/ROUND9.
