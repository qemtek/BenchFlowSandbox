# Guide: adding and testing skills

A skill is reference material deployed into the agent's environment — a
`SKILL.md` describing a procedure, optionally with scripts beside it. Unlike
tools, BenchFlow has a first-class switch for skills, which makes the comparison
clean without any rebuild.

Every task package ships one skill, `bank-case-handling`, generated from
`SKILL_MD` in `tools/make_task.py`. It is shipped, not deployed:
`--skill-mode no-skill` is the default and BenchFlow strips the directory out of
the build context, so the baseline arm cannot see it. Replace it, or point
`--skills-dir` at your own pack, when you want to control the variable yourself.
What it contains and why is [docs/iterations/003](iterations/003-bank-case-handling-skill.md).

---

## Where a skill goes

```
tasks/task-036/environment/skills/<skill-name>/SKILL.md
                                              /scripts/...   (optional)
```

Anything under `environment/` is carried into the image, so the skill travels
with the task.

To give every task the same skill, write it from `generate()` in
`tools/make_task.py` and regenerate. To test one skill on one task, drop the
file in by hand.

---

## The switch

```bash
--skill-mode no-skill     # default
--skill-mode with-skill   # deploy environment/skills/ to the agent
--skills-dir ./my-skills  # use your own pack instead of the task's
```

`no-skill` does more than hide the directory. `benchflow/skill_policy.py` strips
it out of the Docker build context, so a `COPY .` cannot leak it. The comparison
is honest by construction rather than by trust.

`run_experiment.py` passes `--skill-mode` through and logs it as an MLflow
param, so which arm a run belongs to is recorded rather than remembered.

---

## What belongs in a skill rather than the prompt

General instructions belong in the briefing; specific ones belong in a skill.
The dividing line is how many tasks the content applies to, and it is a
mechanical consequence of how skills are delivered: Claude Code shows the model
a one-line `description` and reads the body only if the model asks for it. That
is a context economy. Content that applies to every task has nothing to
economise, and putting it in a skill only adds a chance the model declines it.

`bank-case-handling` is on the wrong side of that line. It restates the
briefing — verify before changing anything, search `/data/documents` for the
procedure, reach operations through `bank_search` — so a model reading its
description correctly concludes it already has that, and 18 rollouts of 24 did.
See [docs/iterations/003](iterations/003-bank-case-handling-skill.md).

The shape that earns a skill here is one procedure out of several, needed by
some cases and not others: the gold actions across the 48 tasks use 35 distinct
bank operations, and a case touches a handful. A description like "use when the
customer disputes a transaction" is a trigger the model can match against the
case notes. "Procedure for handling a customer case end to end" is not,
because it is true of every case and therefore distinguishes none.

---

## A skill worth writing for this domain

Let the observed failures choose the content, and check first that they are the
agent's failures. Seven of ten reviewed rollouts failed
`identity_verified_before_disclosure`, but that criterion was scoring an
ordering no agent could produce — see
[docs/iterations/001](iterations/001-identity-blocker-definition.md). Writing a
skill against it would have been writing against the judge.

What is left after that correction is worth targeting: rollouts that found the
right document and then skipped its numbered eligibility checks, one that found
the bypass-code procedure and escalated instead of completing it, two that
passed a plausible `reason` code rather than the documented one, and a
trajectory that spent its first six calls guessing tool names before its first
search of `/data/documents`.

```markdown
---
name: bank-case-handling
description: Procedure for handling a Rho-Bank customer case end to end — identity verification, knowledge-base lookup, and specialised operations.
---

# Handling a customer case

## 1. Verify before you change anything
Look the customer up with `get_user_information_by_name`, `_by_email`, or
`_by_id`. Compare what they told you against the record, then call
`log_verification` with the values from the record.

The lookup is how you verify, so it comes first. What waits for
`log_verification` is every operation that changes the bank's records, and
every account detail you state in your closing report.

## 2. Find the procedure before acting
`/data/documents` holds the bank's internal documentation. Eligibility rules,
fees and reason codes live there, not in the tool descriptions.

    rg -l "replacement card" /data/documents

## 3. Reaching a specialised operation
Most operations are not in the loaded toolkit. Three steps:

    bank_search              describe what you want to do
    bank_describe_operation  read its arguments, types and defaults
    bank_call_operation      run it

Do not guess arguments. Describe first — several operations take a reason code
that must match a fixed set.

## 4. Finish the job
You are judged on the bank's final records, not on what you say. Every action
the customer needed must actually have been executed.
```

That is the shipped skill, at
`tasks/*/environment/skills/bank-case-handling/SKILL.md`. Edit `SKILL_MD` in
`tools/make_task.py` and regenerate to change it everywhere; drop a file in by
hand to test a variant on one task.

Note what this skill does *not* do: it never names a specific operation or
argument value. A skill that does becomes an answer key, and any lift you
measure is meaningless. The same boundary applies as to `prompt_prefix` in
`docs/01-prompts.md`.

---

## Testing a skill

**1. Does it deploy, and does the agent open it?** These are two questions, and
a score answers neither. A skill that fails to deploy, a skill the agent never
opens, and a skill that does not help all produce the same pass rate.

```bash
python tools/run_experiment.py --tasks tasks/task-036 --capture-provider \
  --skill-mode with-skill --experiment skills --note "smoke: does it deploy"
```

Claude Code puts the skill's `description` in the prompt and reads `SKILL.md`
only when the model calls the `Skill` tool. Deploying a skill therefore makes
it available, not used, and the gap can be most of the arm: the 2026-09-17
with-skill arm offered `bank-case-handling` in 24 rollouts of 24 and had it
opened in 6.

`tools/skill_uptake.py` is the measurement, and `run_experiment.py` logs it on
every captured run:

```bash
python tools/skill_uptake.py jobs/<run> --skill bank-case-handling
```

| metric | reading |
|---|---|
| `skill_rollouts_offered` | 0 on a with-skill arm means it did not deploy |
| `skill_load_rate` | offered but rarely opened: the arm is mostly a second baseline |
| `skill_first_load_call_mean` | opened late means consulted when stuck, not followed as a procedure |

Do not use `total_skill_invocations` for this. It counts ACP events with
`kind == "skill"`, and Claude Code emits the load as `kind: "other"`, so it
reads 0 however many times the skill was opened. Counting the ACP title
`"Load skill"` instead is also wrong: on that same arm it found five of the six
loads, because one rollout's ACP stream omitted a call the provider capture
recorded. The capture is the only complete record, which is why this needs
`--capture-provider`.

`benchflow eval view jobs/<run>` renders a trajectory as a page when you want
to see how the skill was used once you know it was.

**2. Does it help?** Only worth running once step 1 shows a high load rate.
Below that the with-skill arm is the baseline on every rollout that declined,
and no number of tasks will separate the two.

```bash
python tools/run_experiment.py --tasks tasks --skill-mode no-skill \
  --capture-provider --experiment skills --note "baseline"
python tools/run_experiment.py --tasks tasks --skill-mode with-skill \
  --capture-provider --experiment skills --note "bank-case-handling"

python tools/compare_arms.py \
  --baseline <baseline-mlflow-run-id> --treatment <skill-mlflow-run-id> \
  --note "bank-case-handling skill"
```

The oracle gate does not test skills — it never runs the agent. Skills are the
one lever here with no cheap deterministic check, so budget for the rollouts.

---

## Reading the result honestly

`compare_arms.py` wraps `benchflow eval compare-lift`, which pairs rollouts by
task and reports pass-rate and mean-reward deltas with 95% bootstrap confidence
intervals, and records the comparison as its own MLflow run.

**Scoring is binary.** A task is 1.0 or 0.0, so a skill shows up only when it
flips a task outright. An agent that reaches the same answer in half the calls
scores identically. Watch `calls_per_gold_action` and `cost_per_solved_task_usd`
in MLflow for that — both are logged, neither is scored.

**48 tasks is a modest sample.** Sampling noise alone puts the standard error on
pass rate near 7 percentage points, before any agent stochasticity. Pairing
cancels task difficulty, which is most of it, but the interval will still be
wide. If the interval includes zero, the experiment could not tell whether the
skill helped, which is different from showing it did not.
With a single paired task the bootstrap degenerates entirely: low, high and the
observed delta collapse to the same number.

**Check coverage before the delta.** Only tasks with a healthy scored rollout on
both sides enter the paired metrics, so a crash in one arm silently drops that
task from the comparison.

**Check the load rate before the delta.** A delta is a statement about the
rollouts where the skill was read. At a load rate of 0.25 that is a quarter of
the arm, and the interval is wide for a reason no number of extra tasks fixes.

---

## Reviewing behaviour, not just outcome

The database check says whether the end state is right. It says nothing about
whether the agent followed policy on the way there — and a skill about procedure
is aimed squarely at the way there.

```bash
python tools/run_experiment.py --tasks tasks --skill-mode with-skill --review \
  --experiment skills --note "bank-case-handling, judged"
```

`--review` grades the rollouts against `review/rubric.json` and logs the result
to the same MLflow run: per-criterion pass rates as metrics, judge model and
rubric digest as params. Reviews run detached and never modify the rollouts'
rewards, so the objective score stays objective.

This is where a procedural skill should show up first. A skill that fixes
`identity_verified_before_disclosure` without moving pass rate has still done
something real, and only the review can see it.

One caveat: the judge has never been checked against human labels. Treat its
numbers as a signal to investigate, not as ground truth.

---

## Related

- `docs/01-prompts.md` — telling the agent something directly instead
- `docs/02-tools.md` — changing what it can do rather than what it knows
- `docs/versioning-gaps.md` — what a run records
