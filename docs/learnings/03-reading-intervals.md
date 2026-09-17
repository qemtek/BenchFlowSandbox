# Reading a confidence interval

`compare-lift` reports a delta and an interval around it. The interval is the
part that carries the information, and it is the part most easily misread.

Everything below is checkable: `python docs/learnings/interval_simulation.py`
reproduces the numbers.

---

## What the bootstrap actually computes

Each of the 48 tasks contributes one paired outcome: improved (+1), regressed
(−1), or agreed (0). The delta is their mean.

The bootstrap resamples those 48 outcomes **with replacement**, 1,000 times,
recomputing the delta on each resample, then takes the 2.5th and 97.5th
percentiles.

It is answering one specific question:

> Given the 48 tasks I happen to have, how much would this delta move if I had
> drawn a different 48 from the same population?

That framing sets the limits. It accounts for task sampling. It does **not**
account for a biased task set, a broken verifier, or anything systematically
wrong with both arms. A tight interval around a wrong number is still wrong.

---

## What "crosses zero" means, and what it does not

An interval spanning zero means **not shown**. It does not mean *no effect*.

The two get conflated constantly, and the difference is large. A simulated
10-point improvement — genuine, present, worth having — on a 48-task paired
comparison:

```
detected:                 51% of runs
reported as "not shown":  49% of runs
```

**Half the time, a real 10-point gain produces an interval that crosses zero.**
Calling that "no effect" would be wrong on a coin flip.

So write it down the way it happened. "The interval spans −2 to +11, so this
task set cannot resolve it" is honest. "No difference" is a claim the data
cannot support.

---

## Showing there is no difference is a different experiment

If you genuinely need "these two arms are equivalent", a wide interval will not
give it to you. You have to state in advance what difference would be too small
to care about, then show the interval sits **entirely inside** that band.

At 48 tasks the interval is nowhere near tight enough for that. Equivalence
needs far more tasks, or repeats, or both. Worth knowing before you promise
someone that a refactor changed nothing.

---

## The width tells you more than the midpoint

The delta is a point estimate and it will move if you run again. The width tells
you how much.

```
delta +4pp, interval −16 to +24    the experiment could not resolve this
delta +4pp, interval  +1 to  +7    a small effect, actually measured
```

Same delta. Only the second is a result. Read the width first; it tells you
whether the midpoint is worth reading at all.

---

## Running several arms multiplies your false alarms

A 95% interval is wrong 5% of the time by construction. Test one thing and that
is a small risk. Test five and it stops being small.

Simulating five arms that are all genuinely identical:

```
chance at least one looks significant:  18%
```

Roughly one in five sessions where you try five prompt variants, one will look
like a winner and will not be. It will be the one you remember, because it is
the one that confirmed something.

Three defences, in order of cost:

**Decide what you are testing before you run it.** A hypothesis chosen in
advance costs you nothing and removes most of the problem.

**Count your comparisons and say so.** "Best of six variants, interval excluded
zero" is a different and much weaker claim than "the variant I predicted would
help, did".

**Confirm the winner on a fresh run.** If it was noise it will usually not
survive. This is the only defence that actually settles it.

---

## Reproducibility

Pass `--bootstrap-seed` whenever you intend to quote an interval:

```bash
benchflow eval compare-lift --baseline jobs/a --trained jobs/b \
  --out lift.md --json-out lift.json --bootstrap-seed 42
```

Without it the endpoints shift slightly between invocations on identical data.
Harmless for a glance, embarrassing in a document someone else re-runs.

---

## Four sentences to keep

An interval crossing zero means *not shown*, not *no effect*.

Read the width before the midpoint.

Count how many comparisons you ran, and say the number.

A confirming rerun beats any amount of arguing about the first one.

---

## Related

- [01-standard-error.md](01-standard-error.md) — why the intervals are this wide
- [02-paired-comparison.md](02-paired-comparison.md) — how to narrow them
- [interval_simulation.py](interval_simulation.py) — the evidence above
