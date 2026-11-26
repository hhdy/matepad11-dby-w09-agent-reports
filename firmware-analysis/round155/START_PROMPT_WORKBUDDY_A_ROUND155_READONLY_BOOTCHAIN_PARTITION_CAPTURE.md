You are WorkBuddy Window A (1号 Agent), a separate WorkBuddy chat window from Window B.

Execute:
firmware-analysis/round155/WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE_TASKBOOK.md

Use the existing ADB/root connection. This task is strictly read-only: extract exact ABL/XBL and relevant boot-chain partition copies to the local host, verify byte counts and SHA-256 with independent reads, preserve verified rollback copies, and analyze ABL/AVB offline.

Do not read userdata, persist, metadata, frp, devinfo or modem/private data. No reboot, fastboot, recovery, mount/unmount, flash or partition write. Raw device binaries stay local and must not be uploaded.

Publish only the sanitized report:
firmware-analysis/round155/WORKBUDDY_A_ROUND155_READONLY_BOOTCHAIN_PARTITION_CAPTURE_REPORT.md

Read it back and verify the uploaded content, then STOP.