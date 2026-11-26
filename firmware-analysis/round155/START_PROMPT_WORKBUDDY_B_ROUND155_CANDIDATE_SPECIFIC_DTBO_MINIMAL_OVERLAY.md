You are WorkBuddy Window B (2号 Agent), a separate WorkBuddy chat window from Window A. Both agents use WorkBuddy.

Execute:
firmware-analysis/round155/WORKBUDDY_B_ROUND155_CANDIDATE_SPECIFIC_DTBO_MINIMAL_OVERLAY_TASKBOOK.md

Use only your own isolated workspace. Determine whether the RAM-patched candidate can use a no-overlay first-boot path or needs a candidate-specific minimal DTBO. Test scratch outputs with fdtoverlay. The stock Entry 2 overlay is proven incompatible; do not keep retrying it or assume -@ fixes it.

No source branch changes, full kernel build, device/ADB, partition read/write, flash, reboot, fastboot or recovery.

Publish:
firmware-analysis/round155/WORKBUDDY_B_ROUND155_CANDIDATE_SPECIFIC_DTBO_MINIMAL_OVERLAY_REPORT.md

Read back and verify, then STOP.