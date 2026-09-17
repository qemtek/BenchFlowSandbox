# Bootstrapping: where the interval comes from, and how to read it

A comparison gives you a delta and an interval around it. This page covers
where the interval comes from and what it is safe to claim.

Every number below is reproducible: `python docs/learnings/interval_simulation.py`.

---

## The problem it solves

You ran two arms and 6 of 48 tasks changed. Run the same two arms again and you
would get a different figure. How different?
You would need the sampling distribution of a paired delta over binary outcomes
to answer that from a formula — and picking the wrong formula is easy, because
the textbook approximations assume shapes this data does not have when only 6 of
48 tasks differ between the arms.

Bootstrapping sidesteps the question. Instead of deriving the distribution, it
builds one from the data you already have.

---

## How it works

After pairing, each task holds one of three outcomes:

```
+1   improved      5 tasks
-1   regressed     1 task
 0   agreed       42 tasks
```

Those 48 values are the entire input. The procedure is three lines:

1. Draw 48 outcomes **from that set, with replacement**. Some tasks get picked
   twice, some not at all.
2. Compute the delta for that draw.
3. Repeat 1,000 times, then take the 2.5th and 97.5th percentiles of the 1,000
   deltas.

That range is the interval. The logic behind it: your 48 tasks are a sample from
some larger population of possible tasks, and in the absence of that population,
the sample is the best stand-in available. Drawing from it repeatedly imitates
drawing fresh task sets.

The result makes no assumption about the shape of the distribution, which is
what makes it the right tool when you do not know the shape.

---

## What the resample count buys you

`--bootstrap-samples` defaults to 1,000. Raising it does **not** narrow the
interval. It steadies the endpoints:

```
same data, ten repeats each
B=100      low  -1.2pp (varies by 2.1)   high +18.3pp (varies by 4.2)
B=1000     low  -0.2pp (varies by 2.1)   high +18.8pp (varies by 0.0)
B=10000    low  +0.0pp (varies by 0.0)   high +18.8pp (varies by 0.0)
```

At B=100 the upper endpoint wanders by 4 points between runs on identical data,
which is pure simulation artefact. By B=1,000 it has settled. The default is
fine; there is nothing to gain by raising it and a real cost to lowering it.

Width comes from your data — how many tasks disagreed — not from B. If the
interval is too wide, you need more tasks or repeats, not more resamples.

---

## Where it breaks down

**Too few tasks differing between the arms.** With only one task differing out
of 48, the interval collapses toward a point:

```
1 task differs:    +0.0pp to +6.2pp
```

With a single paired task it degenerates completely: low, high and the observed
delta are all the same number, and the interval carries no information at all
while looking perfectly confident.

**A biased task set.** Resampling your 48 tasks cannot reveal anything about
tasks you did not include. If the set over-represents one kind of case, every
bootstrap draw inherits that, and the interval will be tight around a number
that does not generalise. **A narrow interval around a wrong estimate is still
wrong.**

**Anything systematically broken.** A verifier bug affects both arms and every
resample identically. The bootstrap has no view of it.

---

## Reading what comes out

### An interval that crosses zero means *not shown*, not *no effect*

An interval **crosses zero** when its lower bound is negative and its upper
bound is positive:

```
-3pp  ────────────●────────────  +11pp        crosses zero
                  ▲ zero

+1pp  ────────────────●────────  +7pp         does not
```

In the first case the data is consistent with the treatment being worse,
identical, or better. In the second, every value in the range is an improvement,
so the direction is settled even though the size is not.

The two get conflated constantly, and the gap is large. Simulating a genuine
10-point improvement on a 48-task paired comparison:

```
detected:                 51% of runs
reported as "not shown":  49% of runs
```

**Half the time, a real 10-point gain produces an interval spanning zero.**
Calling that "no effect" would be wrong on a coin flip.

Write down what happened. "The interval spans −2 to +11, so this task set cannot
resolve it" is honest. "No difference" is a claim the data cannot support.

### Showing there *is* no difference is a different experiment

If you genuinely need "these two arms are equivalent", a wide interval will not
deliver it. State in advance what difference would be too small to care about,
then show the interval sits **entirely inside** that band. At 48 tasks it is
nowhere near tight enough. Worth knowing before you promise anyone that a
refactor changed nothing.

### Width tells you more than the midpoint

```
delta +4pp, interval -16 to +24    the experiment could not resolve this
delta +4pp, interval  +1 to  +7    a small effect, actually measured
```

Same delta. Only the second is a result. Read the width first — it tells you
whether the midpoint is worth reading at all.

### Several arms multiply your false alarms

A 95% interval is wrong 5% of the time by construction. Simulating five arms
that are all genuinely identical:

```
chance at least one looks significant:  18%
```

Roughly one session in five where you try five variants hands you a false
winner. It will be the one you remember, because it confirmed something.

Three defences, cheapest first: decide what you are testing before you run it;
count your comparisons and say the number out loud; confirm the winner on a
fresh run. Only the last one settles it.

---

## Reproducibility

Pass `--bootstrap-seed` whenever you intend to quote an interval:

```bash
benchflow eval compare-lift --baseline jobs/a --trained jobs/b \
  --out lift.md --json-out lift.json --bootstrap-seed 42
```

Without it the endpoints shift slightly between invocations on identical data,
because the resampling is random. Harmless for a glance, embarrassing in a
document someone else re-runs.

---

## Four sentences to keep

An interval crossing zero means *not shown*, not *no effect*.

Read the width before the midpoint.

Count how many comparisons you ran, and say the number.

A confirming rerun beats any amount of arguing about the first one.

---

## Related

- [01-standard-error.md](01-standard-error.md) — why the intervals are this wide
- [02-paired-comparison.md](02-paired-comparison.md) — what gets bootstrapped
- [interval_simulation.py](interval_simulation.py) — the evidence above
