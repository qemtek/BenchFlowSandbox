# Paired comparison: getting under the noise floor without more tasks

Comparing two arms by their aggregate pass rates needs a 29-point effect before
it can see anything ([standard error](01-standard-error.md)). Running both arms
over the same tasks and differencing per task cuts that to about 10, for no
extra rollouts.

Every figure below is reproducible:
`python docs/learnings/pairing_simulation.py`.

---

## Two sources of variation, only one of which pairing touches

A delta moves between runs for two unrelated reasons, and keeping them apart is
the whole of this page.

**Which tasks you drew.** Your 48 are a sample. task-004 is hard for every
configuration; task-012 is easy for every configuration. Draw a different 48 and
the pass rate moves, regardless of which arm you ran.

**What the agent did that time.** Rerun the identical arm on the identical tasks
and some tasks flip. We have a direct case: 1.00 then 0.0 on the same commit.

`compare-lift`'s interval covers the first. Pairing attacks the first. Nothing
here touches the second.

---

## How pairing removes it

Not by ignoring anything. By **subtracting within each task before averaging**.

Run both arms over the same 48 tasks and compute a per-task difference:

```
d_i  =  treatment_i  −  baseline_i          each one +1, 0, or −1
delta = mean(d_i)
```

Task difficulty sits in both terms of that subtraction, identically, so it
cancels exactly. A task that is hard contributes its hardness to
`treatment_i` and to `baseline_i`, and `d_i` never sees it.

If instead each arm ran its own 48 tasks, difficulty would enter the difference
twice and stay there. That is the entire cost of not pairing.

Simulated, with tasks drawn from a population and a genuine 7-point effect:

```
same 48 tasks   (paired)     SE 3.67pp   detects 10pp
a different 48  (unpaired)   SE 9.85pp   detects 28pp
reduction                    63%
```

**The point estimate is identical either way.** The mean of the per-task
differences equals the difference of the two pass rates — no information is
discarded and nothing is thrown away. Only the variance falls.

---

## What pairing cannot do

Hold the task set fixed and rerun both arms. Now the only thing varying is the
agent, and pairing buys nothing:

```
paired SE on a fixed task set:  6.48pp
```

The two arms' randomness is independent, so there is no shared term to subtract.
This is why pairing does not remove the need for repeat runs: they measure a
different source of variation, and the two add together.

---

## Reading the four cells

The per-task differences group into a familiar table:

```
                        treatment
                      pass    fail
baseline   pass         a       b
           fail         c       d
```

Cells `a` and `d` are the tasks where `d_i = 0`. They are **not discarded** —
they sit in the average as zeros, which is why the denominator is 48 and not 6.
What they contribute is zero variance, and that is the saving.

Cells `b` and `c` carry the signal:

```
c    failed in baseline, passed in treatment    evidence for
b    passed in baseline, failed in treatment    evidence against
```

So the question shifts from "is 62% bigger than 56%" to "among the tasks that
changed, did more improve than regressed, and by enough to outrun chance".

---

## A worked example

You ran both arms over all 48 tasks and sorted the results into the four cells:

```
                                              d_i     count
both passed                                    0       28
both failed                                    0       14
improved   (failed baseline, passed treatment) +1        5
regressed  (passed baseline, failed treatment) −1        1
                                                      ────
                                                        48
```

The delta is the mean of all 48 per-task differences. Forty-two of them are
zero, so the sum is just the improvements minus the regressions:

```
sum of d_i   =  (5 × +1) + (1 × −1) + (42 × 0)  =  +4
delta        =  4 / 48                          =  0.083
             =  +8.3 percentage points
```

Read that as: **the treatment passed four more tasks than the baseline, and four
tasks out of forty-eight is 8.3 percentage points.**

The aggregate route gives the identical number, which is the point:

```
baseline   28 + 1 = 29 passed  →  29/48 = 60.4%
treatment  28 + 5 = 33 passed  →  33/48 = 68.8%
                                  difference = 8.3 percentage points
```

Same delta both ways. What differs is the interval around it. Computed
unpaired, the interval spans roughly ±20 points and the result is unreadable.
Computed paired, the 42 tasks that agreed contribute no variance, so the
interval is roughly a third as wide.

---

## How much it buys you, by how much the arms differ

The paired error depends on how many tasks disagree:

```
tasks that disagree      SE      detectable effect
 2 of 48   ( 5%)        3.2pp          9pp
 4 of 48   (10%)        4.6pp         13pp
 9 of 48   (20%)        6.5pp         18pp
14 of 48   (30%)        7.9pp         22pp

unpaired                9.9pp         28pp
```

Read the right column. A change that moves 10% of tasks is detectable paired and
invisible unpaired.

The counter-intuitive part: **fewer disagreements is better.** A consistent
effect on a small number of tasks is easier to separate from chance than a
scattered one. An arm that changes many tasks in both directions gives a wide
interval however many tasks you run.

---

## Running it

BenchFlow does the pairing and the bootstrap:

```bash
benchflow eval compare-lift \
  --baseline jobs/<baseline-run> --trained jobs/<treatment-run> \
  --out lift.md --json-out lift.json \
  --bootstrap-seed 42
```

The interval around the delta comes from resampling those 48 paired outcomes,
which is the subject of [the next page](03-bootstrapping.md) — including why
`--bootstrap-seed` matters if you intend to quote the result.

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

**Reading "the interval crosses zero" as "no effect".** An interval crosses
zero when its lower bound is negative and its upper bound is positive — say −3
to +11. The data is then consistent with the treatment being worse, identical,
or better, so it has not settled which.

That means *not shown*. You failed to detect something, which is equally
consistent with a real effect too small for this task set to resolve. This is
the most common way to mislead yourself here, and
[03-bootstrapping](03-bootstrapping.md) puts a number on how often it happens.

**Expecting an invisible effect to appear.** Scoring is binary. An agent that
reaches the identical answer in half the tool calls scores exactly the same. If
your change was meant to improve efficiency rather than correctness,
`compare-lift` is the wrong instrument — read `calls_per_gold_action` and
`cost_per_solved_task_usd` instead.

---

## Related

- [01-standard-error.md](01-standard-error.md) — where the floor comes from
- [03-bootstrapping.md](03-bootstrapping.md) — how the interval gets built
- [pairing_simulation.py](pairing_simulation.py) — the evidence above
- [../01-prompts.md](../01-prompts.md), [../03-skills.md](../03-skills.md) —
  the levers you would compare
