# Local Agent execution instructions — DBY-W09 firmware analysis

## Goal
Run the repository's read-only analyzer against the existing local HarmonyOS 4.3 firmware package for Huawei MatePad 11 DBY-W09 and return text-only reports for review.

## Required safety constraints
1. Do not run ADB or fastboot. Do not connect to, reboot, unlock, root, or flash the tablet.
2. Do not execute any scripts or binaries contained in the firmware package.
3. Do not modify, rename, move, or delete any source firmware file.
4. Use a separate output directory outside the firmware source directory.
5. Never upload proprietary image files (boot.img, dtbo.img, ramdisk.img, super.img, vendor images, etc.) to the public GitHub repository.
6. Do not request, print, store, or embed any GitHub PAT. Use the already configured GitHub sign-in/connector if a repository upload is needed.
7. Do not calculate hashes of multi-gigabyte partitions unless explicitly requested. The analyzer defaults to not hashing large images.

## Steps
1. Locate the clone of hhdy/matepad11-dby-w09-agent-reports and read tools/Analyze-DBY-W09-Firmware.ps1 and tools/README-FIRMWARE-ANALYSIS.md.
2. Locate the existing HarmonyOS 4.3 firmware folder or ZIP from the user's prior working directory. Do not ask the user to re-upload the original package if it is already present locally. If multiple candidate firmware packages exist, inspect filenames and select the package already used to produce firmware-hos43/package_inventory.csv.
3. Run the analyzer using Windows PowerShell:

   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\Analyze-DBY-W09-Firmware.ps1" -FirmwarePath "<actual-local-firmware-path>" -OutputPath "<separate-output-path>"

   ExecutionPolicy Bypass applies only to this one PowerShell process; do not change the machine-wide policy.
4. Keep the default MaxExtractMiB value of 512. Do not pass HashLargeFiles.
5. Review the output for errors. Confirm that the source firmware folder/package timestamps and file sizes did not change.
6. Verify all output reports exist: partition_inventory.csv, firmware_analysis.txt, selected_images_sha256.csv, summary.json.
7. Upload only those four text/CSV/JSON files into firmware-analysis/round1/ on a review branch (not binary payloads). If the connector lacks upload permission, return the report files to the user without asking for a PAT.
8. Report the exact local source filename, output location, any skipped images, and all errors. Do not claim that boot.img was unpacked: this analyzer inventories it and reads header fields only.

## Stop conditions
Stop without modifying anything if the local firmware package cannot be identified with confidence; the input is not an extracted directory or ZIP file; the output directory would be inside the firmware source directory; extraction would exceed the default per-file size cap; or an upload would include firmware binaries or sensitive device identifiers.
