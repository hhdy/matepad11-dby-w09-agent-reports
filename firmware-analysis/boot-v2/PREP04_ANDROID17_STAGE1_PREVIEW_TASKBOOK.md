# PREP04 — Android 17 ACK 6.18.33 首个主机端启动包组装

- 发布者 / 技术决策人：1号 AI（ChatGPT）
- 唯一执行者：刚刚完成 PREP03 双包重新交付的那个 WorkBuddy 对话（同一工作区同时持有两份 ZIP）
- 用户无需辨认 Agent 编号；不得转派另一个 WorkBuddy 窗口。
- 设备：Huawei MatePad 11 DBY-W09 / SM8250 / A-only
- 目标：Android 17 ACK 6.18.33 kernel bring-up；之后再集成 DerpFest Android 17
- 本轮范围：只在主机上解析已上传的两个 PREP03 ZIP，并在证据充分时制作 Android 17 候选启动包预览。
- 不连接平板，不执行 ADB / Fastboot / EDL / reboot / temporary boot / partition write / flash。

## 0. 本轮为什么需要 WorkBuddy

AI1 已收到用户上传的两份原始 ZIP，但 ChatGPT 当前主机执行环境无法运行本地二进制处理命令。PREP03 的真实二进制解包、offset 解析、round-trip 和 boot image 重建只能在持有原文件的本机工作区执行。因此本轮只让原 WorkBuddy 会话作为离线主机执行器，技术判断和下一步集成仍由 AI1 负责。

这不是新的泛化审查轮，也不是重新构建内核。禁止连接设备补数据。

## 1. 输入归档身份（必须先校验）

两个 ZIP 应已存在于刚刚报告的本地工作区：
- prep03/windowA/PREP03_WindowA_Device_Inputs.zip
- prep03/windowB/PREP03_WindowB_Kernel_Inputs.zip

期望 ZIP 身份：

| ZIP | Size | SHA-256 |
|---|---:|---|
| Device inputs | 206,133,919 B | 2a6306c339ff2c3ccd200df2bd152618f950aacc54019cdc65f18b1b3dca39e5 |
| Kernel inputs | 45,302,464 B | c2214d15525b16f1708e95bd14f971db660c83f933ddb3dcea3b3c514846b371 |

必须先核对 ZIP 哈希与 zip test，确认完整性，再解压。若不匹配，停止使用该归档并报告，禁止静默用另一份副本替换。

### 1.1 Device inputs 预期内容
- stock-live-boot.img: 100,663,296 B; SHA-256 7a95c897c14a6f9151b6d22308b8086b8f6395d4bd9aa438faab126ae39d24a8
- stock-live-ramdisk.img: 2,097,152 B; SHA-256 4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb
- candidate-dby-w09.dtb: 108,680 B; SHA-256 9d0d76001cf1b156ddbdee0a0e77afaaffa23d77cb8068ab21e407ee4c5fed60
- abl-hos43-pe.bin: 2,597,064 B; SHA-256 a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404
- stock-package-boot.img optional reference: 100,663,296 B; SHA-256 027f88fd6f318523925ca27a4d681d17a9bbca904b0c471ccc05e651d3da19b8
- SHA256SUMS, provenance.txt

### 1.2 Kernel inputs 预期内容
- Image: 44,820,992 B; SHA-256 f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21
- config-used-for-build.config: 238,410 B; SHA-256 0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15
- config-olddefconfig-normalized.config: 237,316 B; SHA-256 efb663e9c792840e2cfbbc03e115996bb486aefe964b448c1717828c55bf042f
- kernel-release.txt, build-provenance.txt, SHA256SUMS
- No Image.gz was produced by the successful build; do not generate one.

Kernel anchors:
- ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9
- source tree: c56d93eafa35057d65176db6594d67d5144868a0
- Kleaf target: //common:dby_w09; reported RC 0
- Kernel .config actually used by Kleaf is 0850213d…; efb663e9… is the subsequent olddefconfig normalized result. Preserve and distinguish both.

## 2. Parse the actual stock live boot image

Use PREP03 parser if it exists in the local workspace (archive SHA-256 from AI1 status: 2ae2338aa9270f61b7df472d99ede06d00c34acee7f4e173aa9a0c8e8bd527e1). Record its version and exact command. If unavailable, use a pinned/identified standard Android boot image parser plus independent byte-level parsing.

ROUND155 report already gives the following expected cross-checks; verify against actual bytes rather than assuming:
- live boot partition size 100,663,296 B;
- Android boot header v2, header size 1,660 B;
- kernel_size 22,256,282 B;
- embedded ramdisk_size 519,986 B;
- dtb_size 1,664,243 B; dtb_addr 0x01f00000;
- AVB footer AVBf absent in the live copy;
- 3 appended FDTs in the DTB slot and a 173-byte tail;
- stock FDT slot hashes reported as df2730f3…, f3dcba83…, 6cda6739….

For the actual image, produce exact:
1. header fields, page size, header size, all payload offsets/alignment/padding;
2. kernel/embedded ramdisk/DTB slot offsets, exact lengths and SHA-256;
3. all three FDT payload sizes, board-id/msm-id metadata and bytes; tail bytes;
4. AVB footer presence/absence and precise partition-tail classification;
5. boot image ID recomputation and independent parser confirmation.

Do not assume stock live boot and package boot are byte-identical. The package copy has a different kernel hash, same ramdisk and FDT slot payloads, and an AVB footer per ROUND155.

## 3. Parse the actual separate ramdisk partition and resolve the duplication warning

The separate live ramdisk partition is 2,097,152 B with pinned SHA-256 above. Do not assume it is raw gzip or header-v0; parse actual bytes.

Report:
- leading bytes / magic / header type;
- whether an Android boot header, vendor header, raw cpio, gzip/lz4 archive, or other container;
- exact inner payload offset/length/hash;
- compressed and uncompressed sizes if determinable;
- AVB/footer/padding offsets;
- archive listing, including init, fstab, modules, first-stage files and directories (do not extract secrets or user data).

Also inspect the 519,986-byte embedded boot ramdisk. Compare both ramdisks by compressed hash, decompressed cpio member list, key file hashes, and init/fstab contents. Determine whether they are duplicate, complementary, or distinct.

### Critical source constraint — do not ignore or overstate

The user supplied a developer conversation record in ROUND136:
- “这个abl不支持boot自定义dt”
- “得内嵌”
- “还有这个ramdisk不能塞boot里”
- “会重复引导”
- “除非你直接跳过ramdisk”

That quotation is user-supplied technical context, not independently proven ABL behavior. It must be reconciled against the exact HOS4.3 boot bytes, separate ramdisk bytes and ABL handoff code. Do not blindly treat it as fact, but do not ignore it either.

ROUND155 established static ABL code references:
- Boot Image Header Info, DTB Size, Single appended DTB found;
- /chosen, linux,initrd-start, linux,initrd-end;
- live FDT initrd range 0xf0000000..0xf015749a;
- ufdt_install_blob / overlay application;
- stock androidboot.dtbo_idx=2;
- candidate one-entry DTBO should be index 0 (static selector result).

Use the extracted PE ABL and its disassembly / call sites to answer:
1. Does ABL actually load/use the ramdisk embedded in the boot v2 image?
2. Does ABL separately load the partition named ramdisk?
3. What exact buffer start/end generates the live initrd 0xf0000000..0xf015749a?
4. Is the 519,986-B embedded ramdisk also passed to Linux, ignored, or used as a fallback?
5. Could embedding the same initramfs twice create the duplicate boot / repeated first-stage init behavior described by the supplied record?
6. What does “boot 自定义 dt 不支持，得内嵌” correspond to in actual ABL code: appended boot-v2 DTB, concatenated FDT slots, kernel-embedded DTB, or a different rule?

If the actual handoff remains unresolved, do not choose preserve/clear/replace ramdisk modes and do not produce a boot candidate using a guessed ramdisk arrangement. Complete the exact binary parse and report the specific missing call-path proof.

## 4. Verify candidate DTB / candidate DTB-slot layout

- Verify candidate DTB FDT magic, totalsize, structure and exact SHA-256.
- Inspect /firmware/android/fstab and the relevant fstab entries (if present) without modifying DTB.
- Parse all three stock fallback FDTs from the stock boot image and inspect their compatible/msm-id/board-id metadata.
- Reconcile PREP03 composer expectation: candidate FDT + stock Kona v2/v1 fallback FDTs + 173-byte tail, expected slot size 1,216,399 B, versus ROUND155 stock live dtb_size 1,664,243 B. Explain every byte difference; do not silently pad or truncate.
- Use the frozen ROUND159 one-entry DTBO only, exact SHA-256 f185c13de5f9d2ca8dc2610c4cef33d12db601bfa29bae079fb5827951c1a6cc. Verify it contains root selector qcom,board-id=<0x200e 0> and exact five rootparam properties already approved in ROUND159.
- Do not apply stock Entry2 fixups to the candidate base. The candidate base has no stock symbols/fixups; the frozen overlay uses the exact target-path "/rootparam" path.

If ABL cannot accept the candidate through the boot v2 DTB slot and must consume a kernel-embedded FDT, do not alter the frozen kernel/Image/DTB in this round. Report exactly how the existing tooling and boot plan must be adjusted; AI1 will decide whether a new kernel build is needed.

## 5. Candidate Stage 1 package — assemble only if §3 and §4 have a fully evidenced answer

The Stage 1 goal is only a host-side ACK 6.18.33 kernel bring-up preview using the current device-matched Android 12/HOS vendor/userspace baseline. This is not the DerpFest Android 17 ROM.

If and only if the actual ABL evidence establishes the correct ramdisk and DTB handoff:
1. Use the live stock boot image as template, not the firmware-package boot with different kernel/footer data.
2. Replace only the kernel with the exact frozen Image, preserve its bytes.
3. Compose/select the candidate DTB slot exactly as established in §4.
4. Apply only the proven ramdisk placement choice:
   - preserve embedded ramdisk byte-for-byte; or
   - clear embedded ramdisk; or
   - preserve/replace another exact component only if ABL behavior proves it.
5. Leave the independent ramdisk partition backup unchanged and separate unless exact evidence says otherwise.
6. Preserve boot v2 header metadata and load addresses; align all payloads as required by actual header page-size.
7. Build an output preview with exact lengths/hashes, boot ID recomputation and independent second-parser validation.
8. Generate JSON manifest and SHA256SUMS.

Do not guess the final partition image size, fill bytes, AVB footer, or signature. If the original live boot has no AVB footer, the preview must not invent one. Do not edit or regenerate vbmeta. Do not call output flashable, accepted, bootable or safe to flash.

If §3 or §4 is unresolved, stop before candidate creation, but deliver all verified parsed facts and a clear single blocker. Do not create multiple speculative candidate variants.

## 6. Required outputs

Create a directory PREP04_ANDROID17_STAGE1_PREVIEW/ in the local workspace with:
- PREP04_REPORT.md — exact parse results, evidence grades, and the Stage 1 package decision;
- stock-boot-facts.json — header fields and exact section offsets/sizes/hashes;
- stock-ramdisk-facts.json — actual separate/embedded ramdisk formats and relationship;
- dtb-slot-facts.json — three stock FDTs + candidate facts + slot layout arithmetic;
- ABL_HANDOFF_EVIDENCE.md — relevant ABL code/string xrefs, call-site/control-flow evidence, exact unknowns;
- candidate/ — only if §3 and §4 pass; the host-side candidate boot-v2 image, with separate DTBO artifact/manifest if needed;
- SHA256SUMS.txt — hashes for every output.

Zip this directory as PREP04_ANDROID17_STAGE1_PREVIEW.zip and attach the ZIP to the current WorkBuddy reply. Also copy to %USERPROFILE%\Desktop\PREP04_ANDROID17_STAGE1_PREVIEW\.

Do not publish raw boot/ramdisk/ABL/kernel binaries or a proprietary candidate package to public GitHub.

## 7. Stop rules

- No device interaction of any kind.
- No kernel/DTB rebuild, no Image compression or modification.
- No flash, temporary boot, reboot, unlock, AVB bypass, vbmeta edit, signature patch or key extraction.
- No speculative ramdisk preserve/clear/replacement choice.
- No speculative DTB packaging choice.
- A missing call-path fact means stop at host parse; report the one remaining blocker rather than starting a new broad audit round.

## 8. Reply format

Start with:
PREP04 状态：候选包已组装 / 解析完成但因单一阻断未组装

Then list:
- exact archive SHA verified (both);
- exact boot v2 parse facts and section hashes;
- separate vs embedded ramdisk comparison;
- ABL initrd start/end mapping;
- candidate DTB slot size arithmetic and fstab result;
- Stage 1 candidate output filename/size/SHA-256, or exact blocker;
- output ZIP SHA-256 and current reply attachment status;
- confirm: no device access, no reboot, no flash, no kernel rebuild.

The task is complete after attaching PREP04_ANDROID17_STAGE1_PREVIEW.zip (or, if objectively blocked, an archive containing all parsed facts and the single blocker report). Stop afterwards.


## 9. AI1 scope correction — this is a kernel validation package, not a complete ROM

This section is an authoritative correction to the task scope. It supersedes any interpretation that all drivers, peripherals, Android services, or DerpFest integration must be complete before making the Stage 1 package.

### 9.1 Driver completeness is NOT a package gate

The purpose is to validate the ACK 6.18.33 kernel on DBY-W09. It is not a production ROM and not the final DerpFest port.

The following may be incomplete, disabled, missing, or left for later work without blocking the Stage 1 validation package, unless a specific item is required by the selected validation checkpoint:
- display / panel / touch;
- GPU / graphics acceleration;
- camera;
- audio;
- Wi-Fi / Bluetooth;
- sensors, GPS, NFC and other optional peripherals;
- power-management polish, suspend/resume optimization, thermal tuning and performance tuning;
- product features and user-facing Android services.

Do not start a driver-completion campaign before first kernel validation. Record what is missing and continue to the next useful checkpoint.

### 9.2 Use staged validation checkpoints

The first test should aim for the earliest meaningful proof, then advance incrementally:

- **Checkpoint K1 — kernel entry / early boot:** ABL transfers control to the ACK Image; ARM64 kernel starts; core CPU/MMU, RAM, GIC, timer and PSCI initialization progresses; early console or another observable kernel log confirms execution. Full Android userspace and peripheral drivers are not required.
- **Checkpoint K2 — storage / first-stage init (next target when K1 succeeds):** essential UFS host/PHY/clock/regulator/reset/interconnect path works sufficiently to enumerate storage; the required boot/ramdisk handoff occurs; first-stage init can read the required partitions. Display/touch/GPU/audio/Wi-Fi etc. still are not prerequisites.
- **Checkpoint K3 — minimal userspace / diagnostic access (when feasible):** init advances sufficiently to expose ADB or another diagnostic channel. USB gadget/UDC support is needed only if ADB-over-USB is the chosen observation path.
- **Checkpoint K4 — broad device functionality:** peripheral drivers and system polish. This is explicitly out of scope for the first validation package.

The package is not required to reach K4. A K1-only package is still useful evidence about kernel startup, even if K2 is not yet reached. The report must state the achieved checkpoint, not label it a full system boot.

### 9.3 Only boot-critical structures remain hard gates

Do not confuse incomplete peripheral drivers with an unresolved boot container. A candidate still needs correct:
- boot image header and payload offsets/alignment;
- kernel Image identity and bytes;
- device DTB / DTBO placement and selector contract;
- initrd/ramdisk handoff arrangement;
- partition boundary and preserved tail handling;
- a legitimate and known test-boot acceptance route before any device operation.

These are boot-protocol / safe-test requirements, not a demand for full driver completeness.

### 9.4 Ramdisk conservative mode: preserve stock, do not invent a new one

For this first kernel-only validation, do not build a new Android 17 or DerpFest ramdisk. Do not insert a new initramfs into boot or into the separate partition.

If the actual stock boot template contains a 519,986-byte embedded ramdisk and the separate 2 MiB ramdisk partition, preserve both source payloads byte-for-byte and preserve their respective stock roles/locations. This avoids introducing a new duplicate initramfs merely for testing. The separate partition must not be copied into the embedded boot ramdisk.

If the packer must move offsets because the kernel size changes, preserve the exact ramdisk payload bytes and report the new offsets. Only clear or replace a ramdisk if exact device evidence demonstrates that is necessary; do not make that change for this test package.

If ABL handoff code remains partly unresolved but the stock embedded and separate ramdisk payloads can both be preserved exactly, the host-side candidate may still be assembled as a **non-flashable experimental preview**, with the unresolved handoff limitation prominently recorded. Do not block all package construction merely because optional drivers are incomplete. However, do not authorize actual flashing until the boot-critical handoff and accepted test path are sufficiently established.

### 9.5 AVB and recovery gate is proportional to the action

- For offline host assembly and parser validation, no signing key or device acceptance proof is required; do not edit vbmeta or forge a footer.
- Before any actual write/flash, establish the device's legitimate acceptance path for the modified image and a credible recovery route. This does not mean that the image must be a production-signed ROM; it means the test image must be accepted through the device's legitimate unlocked/development mechanism, if one is available and verified.
- Do not require all peripheral drivers or a DerpFest system image as a prerequisite to a limited kernel bring-up flash test.
- Do not bypass AVB/OEM protections or imply that flags=3 prove acceptance.

**AI1 priority:** produce one conservatively assembled Stage 1 kernel-validation candidate as soon as the binary formats permit. Report unresolved boot-critical questions as explicit limitations. Do not turn this into a full ROM or driver-completion exercise.
