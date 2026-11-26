# User-Supplied Group Chat Record — DBY-W09 GKI Boot / ABL / Ramdisk Constraints

- Record date: 2026-11-26
- Device/project context: Huawei MatePad 11 (2021), DBY-W09 / SM8250; ACK Android 17 GKI 6.18.33 port.
- Provenance: verbatim conversation excerpt supplied by the user to AI1 (ChatGPT). This is a user-provided chat transcript, not an independently verified technical specification.
- Speaker labels are preserved exactly as supplied.
- Related AI1 review: `kernel-baseline/round136/AI1_ROUND136_SAME_DEVICE_ABL_BOOT_LAYOUT_ADDENDUM.md`

## Verbatim transcript

群主 WQSQW：
这个abl不支持boot自定义dt

群主 WQSQW：
得内嵌

群主 WQSQW：
还有这个ramdisk不能塞boot里

群主 WQSQW：
会重复引导

北极熊：
我去 那他问题还挺多的 我和gpt说一下

群主 WQSQW：
除非你直接跳过ramdisk

群主 WQSQW：
但是那不值得

群主 WQSQW：
而且不优雅

## Provenance and interpretation boundary

This file records only what the user supplied. It does not independently establish:
- what "boot 自定义 dt" means (boot-v2 DTB field, appended Image+DTB, built-in DTB, or DTBO);
- whether "内嵌" means embedded in boot.img or built into the kernel;
- which ramdisk partition/field the ABL consumes or how it handles multiple non-empty ramdisk payloads;
- the exact HOS4.3 ABL build, DTBO selection, or Android 17 boot contract.

Do not turn these statements into code or packaging changes without reconciling them against target HOS4.3 evidence. The same-device public DBY-W09 Linux 7.0 reference is separate evidence and is not automatically the HOS4.3 Android 17 boot specification.
