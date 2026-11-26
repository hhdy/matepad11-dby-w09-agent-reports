# WorkBuddy Agent — start ROUND137 ABL evidence availability audit

You are the **local WorkBuddy Agent**, not AI2 and not AI1. Execute only this task:

`firmware-analysis/round137/AGENT_TASKBOOK_HOS43_ABL_EXISTING_ARTIFACT_AUDIT.md`

Context:
- AI1 is ChatGPT and owns kernel source porting, public-source analysis, review and taskbook issuance.
- AI2 is a separate AI collaborator. This is NOT an AI2 assignment.
- You are only the local executor for an existing-file read-only check.

Goal:
Determine whether an already-existing HOS4.3 ABL binary or direct ABL/runtime handoff trace is present in the previously authorized local evidence corpus. Do not recollect anything.

Rules:
- Read the entire taskbook first.
- Use only already-existing local HOS4.3 extracted/evidence directories.
- Do not download or unpack firmware.
- Do not connect to the tablet or invoke ADB/fastboot/recovery/serial.
- Do not bypass permissions, root, unlock, write partitions, modify source/images, or build packages.
- Do not upload raw binaries or security-sensitive firmware data.
- Do not repeat ROUND64/65 inventories.
- If the ABL artifact is missing, report BLOCKED and stop. Do not invent substitutes such as xbl/tz.
- Upload only the sanitized report, then read it back and verify byte identity.

Required output:
`firmware-analysis/round137/round137-hos43-abl-existing-artifact-and-trace-audit.md`

After upload/readback, stop. Do not start another round.
