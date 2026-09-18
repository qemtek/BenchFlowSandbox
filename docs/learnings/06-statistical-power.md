# Statistical power

Power is the chance that an experiment finds an effect that is really there. An
experiment with 40% power will miss a genuine improvement three times in five,
and report it as a difference too small to distinguish from chance.

Power is the counterpart to the false alarm rate. The 95% interval controls how
often you claim an improvement that does not exist, and that rate is fixed at
one in twenty by the threshold you chose. Power is about the other mistake,
missing one that does, and nothing fixes it for you.

Figures come from `python docs/learnings/scripts/power_simulation.py`, which
simulates comparisons with a known true effect and counts how often the reported
interval excludes zero.

---

## Power at 48 tasks

```
true gain    2pp    found  5.0%
true gain    4pp    found 13.0%
true gain    6pp    found 23.9%
true gain   10pp    found 46.2%
true gain   15pp    found 70.4%
true gain   20pp    found 87.0%
true gain   30pp    found 98.8%
```

Read the middle row first. A change that genuinely improves the pass rate by 10
percentage points, which is about five tasks in 48, gets reported as a difference
under half the time. Run that comparison twice and the likelier outcome is that
at least one of the two runs says "could not tell".

The top row is the floor. A 2-point true gain is found 5.0% of the time, and two
arms that are genuinely identical are found to differ 4.6% of the time, measured
in [page 05](05-mcnemar.md). At that size the experiment carries no information
about the change at all.

The convention in most fields is to design for 80% power, which on this task set
means an effect somewhere around 15 to 20 points. Effects that large are rare
once the obvious problems in a configuration have been fixed.

---

## Power by task count

Holding the true gain at 10 points and varying how many tasks are run:

```
  24 tasks     found 20.6%
  48 tasks     found 46.0%
  96 tasks     found 73.8%
 192 tasks     found 97.8%
 384 tasks     found 100.0%
```

Power climbs faster than the task count suggests. What decides it is how far the
true effect sits above the threshold, measured in standard errors, and
quadrupling the task set halves the standard error, which doubles that distance.
Going from 48 to 192 tasks takes a 10-point gain from a coin flip to a near
certainty.

This is the calculation worth doing before spending the rollouts.
[Page 01](01-standard-error.md) gives the shortcut: multiply the standard error
by 2.8 and you have the smallest effect that reaches 80% power. The 2.8 breaks
into 1.96 to clear the false alarm threshold and 0.84 for the power term, and
that 0.84 is what this page is about.

---

## Findings are larger than the effects behind them

An experiment that misses half of what it is looking for does not miss at
random. It misses the runs where the effect happened to look small, and reports
the runs where it happened to look large.

```
true gain    6pp   found 23.4%   reported  11.2pp   overstated by 1.87x
true gain   10pp   found 45.9%   reported  13.9pp   overstated by 1.39x
true gain   20pp   found 86.5%   reported  21.4pp   overstated by 1.07x
true gain   30pp   found 98.9%   reported  30.2pp   overstated by 1.01x
```

The middle rows are the ones to sit with. When a true 10-point gain is found, it
is reported at 13.9 points on average, because a run that measured it at 7
points did not clear the threshold and was written up as "could not tell". The
selection happens before you see the number.

At 6 points the reporting is worse than the effect is large: a genuine 6-point
improvement, on the occasions it gets through, is published as an 11-point one.

At the bottom of the table the distortion disappears. An effect large enough to
be found almost every time is found at close to its true size, because almost
nothing is being filtered out.

So the exaggeration is a symptom of low power rather than a separate problem.
Fixing the power fixes it.

### What follows for a result you intend to act on

Rerun the winner. A comparison that has already cleared the threshold once gives
an inflated estimate of the gain; the rerun does not, because it is not being
selected on. The first run establishes the direction, the second measures the
size.

Expect the rerun to come in smaller, and treat that as the arithmetic working
rather than as the effect evaporating.

---

## Findings pointing the wrong way

Below a certain size, an experiment can find an effect and get its direction
wrong:

```
true gain    2pp   found  5.1%   of those, wrong direction  4.4%
true gain    4pp   found 13.5%   of those, wrong direction  0.6%
true gain   10pp   found 46.2%   of those, wrong direction  0.0%
```

At a true gain of 2 points, roughly one finding in twenty-three points the wrong
way, so a confident claim that the change made things worse would have been
produced by a change that made things better.

This is rare enough to ignore for effects of 4 points and up, and it is worth
knowing that the floor exists. A small effect measured by a weak experiment can
produce a result that is not merely exaggerated but backwards.

---

## Raising power

Three things move it, in descending order of how much control you have.

**More tasks.** The table above prices this: 48 to 192 tasks takes a 10-point
gain from 46% to 98%. It is the only lever that works on any effect size.

**Pairing.** Running both arms over the same tasks, and comparing task by task,
removes task difficulty from the variance at no cost.
[Page 02](02-paired-comparison.md) covers it, and it is already how
`compare-lift` works.

**Repeat runs.** Running each arm several times and averaging reduces the part
of the variance that comes from the agent behaving differently between runs.
This cuts that component by `√n`, so four runs halve it, and it does nothing for
the part that comes from task difficulty.

What does not raise power: more bootstrap resamples, a different interval
method, or reporting the result more confidently. The first two change how
precisely you measure the uncertainty, not how much of it there is.

---

## What power does not tell you

**It is calculated against an effect size you have to supply.** "The power of
this experiment" is not a number; "the power of this experiment to detect a
10-point gain" is. Quoting one without the other hides the assumption doing all
the work.

**It says nothing after the fact.** Once a comparison has produced a wide
interval, computing the power it had is a restatement of the interval width and
adds nothing. Power is a planning tool, used before the rollouts are spent.

**High power does not make an effect worth having.** A 384-task comparison finds
a 2-point gain reliably. Whether a 2-point gain justifies the change is a
separate question, and the interval is what answers it.

---

## Related

- [01-standard-error.md](01-standard-error.md) — the 2.8 multiplier, and where its 0.84 comes from
- [03-bootstrapping.md](03-bootstrapping.md) — the interval whose behaviour is being counted here
- [04-the-six-task-floor.md](04-the-six-task-floor.md) — the hard limit underneath all of this
- [scripts/power_simulation.py](scripts/power_simulation.py) — the figures above
