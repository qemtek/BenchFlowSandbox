# Confidence intervals

When you compare two configurations, the result is a difference in pass rate
plus a range around it. That range is the confidence interval, and it says how
much the difference would move if you ran the experiment again.

The convention is a 95% interval: the range is set wide enough that, if you
repeated the whole experiment many times, 95% of the ranges produced would
contain the true difference.

This page covers how that range is calculated, and which conclusions it
supports.

Figures come from `python docs/learnings/scripts/interval_simulation.py`.

---

## Two ways to calculate one

**From a formula.** Take the standard error and multiply it by 1.96, which gives
the half-width of a 95% interval. [Page 01](01-standard-error.md) shows how the
standard error is calculated.

**By resampling your own results.** Simulate what would happen if you drew
different task sets, using the results you already have, and read the range off
those simulations. This is called **bootstrapping**.

This project uses bootstrapping, for two reasons. A formula has to be chosen to
match the statistic you are measuring, and the one for a paired comparison of
pass/fail outcomes becomes unreliable when only a few tasks differ between the
arms. Bootstrapping needs no formula and makes no assumption about the shape of
the distribution.

---

## How bootstrapping works

The uncertainty you are trying to measure comes from which tasks you happened to
run. So tasks are what you resample.

Each task contributes one number to the comparison:

```
+1   the treatment passed it, the baseline did not
-1   the baseline passed it, the treatment did not
 0   both passed it, or both failed it
```

The average of those 48 numbers is the difference in pass rates. They are two
descriptions of one quantity. If the treatment won 5 tasks the baseline lost,
lost 1 the baseline won, and the two agreed on the other 42:

```
average of the 48 numbers    (5 − 1) / 48     = 8.3pp
difference in pass rates     33/48 − 29/48    = 8.3pp
```

So resampling tasks is resampling the pass-rate difference. The procedure:

1. Draw 48 tasks at random from your 48, with replacement. Some get picked
   twice, some not at all.
2. Average their numbers. That is one simulated difference in pass rates.
3. Repeat 1,000 times.
4. Take the 2.5th and 97.5th percentiles of the 1,000 simulated differences.

That range is the interval.

Each draw stands in for "a different set of 48 tasks". You cannot draw fresh
task sets from the real world, because you do not have it, so drawing from the
48 you have is the closest available substitute.

The result answers one question: **given the 48 tasks I happen to have, how much
would this difference move if I had drawn a different 48?**

---

## What the resample count controls

`--bootstrap-samples` defaults to 1,000. Raising it does not narrow the
interval. It steadies the endpoints:

```
same data, ten repeats each
B=100      low  -0.8pp (varies by 4.2)   high +16.5pp (varies by 4.2)
B=1000     low  -0.2pp (varies by 2.1)   high +18.8pp (varies by 0.0)
B=10000    low  +0.0pp (varies by 0.0)   high +18.8pp (varies by 0.0)
```

At B=100 the upper endpoint moves by 4 points between runs on identical data,
which is an artefact of the resampling rather than anything in the experiment.
By 1,000 it has settled, so the default is fine.

Width comes from how many tasks disagreed, not from B. A wide interval means you
need more tasks or more repeat runs, never more resamples.

---

## Intervals that cross zero

The interval is a range of plausible values for the true difference between the
two configurations. Zero is the value that means "the two are equally good".

So the useful question is whether zero falls inside the range.

```
-3pp  ────────────●────────────  +11pp        zero is inside
                  ▲ zero

+1pp  ────────────────●────────  +7pp         zero is outside
```

In the top case the plausible answers run from "the treatment is 3 points worse"
through "no difference at all" to "the treatment is 11 points better". The
experiment has not told you which of those is true.

In the bottom case every value in the range is positive. You still do not know
the size of the improvement, but every plausible answer is an improvement, so
the direction is settled.

### What you can conclude, and what you cannot

When zero is inside the range, three statements are available and only one of
them is true:

```
"the treatment is better"        not supported — zero is still plausible
"the treatment is no better"     not supported — +11 is equally plausible
"this experiment could not tell" supported
```

The second is the one people reach for, and it is the mistake. Failing to
demonstrate an improvement is not the same as demonstrating there was none.

The gap between them is large. Simulating a genuine 10-point improvement on a
48-task paired comparison, and counting how often the interval keeps zero out:

```
zero outside the range:   48% of runs
zero inside the range:    52% of runs
```

A real 10-point gain leaves zero inside the range about half the time. Treating
that as evidence of no effect would be wrong on a coin flip.

Write the third statement instead: "the interval runs from −2 to +11, so this
task set cannot resolve the question."

---

## Interval width

```
delta +4pp, interval -16 to +24    the experiment could not resolve this
delta +4pp, interval  +1 to  +7    a small effect, measured
```

The same delta appears in both. Only the second carries information, because
only there does the range exclude the possibility of no change.

---

## Showing two arms are equivalent

A wide interval does not establish "no difference". If you need that claim, set
out in advance what difference would be too small to care about, then show the
interval sits entirely inside that band.

At 48 tasks the intervals are nowhere near tight enough to do this, so it takes
substantially more tasks or repeat runs.

---

## Running several comparisons

A 95% interval leaves the true value outside the range 5% of the time. That is
what the 95% means, and it applies to every comparison you run.

Run one comparison and you accept a 5% chance of a false alarm. Run five and you
have five chances to be unlucky:

```
chance all five are clean      0.95 × 0.95 × 0.95 × 0.95 × 0.95  =  77%
chance at least one is not     100% − 77%                        =  23%
```

So if you test five variants that are all equally good, roughly one time in four
one of them will look better purely by accident.

Three defences, cheapest first:

- decide what you are testing before running it
- report how many comparisons you ran alongside the result
- rerun the apparent winner, which is the only one that settles it

---

## Where bootstrapping breaks down

**Few tasks differing.** With one or two tasks differing out of 48, the interval
collapses toward a point:

```
1 task differs of 48:   +0.0pp to  +6.2pp
2 tasks differ of 48:   +0.0pp to +10.4pp
```

Both lower bounds are zero, because most resamples miss the differing task
entirely. The upper bound of 6.2pp is 3/48, which is what you get when a
resample happens to draw that one task three times.

An interval that cannot go below zero is not evidence that the change helped. It
reflects having almost no data on the question.

**A biased task set.** Resampling cannot reveal anything about tasks you did not
include. If the set over-represents one kind of case, every draw inherits that,
and the interval will be tight around a number that does not generalise.

**Anything systematically wrong.** A verifier bug affects both arms and every
resample identically, so the bootstrap has no view of it.

---

## Reproducing an interval

Pass `--bootstrap-seed` whenever you intend to quote an interval:

```bash
benchflow eval compare-lift --baseline jobs/a --trained jobs/b \
  --out lift.md --json-out lift.json --bootstrap-seed 42
```

Without it the endpoints shift slightly between invocations on identical data,
because the resampling is random.

---

## Related

- [01-standard-error.md](01-standard-error.md) — why the intervals are this wide
- [02-paired-comparison.md](02-paired-comparison.md) — narrowing them first
- [scripts/interval_simulation.py](scripts/interval_simulation.py) — the figures above
