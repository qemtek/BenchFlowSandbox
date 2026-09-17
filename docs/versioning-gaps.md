# Versioning: what is still missing

Written 2026-09-17, after the host-environment drift incident. Everything here
is a gap between what we record today and what a result needs in order to be
trusted, reproduced, or compared against a later run.

Ordered by what hurts first, not by effort.

The baseline this measures against: a run records git state, four content
digests (`tasks`, `environment`, `knowledge`, `prompts`), the vendored tau2
commit, the pinned agent harness, the host interpreter and its dependency lock,
plus BenchFlow and Docker versions. That covers the **inputs**. The gaps below
are mostly about **outputs**, the **judge**, and **enforcement**.

Status as of 2026-09-17: seven of the nine are closed. What remains is one
deferred decision, one process convention, and the variance measurement — and
the last of those now has a mechanism waiting to be run.

---

## 1. The results store is neither versioned nor backed up  — DEFERRED

Our `.gitignore`:

```
jobs/
mlflow.db
mlartifacts/
```

Every input is pinned to a commit. Every output lives in two untracked local
files on one laptop. Lose the machine and you keep perfect provenance for
results you no longer hold.

The comment in `.gitignore` says run outputs are "reproducible from a commit +
digests". That is false for anything involving a model: re-running a pinned
commit produces a different rollout. We have the counterexample already, a task
that scored 1.00 and then 0.0 on identical inputs.

**Decided 2026-09-17:** no remote tracking server. This is a test project, and
a local SQLite store stands in for what would be a hosted database in
production. The local store already satisfies MLflow's
[SQL-backend requirement](https://mlflow.org/docs/latest/genai/datasets/) —
SQLite counts, and the file store does not — so nothing is blocked by staying
local.

What remains is a backup, so a lost working copy does not take the results with
it. Out of scope for now; revisit if results start informing decisions that
outlive the experiment.

**Effort:** small, deferred.

---

## 2. The LLM judge sat outside the tracking system  — DONE

You asked for the deterministic check and the LLM judge to run as one production
gate. Only the deterministic half has provenance.

`benchflow review` writes `jobs/review-*/review_report.json`, which is gitignored
and never reaches MLflow. Nothing links a review to the eval run it judged.

The report already contains what we need:

```json
"reviewer": {"agent": "claude-agent-acp", "model": "claude-sonnet-4-5",
             "environment": "docker",
             "network": "open (explicit --allow-open-network)"}
"rubric":   {"path": ".../review/rubric.json",
             "criteria": ["identity_verified_before_disclosure", ...],
             "contracts": [...]}
```

So this is a plumbing job, not a discovery job. The
[2026 LLM Evaluation Playbook](https://futureagi.com/blog/llm-evaluation-playbook-2026/)
puts it directly: *"Pin the judge model and rubric version. A floating judge
model produces drifting scores. The judge version is part of the eval
contract."* A judge upgrade moves scores with nothing to show for it, exactly
as a model upgrade does.

Note the recorded `"network": "open"`. That is the standing caveat on the
finding that 3 of 5 objectively-passing rollouts breached the verification
blocker, and it should travel with the result rather than living in a doc.

**Done looks like:**
- `tools/run_experiment.py` gains a `--review` path that runs the rubric after
  the eval and logs to the *same* MLflow run.
- Judge model, judge harness pin, rubric digest and network mode become params.
- Per-criterion pass counts become metrics, so `identity_verified_before_disclosure`
  is plottable across runs.
- `review_report.json` is logged as an artifact.

**Done:** `run_experiment.py --review` runs the rubric after the eval and logs
to the same MLflow run. Judge model, judge harness pin, rubric digest, rubric
path, criteria list and network mode are params. Per-criterion results are
metrics, with blockers as pass rates and weighted criteria normalised against
their weight so everything plots on one axis.

Verified against the existing report rather than by spending tokens on a new
review. The parser reproduces the report's own prose summary exactly:

```
review_identity_verified_before_disclosure_pass_rate  0.3    ("3 pass / 7 fail")
review_mean_raw_quality                               0.775  ("average raw quality 0.775")
review_publishable_rate                               0.2    ("publishable=2" of 10)
```

---

## 3. Generation settings were recorded nowhere  — DONE

Checked against a full rollout record in `results.jsonl`:

```
temperature: ABSENT    top_p: ABSENT    seed: ABSENT    max_tokens: ABSENT
```

The reason turned out to matter more than the absence. BenchFlow's ACP runtime
(`benchflow/acp/runtime.py`) sets no sampling parameters at all. The
`BENCHFLOW_MODEL_TEMPERATURE` / `_TOP_P` / `_MAX_TOKENS` variables exist, but
only the `deepagents` and `openclaw` shims read them. For `claude-agent-acp`
there is no path to set them, so they are whatever Claude Code's bundled SDK
defaults to — fixed by the harness pin we now record, and not otherwise
controllable from here.

What *is* controllable is `--reasoning-effort`, a real `benchflow eval run`
flag that we never passed. Left unset it takes an unrecorded default, and
reasoning effort moves both behaviour and cost.

I could not find a 2026 source that names sampling parameters as a required
disclosure, so treat the argument as ours rather than received practice: an
input that changes the output distribution and is not recorded cannot be
distinguished from a different value of that input. Same reasoning we already
accepted for the harness pin.

**Done:** `run_experiment.py` takes `--reasoning-effort` and logs it. Runs that
leave it unset record `harness-default` rather than nothing. `sampling_params`
records that the ACP runtime does not expose them, so the limit is written down
instead of looking like an oversight.

---

## 4. Task definitions had no digest of their own  — DONE

`TRACKED` in `tools/provenance.py` covers `vendor/`, `data/banking_knowledge/`
and `prompts/`. It does not cover `tasks/`.

BenchFlow computes a `task_digest` internally but does not emit it anywhere we
keep. Confirmed absent from both `summary.json` and `results.jsonl`.

**Correction, 2026-09-17.** That check was too narrow, and the conclusion drawn
from it was wrong. `task_digest` is written to every rollout's `config.json`
*and* `result.json` — both inside the archive we log, and `config.json` is the
file this README already singles out as the reason the archive matters:

```
jobs/sub10/2026-09-16__20-48-18/task-004__8dbb5c10/config.json
  "task_digest": "sha256:81af6b78…"
```

It is also exposed as `benchflow tasks digest`, pins releases in the dataset
registry, and is recomputed by `benchflow review --tasks-root` — which we
already pass — to decide whether a task may be admitted as evidence at all. So
we had per-task digests, and digest *enforcement*, before we wrote any.

What was genuinely missing is a run-level value to group runs by, and digests
for everything outside a task package. `provenance.py` now asks BenchFlow for
the per-task map and aggregates it, rather than hashing `tasks/` itself. Two
reasons beyond not duplicating work: a per-task map says *which* task moved,
and a hash of our own could disagree with the one recorded beside the rollout,
which is worse than having none. `PROVENANCE_VERSION` is 3 — same content,
different number, so runs either side of the change are distinguishable.

So the tasks, which are the central artifact, are covered only by the whole-repo
commit. That is the one thing the split-digest design was meant to avoid: any
unrelated commit makes two task sets look different when they are identical.

Current practice treats the dataset like prompts:
*"tag releases, freeze datasets for active CI gates, and review additions in
PR"* ([2026 LLM Evaluation Playbook](https://futureagi.com/blog/llm-evaluation-playbook-2026/)).

**Done:** `digest_tasks` is the aggregate of BenchFlow's 48 per-task digests,
with the full map logged as a `task-digests.json` artifact. `digest_dir` now
matches extensionless files by name so `environment/Dockerfile` is covered in
the three directories we still hash ourselves. An earlier version of this fix
hashed `tasks/` with a suffix filter (`.md .json .py .sh Dockerfile`), which
also meant any future file type in a task package — a skill, an extensionless
fixture — would have been silently uncovered.

Adding a digest changes `combined` for unchanged content, so `collect()` now
reports `provenance_version` (currently 3). Runs either side of a schema change
are distinguishable rather than falsely different.

**Still open:** tagging frozen task sets. The decision is ours — which snapshot
to freeze — but the machinery is not: a dataset registry JSON pins per-task
digests and `benchflow eval run --dataset <name>@<version> --registry <file>`
verifies them before a run starts, using the same `task_digest` we now record.
`benchflow tasks overlap` compares two manifests for task-id and digest overlap.
Worth doing before any scored gate sets a threshold.

---

## 5. No CI gate  — DONE

The oracle check went 48/48 to 0/48 and nothing noticed until it was run by
hand. The cause was an empty `.venv` shadowing an ephemeral `uv` environment, so
`vendor/tau2` stopped importing. No digest moved, because no tracked content
changed.

That is the argument for enforcement in CI rather than discipline. MLflow's
[regression testing guide](https://mlflow.org/docs/latest/genai/eval-monitor/regression-testing/)
describes the mechanism plainly: *"A failing assertion fails the pytest job,
which fails the check, which blocks the pull request, exactly like a unit
test."*

This repo has no remote and no CI service, so the gate is a git hook:
`.githooks/pre-push` runs `check_oracles.py` and blocks the push below 48/48.
Enabled with `git config core.hooksPath .githooks`, which is already set.

Pre-push rather than pre-commit, because the check takes about two minutes.
`git push --no-verify` overrides it.

**Still open:** a hook runs in the same environment it is checking, so it cannot
catch "works on my machine only". A hosted runner building from
`requirements-host.txt` catches that class, and becomes available the moment
this repo gets a remote.

**Also still open:** a *scored* gate — running a frozen task subset and blocking
below a pass-rate threshold — needs run-to-run variance measured first, or the
threshold is guesswork. See §7.

---

## 6. Two small defects  — DONE

**Artifact logging drops files.** `tools/run_experiment.py:181` breaks after the
first match of each filename:

```python
for artifact in ("summary.json", "results.jsonl", "run.log"):
    for p in jobs_dir.rglob(artifact):
        mlflow.log_artifact(str(p))
        break
```

A multi-task run writes one `results.jsonl` per task plus an aggregate. Only one
is kept, chosen by whatever `rglob` returns first. It under-captures silently.

**Cost and token metrics are thrown away.** `summary.json` already carries
`total_cost_usd`, `total_tokens`, `total_input_tokens`, `total_output_tokens`
and `avg_tool_calls_per_task`. None are logged. Cost per solved task is a
headline number sitting unused, and it feeds the efficiency item in
`production-realism.md`.

**Done:** the artifact loop logs every match, namespaced by its directory under
the job root. `total_cost_usd`, `total_tokens`, input/output token splits and
`avg_tool_calls_per_task` are now metrics, plus a derived
`cost_per_solved_task_usd`.

---

## 7. Known limits we cannot close here

**Closed 2026-09-17: the model alias.** Listed here twice as something to check.
Checked: BenchFlow has no model whitelist — its own default is the dated
`claude-haiku-4-5-20251001` — and the string passes through to ACP unchanged. So
a dated snapshot id can be pinned whenever you want it, and using an alias is a
choice rather than a limitation. `run_experiment.py` now prints a note when the
model looks like an alias and logs `model_is_alias` on every run.

**Run-to-run variance is unmeasured.** Not a versioning gap, but it bounds what
versioning buys. Until the same commit is run several times and the spread is
known, no comparison between two runs can be called a real difference. This
belongs to experimental design and should be done before any scored CI gate sets
a threshold.

Part of the work is already available: `benchflow eval compare-lift` pairs
rollouts by task and reports deltas with bootstrap confidence intervals, which
cancels task difficulty — most of the variance — without any repeats. Repeats
are still needed for the residual noise floor, but the pairing is free.

**Update 2026-09-17:** the repeats have a mechanism now.
`run_experiment.py --trials N` delegates to BenchFlow's `--matrix`, which runs
the arm N times into N separate job directories; each trial is a nested MLflow
run and the parent carries `pass_rate_sd`, `pass_rate_spread`, min and max. The
gap is no longer "we have no way to do this", it is "we have not run it yet".

---

## 8. The seam between BenchFlow and MLflow leaked  — DONE

BenchFlow owns the data plane: tasks, rollouts, rewards, digests. MLflow owns
the experimentation plane: which run, which arm, which number to cite. The split
is clean in the direction that matters — nothing in `tasks/`, `vendor/` or any
task config knows MLflow exists, so a task set stays portable and
`benchflow eval run` remains a valid throwaway path.

It leaked in the other direction. The tracking layer was reaching into the data
plane's filesystem instead of consuming an interface it had asked for, four
times, and one of them was a live defect:

**Artifacts found by mtime.** The review report was located by globbing
`jobs/review-*/review_report.json` across the whole repo and taking the newest.
`benchflow review` has `--out-dir`; we were not passing it, so BenchFlow wrote
`jobs/review-<ts>/` and we guessed which one was ours. A stale review directory,
or a second run in flight, would have attached another run's judge scores to
this one — logged as params, with a rubric digest, looking authoritative.
`summarise()` had a milder version of the same habit, taking whichever
`*/summary.json` had the newest mtime.

**Facts recomputed rather than read.** The task digests, above.

**Internals imported because the CLI does not expose them.** `agent_harness()`
reads `benchflow.agents.registry` through BenchFlow's own interpreter, because
`benchflow agent show` prints the launch path but not the install pin. That is
still the only route, so the probe stays — but it used to return `"unknown"` on
any failure, which degrades a provenance field into a plausible-looking string.

**Task internals read directly.** `gold_action_count()` walked
`verifier/gold.json` with `except Exception: pass`, so an unreadable gold file
silently changed the denominator of a headline efficiency metric and made the
agent look more efficient rather than broken.

**Done:** every file the wrapper reads is now one it asked for at a path it
chose — `--health-summary-out`, `--run-config-out`, `--task-manifest-out`,
`benchflow review --out-dir`. `summarise()` refuses a job directory holding more
than one evaluation rather than picking. Probes that cannot read what they claim
to record raise; the run is tagged `provenance_complete=false` and says so on
stderr instead of logging `"unknown"` quietly. `gold_action_count()` fails
loudly. And the missing back-pointer is filled in both directions: `jobs_dir` is
a param, and the job directory holds an `mlflow_run_id` file.

One consequence worth stating plainly, because it changes how a number reads:
`total_cost_usd` is `0.0` on every run so far. Under subscription auth there is
no price source, so that zero means *unpriced*, not *free*, and
`cost_per_solved_task_usd` inherits it. The validity flags now travel with the
values — `telemetry_coverage` as a metric, `cost_priced` as a tag — so the two
cases are distinguishable.

---

## 9. The provider side of every call was unrecorded  — DONE

Not noticed until BenchFlow's own coverage metric was wired up and reported
`missing_llm_trajectory: 1` on every rollout we had ever run.

`trajectory/llm_trajectory.jsonl` is BenchFlow's record of each model call:
request, response, per-call usage, and the dated snapshot that answered. It is
written by the LiteLLM proxy, which authenticates upstream with an API key —
so it is skipped under subscription auth, and the file never exists. Its
absence blocks `benchflow train convert` and `benchflow eval continue`
outright, and costs four things nothing else records: the exact context window
per turn, per-call usage, provider failures, and the resolved model id. On the
alias question in §7 this is the sharper statement: with no capture there is no
dated id anywhere in a rollout, only the string we passed.

**Done:** `tools/capture_proxy.py`, behind `--capture-provider`, described in
[provider-capture](provider-capture.md). Two facts made
it possible, both established by probe rather than assumption — Claude Code
presents its subscription token to a custom `ANTHROPIC_BASE_URL`, and it works
just as well when handed a dummy bearer while the real token is attached
host-side. The second is why the proxy also removes an exposure that predates
it: the credential no longer enters a container that has open network access.

Verified on task-036: 33 exchanges captured, `health_missing_llm_trajectory`
0 where every earlier run reported 1, and `benchflow train convert --row-mode
exchange` producing 33 rows whose 37 tool calls match the rollout's own count.

**Still open:** cost. A subscription call carries no price, so `response_cost`
is null by design rather than a fabricated zero. The capture now holds exact
per-call token counts, which is the input an estimate would need — see
`docs/production-realism.md`.

---

## Order of work

| # | Change | Status |
|---|---|---|
| 2 | fold the review into the MLflow run | done |
| 6 | fix artifact `break`; log cost and tokens | done |
| 4 | digest `tasks/`; version the provenance schema | done |
| 3 | record reasoning effort; document the sampling limit | done |
| 5 | oracle gate as a pre-push hook | done |
| 1 | back up the tracking store | deferred (test project) |
| 8 | close the seam between the two planes | done |
| 9 | capture the provider side on subscription auth | done |
| — | tag frozen task sets | open, and `--dataset` is the tool for it |
| — | measure run-to-run variance | open, mechanism exists (`--trials`) |

After each: `python tools/check_oracles.py` must still report 48/48. The
pre-push hook now enforces that.

---

## Sources

Each link below was fetched on 2026-09-17 and checked against the claim it is
cited for.

- [The 2026 LLM Evaluation Playbook](https://futureagi.com/blog/llm-evaluation-playbook-2026/)
  — supports gap 2 (pin the judge model and rubric version; "the judge version is
  part of the eval contract") and gap 4 (tag dataset releases, freeze the set
  that gates CI, review additions in a PR).
- [MLflow: Regression Testing and CI/CD](https://mlflow.org/docs/latest/genai/eval-monitor/regression-testing/)
  — supports gap 5 (a failing assertion blocks the pull request).
- [MLflow: Building Agent & LLM Evaluation Datasets](https://mlflow.org/docs/latest/genai/datasets/)
  — supports gap 1 (evaluation datasets require a SQL-backed tracking server;
  unavailable on FileStore).

Checked and **not** cited, because they did not support the claims I wanted them
for:

- [LLM-as-a-Judge in 2026 (DeepEval)](https://deepeval.com/blog/llm-as-a-judge)
  — real page, but it covers judge prompt construction, not judge versioning.
- [LLM-as-judge evaluation guide (Openlayer)](https://www.openlayer.com/blog/llm-as-judge-evaluation-guide)
  — real page, but it covers validating a judge against human labels and
  monitoring it in production, not pinning or recording its configuration. Its
  advice to *"iterate prompt wording until correlation exceeds 0.85, then retest
  quarterly"* is worth reading when we come to trusting the rubric, but it says
  nothing about versioning.

No source is cited for gap 3; that argument is ours, and the doc says so.
