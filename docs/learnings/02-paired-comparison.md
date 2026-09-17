# Reducing variance when you measure a change

You run two configurations and one scores higher. You need to know whether it
would still score higher if you ran everything again.

Variance is how much that difference moves between repeats. The smaller the
variance, the smaller an effect you can detect.

This page covers pairing: comparing the two configurations task by task instead
of by their overall scores. Pairing reduces variance without any extra runs.

Figures come from `python docs/learnings/scripts/pairing_simulation.py`.

---

## Where the variance comes from

Two things move the number between repeats.

**Which tasks are in your set.** Tasks vary enormously in difficulty, and that
spread is usually larger than the effect you are testing.

**What the agent did that time.** Rerun one configuration over the same tasks
and some tasks flip. The agent is not deterministic.

They have different remedies. The first is addressed by pairing, below, at no
cost. The second only by repeat runs, which cost rollouts.

(A third, the scorer disagreeing with itself, is near zero when a program checks
the answer and real when a model grades it. Treat it as a property of the
scoring you chose.)

---

## Pairing

Both arms run the same tasks. Given that, there are two ways to compute the
difference between them:

```
unpaired   compare the two overall pass rates
paired     compute the difference on each task, then average those
```

Both give the same answer. If the treatment passed four more of the 48 tasks,
the delta is 4/48 either way, or 8.3 percentage points.

What differs is the uncertainty around it. Comparing overall pass rates treats
the two arms as unrelated, so every task's difficulty counts as noise twice,
once in each arm's rate. Comparing task by task cancels it, because a task's
difficulty sits in both terms of its own subtraction.

```
same runs, compared task by task       standard error  3.67pp
same runs, compared by overall rate    standard error  9.88pp
```

The precision is a property of having run both arms over the same tasks.
Comparing overall rates reports an interval sized for an experiment where they
had not.

---

## What pairing cannot fix

Hold the task set fixed and rerun both arms. Now only the agent varies, and
pairing changes nothing:

```
standard error, fixed task set    6.48pp   with or without pairing
```

The two arms' randomness is independent, so there is no shared term to cancel.

Repetition is the only remedy. Run each arm `n` times and average, and this
component falls by `√n`: four runs to halve it.

Because the two sources add, a paired comparison is still bounded by how erratic
the agent is. Pairing is worth doing regardless, since it is free, but it does
not remove the need for repeats.

---

## How much pairing buys

The two methods are limited by different quantities, so they are worth looking
at separately. Both tables are for 48 tasks, and the detectable effect is
roughly 2.8 standard errors, the margin at which a result is unlikely to be
chance.

**Paired.** Precision depends on how many tasks the two arms disagree on, and
not at all on the pass rate:

```
tasks that differ    standard error    detectable effect
  2 of 48   ( 4%)         2.9pp              8pp
  4 of 48   ( 8%)         4.2pp             12pp
  9 of 48   (19%)         6.2pp             18pp
 14 of 48   (29%)         7.8pp             22pp
 24 of 48   (50%)        10.2pp             29pp
```

Fewer disagreements gives you a tighter interval. A change that flips four
tasks in the same direction is easier to distinguish from chance than one that
flips fourteen in both directions.

**Compared by overall rate.** Precision depends on where the pass rates sit, and
not at all on how much the arms agree:

```
both arms at         standard error    detectable effect
   50%                   10.2pp             29pp
   70%                    9.4pp             26pp
   90%                    6.1pp             17pp
```

Set them side by side at a 50% pass rate. Comparing by rate needs a 29-point
effect. Paired, the same experiment needs 12 points if the arms disagree on four
tasks, or 18 if they disagree on nine.

The bottom row of the first table is the break-even point: once the arms
disagree on half the tasks, pairing buys nothing. That case means the change is
moving tasks in both directions more or less at random, which is a finding in
itself.

Both tables assume 48 tasks. Every figure shrinks with more tasks, by the
`√n` in [01-standard-error](01-standard-error.md), so recompute for the set you
are running.

---

## Running a paired comparison

```bash
benchflow eval compare-lift \
  --baseline jobs/<baseline-run> --trained jobs/<treatment-run> \
  --out lift.md --json-out lift.json
```

This pairs the rollouts by task and puts an interval around the delta. See
[03-bootstrapping](03-bootstrapping.md) for reading that interval.

Three ways it goes wrong:

**Reusing a job directory.** BenchFlow resumes into an existing one and skips
rollouts it considers done, so the second arm does nothing and you compare a set
of rollouts against itself. The report looks clean and the delta sits near zero.

**Ignoring coverage.** Only tasks scored on both sides get paired. If an arm
crashed on five, you are comparing 43, and crashes cluster on the long
complicated tasks, so the delta describes an easier subset than you think.

**Expecting an invisible effect.** Scoring is pass or fail. An agent reaching the
same answer in half the steps scores identically, so a change aimed at
efficiency will not show up here at all.

---

## Related

- [01-standard-error.md](01-standard-error.md) — how large the variance is
- [03-bootstrapping.md](03-bootstrapping.md) — how the interval is built
- [scripts/pairing_simulation.py](scripts/pairing_simulation.py) — the figures above
