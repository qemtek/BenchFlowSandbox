# Iterations

One page per change to the system. Each page says what is changing, what the
numbers were before, and what they were after.

The reason for the folder: this repository exists to run controlled
experiments, and a change to how those experiments are scored deserves the same
treatment as a change to an agent. Without a written baseline, "that fixed it"
is a memory rather than a measurement.

Distinct from `docs/learnings/`, which explains how to read a number, and from
the guides in `docs/`, which explain how to change a lever. These record what
was changed, and what happened.

| | Change | Status |
|---|---|---|
| 001 | [What the identity blocker means](001-identity-blocker-definition.md) | landed, unmeasured |
| 002 | [Telling the agent what disclosure means](002-briefing-disclosure-order.md) | landed, unmeasured |
| 003 | [A procedural skill, aimed at the four remaining failures](003-bank-case-handling-skill.md) | applied, awaiting runs |
| 004 | [Recording which briefing produced a task set](004-briefing-provenance.md) | superseded by 005 |
| 005 | [The briefing moves into MLflow's prompt registry](005-briefing-in-the-prompt-registry.md) | landed |

---

## The rules

**One variable per page.** The rubric and the briefing both touch the same
failure, and changing them together makes the result unattributable. They are
pages 001 and 002 for that reason.

**Write the page before making the change.** The baseline, the prediction and
the measurement plan all have to be fixed in advance, or the result is chosen
after seeing it.

**State a prediction specific enough to be wrong.** "Should improve the blocker
pass rate" cannot fail. "6 of the 7 failures flip, and task-005 does not"
can.

**Work out the floor before spending rollouts.** Paired standard error on this
task set is 3.67pp, so a pass-rate effect needs roughly 7 of 48 tasks to move
before it clears zero. If the change cannot plausibly move that many, say so on
the page and measure something else — per-criterion review rates and
`calls_per_gold_action` are both cheaper and more sensitive than pass rate.

**Re-grading beats re-running where it applies.** A change to the rubric or the
reviewer can be measured against archived rollouts with `benchflow review`,
which costs reviewer rollouts only. A change to the briefing, the tools or a
skill cannot — it changes what the agent does, so it needs fresh rollouts.

**Not every change needs a number.** A change whose case is deductive — a
criterion that cannot be satisfied, a task set that scores a rule it never
states — is `landed, unmeasured`. Write down that the measurement was
considered and dropped, and why, so the absence does not read as an oversight
and nobody later cites the change as an improvement it was never shown to be.

**A run-time switch is worth more than a commit.** A change behind a flag
(`--skill-mode`, `--tasks`, `--config-override`) is measured from one commit
with two runs. A change baked into a file costs an extra task set or a
checkout. When you have the choice, put the variable behind a switch.

**Prove the two arms asked the same questions.** `compare-lift` pairs rollouts
by task id and will pair two tasks that share an id and nothing else.
`tools/compare_arms.py` now runs `benchflow tasks overlap` over the two runs'
task manifests first, and refuses a comparison where the rosters differ, or
where a subset of task packages differs — a stray regeneration that touched six
of 48 produces a delta that looks ordinary and is contaminated. A prompt arm
changes every task digest on purpose, and that case is allowed because
`briefing_prompt_uri` explains it.

**Measure the control when the instrument is stochastic.** The reviewer is an
LLM and disagrees with itself between runs. Comparing a new rubric against an
old report is confounded by that; re-grading the same rollouts under both
rubrics is not.

**Record the run ids.** A page that says "the blocker pass rate went to 90%"
without naming the job directory that produced it is an assertion.

---

## The template

```markdown
# NNN — <what changes, in a phrase>

Status: proposed | applied, awaiting runs | measured | landed | landed, unmeasured | superseded by NNN | reverted
Date: YYYY-MM-DD
Touches: <files>
Moves which digest: <digest_tasks | digest_prompts | ... | none>

## The problem
What is wrong, with the evidence that shows it.

## The change
What will be different afterwards. Exact enough to implement from.

## Baseline
The numbers before, and the run they came from.

## Prediction
What should happen, stated so that it can fail.

## How it is measured
The commands. What the control arm is.

## Result
The numbers after, and the run they came from.

## Verdict
Landed, reverted, or inconclusive — and what it changed about the next step.
```
