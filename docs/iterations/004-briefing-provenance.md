# 004 — Recording which briefing produced a task set

> Superseded the same day by
> [005](005-briefing-in-the-prompt-registry.md), which moved the briefing into
> the prompt registry and removed the duplicate this page was built to police.
> Kept because the two gaps it names are real and the reasoning is why 005
> exists.

Status: superseded by [005](005-briefing-in-the-prompt-registry.md)
Date: 2026-09-17
Touches: `tools/make_task.py`, `tools/run_experiment.py`, all 48
`tasks/*/task.md`
Moves which digest: `digest_tasks`

## The problem

Two gaps, both found while planning how to measure
[002](002-briefing-disclosure-order.md).

**`digest_prompts` cannot distinguish briefing variants.** It hashes every
`.md` and `.yaml` file under `prompts/` (`tools/provenance.py:66`). Keeping two
briefings in the tree is how you run two prompt arms from one commit — and the
moment you do, both arms log the same `digest_prompts`. The field named for
telling prompts apart stops telling them apart exactly when it is needed.

**Nothing noticed a stale task set.** Editing `prompts/briefing.md` without
regenerating left the packages holding the old text while `digest_prompts`
recorded the new. The run was fine; its provenance pointed at a prompt that had
not run. `run_experiment.py` refuses a dirty working tree for this class of
problem and did not catch this one, because the tree was clean — the tasks were
simply out of date.

## The change

**`make_task.py` stamps the source.** Each package's frontmatter now carries
`briefing_file` and `briefing_sha256` under `metadata`. It sits inside the task
package, so BenchFlow's `task_digest` covers it, and two task sets generated
from different briefings are distinguishable by content rather than by
directory name.

**`run_experiment.py` verifies the stamp, then registers the prompt.** Before
the run starts it reads the stamp, compares it against `prompts/<file>`, and
exits if they differ, printing both hashes and the regeneration command. It
also exits if the selected packages carry more than one briefing, which would
mean a half-regenerated set.

Then it registers the briefing text in MLflow's prompt registry under
`bank-briefing` and logs four params: `briefing_file`, `briefing_sha256`,
`briefing_prompt_uri`, `briefing_prompt_version`.

Registration reuses an existing version with identical text rather than
creating a new one, so re-running an arm does not inflate the version number
and a version keeps meaning "a distinct briefing".

## What the registry is and is not for

It is not how the prompt is delivered. Nothing reads `prompts/` at eval time —
the briefing is baked into `task.md` when the package is generated and frozen
into the image. Git stays the source of truth, and a clone reproduces a run
without the registry.

What it adds is a per-briefing identifier, which is the thing `digest_prompts`
cannot supply, plus version diffing in the MLflow UI and retrieval of any
historical briefing text without a checkout.

`MlflowClient.link_prompt_version_to_run` exists and accepts the call, but
`list_logged_prompts` does not read the link back on this store, so it is not
used. Params work and are visible; a call that silently does nothing is worse
than no call.

## Baseline

Not applicable. This changes what a run records, not what an agent does. There
is no score to move, and the deterministic verifier and the rubric are both
untouched.

## How it was verified

```
register_briefing on tasks/  →  prompts:/bank-briefing/1
called twice                 →  same URI, no second version
prompts/briefing.md edited   →  refused, both hashes printed
restored                     →  prompts:/bank-briefing/1 again
check_oracles.py             →  48/48, smoke: stdio transport OK
```

Run against a scratch tracking database, so the project's own `mlflow.db` was
not written to.

## Result

Landed. Every run from this commit records which briefing produced its tasks,
and a stale task set stops the run instead of quietly mislabelling it.

## Verdict

Landed. The gap it closes is the reason 002 could be left unmeasured without
losing the ability to measure a prompt change later: the arms are now
distinguishable in the tracking store, so Level B costs a task set and a run,
not a redesign.
