# McNemar's test

McNemar's test is the standard way to decide whether two configurations, run
over the same set of pass/fail tasks, really differ. It answers with a yes or a
no rather than a size: either the gap between them is larger than chance would
ordinarily produce, or this experiment cannot say.

[Page 04](04-the-six-task-floor.md) covers one case of this test, where every
task that changed hands went the same way. This page covers the general case,
where some went each way, and gives the p-value for any split.

Figures come from `python docs/learnings/scripts/mcnemar_simulation.py`.

---

## The four groups a paired comparison makes

Both arms run the same 48 tasks, so every task falls into one of four groups.
Take a comparison where the baseline passed 29 tasks and the treatment passed
33:

```
both passed               28
both failed               14
treatment passed only      5
baseline passed only       1
                          --
                          48
```

Those groups account for each arm's total: 28 + 5 = 33 for the treatment,
28 + 1 = 29 for the baseline.

---

## Only the disagreements carry information

The 42 tasks that both arms treated the same way say nothing about which arm is
better. They cancel. What remains is 5 tasks the treatment won and 1 the
baseline won, and the whole difference in pass rates comes from those:

```
(5 − 1) / 48  =  8.3 percentage points
```

So the comparison rests on 6 tasks rather than 48. The count of tasks the two
arms disagree on is the amount of evidence you hold, and it is usually far
smaller than the size of the task set suggests.

---

## Working out the p-value

Suppose the change did nothing. Those 6 tasks still came out one way or the
other, for reasons unrelated to the change, so each behaves like a coin flip.
The question is how often 6 coin flips land 5–1 or more lopsided.

Six flips have 2⁶ = 64 possible outcomes. Counting the ones at least as lopsided
as what was observed, in either direction:

```
6–0     1 way          0–6     1 way
5–1     6 ways         1–5     6 ways
                              ----
                              14 ways
```

```
14 / 64  =  0.219
```

That figure is the **p-value**: the chance of seeing a split this lopsided if
the change had no effect. Around one comparison in five would produce it by luck
alone. The usual threshold for calling a result real is 0.05, this does not
clear it, and so the reading is that the experiment could not tell.

---

## p-values by how the disagreements split

```
 4 to 0  ( 4 disagreements)   p = 0.125
 5 to 0  ( 5 disagreements)   p = 0.062
 6 to 0  ( 6 disagreements)   p = 0.031
 5 to 1  ( 6 disagreements)   p = 0.219
 7 to 1  ( 8 disagreements)   p = 0.070
 8 to 1  ( 9 disagreements)   p = 0.039
 9 to 2  (11 disagreements)   p = 0.065
10 to 2  (12 disagreements)   p = 0.039
12 to 4  (16 disagreements)   p = 0.077
```

Two things move the p-value, and the count of disagreements is only one of them.
Nine disagreements split 8 to 1 clears the threshold; eleven split 9 to 2 does
not, because the extra task flipping backwards costs more than the extra
evidence buys.

---

## The bar when every disagreement goes one way

The table above starts at four disagreements because of what happens below that.
A comparison in which every disagreement favours the same arm still needs six of
them to reach 0.05, and that bar holds whatever the size of the task set.

[Page 04](04-the-six-task-floor.md) derives that number and works through what
follows from it.

---

## How the test compares with the interval

`compare-lift` already reports a bootstrap confidence interval, covered in
[page 03](03-bootstrapping.md). It treats a difference as real when the interval
excludes zero. McNemar's test treats a difference as real when the p-value falls
below 0.05. The two can be run on the same data, so it is worth knowing when
they part company.

They part company in one direction only. Across 20,000 simulated experiments,
there was no case where McNemar called a difference real and the interval did
not. The test is the stricter of the two everywhere.

Strictness is a trade, and the simulation prices it. Each row is 20,000
experiments on 48 tasks, counting how often each method called the difference
real:

```
                        interval says real    McNemar says real
two arms genuinely
equal                          4.6%                 0.6%

treatment genuinely
10 points better              45.8%                28.4%
```

The top row counts false alarms, where the methods differ by 4 points and
McNemar is the safer one. The bottom row counts real gains found, where they
differ by 17 points and the interval is the more useful one. A method cannot be
moved down the first column without also moving down the second.

---

## Where the two methods disagree most

Page 03 records a case the interval handles badly: one or two tasks differing
out of 48.

```
1 to 0   interval +0.0pp to +6.2pp   McNemar p = 1.000
2 to 0   interval +0.0pp to +10.4pp   McNemar p = 0.500
```

Both intervals sit entirely at or above zero, which reads like a small
improvement that has been measured. The p-values say the opposite, and they are
right: one task going the treatment's way is exactly what a coin flip produces
half the time, and it is no evidence at all.

This is the case worth running the test for. An interval whose lower bound is
pinned at zero by a shortage of data looks much like an interval whose lower
bound is positive because the change worked.

---

## What the test does not tell you

**It gives no size.** A p-value of 0.03 says the direction is probably real. It
says nothing about whether the gain is 4 points or 20. The interval is what
carries the size, so the two are worth reporting together.

**It ignores everything but pass and fail.** A partial-credit score that moved
from 0.4 to 0.9 without crossing the pass threshold counts as an agreement, and
contributes nothing.

**It assumes one run per task.** Run a task several times and the flips stop
being independent, which the arithmetic above relies on.

**It cannot rescue a small experiment.** When the arms disagree on four tasks,
the test reports that four is not enough, which you already knew. Getting past
the floor takes more tasks, or a change large enough to flip more of them.

---

## Running it

The whole test is one line of arithmetic over the two disagreement counts:

```python
from math import comb

def mcnemar_p(treatment_only: int, baseline_only: int) -> float:
    """Two-sided exact p-value for a paired pass/fail comparison."""
    n = treatment_only + baseline_only
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(treatment_only, baseline_only) + 1))
    return min(1.0, 2 * tail / 2 ** n)
```

The two counts come from the per-task pairs in `lift.json`: tasks where the
treatment passed and the baseline did not, and the reverse.

This is the exact form of the test, which is the one to use here. The older
chi-squared form approximates it, and the approximation is poor at the
disagreement counts a 48-task set produces.

---

## Related

- [01-standard-error.md](01-standard-error.md) — the vocabulary used here
- [04-the-six-task-floor.md](04-the-six-task-floor.md) — the special case this test generalises
- [03-bootstrapping.md](03-bootstrapping.md) — the interval this test sits beside
- [scripts/mcnemar_simulation.py](scripts/mcnemar_simulation.py) — the figures above
