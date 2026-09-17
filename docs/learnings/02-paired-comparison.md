# Paired comparison: getting under the noise floor without more tasks

Comparing two arms by their aggregate pass rates needs a 29-point effect before
it can see anything ([standard error](01-standard-error.md)). Pairing gets that
down to roughly half, and costs nothing but running both arms over the same
tasks — which you were doing anyway.

---

## Why aggregate comparison wastes information

Most of the spread between two runs comes from **which tasks are hard**, not
from which arm is better.

task-004 is difficult under every arm. task-012 is easy under every arm. When
you compare 56% against 62%, that difficulty variation is sitting inside both
numbers, and the comparison cannot tell it apart from the effect you care about.
Difficulty ends up counted as noise.

It is not noise. It is a known, fixed property of each task, identical on both
sides. Pairing exploits exactly that.

---

## What pairing does

Both arms ran the same 48 tasks, so compare them task by task rather than in
aggregate. Every task falls into one of four cells:

```
                        treatment
                      pass    fail
baseline   pass         a       b
           fail         c       d
```

Cells `a` and `d` — where the arms agree — carry **no information about the
difference**. A task both arms passed tells you it was easy, not that the
treatment helped. The same for a task both arms failed.

Only the disagreements matter:

```
c    failed in baseline, passed in treatment    evidence for
b    passed in baseline, failed in treatment    evidence against
```

This is McNemar's test. The question stops being "is 62% bigger than 56%" and
becomes "of the tasks that changed, did more improve than regressed".

---

## A worked example

```
both passed                      28 tasks     no information
both failed                      14 tasks     no information
improved (fail → pass)            5 tasks     evidence for
regressed (pass → fail)           1 task      evidence against
                                 ──────────
                                 48 tasks
```

Aggregate view: 29/48 → 33/48, a 4-point gain sitting inside a ±20-point
interval. Unreadable.

Paired view: 6 tasks changed, 5 of them favourably. That is a much sharper
question, and one a bootstrap can put an interval around.

Note the trade: your effective sample is the 6 discordant tasks, not 48. That
sounds like a loss and is a gain, because you removed the variation that was
drowning the signal rather than averaging over it.

---

## How much it buys you

The paired error depends on how many tasks disagree, not on how many you ran:

```
tasks that disagree      SE      detectable effect
 2 of 48   ( 5%)        3.2pp          9pp
 4 of 48   (10%)        4.6pp         13pp
 9 of 48   (20%)        6.5pp         18pp
14 of 48   (30%)        7.9pp         22pp

unpaired, same 48      10.2pp         29pp
```

Read that from the right column. A change that moves 10% of tasks is detectable
paired and invisible unpaired.

The counter-intuitive part: **fewer disagreements is better**, because a
consistent effect on a small number of tasks is easier to distinguish from
chance than a scattered one. An arm that changes everything randomly gives you a
wide interval no matter how many tasks you run.

---

## Running it

BenchFlow does the pairing and the bootstrap:

```bash
benchflow eval compare-lift \
  --baseline jobs/<baseline-run> --trained jobs/<treatment-run> \
  --out lift.md --json-out lift.json \
  --bootstrap-seed 42
```

The bootstrap resamples the 48 paired results with replacement, 1,000 times,
recomputing the delta each time, and reports the 2.5th and 97.5th percentiles.
It answers: given the task set I happen to have, how much would this delta move
if I had drawn a different 48?

Pass `--bootstrap-seed` if you intend to cite the interval, so it reproduces.

---

## Four ways to fool yourself

**Reusing a job directory.** BenchFlow resumes into an existing directory and
skips rollouts it considers done. Point both arms at one directory and the
second arm does nothing, leaving you comparing a set of rollouts against itself.
It produces a clean report, a delta near zero, and no error at all. Always a
fresh `--jobs-dir` per arm.

**Ignoring the coverage table.** Only tasks with a healthy scored rollout on
*both* sides get paired. If an arm crashed on five tasks you are comparing 43,
not 48 — and crashes are not random, they cluster on the long, complicated
tasks. The delta is then computed over an easier subset without saying so. Read
coverage before you read the delta.

**Reading "interval crosses zero" as "no effect".** It means *not shown*. You
failed to detect something, which is equally consistent with a real effect too
small for this task set. Absence of evidence is not evidence of absence, and
this is the most common way to mislead yourself here.

**Expecting an invisible effect to appear.** Scoring is binary. An agent that
reaches the identical answer in half the tool calls scores exactly the same. If
your change was meant to improve efficiency rather than correctness,
`compare-lift` is the wrong instrument — read `calls_per_gold_action` and
`cost_per_solved_task_usd` instead.

---

## Related

- [01-standard-error.md](01-standard-error.md) — where the floor comes from
- [../01-prompts.md](../01-prompts.md), [../03-skills.md](../03-skills.md) —
  the levers you would compare
