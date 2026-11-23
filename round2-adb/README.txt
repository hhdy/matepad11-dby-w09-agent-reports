MatePad 11 DBY-W09 - Agent Round 2 Report
Captured: 2026-11-23 22:50-22:55 +08:00
Source package: MatePad11_DBY-W09_Agent_操作包_v2.zip

Scope: read-only ADB collection only. No reboot, no fastboot entry, no root,
no partition image pull, no write to any device partition, no EDL/Firehose.
Device serial and MAC addresses are redacted in all text files.

DEVICE STATE
  adb state: device (authorized); battery 96%; model DBY-W09 / HWDBY.
  Device was NOT in fastboot; no reboot was issued.

STATUS OF EACH REQUESTED ITEM
  device/adb_getprop_redacted.txt              PASS
  device/soc_cpu_report_redacted.txt           PASS
  device/pci_report_redacted.txt               PERMISSION DENIED (IDs), PASS (device list)
  device/display_usb_input_report_redacted.txt PASS
  device/partition_names_redacted.txt          PASS
  device/fastboot_getvar_redacted.txt          NOT AVAILABLE (device not in fastboot)
  device/live.dtb + live.dtb.sha256            PERMISSION DENIED (adb pull stat failed)
  device/devicetree_nodes_redacted.txt         PASS (directory listing only)
  device/devicetree_base_redacted.txt          PERMISSION DENIED (file reads via sysfs)
  host/repo_manifest_locked.xml                NOT AVAILABLE (wsl.exe blocked)
  host/gki_tag_commit.txt                      NOT AVAILABLE (values from v2 report, unverified locally)
  host/bazel_version.txt                       NOT AVAILABLE
  host/gki_build.log                           NOT AVAILABLE
  host/gki_dist_sha256.txt                     NOT AVAILABLE

KEY FACTS FROM THIS ROUND
  - SoC: soc_id 356, revision 2.1, chip_name SM8250, machine KONA, family Snapdragon.
  - CPU online 0-7; cpufreq max: policy0=1804800, policy4=2419200,
    policy7=2841600 Hz. That is a 1x2.84 + 3x2.42 + 4x1.8 GHz layout:
    it matches Snapdragon 865 / SM8250, NOT the 3.2 GHz Snapdragon 870 claim.
    Do not write 3.2 GHz OPP into DTS without further evidence.
  - DTB: /sys/firmware/fdt is 800316 bytes but root-only (mode -r--------).
    adb pull failed with "failed to stat remote object ... Permission denied".
    Both /proc/device-tree/* and /sys/firmware/devicetree/base/* file reads
    are PERMISSION DENIED; only directory listings are readable. No root,
    no chmod, no in-device temp file was attempted.
  - The live DTB tree contains a "rootparam" node (matching the boot risk in
    the manual), plus Huawei-specific nodes for charging, wireless power,
    hall sensor, LCD panel and pogopin accessories.
  - PCI: two devices exist (0000:00:00.0, 0000:01:00.0) but vendor/device
    attribute reads are PERMISSION DENIED. Wi-Fi device ID remains unconfirmed.
  - DRM: card0-DSI-1 only (plus DP-1 and Virtual-1), 5 SDE CRTCs;
    display 1600x2560, supported 60 Hz and 120 Hz. ro.hardware=qcom.
  - USB device list is empty; /dev/input has event0-event5.

BLOCKER
  Every wsl.exe invocation is rejected by the command safety deny rule,
  including read-only "wsl --list --verbose" and after sandbox escalation.
  No Ubuntu 24.04 distro is installed. Therefore GKI source sync, tag pinning
  and Kleaf baseline build could not be performed this round.

Writes performed on the device or its partitions: NONE.
