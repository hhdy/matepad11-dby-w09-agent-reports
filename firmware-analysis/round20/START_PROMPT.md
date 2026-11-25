Execute ROUND20 from:
firmware-analysis/round20/AGENT_TASK.md on main.

Read the whole task first. This is an offline, read-only audit of the existing ROUND18 Image and existing ROUND2 HOS4.3 boot.img kernel payload. Use only already-installed WSL tools and the pinned ACK checkout. No public-repository research.

Critical facts:
- ROUND18 Image already compiled: /home/kerneldev/work/matepad11/ack-6.18.33-round18/bazel-bin/common/dby_w09/Image
- sibling outputs: .config, System.map, vmlinux
- Image size 44,820,992 bytes; SHA-256 is recorded in ROUND18 report.
- ROUND19 established base DTB /memory/reg is all zero and none of the nine DTBOs supplies memory or linux,uefi-* properties.
- User confirms private same-device Android 17 DerpFest success precedent; its author will not open-source it. Do not search for their code or ask again.

Do not redeploy WSL, run repo init/sync, download source/toolchains, reapply patches, rerun Kconfig, rebuild Image, modify source/config/firmware, or touch device. No ADB/fastboot/unlock/root/flash/partition write/boot-image repack/sign/deploy.

Inspect EFI_STUB / PE-COFF capability, exact ACK memory initialization and EFI-stub source routes, stock boot kernel compression format, deterministic raw/gzip size and boot-v2 capacity scenarios, and built-in storage driver artifact state. All temporary files stay under a dedicated ROUND20 temp directory; existing outputs remain byte-identical.

Upload only firmware-analysis/round20/round20_efi_stub_memory_handoff_and_boot_payload_compatibility.txt to firmware-audit-v1. No binaries. Stop after one report.
