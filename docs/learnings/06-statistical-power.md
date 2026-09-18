# Statistical power

Power is the chance that an experiment finds an effect that is really there.

Every comparison ends in one of two verdicts, and the change being tested either
works or it does not. That makes four outcomes, two of which are mistakes:

```
                       you declare a result     you do not

change does nothing       false alarm            correct
change works              correct                miss
```

The p-value guards the top row. Power guards the bottom one.

**A p-value is worked out after the run, from the results you got.** It answers
one question: if the change did nothing, how often would a comparison come out
looking like this one? Declaring a result only when that figure falls below 0.05
holds the false alarm rate at one in twenty. You pick the threshold, and it
holds whatever the size of the task set.

**Power is worked out before the run, from an effect size you name.** It answers
a different question: if the change really does improve the pass rate by 10
points, how often would this experiment notice? An experiment with 40% power
misses a genuine 10-point gain three times in five, and reports it as a
difference too small to distinguish from chance.

The difference in one line: a p-value asks whether the result you are holding
could be chance, and power asks whether you would have seen the effect at all if
it had been there.

The rest of this page is about power, because the false alarm rate comes fixed
at one in twenty and power does not come with the experiment. It has to be
bought with tasks.

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

## A weak experiment overstates the gains it finds

Take a change that genuinely improves the pass rate by 10 points, and run the
comparison 20,000 times on fresh 48-task sets. Noise makes the measured gain
different every time: some runs land near 4 points, others near 16.

```
every run                   mean  10.0pp   (20000 runs)
runs that cleared           mean  13.8pp   (9240 runs)
runs written up as unclear  mean   6.6pp   (10760 runs)
smallest gain that cleared         8.3pp
```

Averaged over everything, the measurement is right: 10.0 points against a true
10. Nothing is broken in any individual run.

The trouble is that you never see the whole column. You see one run, and you only
call it a result if its interval cleared zero.

The last line is the mechanism. No run measuring below 8.3 points ever cleared,
because a gap that small cannot hold an interval away from zero on 48 tasks. So
the runs that reached publication were picked for being on the large side, and
their mean is 13.8 rather than 10. The runs that measured the effect accurately
at 6 or 7 points were the ones written up as "could not tell".

The selection is done by the threshold, on the measurement itself, before you
decide what to believe.

### How much it costs, by effect size

```
true gain    6pp   found 23.4%   reported  11.2pp   overstated by 1.87x
true gain   10pp   found 45.9%   reported  13.9pp   overstated by 1.39x
true gain   20pp   found 86.5%   reported  21.4pp   overstated by 1.07x
true gain   30pp   found 98.9%   reported  30.2pp   overstated by 1.01x
```

The distortion tracks the power. At 6 points, where three runs in four are
discarded, a genuine 6-point improvement is published as an 11-point one. At 30
points almost nothing is discarded, so the survivors are nearly the whole column
and the reported figure is the true one.

Exaggeration is therefore a symptom of low power rather than a separate problem.
Buying power fixes both.

### Rerun the winner

Say a comparison came out at +14 points and cleared the threshold. The table
above says the effect behind a reported 14 is more likely to be around 10.

Now run the same comparison again on a fresh set of tasks. The second number
does not carry the same distortion, and the reason is worth being precise about.
The first number reached you only because it was large enough to clear the
threshold; small measurements of the same effect never got that far. The second
number reaches you whatever it says, because you have already committed to
running it and looking. Nothing filters it, so it lands around the true value
instead of above it.

That commitment is the whole mechanism. Rerunning until one of the attempts
looks good is the original filter applied again, and gives back an inflated
number for the same reason the first one was inflated.

So the first run settles the direction and the second measures the size. Expect
the second to come in lower, and read that as the arithmetic behaving rather
than the effect evaporating.

---

## Small effects can be found with the sign reversed

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

**Pairing.** Running both arms over the same tasks and comparing them task by
task. This does not change the gain you measure. It changes the uncertainty
around it, by cancelling the part that comes from some tasks being harder than
others: a task's difficulty sits in both arms' results, so subtracting one from
the other removes it.

[Page 02](02-paired-comparison.md) measures both ways of reading identical runs:

```
compared task by task        standard error  3.67pp
compared by overall rate     standard error  9.88pp
```

Power is decided by how far the true effect sits above that standard error, so
cutting it by a factor of 2.7 does the same work as running a much larger task
set. The standard error falls with the square root of the task count, so buying
the same reduction with tasks alone would take:

```
2.7² = 7.3       48 × 7.3 ≈ 350 tasks
```

A paired comparison on 48 tasks reaches roughly what an unpaired one would need
350 tasks for. This is a saving you already hold rather than one to go and
collect: `compare-lift` pairs by task, which is why the middle row of the first
table on this page reads 46% and not something far worse.

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
