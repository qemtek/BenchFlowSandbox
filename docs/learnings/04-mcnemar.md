# McNemar's test

McNemar's test is the standard way to decide whether two configurations, run
over the same set of pass/fail tasks, really differ. It answers with a yes or a
no rather than a size: either the gap between them is larger than chance would
ordinarily produce, or this experiment cannot say.

An **arm** is one complete configuration (prompt, toolset, skill mode, model,
harness) run over the task set. A **percentage point** is an absolute gap
between two percentages, so a move from 60% to 68% is a rise of 8 percentage
points.

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

## Six disagreements is the floor

```
1 to 0   p = 1.000
2 to 0   p = 0.500
3 to 0   p = 0.250
4 to 0   p = 0.125
5 to 0   p = 0.062
6 to 0   p = 0.031
7 to 0   p = 0.016
```

Five tasks flipping to the treatment, with nothing flipping back, gives 0.062
and falls short. Six gives 0.031 and clears.

That floor does not move with the size of the task set. The test sees only the
disagreements, so running 480 tasks instead of 48 does not lower the bar. It
makes disagreements more likely to accumulate, which is a different thing. Below
six flips all in one direction, no comparison of this kind reaches the usual
threshold, whatever the size of the reported gap.

---

## How the test compares with the interval

The comparison already reported by `compare-lift` is a bootstrap confidence
interval, covered in [page 03](03-bootstrapping.md). It answers a different
question, "how much would this difference move on a different set of tasks",
and treats a result as real when the interval excludes zero.

Simulating 20,000 experiments under three scenarios, and counting how often each
method calls the difference real:

```
no real difference   interval  4.6%   McNemar  0.6%   McNemar without the interval  0.0%
real 4-point gain    interval 13.2%   McNemar  2.9%   McNemar without the interval  0.0%
real 10-point gain   interval 45.8%   McNemar 28.4%   McNemar without the interval  0.0%
```

The last column is zero in every row: McNemar's test never calls a difference
real when the interval does not. It is the stricter of the two throughout.

Strictness cuts both ways. On the top row, where the two arms are genuinely
equal, the test raises a false alarm 0.6% of the time against the interval's
4.6%. On the bottom row, where a real 10-point gain exists, it finds that gain
28% of the time against the interval's 46%. Being hard to fool and being easy to
convince are the same dial.

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

**It cannot rescue a small experiment.** Being told that six disagreements are
needed does not produce them. The remedy is more tasks, or a larger change.

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

- [01-standard-error.md](01-standard-error.md) — how large a gap has to be
- [03-bootstrapping.md](03-bootstrapping.md) — the interval this test sits beside
- [scripts/mcnemar_simulation.py](scripts/mcnemar_simulation.py) — the figures above
