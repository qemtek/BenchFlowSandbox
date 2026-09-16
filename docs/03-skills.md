# Guide: adding and testing skills

> **Cost constraint: one task per run.**
> The OpenRouter key has a small monthly cap and a banking task costs roughly
> $0.15. Run a single task with `--tasks-dir tasks/<task-id>` and
> `--concurrency 1`. A full 40-task arm is ~$6 and would exhaust the balance in
> one command. Check `limit_remaining` at `https://openrouter.ai/api/v1/key`
> before and after.


A skill is reference material deployed into the agent's environment — a
`SKILL.md` describing a procedure, optionally with scripts beside it. Unlike
tools, BenchFlow has a first-class switch for skills, which makes the A/B clean.

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

---

## The switch

```bash
--skill-mode no-skill     # default
--skill-mode with-skill   # deploy environment/skills/ to the agent
--skills-dir ./my-skills  # use your own pack instead of the task's
```

`no-skill` does more than hide the directory. `benchflow/skill_policy.py`
**strips it out of the Docker build context**, so a `COPY .` cannot leak it.
The comparison is honest by construction rather than by trust.

---

## A skill worth writing for this domain

The failure modes we actually observed suggest the content. In one run the
agent took 44 tool calls and still failed; in another it spent turns
rediscovering the call convention. A procedural skill targets exactly that:

```markdown
---
name: bank-case-handling
description: Procedure for handling a Rho-Bank customer case end to end — identity verification, knowledge-base lookup, and discoverable tools.
---

# Handling a customer case

## 1. Identify and verify before anything else
Look the customer up with `get_user_information_by_name`, `_by_email`, or
`_by_id`. Compare what they told you against the record, then call
`log_verification` with the values from the record. Do this before disclosing
or changing anything.

## 2. Find the right procedure in the knowledge base
`/data/documents` holds the bank's internal documentation. Search it before
acting:

    rg -l "replacement card" /data/documents

## 3. Unlock discoverable tools before calling them
Some procedures need a tool that `bank list` does not show. The documentation
names it. Unlock, then call:

    bank call unlock_discoverable_agent_tool '{"agent_tool_name":"<name>"}'
    bank call call_discoverable_agent_tool '{"agent_tool_name":"<name>","arguments":"{\"k\":\"v\"}"}'

Note `arguments` is a JSON **string**, not an object.

## 4. Finish the job
You are judged on the bank's final records, not on what you say. Every action
the customer needed must actually have been executed.
```

Write that to
`tasks/task-036/environment/skills/bank-case-handling/SKILL.md`.

To apply it across all tasks, add it to `make_task.py` so every generated
package carries it.

---

## Running the comparison

```bash
# baseline: no skill
benchflow eval run --tasks-dir tasks/task-036 \
  --agent opencode --model openrouter/anthropic/claude-sonnet-4.5 \
  --skill-mode no-skill --jobs-dir jobs/skill-base --concurrency 1

# treatment: skill deployed
benchflow eval run --tasks-dir tasks/task-036 \
  --agent opencode --model openrouter/anthropic/claude-sonnet-4.5 \
  --skill-mode with-skill --jobs-dir jobs/skill-arm --concurrency 1

benchflow eval compare-lift --baseline jobs/skill-base --trained jobs/skill-arm \
  --out lift.md --json-out lift.json
```

---

## Reading the result honestly

`compare-lift` pairs rollouts by task and reports pass-rate and mean-reward
deltas with 95% bootstrap confidence intervals.

Two things to keep in mind.

**Scoring is binary here.** A task is 1.0 or 0.0, so a skill shows up only when
it flips a task outright. Partial improvements are invisible.

**39 tasks is a modest sample.** The interval will be wide. Treat a delta whose
CI crosses zero as "not shown", not as "no effect". With a single paired task
the bootstrap degenerates entirely — `low == high == the observed delta`.

Also check the coverage table before the delta: only tasks with a healthy,
scored rollout on **both** sides enter the paired metrics, so a crash in one arm
silently drops that task from the comparison.

---

## Reviewing behaviour, not just outcome

The database check says whether the end state is right. It says nothing about
whether the agent followed policy on the way there. `review/rubric.json` carries
blocker criteria for that — verified identity before disclosure, disclosed no
other customer's data, invented no policy.

```bash
benchflow review jobs/skill-arm --rubric tasks/task-036/review/rubric.json \
  --model openrouter/anthropic/claude-sonnet-4.5
```

Reviews run detached and never modify the rollouts' rewards, so the objective
score stays objective. Reviewing the **passing** rollouts (`--passing`) is the
interesting case: an agent that reached the correct database state via a
compliance breach.
