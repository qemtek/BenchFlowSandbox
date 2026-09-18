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
- `skill_load_rate` and `skill_first_load_call_mean` — whether the skill was
  opened at all, and whether it was opened early enough to act as a procedure
  (`tools/skill_uptake.py`). Without them, "the skill did not help" and "the
  agent never read it" are the same number.

  Written before the run as `total_skill_invocations`, which turned out to
  measure nothing here; the uptake metrics replaced it afterwards and both arms
  were backfilled. See below.

## How it is measured

Two runs, same commit, separate job directories (BenchFlow resumes into an
existing one and would compare the arm against itself).

### The half-set, and why

The first attempt ran all 48 tasks in one arm and lost 27 of them to
`provider_rate_limit`, so it scored 21 and could not be compared with anything.
The subscription cap is a six-hour rolling window, so concurrency does not help:
total volume is the only lever. Both arms over 24 tasks answers more than one
broken arm over 48.

`tools/half_set.txt` holds the 24, chosen before either arm ran by a rule with
no room for judgement: sort every task by its gold action count, ties broken by
id, and take every second one. That makes the half-set span the difficulty range
in the same proportions as the full set rather than accidentally collecting the
short tasks.

```
set         n  golds   mean  min  max   med
full       48    575   12.0    1   34  12.5
half-set   24    279   11.6    1   25  12.0
```

Recorded here rather than in a shell history, because a task subset chosen after
seeing results is not a subset, it is a selection.

### The runs

```bash
python tools/run_experiment.py --tasks tasks --skill-mode no-skill \
  --model claude-sonnet-4-5-20250929 --capture-provider --concurrency 8 \
  $(sed 's/^/--include /' tools/half_set.txt | tr '\n' ' ') \
  --experiment skills --note "003 baseline, 24-task half-set"

python tools/run_experiment.py --tasks tasks --skill-mode with-skill \
  --model claude-sonnet-4-5-20250929 --capture-provider --concurrency 8 \
  $(sed 's/^/--include /' tools/half_set.txt | tr '\n' ' ') \
  --experiment skills --note "003 treatment, 24-task half-set"

python tools/compare_arms.py --baseline <run-id> --treatment <run-id> \
  --note "bank-case-handling on the 24-task half-set"
```

`--review` is deliberately not passed. It is 24 more rollouts per arm and it is
the half that can be deferred at no loss: `benchflow review` grades the archived
job directory whenever there is headroom, for the same result.

The model is pinned. The capture on the failed attempt resolved the alias to
`claude-sonnet-4-5-20250929`, which is the only place that id has ever appeared
in this project, so there is no longer an excuse for recording an alias.

### What to read, in order

1. `health_coverage` and `errored` on **both** arms. The failed attempt scored
   21 of 48 and still printed a pass rate. Anything below full coverage means
   the rest of the numbers describe a different experiment from the one
   intended.
2. `skill_rollouts_offered` and `skill_load_rate` on the treatment arm. At zero
   offered the skill never deployed; at a low load rate it deployed and was
   declined, and the arm is mostly a second baseline. Either way nothing else
   in the run bears on whether the skill works.
3. `compare_arms.py`, which refuses arms that did not ask the same questions
   and reports the interval rather than the point estimate.

### The floor, at this size

Paired standard error on 48 tasks is 3.67pp. Halving the task count widens it
by roughly √2, to about 5.2pp, so a pass-rate effect needs something like 5 of
the 24 tasks to flip before the interval clears zero.

The four failures this skill targets are 2 of the 24 in the half-set. So
`pass_rate` cannot settle this, and it was never going to: the per-rollout
review criteria and `calls_per_gold_action` are the measurements with the
resolution to see an effect, and the review is now deferred. State plainly in
the Result section that the deterministic arm is underpowered by construction.

## Result

Measured 2026-09-17/18. Baseline `fea7eb97`, treatment `90f6336f`, comparison
`7eb5535b`. 24 tasks, full coverage on both arms, `skill_mode` the only lever
`compare_arms.py` found moving.

```
                  no-skill   with-skill
passed              3 / 24       3 / 24
tool calls             751          759
calls per gold        2.69         2.72

pass-rate delta  +0.000   95% CI [-0.208, +0.208]
```

Undecided, as predicted. Six tasks were discordant — `task-012`, `task-036`,
`task-043` gained, `task-050`, `task-062`, `task-075` lost — which nets to
nothing and is roughly the number the floor said would be needed to see an
effect at all.

### The treatment arm mostly did not receive the treatment

The more useful finding came from the provider capture, not the scores. The
skill's *name* reached the model in 24 of 24 rollouts; its *body* in 6.

```
skill body loaded:  task-085 task-087 task-088 task-091 task-092 task-095
```

Claude Code advertises an available skill and reads `SKILL.md` only when it
judges the skill relevant. So 18 of 24 treatment rollouts ran with the skill
present and unread. This is not a test of the skill; it is a test of offering
one, and the pass-rate result above should be read as such.

```
skill_rollouts_offered      24
skill_rollouts_opened        6
skill_load_rate           0.25
skill_first_load_call_mean 15.7   (max 24)
```

None of the six opened it at the start:

```
task-085  call 16 of 83      task-091  call 24 of 85
task-087  call 14 of 53      task-092  call 16 of 68
task-088  call 13 of 32      task-095  call 11 of 54
```

The skill is written as a procedure — step 1 is "list every distinct request
before acting" — and every model that read it had been acting for at least
eleven calls. So the six are not six tests of the skill either. They are six
agents consulting a reference once already committed to an approach, which is
a different intervention from the one the page proposed.

In the 6 where it was read, neither arm passed anything, and calls per gold
action moved the wrong way, 1.79 to 1.97. Six tasks, so that is an observation
rather than a finding.

### Why it was declined: the skill restates the briefing

The uptake is not a quirk of the description's wording. The content was already
in the prompt:

| Briefing | Skill |
|---|---|
| "Verify the customer's identity and record it with `log_verification` before you change anything… 1. Look the customer up 2. Compare 3. Call `log_verification`" | 2. Verify before you change anything |
| "policy live in the bank's internal documentation at `/data/documents`; search it and follow the procedure it describes" | 3. Find the documented procedure |
| "`bank_search` → `bank_describe_operation` → `bank_call_operation`" | 4. Reach a specialised operation |

A model reading *"Procedure for handling a Rho-Bank customer case end to end —
reading every request, verifying identity, finding the documented procedure…"*
against a briefing that already says all of that concludes there is nothing to
fetch, and declines. On this reading the 18 refusals were correct, and the
experiment was mis-specified rather than the agent mis-behaving.

Only step 1, listing every distinct request before acting, is content the
briefing does not carry — and it is general, so it belongs in the briefing too.
That is iteration 006. What belongs in a skill is the content that applies to
some cases and not others; see `docs/03-skills.md`.

### `total_skill_invocations` does not measure this

Both arms logged `total_skill_invocations: 0`, including the arm where six
rollouts demonstrably read the file. This page and `docs/03-skills.md` both
tell the reader to check that metric first and to treat zero as "the skill
never deployed". On this evidence the metric does not count Claude Code skill
reads, so zero means nothing either way.

The cause is a shape mismatch: the counter takes ACP events with
`kind == "skill"`, and Claude Code emits the load as
`{"kind": "other", "title": "Load skill"}`.

Counting that ACP title instead is also wrong. Doing so on this arm finds five
of the six loads: `task-087` called the `Skill` tool and its ACP stream does not
record it. The provider capture is the only complete record, so the measurement
is `tools/skill_uptake.py`, which reads `Skill` tool calls out of
`trajectory/llm_trajectory.jsonl` and is logged on every captured run. Both arms
here were backfilled with it.

Without `--capture-provider` none of this exists, and the uptake problem would
have been invisible — the arms would have looked like a clean null result.

### The confound, resolved by 007

This page originally offered two explanations for which rollouts opened the
skill: five of the six were in the batch replayed by `--resume`, and the
loaders were larger tasks. Both are wrong.

[007](007-per-task-starting-state.md) found that 7 of these 24 tasks were
unsolvable — the customer to be verified was absent from the task's own seed
database, so there was no route to a `user_id`.

```
skill opened:  6 of the 7 unsolvable tasks
               0 of the 17 solvable tasks
```

The model opened the skill when it was stuck with no way forward. The load rate
of 0.25 measured how many tasks were broken, not how many made the skill look
relevant.

It also changes the scores on this page. Both arms passed 3, read here as 3 of
24. Against a reachable denominator it is 3 of 17.

### What this licenses

Nothing about whether the skill helps. Two things it does establish:

- Uptake, not content, is the binding constraint, and the cause of the low
  uptake is duplication rather than wording. A skill that restates the briefing
  has nothing to offer a model that has already read the briefing. Getting it
  read means writing a skill that carries content the prompt does not.
- The no-skill arm is clean. The skill body appears in 0 of 24 baseline
  rollouts and the name in 0 of 24, so BenchFlow's stripping works as
  `docs/03-skills.md` claims: honest by construction.

## Verdict

Inconclusive on the question asked, and mis-specified besides. The skill was
general content placed in a mechanism built for conditional content, so the
agent was offered a procedure it already had and declined it 18 times out of
24. Recorded rather than retried: retrying this design would buy the same
answer.

It splits into two successors. Step 1 is general, so it goes in the briefing
(006, the prompt lever). Per-procedure skills are what the skills lever was
for, and they need content the briefing does not carry (007, conditional on the
knowledge base not already covering it).

The next run worth paying for is not this one repeated. It is the noise floor:
one arm, twice, unchanged. Six discordant tasks out of 24 with a zero net delta
is equally consistent with a real two-way effect and with an agent that flips
six tasks between identical runs, and until that number exists no comparison
here can be read.
