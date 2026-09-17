# 005 — The briefing moves into MLflow's prompt registry

Status: landed
Date: 2026-09-17
Touches: `tools/make_task.py`, `tools/run_experiment.py`,
`tools/register_briefing.py` (new), `prompts/briefing.md` →
`prompts/briefing.seed.md`, all 48 `tasks/*/task.md`
Moves which digest: `digest_tasks` and `digest_prompts`
Supersedes: [004](004-briefing-provenance.md)

## The problem

[004](004-briefing-provenance.md) gave every task package a stamp naming the
briefing file and its hash, and made `run_experiment.py` refuse to start when
`prompts/briefing.md` had moved since the tasks were generated.

It worked, and it was the wrong shape. The briefing existed twice — once as a
file in git, once as a registered version in MLflow — and the refusal existed
only to police the gap between the two copies. A check whose entire purpose is
to catch drift between two things that should not both exist is a symptom, not
a fix.

The argument made at the time for keeping the file authoritative was that
MLflow caches prompts and a prompt could change under a run. That was wrong.
`MLFLOW_ALIAS_PROMPT_CACHE_TTL_SECONDS` defaults to 60, but
`MLFLOW_VERSION_PROMPT_CACHE_TTL_SECONDS` defaults to `inf`: a pinned version is
fetched once and never re-resolved. The hazard applies to aliases, which nothing
here uses.

## The change

The registry is the source of truth for briefings. There is one copy.

**`make_task.py` loads the briefing by pinned version.** `--briefing-version N`,
defaulting to the newest registered, and the resolved URI is printed before
generation starts. It stamps `briefing_prompt_uri` into each package's
frontmatter:

```yaml
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/1
```

**`run_experiment.py` only reads.** It recovers the URI from the packages and
logs it. No write path to the registry exists at run time, so a run cannot
change the prompt it is recording.

**The staleness check is gone**, because a pinned version is immutable and
there is nothing to drift from. What remains is a check for a half-regenerated
task set — packages pointing at two different versions — which stops the run
before rollouts are paid for.

**`tools/register_briefing.py` seeds or imports.** Two moments need text to
enter the registry from outside: a fresh tracking store with nothing in it, and
a variant drafted elsewhere. Ordinary edits do not go through it; you edit in
the MLflow UI and saving creates the next version.

**The placeholder is now `{{scenario}}`**, MLflow's convention, replacing the
bespoke single-brace `{scenario}`. Registration refuses a briefing that lacks
it, since that would give all 48 tasks the same empty case.

**`prompts/briefing.md` became `prompts/briefing.seed.md`**, named the way
`verifier/db.seed.json` is: a starting point read once, not a live copy that has
to be kept in step. Editing it after seeding does nothing, which is the point.

## What this buys

**A prompt change becomes measurable from one commit.** Two task sets generated
from two versions run side by side:

```bash
python tools/make_task.py … --briefing-version 1 --out tasks
python tools/make_task.py … --briefing-version 2 --out tasks-v2
```

The arms log different `briefing_prompt_uri` values. Under the old scheme two
briefings in `prompts/` collided in one `digest_prompts`, so the field meant to
tell prompts apart failed exactly when it was needed — that collision is why
[002](002-briefing-disclosure-order.md) was left unmeasured rather than isolated.

**One identifier instead of three.** `briefing_prompt_uri` replaces a filename,
a content hash and a directory digest. Versions are immutable and cannot
collide.

**It matches what MLflow documents**, so the convention does not have to be
learned from this repository.

## What it costs

**A bootstrap step.** An empty registry cannot generate tasks. `register_briefing.py`
covers it, but it is a step a fresh checkout has to know about, and the guide
says so.

**`make_task.py` gained a dependency.** It was stdlib-only and ran anywhere.
Generating tasks now needs `mlflow` and a reachable tracking store.

## Baseline

Not applicable. This changes where the briefing is stored and what a run
records, not what any agent is told. The briefing text is byte-identical to
[002](002-briefing-disclosure-order.md) apart from `{scenario}` becoming
`{{scenario}}`, which is substituted away before the agent sees it.

## How it was verified

```
register_briefing.py               →  prompts:/bank-briefing/1
register_briefing.py again         →  already registered, unchanged (no v2)
make_task.py (no version given)    →  briefing prompts:/bank-briefing/1, 48 generated
task.md                            →  briefing_prompt_uri stamped, {{scenario}} substituted
briefing_identity over 48 tasks    →  prompts:/bank-briefing/1
one task edited to point at /9     →  refused, both URIs printed
check_oracles.py                   →  48/48, smoke: stdio transport OK
```

## Result

Landed. One authoritative briefing, addressed by immutable version, recorded on
every run, and no reconciliation machinery between copies.

## Verdict

Landed, and [004](004-briefing-provenance.md) is superseded rather than built
on. The stamp survives in a better form; the file-hash check and the run-time
registration were both scaffolding around a duplicate that should not have
existed.
