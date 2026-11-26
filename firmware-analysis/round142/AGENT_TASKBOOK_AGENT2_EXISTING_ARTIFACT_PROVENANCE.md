# ROUND142 — 2号 Agent existing-artifact provenance addendum

- Executor: **2号 Agent** (the same second local execution Agent that executed ROUND140)
- Dispatched by: AI1 (ChatGPT)
- Not the executor: 2号 AI; WorkBuddy Agent
- Device: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Candidate tree: afe9517f8062b96bfeb5b4dd5714942861e6a44b
- ROUND140 workspace owner: 2号 Agent
- Mode: strictly offline, read-only inspection of artifacts already produced by ROUND140
- Report branch: agent2/round142-existing-artifact-provenance
- Report path: firmware-analysis/round142/round142-agent2-existing-artifact-provenance-addendum.md

## 0. Role and authorization boundary

This is a **2号 Agent** task. It is not a 2号 AI task and must not be transferred to WorkBuddy Agent.

2号 Agent may inspect only its own already-existing ROUND140 workspace:
- independent source tree: /home/kerneldev/work/matepad11/round140-agent2/tree
- its own logs: /home/kerneldev/work/matepad11/round140-agent2/logs
- its own build staging and output root: /home/kerneldev/work/matepad11/round140-agent2/a30build
- its own independent DTB output: /home/kerneldev/work/matepad11/round140-agent2/out-dtb

Do not inspect any other Agent's workspace, including WorkBuddy Agent or 2号 AI. If the listed files are no longer accessible, mark them NOT FOUND and stop that subtask. Do not search arbitrary drives, home directories, user folders, cloud storage or external repositories.

This task authorizes no device access, no build, no network requests, no source changes and no dependency fetch. The only permitted activity is reading and hashing already-existing files created during ROUND140.

## 1. Read first

1. ROUND140 report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/agent2/round140-independent-preboot-tests/firmware-analysis/round140/round140-agent2-independent-build-and-preboot-test-report.md
2. AI1 ROUND140 review:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round140/AI1_ROUND140_INDEPENDENT_REVIEW_AND_ROUND141_DISPOSITION.md
3. 2号 AI ROUND141 report:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai2/round141-candidate-preboot-risk-review/firmware-analysis/round141/AI2_ROUND141_CANDIDATE_PREBOOT_ARCHITECTURE_RISK_REVIEW.md
4. AI1 ROUND141 review:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/ai1/round130-stagea-ufs-lifecycle-integration/kernel-baseline/round141/AI1_ROUND141_INDEPENDENT_REVIEW_AND_ROUND142_DISPOSITION.md

## 2. Workstream A — BTF / pahole provenance from existing ROUND140 artifacts

Using only existing logs and tool files already present in the ROUND140 workspace:

1. Locate any already-existing command logs or Bazel action logs that identify:
   - pahole / dwarves binary path, version and SHA-256;
   - BTFGen / resolve_btfids binary path, version and SHA-256;
   - exact BTF generation command line, flags and input/output paths;
   - environment values that materially affect BTF output;
   - kernel signing certificate generation command/configuration and the output artifact responsible for the 1,072-byte .init.data difference.
2. Hash an existing local tool binary only if it is already present in the ROUND140 workspace or pinned prebuilt tree used by that run. Do not install or fetch any tool.
3. Compare the existing logs to the ROUND140 report's BTF explanation:
   - extra BTF name ro_image_end;
   - +136 type bytes and +13 string bytes;
   - downstream .BTF_ids / __stop_BTF / build-id differences.
4. State separately:
   - CERTIFICATE DIFFERENCE: directly demonstrated / supported / unknown;
   - BTF DELTA CAUSE: directly demonstrated / supported / unknown;
   - BTF CROSS-BUILD REPRODUCIBILITY: proven / not proven.
5. If the exact command or binary provenance does not exist in retained logs, report NOT FOUND. Do not reproduce the build or create new BTF output.

Do not upload full build logs, binaries, certificates, private keys, signatures, key identifiers or sensitive material. Only sanitized tool names, versions, hashes of public prebuilt tool binaries, command templates and bounded excerpts may be included.

## 3. Workstream B — Bazel / Kleaf repository fetch and cache provenance

This item is required because ROUND140 reported external Kleaf repositories fetched at build time with HTTP 200 responses from mirror.bazel.build and github.com, while its taskbook required aborting rather than fetching dependencies when the existing local cache was insufficient.

Inspect only existing ROUND140 log and output files under the exact workspace paths listed in §0. Do not run Bazel, repository rules, curl, wget, git fetch, sync or any command that could make a network request.

For each fetch event, determine where possible:
- repository / archive name;
- URL host (redact tokens, credentials and signed query strings);
- whether the event was a cache hit, cache miss, metadata check or payload transfer;
- response code;
- bytes transferred if already recorded;
- whether the fetched payload was actually needed for the successful build;
- whether the report's HTTP 200 line refers only to metadata or to an actual repository payload.

Final classification must be one of:
- COMPLIANT — evidence shows no prohibited new dependency payload was fetched;
- DEVIATION — evidence proves a new dependency payload was fetched despite the stop-on-missing-cache instruction;
- UNRESOLVED — existing logs do not distinguish metadata/cache checks from payload downloads.

Do not reconstruct the network activity, rerun the build, clear caches or fetch anything again. If logs do not exist, say so.

## 4. Workstream C — Candidate UFS source readback from the 2号 Agent's own tree

Use only the already-existing ROUND140 source tree at /home/kerneldev/work/matepad11/round140-agent2/tree. No new patch application or source checkout.

Read-only inspect:
1. drivers/ufs/host/ufs-qcom.c for the candidate qcom,vddp-ref-clk-supply consumer:
   - compatibility guard;
   - regulator name passed to devm_regulator_get;
   - load property;
   - regulator_set_load / regulator_enable call;
   - initialization call site and ordering relative to UFS/PHY setup.
2. Search that same candidate file/tree for any actual consumer of qcom,vccq-parent-supply. A DT property or comment is not a consumer.
3. Read arch/arm64/boot/dts/qcom/huawei-dby-w09.dts:
   - UFS host vcc / vccq / vccq2 / qcom,vddp-ref-clk / qcom,vccq-parent properties;
   - provider labels and supply-node identity;
   - vdd-hba omission and corresponding power-domains;
   - six regulator nodes' status-property presence/absence.
4. For every regulator node with no status property, state only:
   - Device Tree node is available by the OF default convention;
   - runtime hardware enable state remains UNKNOWN.
   Do not write "status absent means regulator enabled".
5. Check provider phandles against the already-existing ROUND140 DTB text/decompile output, if present. Do not regenerate a DTB or run dtc.

Output a property → provider → code consumer → result table, with exact source file lines. Keep physical PMIC input parents UNKNOWN.

## 5. What this round must not attempt to close

No amount of build-log inspection can close the following hardware gates. Carry them forward unchanged:
- physical PMIC input parents for L5/L6/L9/L17/S4/S8;
- runtime UFS rail enable state and actual voltage;
- MMCX/MX runtime CMD-DB / RPMh votes;
- final post-ABL FDT and usable RAM tuples;
- reserved-memory range ownership;
- actual device DTBO partition identity and ABL selection;
- ABL boot-v2 / independent ramdisk consumption behavior;
- full cryptographic AVB verification and vbmeta_cust footer provenance;
- complete device-matched partition backups and tested HOS4.3 recovery route.

No device read, connection or permission escalation is authorized.

## 6. Strict prohibitions

- No tablet connection, USB, ADB, fastboot, recovery, serial, reboot or bootloader operation.
- No partition access, FDT read, root, privilege escalation or permission bypass.
- No compilation, Kbuild, Kleaf, Bazel build, dtc, dtbs_check or test execution.
- No network access, dependency fetch, firmware download or git fetch.
- No source, patch, DTS, DTBO, Kconfig, config, manifest, candidate tree, branch or Image modification.
- No cache clearing, worktree deletion or cleanup of any user data.
- No access to another Agent's private workspace.
- No package, boot image, AVB or signing operation.
- No declaration of first-boot readiness.

## 7. Output and final status

Create:
firmware-analysis/round142/round142-agent2-existing-artifact-provenance-addendum.md

Include:
- exact executor identity: 2号 Agent;
- inspected file paths and SHA-256 for relevant text logs/tool binaries;
- BTF / certificate provenance result;
- Bazel/Kleaf fetch/cache classification;
- candidate UFS consumer readback table with line numbers;
- correction that absent DT status means node availability, not electrical regulator enablement;
- all NOT FOUND, UNKNOWN and unavailable items;
- concise impact on first-boot gates.

Final status:
- PASS — EXISTING PROVENANCE COMPLETE: all three workstreams have adequate existing artifacts and no prohibited fetch is indicated;
- PARTIAL — SOME PROVENANCE NOT RETAINED: candidate code readback is complete but one or more existing build/fetch logs are absent or inconclusive;
- DEVIATION — NEW DEPENDENCY PAYLOAD FETCH CONFIRMED: report what was fetched; do not retry it;
- BLOCKED — ROUND140 OWN WORKSPACE UNAVAILABLE.

Upload only sanitized Markdown to branch agent2/round142-existing-artifact-provenance. Read it back and verify byte identity. Then stop. No follow-on task, device access, build or flash is authorized.
