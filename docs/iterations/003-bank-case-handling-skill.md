# 003 — A procedural skill, aimed at the four remaining failures

Status: applied, unmeasured
Date: 2026-09-17
Touches: `tools/make_task.py` (`SKILL_MD`), adds
`tasks/*/environment/skills/bank-case-handling/SKILL.md`
Moves which digest: `digest_tasks`
Depends on: [001](001-identity-blocker-definition.md), which removed the
failure this skill would otherwise have been written against

## The problem

`docs/03-skills.md` proposed a skill motivated by the statistic that seven of
ten reviewed rollouts disclosed account details before logging verification.
001 showed that criterion was scoring an ordering no agent could produce, so a
skill written against it would have been written against the judge.

What survives that correction is four failures with the same shape — the agent
found the right document and then did not follow it:

| Task | Reward | What happened |
|---|---|---|
| task-043 | 0.0 | Found the retention procedure, skipped its eligibility checks: pending disputes, pending replacement cards, prior closure attempts |
| task-005 | 0.0 | Found the bypass-code procedure, verified the code, then escalated instead of completing the procedure |
| task-008 | 0.0 | Found the correct reason code in the documentation and passed a different one |
| task-014 | 0.0 | Passed `fraud_or_security_concern` where the documented trigger matched `unconfirmed_external_communication` |

A fifth pattern shows in the trajectories rather than the scores. `task-043`
spent its first six calls on `bank list`, three `bank search` guesses and two
`--help` reads; its first search of `/data/documents` was call 12. The order is
backwards — the documentation names the operation each procedure ends in, so
searching it first answers both questions at once.

## The change

`SKILL_MD` in `tools/make_task.py`, written to every package at
`environment/skills/bank-case-handling/SKILL.md`. Seven numbered steps, one per
observed failure:

1. List every distinct request before acting — several cases carry four or
   more, and `task-092` carries twenty-one gold actions across four cards.
2. Verify before you change anything, with the ordering 001 and 002 settled.
3. Search the documentation before searching for a tool.
4. Follow the whole procedure, not its last step: the eligibility checks near
   the top are part of it, and escalating is not a substitute for completing a
   procedure that applies.
5. `bank_search` → `bank_describe_operation` → `bank_call_operation`, describe
   before calling.
6. Closed-set arguments come from the documentation, not from judgement.
7. Check each request from step 1 against what was actually executed.

It names no specialised operation, no argument value and no reason code. The
only tools named — `log_verification`, `bank_search`,
`bank_describe_operation`, `bank_call_operation` — are in the loaded toolkit
and already named in the briefing, so the skill reveals nothing the agent could
not see. The boundary is the one `docs/01-prompts.md` sets for `prompt_prefix`:
procedure is allowed, solution content is not.

**Shipped, not deployed.** `--skill-mode no-skill` is the default and
`benchflow/skill_policy.py` strips the directory out of the Docker build
context, so adding the file does not change the baseline arm — a `COPY .`
cannot leak it. `--skill-mode with-skill` is the entire difference between the
two arms, and `run_experiment.py` logs it as a param.

## Baseline

Not yet run. Unlike [002](002-briefing-disclosure-order.md), this one is cheap
to isolate: `--skill-mode` is a run-time flag, so both arms come from the same
commit with no second task set and no checkout. That is the whole reason 002 was
left unmeasured and this one was not.

The baseline arm is `--skill-mode no-skill` at this commit. BenchFlow deletes
the bundled skills directory from the staged copy before building, so the
baseline agent sees exactly what it would have seen before the skill existed.

## Prediction

To be written against the baseline before the treatment arm runs, and it has to
name a number.

The honest bound is already known. The four failures above are 4 of 48, or 8.3
percentage points, and paired standard error on this task set is 3.67pp — so
even fixing all four sits inside the noise on `pass_rate`. Stated here rather
than discovered afterwards.

The measurements that can carry a result:

- `review_handled_request_completely_mean_score` — steps 1 and 7 target it, and
  it is scored per rollout rather than per task flip.
- `review_grounded_in_knowledge_base_mean_score` — step 3 targets it.
- `calls_per_gold_action` — step 3 should reduce it. `task-043` used 28 calls
  for 5 gold actions, six of them spent guessing tool names before its first
  search of the documentation.
- `total_skill_invocations` — whether the skill was opened at all
  (`tools/run_experiment.py:377`). Without it, "the skill did not help" and
  "the agent never read it" are the same number.

## How it is measured

Two runs, same commit, separate job directories:

```bash
python tools/run_experiment.py --tasks tasks --skill-mode no-skill \
  --experiment skills --note "003 baseline" --review
python tools/run_experiment.py --tasks tasks --skill-mode with-skill \
  --experiment skills --note "003 bank-case-handling" --review

benchflow eval compare-lift \
  --baseline jobs/<baseline-run> --trained jobs/<skill-run> \
  --out lift.md --json-out lift.json
```

Separate job directories, or BenchFlow resumes into the first and compares the
arm against itself.

Read `total_skill_invocations` on the treatment arm before anything else. If it
is zero the skill never deployed, and nothing else in the run says whether the
skill works.

Both arms are graded under the 001 rubric and carry the same
`briefing_prompt_uri`, so the only difference between them is the skill.

The oracle gate cannot test this. `check_oracles.py` never runs an agent, so
skills are the one lever here with no cheap deterministic check.

## Result

Not yet measured. The change is in the tree: `SKILL_MD` added to
`tools/make_task.py`, all 48 packages regenerated with an identical `SKILL.md`
(one distinct checksum across 48 files), `check_oracles.py` prints 48/48 and
`smoke: stdio transport OK`.

## Verdict

Pending the two runs above. This is the only one of the three changes whose
claim rests on a measurement.
