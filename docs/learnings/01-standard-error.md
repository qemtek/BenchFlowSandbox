# Standard error: how big a difference has to be before it means anything

Every pass rate this rig produces is an estimate. Run the identical
configuration twice and you get two different numbers. Standard error is how far
apart those numbers are expected to be, and knowing it is what separates a
result from a coincidence.

Throughout these pages, an **arm** is one complete configuration — prompt,
toolset, skill mode, model, harness — run over the task set. Comparing two arms
is the whole activity.

---

## The number for our set

A pass rate is a proportion, so its standard error is:

```
SE = √( p(1−p) / n )
```

`p` is the pass rate, `n` the number of tasks. For 48 tasks at a 50% pass rate:

```
√(0.25 / 48) = 0.072
```

**About 7 percentage points.** A single arm scoring 56% is really saying
"somewhere around 49–63%, at one standard error".

A note on units, used throughout these pages. A **percentage point** (`pp`) is
an absolute difference between two percentages. Going from 56% to 62% is a rise
of 6 percentage points, but a rise of about 11% in relative terms. Everything
here is in percentage points, because that is what "how many tasks changed"
translates into directly: on a 48-task set, one task is 2.1pp.

---

## How it varies

Two things move it, and only one is under your control.

```
             p=0.5     p=0.7     p=0.9
n =  24      10.2pp     9.4pp     6.1pp
n =  48       7.2pp     6.6pp     4.3pp
n =  96       5.1pp     4.7pp     3.1pp
n = 192       3.6pp     3.3pp     2.2pp
n = 480       2.3pp     2.1pp     1.4pp
```

**Sample size.** The `√n` in the denominator means halving the error costs four
times the tasks. Going from 48 to 96 buys you 7.2 → 5.1. Going to 480 — every
task run ten times — buys 2.3. There is no cheap route to precision.

**Where the pass rate sits.** `p(1−p)` peaks at 0.5 and falls away at both ends.
An arm passing 90% of tasks has a tighter estimate than one passing half. This
is not under your control, but it explains why a near-ceiling result feels
steadier than a middling one.

---

## Comparing two arms is worse than measuring one

Each arm carries its own error, and comparing them combines both:

```
SE(difference) = √( SE₁² + SE₂² )
```

At 48 tasks and p≈0.5 for both arms, that is **10.2 points**. The 95% interval
on the difference spans ±20 points.

Put the consequence plainly: to reliably detect a difference between two
independently-run arms of 48 tasks, the true effect has to be about **29
percentage points** — fourteen tasks flipping. Anything smaller and you will
usually fail to see it.

That is the honest ceiling on unpaired comparison at this scale, and it is why
[paired comparison](02-paired-comparison.md) is not optional.

---

## What this figure leaves out

Everything above assumes the only randomness is *which tasks are in your set*.
It treats the agent as deterministic.

It is not. We have a direct counterexample: one task scored 1.00 and then 0.0 on
identical inputs, a pinned commit, and the same model. The agent filed two
disputes nobody asked for.

So 7 points is a **floor**, not an estimate. The real figure is larger and
currently unmeasured. Measuring it means running one arm several times over the
full set and reading the spread — which is the outstanding item in
[versioning-gaps](../versioning-gaps.md).

Until that is done, treat any single-digit difference as noise by default.

---

## Practical rules

**Never quote a pass rate without n.** "62%" is not a result; "62% of 48" is.

**Compute the floor before running the arm.** If the effect you are hoping for
is smaller than the floor, the experiment cannot answer the question, and the
time to know that is before you spend the rollouts.

**A change that flips one or two tasks is not a finding.** At n=48 one task is
2.1 points, well inside the noise.

**Prefer pairing.** It attacks the largest component of the variance directly
rather than paying for more tasks. See the next page.

---

## Related

- [02-paired-comparison.md](02-paired-comparison.md) — how to get under this floor
- [../versioning-gaps.md](../versioning-gaps.md) — why variance is still unmeasured
