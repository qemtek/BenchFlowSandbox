# The six-task floor

Six tasks have to change hands, with none changing back, before a comparison of
two configurations can be called statistically significant. **Statistically
significant** means the result is larger than chance would ordinarily produce,
at the usual threshold of one false alarm in twenty.

The floor holds whether the task set has 10 tasks or 1,000, which is the part
that surprises people. This page shows where it comes from and what follows from
it.

Figures come from `python docs/learnings/scripts/mcnemar_simulation.py`.

---

## Only tasks that change hands count

Run two arms over the same tasks and most tasks come out the same way twice.
Those say nothing about which arm is better. The comparison rests entirely on
the tasks where one arm passed and the other failed.

[Page 05](05-mcnemar.md) works through why. The short version: a task both arms
passed contributes the same amount to both pass rates, so it cancels out of the
difference between them.

So the quantity that decides whether you have a result is not the size of the
task set. It is the number of tasks that changed hands, and how one-sided they
were.

---

## Where the six comes from

Say six tasks changed hands and all six went to the treatment. If the change did
nothing, each of those six came out the way it did for reasons unconnected to
the change, so each is a coin flip. Six flips all landing on the treatment has a
chance of `(1/2)⁶`, or 1 in 64.

That is not yet the answer, because of what a p-value measures. It is not the
chance of the exact result you got. It is the chance that you would have
declared a result at all, when nothing was going on. So it depends on the rule
you were going to declare by, and the rule here is:

```
every task that changed hands went the same way  ->  call it a result
```

That rule fires in two situations. Six tasks to the treatment fires it. Six
tasks to the baseline also fires it, as a regression rather than an improvement,
and you would still have stopped and written the finding up. Chance gets both
routes to set the rule off, so both are counted:

```
all six to the treatment    1/64
all six to the baseline     1/64
                            ----
rule fires by chance        2/64  =  0.031
```

A test counting both directions this way is called **two-sided**. Writing `b`
for the number of tasks that changed hands, the condition to clear a threshold
of 0.05 is:

```
2 × (1/2)^b  <  0.05
        2^b  >  40
          b  =  6        2⁶ = 64 clears it, 2⁵ = 32 does not
```

Six is the smallest number of coin flips for which a clean sweep happens rarely
enough to clear that threshold. Flip a coin five times, get five heads, and
nobody concludes the coin is weighted, because five flips do that once in every
sixteen attempts.

Nothing in that derivation refers to evaluation or task sets at all. It is a
fact about the threshold 0.05, and it moves when the threshold does:

```
p < 0.10, two-sided      5 tasks
p < 0.05, two-sided      6 tasks
p < 0.05, one-sided      5 tasks
p < 0.01, two-sided      8 tasks
```

The one-sided row is the case where your rule only fires in one direction: you
committed in advance that a regression would not count as a finding, and that
you would carry on regardless if the arrow pointed the other way. The rule then
has one route rather than two, the doubling drops out, and five tasks clear the
threshold at 1/32.

That commitment has to be made before the results are in. Choosing the direction
after seeing which way the tasks fell is how a threshold gets quietly halved.

---

## The size of the task set does not change it

```
  10 tasks   5 to 0   p = 0.062   gap +50.0pp
  10 tasks   6 to 0   p = 0.031   gap +60.0pp
  48 tasks   5 to 0   p = 0.062   gap +10.4pp
  48 tasks   6 to 0   p = 0.031   gap +12.5pp
1000 tasks   5 to 0   p = 0.062   gap +0.5pp
1000 tasks   6 to 0   p = 0.031   gap +0.6pp
```

Six tasks changing hands cleanly gives the same p-value in all three set sizes.
The reasoning holds up: in the 1,000-task row, 994 tasks came out the same way
under both arms and told you nothing, leaving the same six coin flips as the
10-task row.

What the set size does change is the gap those six tasks represent, shown in the
last column. Six of 10 is a 60-point gap. Six of 1,000 is 0.6 of a point.

A larger task set also makes disagreements easier to come by, so clearing the
floor gets easier as the set grows. The bar itself stays put.

---

## Tasks changing back cost two each

The floor assumes a clean sweep, which is the best case. Every task that moves
the wrong way is evidence against the change and has to be paid for:

```
0 tasks changing back      6 to 0     p = 0.031
1 task  changing back      8 to 1     p = 0.039
2 tasks changing back     10 to 2     p = 0.039
3 tasks changing back     12 to 3     p = 0.035
```

One task going the wrong way costs two more going the right way, every time.

This is the case worth planning around, because clean sweeps are rare. A change
that moves 9 tasks forward and 2 back gives p = 0.065, so it sits further from a
result than one moving 6 forward and none back at p = 0.031, despite moving
eleven tasks against six.

On a large task set the clean sweep stops being realistic at all. Noise alone
produces tasks moving both ways, so a 1,000-task comparison looks more like 40
forward and 25 back than 6 and 0.

---

## Clearing the floor is not the same as having a result worth having

The bottom row of the table above is significant at p = 0.031 and describes a
gap of 0.6 of a percentage point. Both statements are true at once.

Significance answers "is the direction real". It says nothing about size, and
the two questions come apart in both directions:

```
6 tasks of 1000 changing hands     real, and far too small to act on
14 tasks of 48 changing hands      large, and could still be chance if 6
                                   of them went the other way
```

So the floor is a filter rather than a verdict. Below it, stop; the comparison
cannot produce a result. Above it, read the confidence interval from
[page 03](03-bootstrapping.md), which is what carries the size.

---

## When the floor does not apply

**Partial-credit scoring.** The floor is a consequence of pass and fail being
the only two outcomes. A score that moved from 0.3 to 0.8 without crossing the
pass threshold counts as no change, though it plainly is one. Comparisons
on a continuous score use a different test, one that reads the size of each
task's movement as well as its direction, and it can reach significance on fewer
tasks.

**Several runs per task.** The arithmetic treats each task as one coin flip.
Run a task five times in each arm and it stops being one flip, and the floor is
no longer the right bar.

**Anything other than comparing two arms on shared tasks.** A single arm's pass
rate, or two arms run over different task sets, are different questions with
different arithmetic. [Page 01](01-standard-error.md) covers those.

---

## Using it

Before reading a delta or an interval, count two numbers: tasks the treatment
won, and tasks the baseline won. Both are in the per-task pairs in `lift.json`.

```
treatment won < 6                      no result is possible
treatment won < 8, baseline won 1      no result is possible
treatment won < 10, baseline won 2     no result is possible
```

In those cases the interval around the delta is not worth reading, however
favourable it looks. [Page 05](05-mcnemar.md) gives the exact p-value for splits
the table above does not cover.

---

## Related

- [01-standard-error.md](01-standard-error.md) — the vocabulary used here
- [05-mcnemar.md](05-mcnemar.md) — the test this floor comes out of
- [03-bootstrapping.md](03-bootstrapping.md) — the interval to read once it clears
- [scripts/mcnemar_simulation.py](scripts/mcnemar_simulation.py) — the figures above
