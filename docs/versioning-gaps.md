# Versioning: what is still missing

Written 2026-09-17, after the host-environment drift incident. Everything here
is a gap between what we record today and what a result needs in order to be
trusted, reproduced, or compared against a later run.

Ordered by what hurts first, not by effort.

The baseline this measures against: commit `e3f1b45` records git state, three
content digests, the vendored tau2 commit, the pinned agent harness, the host
interpreter and its dependency lock, plus BenchFlow and Docker versions. That
covers the **inputs**. The gaps below are mostly about **outputs**, the **judge**,
and **enforcement**.

---

## 1. The results store is neither versioned nor backed up

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

**Done looks like:** the tracking store survives the loss of this working copy.
Either a remote MLflow tracking server with a SQL backend, or a scheduled export
of `mlflow.db` plus `mlartifacts/` to somewhere durable. A remote server is the
documented path and also unblocks MLflow's evaluation-dataset features, which
[require a SQL-backed tracking server](https://mlflow.org/docs/latest/genai/datasets/)
and do not work on the file store at all.

**Effort:** small for a backup script. Medium for a remote server.

---

## 2. The LLM judge sits outside the tracking system

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

**Effort:** small.

---

## 3. Sampling parameters are recorded nowhere

Checked against a full rollout record in `results.jsonl`:

```
temperature: ABSENT    top_p: ABSENT    seed: ABSENT    max_tokens: ABSENT
```

I could not find a 2026 source that names sampling parameters as a required
disclosure, so take this as our own reasoning rather than received practice:
temperature and top_p change the output distribution, and a run recorded without
them cannot be distinguished from a run that used different ones. That is the
same argument we already accepted for the harness pin.

BenchFlow does not appear to surface them in its output, so we likely have to
set them explicitly via `--config-override` and log what we set, rather than
reading back what was used. That is weaker, because an unset default can still
change under us, but it is better than nothing.

**Done looks like:** sampling parameters are explicit in the run config and
logged as MLflow params. If BenchFlow cannot pin them, that limit is written
down rather than assumed away.

**Effort:** small, plus an unknown on what BenchFlow exposes.

---

## 4. Task definitions have no digest of their own

`TRACKED` in `tools/provenance.py` covers `vendor/`, `data/banking_knowledge/`
and `prompts/`. It does not cover `tasks/`.

BenchFlow computes a `task_digest` internally but does not emit it anywhere we
keep. Confirmed absent from both `summary.json` and `results.jsonl`.

So the tasks, which are the central artifact, are covered only by the whole-repo
commit. That is the one thing the split-digest design was meant to avoid: any
unrelated commit makes two task sets look different when they are identical.

Current practice treats the dataset like prompts:
*"tag releases, freeze datasets for active CI gates, and review additions in
PR"* ([2026 LLM Evaluation Playbook](https://futureagi.com/blog/llm-evaluation-playbook-2026/)).

**Done looks like:** a fourth digest over `tasks/`, logged as a param, and a git
tag marking the frozen set that any CI gate runs against.

**Effort:** small for the digest. The tagging convention is a process decision.

---

## 5. No CI gate

The oracle check went 48/48 to 0/48 and nothing noticed until it was run by
hand. The cause was an empty `.venv` shadowing an ephemeral `uv` environment, so
`vendor/tau2` stopped importing. No digest moved, because no tracked content
changed.

That is the argument for enforcement in CI rather than discipline. MLflow's
[regression testing guide](https://mlflow.org/docs/latest/genai/eval-monitor/regression-testing/)
describes the mechanism plainly: *"A failing assertion fails the pytest job,
which fails the check, which blocks the pull request, exactly like a unit
test."*

**Done looks like:**
- `python tools/check_oracles.py` runs on every push and fails the build below
  48/48.
- The host environment is built from `requirements-host.txt`, so CI catches
  dependency drift the same way it just caught us.
- Later: a small frozen task subset run as a scored regression gate, with a
  threshold that blocks a merge.

**Effort:** small for the oracle gate. Medium for a scored gate, because it needs
the variance work below to set an honest threshold.

---

## 6. Two small defects

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

**Effort:** minutes each.

---

## 7. Known limits we cannot close here

**The model alias.** `claude-sonnet-4-5` points at whichever snapshot is current.
The weights behind a given snapshot never change, so the exposure is a version
bump we did not ask for rather than drift under a fixed name. BenchFlow does not
resolve the alias to a dated snapshot in anything it writes. Worth checking
whether passing a dated model id works, and pinning it if so.

**Run-to-run variance is unmeasured.** Not a versioning gap, but it bounds what
versioning buys. Until the same commit is run several times and the spread is
known, no comparison between two runs can be called a real difference. This
belongs to experimental design and should be done before any scored CI gate sets
a threshold.

---

## Order of work

| # | Change | Why now | Effort |
|---|---|---|---|
| 2 | fold the review into the MLflow run | completes the gate you asked for | small |
| 6 | fix artifact `break`; log cost and tokens | minutes, removes silent loss | tiny |
| 1 | back up or remote the tracking store | everything else points at it | small–medium |
| 4 | digest `tasks/`; tag frozen sets | restores the split-digest property | small |
| 5 | oracle gate in CI | catches the failure we just had | small |
| 3 | pin and log sampling parameters | unrecorded input that moves outputs | small + unknown |

After each: `python tools/check_oracles.py` must still report 48/48.

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
