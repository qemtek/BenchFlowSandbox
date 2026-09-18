# 006 — Listing every request moves into the briefing

Status: applied, awaiting runs
Date: 2026-09-18
Touches: `prompts/briefing.seed.md`, the prompt registry, all 48 `tasks/*/task.md`
Moves which digest: `digest_tasks` and `digest_prompts`
Follows: [003](003-bank-case-handling-skill.md)

## The problem

[003](003-bank-case-handling-skill.md) shipped a seven-step skill and measured
nothing, because the agent opened it in 6 rollouts of 24. The cause was not the
description's wording. Six of its seven steps restated the briefing, so a model
that had read the briefing correctly concluded there was nothing to fetch.

One step did not restate anything:

> **1. List every distinct request before acting.** A case often contains more
> than one. You are judged on all of them, and a case that ends with one
> handled and three ignored scores the same as one where you did nothing.

The briefing's closing paragraph says "every action the customer needed must
actually be executed before you stop", which states the scoring rule. It does
not tell the agent to enumerate the requests before starting, and the two are
different instructions: one says what will be counted, the other says what to
do first.

That content applies to every case. A skill delivers content conditionally —
Claude Code shows the model a one-line description and reads the body only if
asked — so general content in a skill buys nothing and adds a chance of being
declined. It belongs in the prompt, where it arrives in every rollout.

## The change

Add an instruction to `prompts/briefing.seed.md`, in the "What to do now"
section, before the existing sentence about the final state:

> Read the case notes through and list every distinct request the customer
> made before you act on any of them. A case often contains more than one, and
> you are judged on all of them.

Register the result as `bank-briefing` version 2 and regenerate the 48 task
packages against it, so every task records `briefing_prompt_uri:
prompts:/bank-briefing/2`.

Nothing else changes. `bank-case-handling` stays as it is for now: it is
superseded by [007](007-per-procedure-skills.md) rather than by this page, and
deleting it here would put two changes in one comparison.

## Baseline

`fea7eb97`, the no-skill arm of 003: 24 tasks, full coverage, 3 passed,
pass rate 0.125, 751 tool calls, 2.69 calls per gold action.

That arm ran at `prompts:/bank-briefing/1`, which is the briefing this page
changes, so it is the control for this comparison as well.

Multi-request cases are most of the set. Across the 48 tasks the reference
actions average 3.0 distinct action types, and 19 tasks require six or more
bank operations, so an agent that handles the first request and stops loses
those outright.

## Prediction

The briefing change should raise the pass rate, and the effect should be
concentrated in tasks with more than one request.

Stated so it can fail: **at least 3 of the 24 half-set tasks flip from fail to
pass, and the tasks that flip have more gold actions than the ones that do
not.** A delta whose interval includes zero, or flips spread evenly across
task sizes, does not support the claim.

`review_handled_request_completely_mean_score` should rise. That criterion is
scored per rollout rather than per task flip, so it can move on rollouts that
still fail overall, and it is the more sensitive instrument at this sample size.

This is the same prediction 003 made and could not test, because the content
reached 6 rollouts. Here it reaches 24 by construction, and no uptake number
stands between the change and the result.

## How it is measured

Both arms over the pre-registered half-set in `tools/half_set.txt`, `no-skill`
on both sides so the skill is not a second variable:

```bash
python tools/register_briefing.py --from-file prompts/briefing.seed.md
python tools/make_task.py --briefing-version 2

python tools/run_experiment.py --tasks tasks --skill-mode no-skill \
  --capture-provider --review --experiment briefing \
  --note "v2: list every request" $(cat tools/half_set.txt | sed 's/^/--include /')

python tools/compare_arms.py --baseline fea7eb97fee04c3f9132340e571a38c0 \
  --treatment <new-run-id> --note "briefing v2"
```

The control arm is `fea7eb97` rather than a fresh run. That is only sound
because nothing else moved between them: same 24 tasks, same agent, same
model, same skill mode. `compare_arms.py` will report `briefing_prompt_uri` and
`digest_tasks` as the levers that differ and accept the pair, which is what
that guard is for — a briefing arm changes every task digest on purpose.

### What to read, in order

1. `health_coverage` on both arms. Below 1.0 the rest describes a different
   experiment.
2. `compare_arms.py`'s interval, not its point estimate.
3. `review_handled_request_completely_mean_score` on both arms.
4. Whether the flipped tasks are the larger ones. A win concentrated in
   single-request tasks would mean something other than this change caused it.

### The floor, at this size

Paired standard error on 24 tasks is about 5.2pp, so a pass-rate effect needs
roughly 3 of 24 tasks to flip one way before it clears noise. 003 saw six tasks
change hands for a net zero, which is what the floor looks like when nothing is
happening — and the noise floor run that would let us tell the two apart has
still not been done. Until it has, a result here that clears the floor is
suggestive rather than settled.

## Result

Applied 2026-09-18. `prompts:/bank-briefing/2` registered
(`0a77af1898ce`), all 48 task packages regenerated against it, oracle gate
48/48 with the stdio smoke test advertising 17 tools. Only `task.md` changed in
each package, so `digest_environment` is unmoved and the skill is untouched.

The arms have not been run. They are held behind the noise floor: 003 produced
six discordant tasks for a net zero delta, and without a repeat of one
unchanged arm there is no way to tell a real three-task effect from that.

## Verdict

Pending the runs.
