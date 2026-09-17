# How much a pass rate moves between runs

A pass rate is an estimate. Run the same configuration on two different sets of
48 tasks and you get two different numbers, because each set contains its own
mix of easy and hard tasks.

Standard error measures how far apart those numbers are likely to be. It tells
you the smallest difference you can distinguish from noise.

Two terms are used throughout these pages.

An **arm** is one complete configuration (prompt, toolset, skill mode, model,
harness) run over the task set.

A **percentage point** (`pp`) is an absolute gap between two percentages. A move
from 56% to 62% is a rise of 6 percentage points, and a rise of 11% in relative
terms; everything here uses the absolute version. Percentage points are the
convenient unit because they convert directly into tasks: on a 48-task set, one
task changing from fail to pass moves the pass rate by 1/48, which is 2.1
percentage points.

---

## Calculating the standard error

A pass rate is a proportion, so:

```
SE = √( p(1−p) / n )
```

`p` is the pass rate, `n` the number of tasks. For 48 tasks at a 50% pass rate:

```
√(0.25 / 48) = 0.072
```

About 7 percentage points. An arm scoring 56% is really saying "somewhere
around 49% to 63%, at one standard error".

---

## What changes the standard error

```
             p=0.5     p=0.7     p=0.9
n =  24      10.2pp     9.4pp     6.1pp
n =  48       7.2pp     6.6pp     4.3pp
n =  96       5.1pp     4.7pp     3.1pp
n = 192       3.6pp     3.3pp     2.2pp
n = 480       2.3pp     2.1pp     1.4pp
```

**The number of tasks**, which you control. The `√n` means halving the error
costs four times the tasks: 48 to 96 takes you from 7.2 to 5.1, and reaching 2.3
needs 480. Halving the error costs four times the tasks, every time.

**Where the pass rate sits**, which you do not. `p(1−p)` peaks at 0.5 and falls
away at both ends, so an arm passing 90% of its tasks carries less uncertainty
than one passing half.

---

## Comparing two arms

Each arm carries its own error, and a comparison combines them:

```
SE(difference) = √( SE₁² + SE₂² )
```

At 48 tasks with both arms near 50%, that is 10.2 percentage points.

To call a difference real you need it to clear roughly 2.8 standard errors,
which is the margin at which a result is unlikely to be chance. So an effect has
to reach about **29 percentage points**, or fourteen tasks flipping, before this
comparison would reliably detect it.

That figure belongs to those conditions only. It falls with more tasks and with
pass rates further from 50%, by the same formula above, so recompute it for the
set you are running.

Most of that cost is avoidable. Comparing the two arms task by task, instead of
comparing their overall rates, removes the largest part of it. That is what
[page 02](02-paired-comparison.md) covers.

---

## What the formula does not cover

It assumes the only randomness is which tasks are in your set, and treats the
agent as deterministic. Rerun one arm unchanged and some tasks will flip anyway.
In this project a task scored 1.00 and then 0.0 across two runs with the code,
prompts and model all held fixed.

So 7 points is a floor rather than an estimate, and the true figure is larger.
Finding it means running one arm several times over the full set and reading the
spread, which has not been done here yet.

---

## Rules of thumb

**Quote `n` with every pass rate.** "62%" is not a result. "62% of 48" is.

**Work out the floor before spending the rollouts.** If the effect you are
hoping for is smaller than the smallest you could detect, the experiment cannot
answer the question, and that is worth knowing in advance.

**Treat one or two changed tasks as noise.** One task moves a 48-task pass rate
by 2.1 points and two move it by 4.2, both well inside a 7-point standard
error.

---

## Related

- [02-paired-comparison.md](02-paired-comparison.md) — reducing the variance
- [03-bootstrapping.md](03-bootstrapping.md) — putting an interval on a result
