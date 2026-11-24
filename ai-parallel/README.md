# Parallel AI workstreams

This directory coordinates independent work performed by an additional GitHub-connected AI. It is separate from the read-only local firmware Agent workflow documented in `AGENT_TASK.md`.

## Current split

| Workstream | Owner | Scope | Write location | Status |
|---|---|---|---|---|
| ROUND53 + next Stage-A dependency closure | ChatGPT / primary AI | Kconfig, storage-first config, boot/storage dependencies, main handoff | `main` (only the primary AI updates canonical artifacts) | In progress |
| ROUND54 | Second AI | Independent source-level correctness review of ROUND32/36/37/33/52 UFS patch series, binding schema, DTS and lifecycle/error paths | `ai-parallel/round54-ufs-review` only | Ready for assignment |

## Second AI entry points

- Task contract and hard rules: [ROUND54_TASK.md](ROUND54_TASK.md)
- Copy/paste startup prompt: [SECOND_AI_START_PROMPT.md](SECOND_AI_START_PROMPT.md)
- Dedicated branch: `ai-parallel/round54-ufs-review`
- Review report path: `ai-parallel/round54/ROUND54_REVIEW.md` on the dedicated branch

The branch was created from the latest `main` after the task contract was committed. The report template is already present on that branch.

## Collaboration protocol

1. The second AI must independently re-derive findings from the pinned ACK source; it must not rubber-stamp previous reports.
2. It may commit only to its dedicated branch. It must not touch canonical patch drafts or report files.
3. Candidate corrections, if proven necessary, stay under `ai-parallel/round54/candidates/`.
4. Do not create a PR or merge. The primary AI will review the results and decide whether any candidate is safe to port to canonical work.
5. Both AIs preserve Stage A first: ACK 6.18.33 kernel port and boot/storage acceptance before DerpFest Stage B.
6. The separate local Agent remains read-only and is not required for ROUND54. Do not create another firmware task.

## Shared project baseline

- Device: Huawei MatePad 11 (2021), DBY-W09, KONA / SM8250 rev 2.1.
- Fixed ACK source: `aosp-mirror/kernel_common@8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a`.
- ROUND12 AVB inspection: uploaded but BLOCKED at the trusted local AVB-tool gate.
- ROUND13 PM8150 mode/DRMS audit: complete.
- ROUND14 MMCX/MX ARC corner/dropout and S8 static enable audit: complete.
- ROUND49/50/51: UFS regulator lifecycle and ARC source interpretation complete at source-review level.
- ROUND52: UFS binding/driver drafts are present; end-to-end strict in-memory hunk-position simulation passed 15/15.
- ROUND53: Kconfig static dependency closure report created; actual Kconfig resolution, final `.config`, Kleaf build and boot remain unrun.

No device was unlocked, rooted, flashed or written; no actual kernel build or device boot is claimed.
