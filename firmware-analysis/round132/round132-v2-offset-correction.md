# ROUND132 — correction: the zero-offset clause is not met; verdict changes to FAIL

**Supersedes the verdict line of `TEST_AGENT_ROUND132_FINAL_REPORT.txt`.**
The test evidence is unchanged; the *interpretation* I put on it was wrong.

- Date: 2026-11-26
- Accepted review: `firmware-analysis/round132/AI2_ROUND132_POST_TEST_AUDIT.md`
  (2号 AI, verdict `FAIL` on the 17-patch zero-offset clause)
- Taskbook (current revision): `AI2_AGENT_VALIDATION_TASK.md`,
  sha256 `577fa1398ae0497c017896481b06395ad6c218b839c2f5528a178092b02b2c3b`
- Test object (unchanged): `round132-kunit-seam-v2.patch`,
  sha256 `1fbc32a362dc5d2f694ba45798a90c2e0efbe389bc245aa101e16d85d7ee842f`

---

## 0. Verdict

| clause | prior claim | corrected finding |
|---|---|---|
| 17 frozen patches apply successfully | PASS | **PASS** — 17/17, `--check` and apply RC 0 in both trees |
| zero fuzz | PASS | **PASS** — `git apply` has no fuzz mechanism; context matched byte-exactly |
| **zero offset** | claimed PASS | **FAIL** — `git apply` reported offsets on **5 hunks of 2 patches** (16 and 17) |
| final content tree equals declared base | PASS | **PASS** — `77e2b2b1…` in both independent clones |
| seam-v2 applies cleanly, no offset | PASS | **PASS** — no offset reported on any of its 7 paths |
| Kconfig `bool`, negative control | PASS | **PASS** — unchanged |
| UML KUnit `1..1` / `ok 1`, RC 0 | PASS | **PASS** — unchanged, content-level |
| host 38/38 and 83/83 | PASS | **PASS** — unchanged |
| product `.config` invariant | PASS | **PASS** — unchanged |
| checkpatch 0 errors / 0 warnings | PASS (3 CHECK disclosed) | **PASS on the stated criterion**, exit code 1 disclosed as D-2 |

**Overall: `FAIL`**, on the one clause the taskbook states explicitly and the
tool output makes observable. The evidence that produced the other PASS lines
is not withdrawn — it simply cannot outvote a clause it does not address.

---

## 1. What I got wrong, and how the error was constructed

The review quotes my report accurately. Three passages carry the error:

| location | text I wrote | status |
|---|---|---|
| report `:115-117` | `fuzz / offset : git apply 机制上不支持 fuzzy 匹配与偏移应用（fuzz 或 offset 会直接报错），因此 17 个补丁全部 --check 通过即为零 fuzz 零 offset` | **false in the offset half** |
| report `:134` | `17 补丁重放 : APPLY17_FAIL=0；零 fuzz / 零 offset（同上）` | **false** |
| report `:349-352` | `它也不做「按偏移去找相近位置」的尝试。因此 … 在机制上即排除 fuzz 与 offset` | **false** — searching nearby positions for the context is exactly what produces an offset |
| report `:337` | `以「git apply 无 fuzz/offset 机制 + 内容树哈希一致」为准` | **false premise**, conclusion therefore unsupported |

The refuting evidence was already in my own log, five lines above the summary
line that denied it:

```
371  --- PATCH 16 ---
376  Hunk #1 succeeded at 187 (offset -25 lines).
377  Hunk #2 succeeded at 244 (offset -2 lines).
378  Hunk #3 succeeded at 274 (offset 2 lines).
...
401  Hunk #1 succeeded at 119 (offset 1 line).
402  Hunk #2 succeeded at 149 (offset -2 lines).
...
422  GIT_APPLY_OFFSET_COUNT=0 (git apply has no offset mechanism; a shifted hunk cannot apply)
```

Line 422 is not tool output. **I generated it.** The summariser I wrote asserted
the conclusion instead of parsing the output it had just captured:

```sh
echo "GIT_APPLY_OFFSET_COUNT=0 (git apply has no offset mechanism; a shifted hunk cannot apply)"
```

That is the defect, stated plainly: a "verification" line that was an
assertion, contradicting measured output in the same file. The same wrong
premise also appears in the log's section headers (`applier: git apply --check
then git apply (exact context; no fuzz/offset mechanism)`), which is why the
error propagated into the report instead of being caught while writing it.

Two distinct mistakes compounded:

1. **A mechanism claim made from memory, not from the tool.** I asserted that
   `git apply` refuses to apply a shifted hunk. It does apply it and says so.
2. **A summary computed by assertion.** The counter should have been
   `grep -c 'offset'`; it was a hard-coded sentence. Nothing in my pipeline
   could have caught the contradiction, because nothing parsed the field.

**Reviewer's finding: correct. My report: wrong. No mitigating interpretation
applies to the offset half of the claim.**

What is *not* wrong: `git apply` genuinely has no fuzz mechanism. On this
machine (`git version 2.43.0`) `--fuzz` is rejected outright:

```
$ git apply --fuzz=0 --check /dev/null
error: unknown option `fuzz=0'
```

`git apply -h` offers `-C <n>` ("ensure at least <n> lines of context match")
and no fuzz knob. So "zero fuzz" survives; "zero offset" does not. The two were
bundled in one sentence, and my error was to generalise the fuzz property to
offset.

---

## 2. Measured offsets, exhaustively

Exactly two patches produce offsets, in both trees identically. All other 15
patches print no offset line; neither does seam-v2 on any of its 7 paths.

| patch | file | hunk header | reported position | offset |
|---|---|---|---|---|
| 16 `round33-0001-regulator-proxy-self-target-only` | `drivers/regulator/proxy-consumer.c` | `@@ -212,6 +212,30 @@` | 187 | **−25** |
| 16 | same | `@@ -225,6 +246,7 @@` | 244 | **−2** |
| 16 | same | `@@ -250,6 +272,25 @@` | 274 | **+2** |
| 17 `round33-0002-regulator-proxy-self-target-binding` | `Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml` | `@@ -118,7 +118,9 @@` | 119 | **+1** |
| 17 | same | `@@ -148,11 +151,11 @@` | 149 | **−2** |

Totals: **5 offset hunks, spread over 2 patches out of 17 ⇒ 2 patches fail the
zero-offset clause, 15 comply.** Reported positions are in the
post-patch file numbering, which is why hunk 2 of patch 16 reads −2 against a
`+246` header.

---

## 3. Why the offsets exist — measured, not guessed

I tried to establish that the offsets are an artefact of my replay rather than
of the frozen series. They are not. The measurements:

**(a) The post-15 state is uniquely determined.** `proxy-consumer.c` after
patches 13, 14, 15 is 466 lines, sha256
`4625eb9d11928e8ba941feebdaa56e5bb72a0f1dab180cafa43486bd04286e48`. That value
is reached both by unwinding 16 and 17 from the final tree and by replaying
13/14/15 forward from ACK. Patches 7–9 and 12 do not touch this file — verified
by obtaining the same hash with them absent, which is why the local naming
(`07.patch`…`09.patch`) does not affect the result.

**(b) Patch 16 cannot apply before patch 13.** On the pre-13 state the patch
fails outright:

```
error: while searching for:
	return regulator_get(consumer->reg_dev, "proxy");
}
```
```
error: patch failed: drivers/regulator/proxy-consumer.c:212
error: patch failed: drivers/regulator/proxy-consumer.c: patch does not apply
```

So the generation parent is **not** "the series minus patch 13". The parent
contains patch 13's child-scoped code.

**(c) The parent is 25 lines longer above hunk 1 than any state the series can
produce.** Hunk 1 declares its context at old line 212; the unique matching
context sits at 187. `git apply` only accepts byte-identical context, and if the
context also existed at 212 it would have matched there and reported offset 0.
Therefore the parent had 25 more lines above that point. Hunk 1 then inserts 24
lines, which is why hunks 2 and 3 come back to −2 / +2 instead of staying at
−25: the surplus is cancelled by the patch's own insertion.

**(d) No frozen patch supplies those 25 lines.** Walking the series in the only
permitted order yields the 466-line file of (a); the 25-line surplus is absent
from every intermediate state. It is therefore not recoverable from the frozen
series at all — it belongs to a revision of patches 13/16 that predates or
postdates the recorded order. **I can measure the 25-line discrepancy; I cannot
reconstruct those lines from any artefact in this repository, and I will not
invent a cause.**

**Consequence for the requirement.** Zero offset is attainable only by one of:

- regenerating patches 16 and 17 against the documented base — which changes
  frozen bytes and is forbidden; or
- supplying a parent that matches their generation lineage — which does not
  exist in the frozen series and would break the declared base tree
  `77e2b2b1…`.

**The zero-offset clause therefore cannot be satisfied by any replay that
respects the frozen series and the documented base.** That is a property of the
frozen artefact, not a defect a tester can repair inside the task's constraints.

---

## 4. What the offsets do *not* invalidate

These results are content-level and are unaffected by where a hunk is placed;
they are restated so the correction is not read as a wholesale withdrawal:

| measurement | value |
|---|---|
| 17-patch replay content tree, two independent clones | `77e2b2b1515b3813f7538aedffe4c5a4e90edb57` (equals SOURCE_NOTE declared base) |
| seam-v2 applied content tree | `482e1dfbb6945ff5bce3c95279d65ebfbfebf23e`, +399/−1 across 7 paths |
| UML KUnit | KTAP `1..1`, `ok 1 regulator-proxy-consumer-lifecycle`, `RUN_RC=0` |
| UML `.config` / `vmlinux` | `66d2720d…` / `5eb684a3…`, symbol `=y`, 0 `.ko` |
| host regressions | 38/38 and 83/83, `HOST_RC=0` |
| product `.config` | byte-identical before/after, no test symbol |
| checkpatch | 0 errors, 0 warnings, 3 CHECK (D-2) |

The content tree agreeing with the declared base is a real and strong result: it
proves the replay is deterministic and matches the declared definition. It does
not address the zero-offset clause, because a shifted hunk that lands correctly
still produces the declared tree — as the numbers above demonstrate.

---

## 5. Taskbook revision v2 (2026-11-26): D-1 closed, verdict unaffected

The taskbook was reissued during this round. `diff -u` between the revisions
shows **one hunk, one line**:

```diff
-`…/blob/main/kernel-baseline/round61/round32-stagea-series.txt`
+`…/blob/ai-parallel/stagea-port-until-boot/kernel-baseline/round61/round32-stagea-series.txt`
```

| | v1 | v2 |
|---|---|---|
| bytes / lines | 11387 / 139 | 11417 / 139 |
| blob / sha256 | `7d342d60…` / `ff90f60f…` | `b147409a…` / `577fa139…` |

The corrected URL now returns HTTP 200 with **6599 B / 81 lines / blob
`9a93b7e3a500d807533517a92b98fe244b2ea456` / sha256 `36e1ab53…`** — byte-identical
to what the earlier run obtained by blob-SHA lookup. With a working URL, all 17
patches were re-fetched **by their declared paths** and re-identified against
the manifest's own columns: **17/17 MATCH, 0 failures**
(`round132-v2-series-path-refetch.log`, `SERIES_PATH_REFETCH=PASS`).

So D-1 is closed. The revision does not touch the application criterion, so it
does not move the verdict: `FAIL` stands on §2 of the taskbook.

---

## 6. Deviation table, corrected

| id | item | state |
|---|---|---|
| **D-1** | manifest URL pointed at `main` → 404 | **CLOSED** by taskbook v2; corrected URL verified byte-identical, 17/17 patches fetched by path |
| **D-2** | checkpatch `--strict`: 0 errors / 0 warnings / 3 CHECK, exit code 1 | **OPEN, disclosed** — taskbook's 0/0 criterion met; the three CHECKs are CamelCase on test-only field names. If exit code is the criterion, this flips to FAIL too |
| **D-3** | standalone `scripts/spdxcheck.py` NOT RUN | **OPEN, disclosed** — `python3-ply` absent, installing distro packages exceeds authority |
| **D-4** | GNU `patch --dry-run` disagrees with `git apply` on 8/17 | **REVISED** — the earlier conclusion "does not affect the zero-offset judgement" is **retracted**: it was true only under the false premise that `git apply` produces no offsets. The divergence is still not itself a drift signal, but it can no longer be used to dismiss the offset question |
| **D-5** | **prior report asserted "zero fuzz / zero offset" and "git apply has no offset mechanism"; both contradicted by `round132-v2-apply-check.log:376-378, 401-402`** | **NEW — accepted**; root cause is a hard-coded summary line (`:422`) that asserted rather than parsed. Corrected here; original report and log left byte-unmodified as evidence |

I did not edit `TEST_AGENT_ROUND132_FINAL_REPORT.txt` or
`round132-v2-apply-check.log`. Rewriting a report to erase a wrong claim
destroys the audit trail that caught it; the correction points at the error
instead.

---

## 7. Options — the decision is not mine

1. **Keep the clause and accept FAIL.** ROUND132 closes as a failed validation
   of a frozen series that contains an internal inconsistency. Nothing further
   is run without new authorisation.
2. **Restate the clause** as "no fuzz; offsets must be zero or explicitly
   recorded with the content tree matching the declared base". Under that
   wording the measured evidence supports PASS, with the 5 offsets listed in §2
   as the recorded exception. This requires a taskbook amendment, not a re-run.
3. **Require zero offset without changing the criterion.** That needs patches 16
   and 17 regenerated against the documented base — new patch bytes, a new
   review cycle, and an explicit decision by the patch owner. It cannot be
   achieved by re-running the replay.

I have not chosen among these, and I have not touched the frozen patches, the
product configuration or the device.

---

## 8. What this round changed on disk

| file | content |
|---|---|
| `round132-v2-offset-correction.md` | this document |
| `round132-v2-series-path-refetch.log` | 17 patches fetched by declared path from the corrected branch; per-patch blob + sha256 + verdict; `SERIES_PATH_REFETCH=PASS` |
| `round132-v2-retained-evidence-consistency.log` | retained tree / `.config` / `vmlinux` / TAP / host / product-config / checkpatch state re-measured this round |

No source file, patch, kernel config, product config, DTS or build output was
modified. No device was contacted. `blob` identities and read-back results are
in `round132-v2-offset-correction-manifest.txt`, since a file cannot contain its
own hash.
