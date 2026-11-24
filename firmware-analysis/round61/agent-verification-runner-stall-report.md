# Agent Verification Report — ROUND61 Hosted Runner "Stall"

- **Report type:** Independent verification (third-party, read-only)
- **Executor:** Independent verification agent (local WorkBuddy agent, Windows 11 + WSL2), acting as the "Agent 3" requested by the taskbook
- **Taskbook under execution:** `kernel-baseline/round61/AGENT_VERIFICATION_TASKBOOK_SECOND_AI.md` (blob `0a215a6e`, 4729 B), branch `ai-parallel/stagea-port-until-boot`
- **Repository observed:** `hhdy/matepad11-dby-w09-agent-reports` (public, admin-scoped token)
- **Verification window (UTC):** 2026-11-24T18:10:54Z → 2026-11-24T18:30Z (observation continues; the decisive event landed inside the window)
- **Revision:** rev 2 — revised after the flagged run reached a terminal state during observation. Rev 1 (18:21Z) concluded `NOT_STALLED / ALIVE` at ~85 % confidence; rev 2 upgrades this to **confirmed by direct outcome**.

## VERDICT

**`CONFIRMED_NOT_STALLED — THE FLAGGED RUN SUCCEEDED.`**

Run **45453412267** — the run the taskbook describes as having "stopped reporting progress" and whose status was deemed untrustworthy — **completed successfully at 2026-11-24T18:22:49Z**, exit 0, and published both the Image and a 210 MB evidence artifact.

| Item | Value |
|---|---|
| Run | 45453412267 (job 138656311747) |
| Final status / conclusion | `completed` / **`success`** |
| Step 3 duration | 17:52:59Z → 18:21:43Z = **28 m 44 s** |
| Job duration | 17:52:56Z → 18:22:48Z = **29 m 52 s** |
| Bazel build | `Elapsed time: 1348.097s` (22 m 28 s), 775 actions, "Build completed successfully" |
| Config validation | `PASS: all 31 required storage-first symbols are present as =y` |
| Artifact | `round61-ack-6.18.33-image-build`, **210 436 545 B**, artifact id 14951184014 |
| Published commit | `019463c350223a6b79654cea5f074ece6c9961c5` — "ROUND61: publish hosted manifest and Image build result" |
| **New build run justified** | **No — the objective is already achieved by the run that was declared stalled** |

The "stall" was an **observability artifact**, not a runner fault: a single monolithic workflow step hid a 22½-minute invisible build action, and `updated_at` was being read as a heartbeat when it only changes on state transitions.

---

## 1. Scope and constraints honoured

This report addresses only the runner-stall diagnosis requested in the taskbook.

Not performed: no kernel source / patch / DTS / Kconfig / boot image / AVB modification; no workflow change applied; **no run cancelled**; **no new build started**; no device interaction. All GitHub access was read-only (`GET`), except the later publication of this report file itself (a new `.md`, which is not a workflow trigger path).

Statements are tagged **[OBSERVED]** (read directly from GitHub API/logs) or **[INFERRED]** (reasoning).

---

## 2. Run and job states — readings at 18:16:18Z, before completion

| Field | Run 45455279898 | Run 45453412267 |
|---|---|---|
| Workflow | ROUND61 manifest-pinned Kleaf target and Image build (id 429302330) | same |
| Display title | "restart manifest-pinned Kleaf build after hosted run stopped reporting progress" | "retry pinned Kleaf build after narrow checkpatch false-positive handling" |
| `head_sha` | `4877a6d2afb643e69e1ac68685983c4495e20936` | `1b833dd74ddb39dd90f7a691f62ce313e0dfe5d2` |
| `created_at` / `run_started_at` | 18:03:14Z | 17:52:53Z |
| `updated_at` at the time | 18:03:18Z | **17:52:57Z** ← frozen, the premise of the "stall" claim |
| Job id | 138662922161 | 138656311747 |
| Job `started_at` | 18:03:17Z | 17:52:56Z |
| Runner | id 1000000120, "GitHub Actions 1000000120", group `GitHub Actions` (0), label `ubuntu-22.04` | id 1000000119, same group/label |
| Artifacts at the time | 0 | 0 |
| Timing API | `billable.UBUNTU.total_ms: 0` | `billable.UBUNTU.total_ms: 0` |

Step granularity at the time (identical shape in both runs) **[OBSERVED]**: steps 1–2 `completed/success`; **step 3 `in_progress`, `started_at` 17:52:59Z / 18:03:23Z**; steps 4, 5, 10 `pending`.

Note that the API could only ever say "step 3 in progress". Everything from `repo init` to the finished `Image` lives inside that one step (§3).

---

## 3. What step 3 actually does — and why it is unobservable

From `.github/workflows/round61-manifest-kleaf-build.yml` **[OBSERVED]** (21 188 B at branch HEAD):

- `runs-on: ubuntu-22.04`, **`timeout-minutes: 180`** at job level.
- Step 3 is a **single `bash` step** containing the entire pipeline: apt install → install `repo` → `repo init --depth=1` → `repo sync -c --no-tags --no-clone-bundle --optimized-fetch -j4` → ACK tag pin + `repo manifest -r` → toolchain discovery → 9 patches → `checkpatch` ×3 + `go install buildifier` + `buildifier -mode=check` + unit tests → `tools/bazel query` → `tools/bazel cquery --output=files` → `tools/bazel build --jobs=3 --verbose_failures` → validate `.config`, copy and hash Image/System.map/vmlinux.
- **No `concurrency:` block** exists **[OBSERVED]** (grep of the workflow returns nothing). Run 45455279898 (18:03) was therefore started while run 45453412267 (17:52) was still building.

Consequence: while a run is inside step 3, the API exposes **no** intermediate state. A reviewer polling only run/job/step status sees an unchanging `in_progress` for the whole 28 minutes and cannot distinguish progress from a hang. This is the mechanical origin of the false "stall" verdict.

---

## 4. Log retrieval — all routes attempted, with a decisive control

The taskbook's central difficulty is the `BlobNotFound` response. Routes attempted **[OBSERVED]**:

| # | Route | Result |
|---|---|---|
| A1 | `GET /actions/jobs/138662922161/logs` (live) | **404**, Azure XML `<Code>BlobNotFound</Code>`, `Time: 18:10:54.3488616Z` |
| A2 | `GET /actions/jobs/138656311747/logs` (live) | **404**, `BlobNotFound`, `Time: 18:10:56.6039473Z` |
| A3 | `GET /actions/runs/45455279898/logs` | **404**, JSON `{"message":"Not Found"}` |
| A4 | `GET /actions/runs/45453412267/logs` | **404**, JSON `{"message":"Not Found"}` |
| A5 | `GET /actions/runs/45455279898/attempts/1/logs` | **404**, JSON `{"message":"Not Found"}` |
| A6 | `GET /actions/runs/{id}/artifacts` | 200, `total_count: 0` (step 5 had not run) |
| A7 | Web job page, unauthenticated (public repo) | 200, 152 924 B HTML — `Sign in` prompts, **no log body** |
| A8 | Web job page with `Authorization: Bearer <PAT>` | 200, **byte-identical** 152 924 B — a PAT is not a web session, so no logs |
| A9 | **Control:** `GET /actions/jobs/138652239787/logs` (the *completed* job of run 45452267778) | **200**, `text/plain`, **53 617 B** of real log |

**A9 is decisive.** The same endpoint returning `BlobNotFound` for the live jobs returns a full `text/plain` log for a *finished* job. So `BlobNotFound` means exactly "**the log blob is not uploaded yet, because the job has not finished**" — it carries **no information** about runner liveness.

**A7** explains why the UI cannot substitute: the server-rendered `<check-step>` for step 3 has `data-started-at="…"` and an **empty `data-log-url`**, while completed steps 1–2 do have one. GitHub mints a log URL only after a step completes; live streaming exists only inside an authenticated browser session's WebSocket, which no API token can reach.

**Final confirmation of the mechanism:** once run 45453412267 finished, `GET /actions/jobs/138656311747/logs` returned **HTTP 200** with **66 898 B** of log. The endpoint never was broken; the job simply had not finished.

**Conclusion for taskbook item 3:** logs were genuinely unavailable for the live runs **by platform design** — and this was not a symptom of the runner.

---

## 5. Duration calibration — and the measured ground truth

### 5.1 History of this workflow

All 12 runs of workflow 429302330 **[OBSERVED]**:

| Run | head_sha | status | conclusion | duration |
|---|---|---|---|---|
| 45455279898 | 4877a6d2 | in_progress at 18:16 (still at 18:35) | — | — |
| **45453412267** | 1b833dd7 | **completed** | **success** | **1796 s (29 m 56 s)** |
| 45452267778 | 4a2db766 | completed | failure | 336 s |
| 45450833773 | a9606778 | completed | failure | 423 s |
| 45450671170 | 1db78203 | completed | failure | 327 s |
| 45449838606 | 9963b227 | completed | failure | 510 s |
| 45449517911 | 558c2d2d | completed | failure | 323 s |
| 45448441783 | 1f62f80c | completed | failure | 367 s |
| 45446186250 | 17fc9603 | completed | failure | 381 s |
| 45444678133 | 82f218ad | completed | failure | 370 s |
| 45442933079 | 9934bf73 | completed | failure | 339 s |
| 45441246235 | 2229d9b8 | completed | failure | 22 s |

The 10 historical failures span **22–510 s** because they aborted at cheap gates; the single success took **1796 s**, i.e. 3.5× the longest failure.

### 5.2 What the failures actually aborted on

From the retrieved log of run 45452267778 (`53 609` chars) **[OBSERVED]**:

| UTC | Event |
|---|---|
| 17:46:33 | job start; apt install, `repo init` |
| **17:51:34** | **`repo sync has finished successfully.`** → sync = **301 s**, for `--depth=1 -c -j4` |
| 17:51:38 | ACK tag fetched; `checkout 8ad08f75` |
| 17:51:41 | `repo manifest -r` written; `MODULE.bazel.lock absent before Bazel analysis` |
| 17:51:42 | JDK 11.0.15, Bazel 8.7.0 server up, clang, rustc located |
| 17:51:46–47 | **all 9 patches applied**; diffstat `8 files changed, 609 insertions(+), 7 deletions(-)` |
| 17:51:47 | checkpatch: `0 errors, 0 warnings, 0 checks, 232 lines` then `0/0/0, 104 lines` |
| 17:51:48 | checkpatch #3: `CHECK: Avoid CamelCase: <init_load_uA>` → `0 errors, 0 warnings, 1 checks` → exit 1 |

The other failures before it were `exit 127` from `clang.real: error while loading shared libraries: libtinfo.so.5` — fixed later by installing `libtinfo5`. **All 10 failures died at or before checkpatch**, within ~5–8.5 min. This is why the historical envelope looks fast; it is an artefact of aborting early, not of the pipeline being cheap.

### 5.3 The successful run's measured breakdown

From the completed log of run 45453412267 (`66 890` chars) **[OBSERVED]**:

| UTC | Event | Phase cost |
|---|---|---|
| 17:52:56 | job start | — |
| 17:52:59 | step 3 starts; apt + `repo init` | |
| ~17:58:0x | `repo sync` complete (same ~5 min as the calibration run) | ~5 m |
| 17:58:56 | unit tests: **`Ran 9 tests in 0.009s` → `OK`**; checkpatch and buildifier gates passed | |
| 17:59:06 | `Analyzing: target //common:dby_w09` (bazel query) | |
| 17:59:12 | cquery: `.config`, `Image`, `System.map`, `vmlinux` | **373 s (6 m 13 s)** end-to-end to here |
| 17:59:12 → 18:21:41 | `Building kernel (dby_w09_storage_first.fragment)` progress 1s → 1241s → `no actions running` | **1348 s (22 m 28 s)** |
| 18:21:41 | `PASS: all 31 required storage-first symbols are present as =y`; `INFO: Build completed successfully, 775 total actions` | |
| 18:21:43 | step 3 completes; `ROUND61_MANIFEST_KLEAF_IMAGE_BUILD=PASS`; publish commit `019463c350` | |
| 18:21:45–18:21:56 | artifact upload (210 436 545 B) | |
| 18:22:48 / 18:22:49 | job / run complete, `success` | |

**Decomposition: 6 m 13 s of cheap work, then 22 m 28 s of a single invisible build action, then 13 s of publication.** The build occupied 78 % of the step, and was the *only* thing happening during the period the second AI judged "no progress".

### 5.4 Cross-host calibration

- This verification host: **12 vCPU / 7 GiB**; a cold `tools/bazel build //common:dby_w09` with `--jobs=2` took **360.3 s** (ROUND18, exit 0).
- Hosted: **4 vCPU** (from the run's own published `Runner resources: CPUs=4`), `--jobs=3`, took **1348 s**.
- Ratio **3.74×** — squarely inside the 2–5× range predicted in rev 1. But rev 1's *total* estimate (30–60 min, tail 100 min) was too pessimistic on the low end: the real answer was 28 m 44 s, because the pre-build overhead is only 6 min, not 11+. Corrected: **expected step-3 wall time ≈ 6 min + 3.5–4× the local build time.**

---

## 6. Root cause of the *apparent* stall

### Premise 1 — "`updated_at` never advanced, therefore the status is stale" → **invalid, and now disproven**

`updated_at` is not a heartbeat; it moves only on run/job state transitions. Proof **[OBSERVED]**: run 45452267778 was `created_at 17:46:31` / `updated_at 17:52:07` — equal to its *completion* moment, with no bumps during 336 s of real work. Run 45453412267's `updated_at` stayed at `17:52:57` for the entire 29 minutes and then jumped to `18:22:49` **exactly at completion**. The frozen value carried zero information; it was not evidence of anything.

### Premise 2 — "BlobNotFound means there is no trustworthy output" → **invalid**

Refuted by control A9 (§4) and by the post-completion observation: the same endpoint returned 404 while running and 200 `text/plain` / 66 898 B after finishing. Absence of logs *was by design*, not evidence of absence of a runner.

### Premise 3 — "20 minutes without a terminal state is abnormal" → **invalid**

The history was short only because all previous runs aborted at checkpatch within 5–8.5 min. Once a run survives that gate it enters a 22½-minute build that cannot be observed. Comparing a survivor's elapsed time to the abort times of failures is a category error — and here it produced a false negative on a run that went on to succeed.

### Contributing design defects (the real, fixable causes)

1. **Monolithic step 3.** The API's finest granularity is `steps[]`; with one step, a 22-min build is structurally invisible. This is what made an obviously-progressing run look dead.
2. **No `concurrency` control.** A "watchdog recovery" push at 18:03:14 started a duplicate build **4 m 15 s into a build that later succeeded**. Cost: one extra ~30-min runner allocation and one extra ~200 MB artifact.

### Confidence (rev 2, post-outcome)

| Claim | Confidence |
|---|---|
| Run 45453412267 was alive and progressing the whole time | **Confirmed by outcome** |
| The "stall" was an observability artifact, not a runner fault | **High (~95 %)** |
| Run 45455279898 will also succeed (it is a duplicate of the same source tree) | **High** — its only source delta is the trigger `.txt` |
| A repeated "stall" will recur on the next long build unless §8 is applied | **High** |

---

## 7. Predictions vs outcomes (self-scoring)

| Rev-1 prediction | Outcome |
|---|---|
| Run 45453412267 terminal in **18:30–19:35** | **Wrong on timing** — it completed at **18:21:43**, ~8 min *earlier* than my lower bound. Cause: I over-estimated pre-build overhead at 11 min; it was 6 m 13 s. |
| Run 45455279898 terminal in 18:40–19:45 | **Pending at 18:30** — 26 min into step 3, still `in_progress`, no failure signal |
| On completion, logs flip 404 → 200 and artifacts 0 → 1 | **Correct** — 200 / 66 898 B; artifact `round61-ack-6.18.33-image-build` |
| Substantive claim: not stalled, will finish without intervention | **Correct** |

Being early rather than late does not change the diagnosis, but the calibration error is recorded rather than smoothed over.

---

## 8. Recommended next action

**1. Do not start a new run.** The objective — a manifest-pinned ACK-derived DBY-W09 Image — is already produced, validated and published by the very run that was declared stalled.

**2. Treat run 45455279898 as strictly redundant.** Its `head_sha 4877a6d2` differs from `1b833dd7` only in `kernel-baseline/round61/run-manifest-kleaf-build.txt`; the kernel tree is identical, so its result can only duplicate the existing one. If the owner wants to reclaim ~30 min of runner time and one 200 MB artifact, cancelling it is reasonable — but that is an owner decision (taskbook §3) and is not required for correctness. If left alone, it will simply overwrite `hosted-build-latest.md` with an equivalent result from a higher run id, which its publish step permits by design.

**3. Do *not* add `cancel-in-progress: true`.** This is a correction to rev 1. With that setting, the 18:03 recovery push would have **cancelled run 45453412267 four minutes into a build that went on to succeed**. The concurrency guard should not be "cancel the old one on every push"; it must be "do not start a second build on a false stall signal".

**4. Replace the watchdog rule.** Current rule: `updated_at` unchanged ⇒ stalled (false positive guaranteed during long builds). Correct rule: take the **current step's `started_at`** from `GET /actions/runs/{id}/jobs` and alert only when its age exceeds a stage-aware budget — for this workflow, ≈ **50 min** (measured 28 m 44 s, ×1.75 headroom), with the hard backstop being `timeout-minutes: 180`. This budget is anchored on measurement, not guesswork: the duplicate run 45455279898 was still healthy at **26 min** in the same step, so any threshold materially below ~45 min would reproduce the same false alarm.

**5. Split step 3 into per-stage steps** (§9b). This is the durable fix: with per-stage steps, the 22-min build becomes its own `in_progress` step with its own timestamps, and "stall" can be localised in one API call. Secondary benefit: a failure reports its stage directly instead of requiring log archaeology.

**6. Fix two reporting defects noticed in the result file** (cosmetic but misleading):
- `Clang path: prebuilts/clang/host/linux-x86/clang-3289846/bin/clang` — that directory reports `Android clang version 3.8.275480`, i.e. it is **not** the compiler Kleaf builds with (`build.config.constants` pins `CLANG_VERSION="r584948c"`). The `find … | sort | head -n 1` heuristic picks the alphabetically first tree, not the pinned one. Report it as "first clang on disk", or resolve the version Kleaf actually uses.
- `Rust path: …/1.91.1.p2/bin/rustc` vs `RUSTC_VERSION="1.91.1.p3"` — same heuristic, same caveat.

No new run is justified: **no.**

---

## 9. Proposed minimal workflow diff (not applied — awaiting approval)

**(a) Concurrency — prevent duplicate builds without killing healthy ones.** Deliberately **not** `cancel-in-progress`:

```yaml
# insert after the existing "permissions:" block, before "jobs:"
concurrency:
  group: round61-manifest-kleaf-build
  cancel-in-progress: false
```

Combined with recommendation 4 (stage-aware watchdog), this removes the incentive to fire a "recovery" push at all. If an explicit supersede is genuinely wanted, cancel the old run by id first, then push — the order matters.

**(b) Observability — split step 3 into per-stage steps.** Behaviour-preserving apart from API granularity:

```yaml
      - name: Preflight and toolchain install
      - name: Repo init and sync at immutable manifest
      - name: Pin ACK source and record manifest
      - name: Discover manifest-provided toolchain
      - name: Apply ordered patch series
      - name: Strict checkpatch, buildifier and unit tests
      - name: Bazel query and cquery
      - name: Build DBY-W09 Image        # the 22-minute long pole, isolated
      - name: Validate config and hash artifacts
```

Because `WORK`, `ART`, `REPORT` and `stage` currently live inside one shell, they must move to job-level `env:` (e.g. `WORK: ${{ runner.temp }}/ack-6.18.33`). The `finish()` trap that writes `round61-result.md` stays on the build step.

---

## 10. Confirmed build outcome and cross-validation against an independent local build

### 10.1 Artifacts produced by run 45453412267 **[OBSERVED]**

| Artifact | Size (B) | SHA-256 |
|---|---:|---|
| `Image` | **44 820 992** | `e3c1cb564f767ed6c9961298b9bafd10473facaddbc92dc38247bd8290400e40` |
| `dby_w09.config` | **238 376** | `5f7fd8b32a4127b7ca10d2333d71e6d10aec7a566cf886251f7bc2af253366d7` |
| `System.map` | — | `144b8f36cc600c9be08e95a9d9428aae21261c7e93364226cf6fb6b985569a64` |
| `vmlinux` | — | `64d9aa42111bf0fe67864eef0e7bc4b6b6cf3588ce7d2971dcc915fb93b71ade` |
| `manifest-pinned.xml` | — | `6449879cd7081345cf0a2e7060a1e40b9edfe1b8b22629263c96f8e2141a1f11` |
| `applied-source.diff` | — | `9be219f2d3cace352c72a9d13c8ddbc05a2bf413a13e45324da7362883248da7` |

Bundled as artifact **`round61-ack-6.18.33-image-build`**, 210 436 545 B, id 14951184014, uploaded 18:21:56Z.

`cquery --output=files` resolved to exactly four products — `.config`, `Image`, `System.map`, `vmlinux` — with **no DTB, no DTBO, no `boot.img`, and no `base_kernel`**, i.e. the target is Image-first, as the taskbook asserted.

Published result file `kernel-baseline/round61/hosted-build-latest.md` (blob `fab98c09`, 6662 B) now reads `Last stage: complete`, `Exit code: 0`, and ends with `BUILD_PASS`.

### 10.2 Independent local reproduction (this agent, ROUND18) **[OBSERVED]**

| Property | Hosted runner (4 vCPU) | Local WSL2 (12 vCPU) | Verdict |
|---|---|---|---|
| `.config` size / SHA-256 | 238 376 / `5f7fd8b3…6d7` | 238 376 / `5f7fd8b3…6d7` | **byte-identical** |
| `Image` size | 44 820 992 | 44 820 992 | identical size |
| `Image` SHA-256 | `e3c1cb56…` | `983b342e…` | differs (see below) |
| Unit tests | `Ran 9 tests` → `OK` | 9 tests pass | same suite, same count |
| `cquery` product set | 4 files, Image-first | 4 files, Image-first | identical |
| Build wall time | 1348 s (`--jobs=3`) | 360 s (`--jobs=2`) | 3.74× |

**The `.config` result is a genuine cross-host cross-validation:** two independent machines, two independent Bazel invocations, two different `--jobs` settings, and the *same* 238 376-byte configuration with the *same* SHA-256. Kconfig resolution and the `dby_w09_storage_first.fragment` + `gki_defconfig` layering are therefore deterministic and reproducible.

**The `Image` hash difference is expected [INFERRED]**: same size, different bytes is the signature of an embedded build-time string (`UTS_VERSION` contains the compile date/time and host), with an identical-length replacement. The two builds differ only in wall-clock timestamp; content-length is preserved, hence identical size. This should not be read as source divergence — the `.config` identity rules that out.

One hosted-side advantage worth recording: `go install github.com/bazelbuild/buildtools/buildifier@latest` **succeeded** in CI and `buildifier -mode=check common/BUILD.bazel` ran as a gate. In ROUND18 the same agent reported buildifier as `NOT_PROVIDED` in the fixed ACK workspace; the hosted workflow is therefore *stronger* on that specific gate.

---

## 11. Limitations of this verification

- **No live log access while running.** All nine routes in §4 were attempted; GitHub exposes job logs only after completion, and the browser live-stream is not reachable with an API token. This limitation was proven with a control experiment rather than asserted, and it dissolved the moment the job completed.
- **No hosted-runner process/CPU introspection.** GitHub exposes no runner detail for ephemeral hosted runners (that endpoint is self-hosted only). Liveness was therefore established indirectly — by state consistency, by duration calibration, and finally by the terminal outcome itself.
- **No re-adjudication of phase status.** This report concerns runner observability only; it neither confirms nor disputes the branch's Phase A–G labels, and it makes no claim about device behaviour, boot, or flashability.
- **Run 45455279898 was still in progress** at the close of this window; no claim is made about its result beyond the assessment that its source tree is identical to the successful run's.

---

## 12. Observation log

| UTC | Observation |
|---|---|
| 18:10:54Z | job 138662922161 logs → 404 `BlobNotFound` (`RequestId 5f95e3eb…`) |
| 18:10:56Z | job 138656311747 logs → 404 `BlobNotFound` (`RequestId 20fd37d0…`) |
| 18:12:39Z | both runs `in_progress`; steps 1–2 success, step 3 in progress, 4/5/10 pending; artifacts 0; timing 0 ms |
| 18:12:56Z | branch HEAD `84efbb72`; no run newer than 18:03:14Z; workflow has no `concurrency` |
| 18:13:47Z | `check-runs` for both head SHAs: `manifest-kleaf-build`, `in_progress`, no `output.summary` |
| 18:14:41Z | background poller started (60 s interval) |
| 18:14:53Z | alternate routes: A3/A5 → 404 JSON; A7/A8 → 200 HTML with no log body; **A9 control → 200 `text/plain`, 53 617 B** |
| 18:16:18Z | step-3 elapsed: run B **12.9 min**, run A **23.3 min** — both beyond the 8.5 min historical maximum |
| **18:24:28Z** | **run 45453412267: steps 3, 4, 5, 10 all `completed/success`; artifacts = 1** |
| **18:25:33Z** | **run 45453412267: `completed` / `success`, `updated_at 18:22:49Z`** |
| 18:26:38Z | poller `SAME` — run B unchanged (step 3 building) |
| 18:27Z | completed job log retrieved: 200, 66 898 B; build `1348.097s`, `775 total actions`; config validation `PASS 31/31`; Image `44 820 992 B`; artifact 210 436 545 B |
| 18:28Z | branch HEAD advanced to `019463c350` "ROUND61: publish hosted manifest and Image build result"; `hosted-build-latest.md` → `Last stage: complete`, `Exit code: 0`, `BUILD_PASS` |
| 18:30Z | `.config` SHA-256 `5f7fd8b3…` matched against the independent local ROUND18 build — identical |
| 18:35Z | run 45455279898 still `in_progress` in step 3 (duplicate of the same source tree) |
| 18:29:36Z | run 45455279898 step 3 elapsed **26 min** — still below the successful run A's 28 m 44 s, `in_progress`, artifacts 0, no failure signal |

**Net result of the verification: the run suspected of being orphaned finished successfully 29 m 56 s after it started, published the Image, and uploaded its evidence. No intervention was needed and none was performed.**
