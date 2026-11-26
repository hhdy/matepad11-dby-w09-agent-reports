You are WorkBuddy Window A (1号 Agent).

Execute:
firmware-analysis/round157/WORKBUDDY_A_ROUND157_PRIMARY_KERNEL_BUILD_AND_ABL_FINAL_PROOF_TASKBOOK.md

Use your own ROUND154 RAM-patched source tree and ROUND155 local ABL binaries. Run the primary full kernel build with the established //common:dby_w09 target, verify the final built DTB, and close the exact /memory write primitive, overlay-fixup atomicity, and ABL/libavb signature/descriptor path as far as the binary allows.

Publish both:
- firmware-analysis/round157/WORKBUDDY_A_ROUND157_PRIMARY_KERNEL_BUILD_AND_ABL_FINAL_PROOF_REPORT.md
- firmware-analysis/round157/AI1_R157_RAM_DTS_PATCH.patch

Keep all raw binaries and full local logs on the host. No device, ADB, partition operation, boot image packaging, flash, reboot, fastboot or recovery. Read back both artifacts and verify them, then STOP.