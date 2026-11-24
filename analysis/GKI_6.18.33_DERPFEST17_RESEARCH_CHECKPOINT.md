# Android GKI 6.18.33 / DerpFest 17 research checkpoint

Date: 2026-11-24

## Current baseline decision

- Target kernel source: Android Common Kernel release tag `android17-6.18.33_r00`.
- Architecture: arm64.
- Build system: Android Kleaf/Bazel; do not assume legacy `make Image` is the supported final Android build path.
- Device-specific code must be kept separate from generic GKI as much as possible.
- The first milestone is a clean, reproducible host-side build of the pinned ACK baseline and build artifact inspection—not flashing.
- Later device modules must be evaluated against the selected GKI KMI and module signing/ABI rules. Do not take 4.19 vendor .ko files and load them on 6.18.
- Device-specific packaging cannot be finalized until Round 3 resolves the actual boot header, ramdisk(s), DTB/DTBO and Huawei rootparam flow.

## Evidence / official references

1. AOSP GKI release-build page for android17-6.18:
   https://source.android.com/docs/core/architecture/kernel/gki-android17-6_18-release-builds
   - Lists kernel artifacts such as Image, compressed Images, boot.img, System.map, vmlinux, vmlinux.symvers, modules.builtin and system_dlkm staging archive.
   - These metadata artifacts are useful when building mixed/vendor modules; they are not all needed for the very first generic baseline build.
   - Android 17 GKI boot image header os_version/SPL handling differs from older assumptions; boot packaging must be validated against target firmware and AVB chain.

2. AOSP GKI release process:
   https://source.android.com/docs/core/architecture/kernel/gki-releases
   - android17-6.18 is an active GKI release line.
   - The 16 KB release variant exists for android17-6.18; the device's filesystem, bootloader, vendor and userspace compatibility must be checked before choosing page size.
   - Do not infer that this tablet can use 16 KB pages merely because the GKI branch provides it.

3. DerpFest-AOSP organization:
   https://github.com/DerpFest-AOSP
   - The official organization advertises Android 17 support and an Android 17 manifest. A manifest branch existing is not proof DBY-W09 is supported.
   - Device-specific device tree, vendor tree, kernel tree and build target remain to be created/validated.

## Important version correction

The previous plan pinned `android17-6.18.33_r00`. This is a release tag and is acceptable as a reproducible starting point, but it is not necessarily the newest tag as of this checkpoint. AOSP release data currently lists newer android17-6.18 releases (e.g. 6.18.32 branch respins and the 6.18.33_r00 tag). Before locking the kernel for a long-term project, compare the exact release tag's manifest, source SHA and required KMI with the selected ROM tree. For reproducibility, keep the exact tag or commit pinned; do not follow a moving branch.

## Build sequencing

### Phase A — host baseline

1. Obtain the exact ACK tag/manifest.
2. Record manifest revision, source commit, toolchain versions and host OS.
3. Build the generic arm64 GKI using the official documented Kleaf target from that tag.
4. Archive only logs and small text metadata, not build outputs in the reports repository.
5. Verify kernel artifact type, compression, build ID, config and module metadata.
6. Do not attempt device boot.

### Phase B — device research

Wait for Round 3 outputs. Then identify:

- Boot header and image layout
- Kernel/ramdisk/DTB placement
- Huawei rootparam and DTBO dependency
- Super logical partition map
- Vendor/ODM VINTF and HAL requirements
- Firmware/module dependencies
- Android 17 framework versus existing vendor compatibility

### Phase C — integration plan

Only after Phase B, create a device-specific repository and design:

- device tree / board configuration
- boot image packaging strategy
- DTB/DTBO integration
- vendor modules and KMI strategy
- init/fstab/VINTF compatibility
- recovery and rollback strategy

No flashing until a verified backup, recovery path, exact partition layout and boot image format are established.

## Known blocker

The current reports repository is public and contains an unredacted device serial in the first-round report. The owner should set it Private and sanitize the file/history before making it public again. The exposed GitHub PAT must be revoked; it must not be used in this project.
