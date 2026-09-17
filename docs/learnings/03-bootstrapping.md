# Where the interval comes from, and what it means

A comparison gives you a delta and an interval around it. This page covers how
the interval is built and what it licenses you to say.

Figures come from `python docs/learnings/scripts/interval_simulation.py`.

---

## Building it

After pairing, each of the 48 tasks holds one of three outcomes. Suppose five
improved, one regressed, and the rest agreed:

```
+1   improved      5 tasks
-1   regressed     1 task
 0   agreed       42 tasks
```

Those 48 values are the whole input. The procedure:

1. Draw 48 outcomes from that set, with replacement. Some tasks get picked
   twice, some not at all.
2. Compute the delta for that draw.
3. Repeat 1,000 times, then take the 2.5th and 97.5th percentiles of the 1,000
   deltas.

That range is the interval.

The reasoning is that your 48 tasks are a sample from a larger population of
possible tasks. You do not have that population, so the sample stands in for it,
and drawing from the sample repeatedly imitates drawing fresh task sets.

The result is an answer to one question: **given the 48 tasks I happen to have,
how much would this delta move if I had drawn a different 48?**

A formula exists for this particular case, but it needs choosing correctly and
its approximations get unreliable when few tasks differ. Resampling needs no
derivation and no assumption about the shape of the distribution.

---

## What the resample count controls

`--bootstrap-samples` defaults to 1,000. Raising it does not narrow the
interval. It steadies the endpoints:

```
same data, ten repeats each
B=100      low  -1.2pp (varies by 2.1)   high +18.3pp (varies by 4.2)
B=1000     low  -0.2pp (varies by 2.1)   high +18.8pp (varies by 0.0)
B=10000    low  +0.0pp (varies by 0.0)   high +18.8pp (varies by 0.0)
```

At B=100 the upper endpoint moves by 4 points between runs on identical data,
which is an artefact of the resampling rather than anything in the experiment.
By 1,000 it has settled, so the default is fine.

Width comes from how many tasks disagreed, not from B. A wide interval means you
need more tasks or more repeat runs, never more resamples.

---

## An interval that crosses zero

An interval **crosses zero** when its lower bound is negative and its upper
bound positive:

```
-3pp  ────────────●────────────  +11pp        crosses zero
                  ▲ zero

+1pp  ────────────────●────────  +7pp         does not
```

In the first case the data is consistent with the treatment being worse,
identical, or better. In the second, every value in the range is an improvement,
so the direction is settled even if the size is not.

Crossing zero means the result was **not shown**. It does not mean there is no
effect. Simulating a genuine 10-point improvement on a 48-task paired
comparison:

```
detected:                 51% of runs
reported as "not shown":  49% of runs
```

A real 10-point gain produces an interval spanning zero about half the time, so
reporting that as "no effect" would be wrong on a coin flip. "The interval spans
−2 to +11, so this task set cannot resolve it" is the accurate version.

---

## Width matters more than the midpoint

```
delta +4pp, interval -16 to +24    the experiment could not resolve this
delta +4pp, interval  +1 to  +7    a small effect, measured
```

The same delta appears in both. Only the second carries information, because
only there does the range exclude the possibility of no change.

---

## Showing that two arms are equivalent

A wide interval does not establish "no difference". If you need that claim, set
out in advance what difference would be too small to care about, then show the
interval sits entirely inside that band.

At 48 tasks the intervals are nowhere near tight enough to do this, so it takes
substantially more tasks or repeat runs.

---

## Running several comparisons at once

A 95% interval excludes the true value 5% of the time by construction. A
bootstrap percentile interval is approximate, so its real rate is near but not
exactly that; measured on this setup it is 4%.

Simulating five arms that are all genuinely identical, each with its own 4%
chance of a false alarm:

```
chance at least one looks significant:  18%
```

So one session in five where you try five variants produces a false winner,
which will tend to be the variant you then pursue.

Three defences, cheapest first:

- decide what you are testing before running it
- report how many comparisons you ran alongside the result
- rerun the apparent winner, which is the only one that settles it

---

## Where the method breaks down

**Few tasks differing.** With one task differing out of 48, the interval
collapses toward a point:

```
1 task differs:    +0.0pp to +6.2pp
```

The upper bound is 3/48, because a resample can draw that single task up to
three times. With one paired task in total it degenerates entirely: the two
bounds and the observed delta are the same number, and the interval carries no
information while appearing exact.

**A biased task set.** Resampling cannot reveal anything about tasks you did not
include. If the set over-represents one kind of case, every draw inherits that,
and the interval will be tight around a number that does not generalise.

**Anything systematically wrong.** A verifier bug affects both arms and every
resample identically, so the bootstrap has no view of it.

---

## Reproducibility

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
