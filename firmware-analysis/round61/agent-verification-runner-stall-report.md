# Agent Verification Report — ROUND61 Hosted Runner "Stall"

- **Report type:** Independent verification (third-party, read-only)
- **Executor:** Independent verification agent (local WorkBuddy agent, Windows 11 + WSL2), acting as the "Agent 3" requested by the taskbook
- **Taskbook under execution:** `kernel-baseline/round61/AGENT_VERIFICATION_TASKBOOK_SECOND_AI.md` (blob `0a215a6e`, 4729 B), branch `ai-parallel/stagea-port-until-boot`
- **Repository observed:** `hhdy/matepad11-dby-w09-agent-reports` (public, admin-scoped token)
- **Verification window (UTC):** 2026-11-24T18:10:54Z → 2026-11-24T18:21:30Z (primary collection), with continued polling
- **Verdict:** `NOT_STALLED / ALIVE_AND_ADVANCING` — the two runs are **not** orphaned and **not** stale; the reported "stall" is an **observability artifact** produced by a single monolithic workflow step combined with a misuse of `updated_at` as a heartbeat.
- **New build run justified:** **No.**

---

## 1. Scope and constraints honoured

This report addresses only the runner-stall diagnosis requested in the taskbook.

Not performed: no kernel source / patch / DTS / Kconfig / boot image / AVB modification; no workflow change applied; no run cancelled; no new build started; no device interaction of any kind. All GitHub access was read-only (`GET`), except the later publication of this report file itself (a new `.md`, which is not a workflow trigger path).

Every statement below is tagged as **[OBSERVED]** (read directly from GitHub API/logs) or **[INFERRED]** (reasoning from observations).

---

## 2. Run and job states — exact readings

Collection timestamp for this table: **2026-11-24T18:16:18Z**.

| Field | Run 45455279898 | Run 45453412267 |
|---|---|---|
| Workflow | ROUND61 manifest-pinned Kleaf target and Image build (id 429302330) | same |
| Display title | "ROUND61: restart manifest-pinned Kleaf build after hosted run stopped reporting progress" | "ROUND61: retry pinned Kleaf build after narrow checkpatch false-positive handling" |
| Event / attempt | push / 1 | push / 1 |
| `head_sha` | `4877a6d2afb643e69e1ac68685983c4495e20936` | `1b833dd74ddb39dd90f7a691f62ce313e0dfe5d2` |
| `created_at` | 2026-11-24T18:03:14Z | 2026-11-24T17:52:53Z |
| `run_started_at` | 2026-11-24T18:03:14Z | 2026-11-24T17:52:53Z |
| `updated_at` | 2026-11-24T18:03:18Z | 2026-11-24T17:52:57Z |
| `status` / `conclusion` | in_progress / null | in_progress / null |
| Job id | 138662922161 | 138656311747 |
| Job `started_at` | 2026-11-24T18:03:17Z | 2026-11-24T17:52:56Z |
| Job `completed_at` | null | null |
| Runner id / name | 1000000120 / "GitHub Actions 1000000120" | 1000000119 / "GitHub Actions 1000000119" |
| Runner group | GitHub Actions (id 0) | GitHub Actions (id 0) |
| Labels | `ubuntu-22.04` | `ubuntu-22.04` |
| Artifacts | 0 | 0 |
| Timing API (`billable.UBUNTU.total_ms`) | 0 | 0 |

Step-level state **[OBSERVED]** (identical in both runs):

| # | Step | Status | Conclusion | started_at |
|---:|---|---|---|---|
| 1 | Set up job | completed | success | 18:03:18Z / 17:52:57Z |
| 2 | Checkout dedicated implementation branch | completed | success | 18:03:19Z / 17:52:58Z |
| 3 | Sync official Android kernel manifest and build the DBY-W09 Image | **in_progress** | null | **18:03:23Z / 17:52:59Z** |
| 4 | Publish build result to the dedicated branch | pending | null | — |
| 5 | Upload pinned build evidence and Image artifacts | pending | null | — |
| 10 | Post Checkout dedicated implementation branch | pending | null | — |

Elapsed time inside step 3 at 18:16:18Z **[OBSERVED]**:

- Run 45455279898: **12.9 min** of a 180-min job timeout
- Run 45453412267: **23.3 min** of a 180-min job timeout

Both jobs remain registered to a **GitHub-hosted** runner ID and are **not** in `queued` or `waiting` state. GitHub has **not** marked either job failed, cancelled, or "runner lost".

---

## 3. What the code at step 3 actually does

From `.github/workflows/round61-manifest-kleaf-build.yml` **[OBSERVED]** (21 188 B, at branch HEAD):

- `runs-on: ubuntu-22.04`, **`timeout-minutes: 180`** at job level.
- Step 3 is a **single `bash` step** containing the *entire* pipeline:
  1. `apt-get update` + install (bc, bison, flex, libelf, libssl, libncurses, **libtinfo5**, python3-venv, rsync…)
  2. install `repo` launcher
  3. `repo init -u .../kernel/manifest -b common-android17-6.18 --depth=1`
  4. `repo sync -c --no-tags --no-clone-bundle --optimized-fetch -j4`
  5. ACK tag fetch + `checkout --detach 8ad08f75…` + `repo manifest -r`
  6. locate JDK11 / Bazel wrapper / Clang / Rust
  7. apply 9 patches (`git apply --check` then `git apply`)
  8. `checkpatch.pl` × 3, `go install buildifier`, `buildifier -mode=check`, unit tests
  9. `tools/bazel query`, `tools/bazel cquery --output=files`
  10. `tools/bazel build --jobs=3 --verbose_failures //common:dby_w09`
  11. validate `.config`, copy Image/System.map/vmlinux, hash them

Because **all of the above is one step**, the Actions API can only ever report `step 3: in_progress` from the beginning of `repo init` until the very end of the Image build. There is no intermediate state to report, and no `steps[]` timestamp advances.

There is **no `concurrency:` block** in the workflow **[OBSERVED]** (grep returns nothing). Consequently run 45453412267 (17:52) was still running when run 45455279898 (18:03) was started; the two builds duplicate the same work on two separate runners.

---

## 4. Log retrieval — all routes attempted, with a control experiment

The taskbook's central difficulty is the `BlobNotFound` response. The following routes were attempted **[OBSERVED]**:

| # | Route | Result |
|---|---|---|
| A1 | `GET /repos/{o}/{r}/actions/jobs/138662922161/logs` | HTTP **404**, Azure XML `<Code>BlobNotFound</Code>`, `Time: 2026-11-24T18:10:54.3488616Z` |
| A2 | `GET /repos/{o}/{r}/actions/jobs/138656311747/logs` | HTTP **404**, `BlobNotFound`, `Time: 2026-11-24T18:10:56.6039473Z` |
| A3 | `GET /actions/runs/45455279898/logs` | HTTP **404**, JSON `{"message":"Not Found"}` |
| A4 | `GET /actions/runs/45453412267/logs` | HTTP **404**, JSON `{"message":"Not Found"}` |
| A5 | `GET /actions/runs/45455279898/attempts/1/logs` | HTTP **404**, JSON `{"message":"Not Found"}` |
| A6 | `GET /actions/runs/{id}/artifacts` | HTTP 200, `total_count: 0` (expected: step 5 has not run) |
| A7 | Web UI job page, unauthenticated (public repo) | HTTP 200, 152 924 B HTML — but contains `Sign in` prompts and **no log body** |
| A8 | Web UI job page with `Authorization: Bearer <PAT>` | HTTP 200, **byte-identical 152 924 B** — a PAT is not a web session cookie, so no logs |
| A9 | **Control:** `GET /actions/jobs/138652239787/logs` (the *completed* job of run 45452267778) | HTTP **200**, `Content-Type: text/plain`, **53 617 B** of real log |

**A9 is the decisive control.** The very same endpoint that returns `BlobNotFound` for the two live jobs returns a complete `text/plain` log for a *finished* job. Therefore `BlobNotFound` means precisely "**the log blob has not been uploaded yet, because the job has not finished**" — it does **not** mean "the runner is gone", and it must not be read as evidence about runner liveness.

**A7 additionally shows** why the UI cannot help either: in the server-rendered HTML, step 3's `<check-step>` element carries `data-started-at="2026-11-24T18:03:23Z"` and **`data-log-url` is empty**, while steps 1 and 2 (completed) do have a `data-log-url`. GitHub only mints a log URL after a step completes. Live streaming logs exist only inside an authenticated browser session's WebSocket, which is not exposed to any API token.

**Conclusion for taskbook item 3:** logs are genuinely unavailable for these runs **by platform design**, and this is not a symptom of the runner. All nine routes above are documented so the limitation is on record rather than guessed at.

---

## 5. Duration calibration — why 13 / 23 minutes is normal

### 5.1 The observed history of this workflow

All 12 runs of workflow 429302330, ordered **[OBSERVED]**:

| Run | head_sha | status | conclusion | created → updated |
|---|---|---|---|---|
| 45455279898 | 4877a6d2 | in_progress | — | live (see §2) |
| 45453412267 | 1b833dd7 | in_progress | — | live (see §2) |
| 45452267778 | 4a2db766 | completed | failure | **336 s** |
| 45450833773 | a9606778 | completed | failure | **423 s** |
| 45450671170 | 1db78203 | completed | failure | **327 s** |
| 45449838606 | 9963b227 | completed | failure | **510 s** |
| 45449517911 | 558c2d2d | completed | failure | **323 s** |
| 45448441783 | 1f62f80c | completed | failure | **367 s** |
| 45446186250 | 17fc9603 | completed | failure | **381 s** |
| 45444678133 | 82f218ad | completed | failure | **370 s** |
| 45442933079 | 9934bf73 | completed | failure | **339 s** |
| 45441246235 | 2229d9b8 | completed | failure | **22 s** |

Maximum ever observed: **510 s (8.5 min)**. Median ≈ 350 s.

### 5.2 Why the history is short — and why it is not a comparison baseline

The short runs are short **because they aborted early at cheap gates**, not because the pipeline is cheap. From the retrieved log of run 45452267778 (`job_138652239787.log`, 53 609 chars) **[OBSERVED]**, the real per-stage timeline is:

| Wall clock (UTC) | Event |
|---|---|
| 17:46:33 | job start |
| 17:46:35 | step 3 begins; apt install, `repo init` |
| **17:51:34** | **`repo sync has finished successfully.`** → sync took **301 s (5m01s)** for `--depth=1 -c -j4` |
| 17:51:38 | ACK tag fetched, `checkout 8ad08f75` |
| 17:51:41 | `repo manifest -r` written; `MODULE.bazel.lock absent before Bazel analysis` |
| 17:51:42 | JDK 11.0.15, Bazel 8.7.0 server up, clang 3.8.275480, rustc 1.91.1-dev located |
| 17:51:46–47 | **all 9 patches applied** (`git apply --check` + `git apply`), diffstat `8 files changed, 609 insertions(+), 7 deletions(-)` |
| 17:51:47 | checkpatch patch 1: `total: 0 errors, 0 warnings, 0 checks, 232 lines`; patch 2: `0/0/0, 104 lines` |
| 17:51:48 | checkpatch patch 3: `CHECK: Avoid CamelCase: <init_load_uA>` → `total: 0 errors, 0 warnings, 1 checks` → step exits 1 |
| 17:51:50 | runner cleanup |

So: **everything up to and including checkpatch costs ≈ 5m15s** on this runner, of which 5m01s is the manifest sync. The 10 previous failures all occurred at or before this point (exit 127 = clang `libtinfo.so.5` missing; exit 1 = the CAMELCASE CHECK).

**Therefore the two live runs, at 12.9 and 23.3 minutes, have necessarily passed the checkpatch gate** — the only gate that has recently rejected this branch. They are inside the remaining stages: `go install buildifier`, `tools/bazel query`, `tools/bazel cquery`, and the cold `tools/bazel build`.

### 5.3 Cost of the remaining stage

- Hosted runner resources, from the branch's own published result file `hosted-build-latest.md` **[OBSERVED]**: `CPUs=4`, `/dev/root 146G, 91G used, 55G avail`; JDK11 / clang-3289846 / rustc 1.91.1.p2 all resolved.
- Local calibration **[OBSERVED]**: this verification host has **12 vCPU / 7 GiB**, and a *warm-source, cold-build* `tools/bazel build //common:dby_w09` with `--jobs=2` took **360.3 s** (ROUND18, exit 0, 44 820 992 B Image).
- The hosted job uses `--jobs=3` on **4 vCPU**. A cold arm64 kernel build at 4 vCPU is realistically **2–5× slower** than 12 vCPU, i.e. **12–30 min** for the compile alone, plus bzlmod/external-dependency fetch for a workspace with no `MODULE.bazel.lock` (explicitly logged as absent), plus the `repo sync` 5 min already spent.

**Expected total step-3 duration: roughly 30–60 min, with a plausible tail to 100 min.** A run sitting at 13 or 23 min is not merely "not stalled" — it is **on schedule**.

---

## 6. Root cause of the *apparent* stall

Three premises in the taskbook are each invalid. The diagnosis is the conjunction of them.

### Premise 1 — "`updated_at` never advanced, therefore status is stale" → **invalid**

`updated_at` is not a heartbeat. It is bumped only when the **run or job changes state**. Proof from this very workflow **[OBSERVED]**: run 45452267778 was `created_at 17:46:31` and `updated_at 17:52:07` — `updated_at` equals the moment of *completion*, with no intermediate bumps during its 336 s of real work. Likewise run 45453412267's `updated_at` is `17:52:57`, i.e. job-start +1 s, and it will not move again until step 3 finishes or the job fails.

A frozen `updated_at` therefore carries **zero information** about whether the step is progressing, especially when the step is a 40-minute monolith. Using it as a liveness signal guarantees a false "stall" verdict on every long build.

### Premise 2 — "log endpoint returns BlobNotFound, therefore no evidence the runner is alive" → **invalid**

Refuted by the control experiment A9 (§4): the same endpoint returns HTTP 200 with 53 617 B of text for a completed job. GitHub uploads a job's log blob **at completion**. `BlobNotFound` on a live job is the expected, documented-by-behaviour result. It is an absence of evidence *by design*, not evidence of absence.

### Premise 3 — "20 minutes without a terminal state is abnormal" → **invalid**

The only reason the history looks fast is that all 10 prior runs died at a cheap gate (§5.2). Once a run survives checkpatch, it enters the one genuinely expensive stage, which cannot finish in ~5 minutes on 4 vCPU. Comparing a survivor's elapsed time against the abort-time of failures is a category error.

### Contributing design defect — the real cause of the confusion

Step 3 being **one monolithic step** is what makes this ambiguous. The API's finest granularity is `steps[]`; with a single step, the API is structurally incapable of saying "sync done, patches done, checkpatch done, now building". A reviewer looking only at the API sees an unchanging `in_progress` for the entire 30–60 min and has no way to distinguish progress from a hang. **The observability gap is self-inflicted.**

Secondary defect: **no `concurrency:` block**. Run 45455279898 was launched as a "recovery" while 45453412267 was still alive, so two identical builds now consume two runners, and the branch's publish step has to arbitrate between them (it does so correctly: it compares the existing `Workflow run ID` and refuses to overwrite a newer result — but that is a mitigation, not a fix).

### Confidence

| Claim | Confidence |
|---|---|
| Both jobs are attached to live hosted runners and executing, not orphaned | **High (~85 %)** |
| The "stall" is an observability artifact, not a runner fault | **High (~90 %)** |
| Both runs will reach a terminal state without manual intervention | **Medium-high (~80 %)** — bounded by `timeout-minutes: 180` |
| The remaining stage is the Bazel build (rather than some new hang inside step 3) | **Medium (~70 %)** — not directly observable; see §7 for the falsifiable test |

The residual uncertainty is honest: I cannot read live CPU, live log, or process state on a GitHub-hosted runner. What I *can* say is that every observable signal that would indicate an orphan (job failure, cancellation, runner-loss annotation, `queued` regression, step rollback) is **absent**, and every signal consistent with normal long execution is **present**.

---

## 7. Falsifiable predictions and the decision deadline

Per taskbook item 5 (has either run been superseded?) **[OBSERVED]**:

- Branch HEAD is now `84efbb7223b58b9ff68b480a1fab57f877dbacd0` (2026-11-24T18:07:40Z), whose only change is `kernel-baseline/round61/PROGRESS.md`.
- The workflow triggers **only** on pushes that touch `kernel-baseline/round61/run-manifest-kleaf-build.txt`. `84efbb72` (and `2c0d083e`, which added the taskbook) do **not** match, so **no third run exists or has been queued**.
- `4877a6d2` (run B's trigger) and `1b833dd7` (run A's trigger) each modified exactly that one trigger file — consistent with the `push` events recorded.

So run 45453412267 is superseded **in intent** by 45455279898, but is **not cancelled and still running** — it is a duplicate, not a stale record.

Predictions that would confirm this report (all times UTC):

1. **Run 45453412267** (step 3 from 17:52:59) reaches a terminal state in the window **18:30 – 19:35** (38–100 min). 
2. **Run 45455279898** (step 3 from 18:03:23) reaches a terminal state in the window **18:40 – 19:45**.
3. On completion, `GET /actions/jobs/{job_id}/logs` flips from `404 BlobNotFound` to `200 text/plain`, and `artifacts.total_count` flips from 0 to 1 (`round61-ack-6.18.33-image-build`).

**Falsification / escalation threshold:** if **either** run's step 3 exceeds **~110 minutes** of elapsed time (run A ≈ 19:43Z, run B ≈ 19:53Z) with no transition, the "alive and building" hypothesis should be abandoned for that run and it should be treated as a genuine hang. Absolute backstop: GitHub will fail the job itself at **180 min** (run A ≈ 20:53Z, run B ≈ 21:03Z).

---

## 8. Recommended next action

**Decision: wait. Do not start a new run. Do not cancel yet.**

1. **Do not create a third run.** It would add a third concurrent duplicate build, consume a third runner, produce no new diagnostic information, and worsen the branch-publish arbitration. Taskbook §3 already limits "no more than one new build"; the correct number here is **zero**.
2. **Do not cancel either run before the escalation threshold.** Cancelling destroys the only in-flight attempt to get past checkpatch, which is precisely what has blocked all 10 previous runs. If the owner wants to reduce cost, cancelling the **older** run (45453412267) is the reasonable choice — it is the one superseded in intent — but this requires explicit owner authorization and is not a diagnosis-driven action.
3. **Keep a single watcher on the terminal state** by polling `GET /actions/runs/{id}/jobs` at ~5 min intervals. Either of two transitions ends the wait: `step 3 → completed`, or `status → completed` + `artifacts.total_count > 0`.
4. **When it finishes, fix the observability defect (this is the durable remedy):** split the monolithic step 3 into separate steps — `preflight`, `repo init/sync`, `pin ACK + manifest`, `toolchain discovery`, `apply patches`, `checkpatch + buildifier + unit tests`, `bazel query/cquery`, `image build`, `validate + hash`. The Actions API then exposes a real per-step `started_at`/`completed_at` timeline and a "stall" can be localised in one API call instead of requiring a third-party investigation.
5. **Add concurrency control** (see §9) so a "recovery" trigger cancels the superseded run instead of racing it.
6. **Stop using `updated_at` as a heartbeat** in the ROUND61 watchdog logic; use `steps[].started_at` of the current step, or (after fix 4) the last completed step.

Whether a new run is justified: **no**, not while these two are alive, and not before the escalation threshold of §7.

---

## 9. Proposed minimal workflow diff (not applied — awaiting approval)

Taskbook §3 requires proposing rather than applying. Two changes, in priority order.

**(a) Concurrency guard — prevents duplicate builds (4 added lines):**

```yaml
# insert after the existing "permissions:" block, before "jobs:"
concurrency:
  group: round61-manifest-kleaf-build
  cancel-in-progress: true
```

Effect: the 18:03 "recovery" push would have cancelled the 17:52 run instead of running alongside it. Note this changes behaviour (automatic cancellation), so it should be an explicit owner decision.

**(b) Observability — split step 3 into per-stage steps.** The substance is unchanged; only `name:` boundaries and `if: always()` on the publication step are affected. Sketch:

```yaml
      - name: Preflight and toolchain install
        run: | …apt-get install…
      - name: Repo init and sync at immutable manifest
        run: | …repo init/sync…; test "$(git -C .repo/manifests rev-parse HEAD)" = "$MANIFEST_COMMIT"
      - name: Pin ACK source and record manifest
        run: | …fetch tag, checkout 8ad08f75, repo manifest -r…
      - name: Discover manifest-provided toolchain
        run: | …JDK/Bazel/Clang/Rust…
      - name: Apply ordered patch series
        run: | …9 × git apply --check && git apply…
      - name: Strict checkpatch, buildifier and unit tests
        run: | …
      - name: Bazel query and cquery
        run: | …tools/bazel query / cquery…
      - name: Build DBY-W09 Image
        run: | …tools/bazel build --jobs=3…   # the long pole, isolated
      - name: Validate config and hash artifacts
        run: | …
```

Because environment variables such as `WORK`, `ART`, `REPORT` and `stage` currently live inside one shell, they must move to job-level `env:` (e.g. `WORK: ${{ runner.temp }}/ack-6.18.33`). The `finish()` trap that writes `round61-result.md` would be retained on the build step. This is a behaviour-preserving refactor except for the improved API granularity.

---

## 10. Explicit limitations of this verification

Documented so the acceptance criteria are met by disclosure rather than by inference:

- **No live log access.** All nine routes in §4 were attempted; GitHub exposes job logs only after completion, and live streaming requires a browser session. The limitation is the platform's, reproduced here with a control experiment rather than asserted.
- **No hosted-runner process/CPU visibility.** GitHub-hosted runners expose no `GET /actions/runners/{id}` detail for ephemeral runners (that endpoint is self-hosted only). Liveness is therefore established by state-consistency and duration-calibration reasoning, not by direct process observation.
- **No artifact, `.config`, Image, query or cquery output exists yet** for either run (`artifacts.total_count = 0`). This report claims **none**, consistent with taskbook §3 ("Do not invent a successful Bazel query, cquery, final `.config`, or Image artifact").
- **Phase status is not re-adjudicated here.** This report concerns runner observability only. It neither confirms nor disputes the branch's Phase A/B/C/D/E/F/G labels.
- **Post-report observation window.** A background poller was left running against both runs; any state transition observed after this report's timestamp is appended in §11 if present.

---

## 11. Running observation log

| UTC | Observation |
|---|---|
| 18:10:54Z | job 138662922161 logs → 404 `BlobNotFound` (`RequestId 5f95e3eb…`) |
| 18:10:56Z | job 138656311747 logs → 404 `BlobNotFound` (`RequestId 20fd37d0…`) |
| 18:12:39Z | both runs `in_progress`; steps 1–2 success, step 3 in progress, 4/5/10 pending; artifacts 0; timing 0 ms |
| 18:12:56Z | branch HEAD `84efbb72`; no run newer than 18:03:14Z; workflow has no `concurrency` |
| 18:13:47Z | `check-runs` for both head SHAs: single check `manifest-kleaf-build`, `status=in_progress`, no `output.summary` |
| 18:14:41Z | background poller started, 60 s interval |
| 18:14:53Z | alternate routes A3/A5 → 404 JSON; A2/A3 web HTML → 200 but no log body; **A9 control → 200 `text/plain` 53 617 B** |
| 18:16:18Z | step-3 elapsed: run B **12.9 min**, run A **23.3 min**; both far beyond the 8.5 min historical maximum |
| 18:15:47Z – 18:21:30Z | poller reports `SAME` on every interval — no regression, no failure, no step rollback |

No state transition occurred during the primary observation window, which is itself expected: the runs are inside the long build stage.
