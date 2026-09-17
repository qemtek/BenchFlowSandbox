# Guide: adding and testing skills

A skill is reference material deployed into the agent's environment — a
`SKILL.md` describing a procedure, optionally with scripts beside it. Unlike
tools, BenchFlow has a first-class switch for skills, which makes the comparison
clean without any rebuild.

These task packages ship **no skills**. That is deliberate: you author the
skill, so you control the variable instead of inheriting someone else's.

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

## A skill worth writing for this domain

Let the observed failures choose the content. Seven of ten reviewed rollouts
disclosed account details before logging verification, and one task took 63 tool
calls against a one-action gold. A procedural skill targets exactly that:

```markdown
---
name: bank-case-handling
description: Procedure for handling a Rho-Bank customer case end to end — identity verification, knowledge-base lookup, and specialised operations.
---

# Handling a customer case

## 1. Verify before you read anything back
Look the customer up with `get_user_information_by_name`, `_by_email`, or
`_by_id`. Compare what they told you against the record, then call
`log_verification` with the values from the record.

Reading an account detail back to the customer is disclosure. Verify first.

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

Write it to `tasks/task-036/environment/skills/bank-case-handling/SKILL.md`.

Note what this skill does *not* do: it never names a specific operation or
argument value. A skill that does becomes an answer key, and any lift you
measure is meaningless. The same boundary applies as to `prompt_prefix` in
`docs/01-prompts.md`.

---

## Testing a skill

**1. Does it deploy?** Run one task with the skill on and check the agent
mentions it or follows it. A skill that silently fails to deploy looks exactly
like a skill that does not help.

```bash
python tools/run_experiment.py --tasks tasks/task-036 \
  --skill-mode with-skill --experiment skills --note "smoke: does it deploy"
```

A skill that silently fails to deploy and a skill that does not help look
identical in the score. `benchflow eval view jobs/<run>` renders the trajectory
as a page, so you can see whether the agent read it at all.

**2. Does it help?** Both arms over the whole set, separate job directories:

```bash
python tools/run_experiment.py --tasks tasks --skill-mode no-skill \
  --experiment skills --note "baseline"
python tools/run_experiment.py --tasks tasks --skill-mode with-skill \
  --experiment skills --note "bank-case-handling"

benchflow eval compare-lift \
  --baseline jobs/<baseline-run> --trained jobs/<skill-run> \
  --out lift.md --json-out lift.json
```

The oracle gate does not test skills — it never runs the agent. Skills are the
one lever here with no cheap deterministic check, so budget for the rollouts.

---

## Reading the result honestly

`compare-lift` pairs rollouts by task and reports pass-rate and mean-reward
deltas with 95% bootstrap confidence intervals.

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
