# Overfitting to your evaluation set

Overfitting to an evaluation set means tuning a configuration until it fits the
particular tasks you are testing on rather than the work those tasks stand for.
The pass rate on that set rises. Performance on anything else does not.

It happens through ordinary work. Run the evaluation, look at what failed,
change the prompt or the tools, run it again, keep what scored better. Each
round keeps a change partly because it helped and partly because it happened to
suit these tasks, and the second part accumulates.

Figures come from `python docs/learnings/scripts/overfitting_simulation.py`.

---

## What tuning against a set produces on its own

In the simulation below, every change tried is worth exactly nothing: the
configuration's true pass rate is 50% at the start and 50% after every change.
The only thing that varies is which tasks happen to pass, because the agent is
not deterministic. Each round proposes a change and keeps it if the set scores
better.

```
rounds of tuning    tuned set    fresh tasks    apparent gain
       0              50.0%         50.1%           +0.0pp
       5              55.6%         50.2%           +5.6pp
      10              59.9%         50.1%           +9.9pp
      20              66.5%         50.1%          +16.5pp
      50              77.6%         50.1%          +27.6pp
```

Fifty rounds take the set from 50% to 77.6% without a single change having done
anything. The middle column is what the configuration is worth on tasks it was
not tuned against, and it does not move at all.

That flat middle column is the optimistic case, and the next section covers what
happens when it is not flat.

The mechanism is selection. A change that is genuinely neutral still moves some
tasks each way. Keeping only the changes that scored better means keeping the
runs where the movement happened to be favourable, and discarding the rest. Do
that fifty times and you have collected fifty helpings of good luck into one
configuration.

---

## When fitting the set costs performance elsewhere

The simulation above assumes every change is harmless everywhere except in what
it does to the score. Tuning often is not harmless. A change that fits these
tasks frequently fits them by narrowing something: an instruction that names the
case in front of you, a special path for a format that happens to appear here, a
heuristic that suits these inputs. Each of those costs performance on the cases
it did not anticipate.

Repeating the tuning with each accepted change costing one point of true
quality:

```
rounds of tuning    tuned set    fresh tasks    gap
       0              49.9%         49.7%       0.1pp
       5              55.4%         48.1%       7.3pp
      10              59.5%         46.8%      12.7pp
      20              65.2%         45.0%      20.2pp
      50              74.2%         41.7%      32.6pp
```

The set now reports 74.2% for a configuration that performs at 41.7%, which is
worse than the 50% it started from. Fifty rounds of tuning made the system worse
while the evaluation recorded a 24-point improvement.

The one-point cost per change is an assumption rather than a measured quantity,
and the real figure depends entirely on what kind of changes the tuning makes.
The shape does not depend on the size of it. Whenever fitting the set trades
against general behaviour, the two columns move apart from both ends, and the
number you are reading moves the wrong way twice as fast as the thing it claims
to measure.

This is also why a flat held-out score during a productive-looking tuning run is
not reassuring. Flat is the good case.

---

## Keeping each improvement compounds; a single sweep does not

The same budget of variants, tried all at once and judged in one go:

```
variants tried    tuned set    apparent gain
       1            50.2%         +0.2pp
       5            58.2%         +8.2pp
      10            61.0%        +11.0pp
      20            63.5%        +13.5pp
      50            66.2%        +16.2pp
```

Fifty variants judged together give 16.2 points. Fifty rounds of keep-what-works
give 27.6. Sequential tuning is worse because each accepted change becomes the
starting point for the next, so the luck is banked and built upon, while a sweep
only ever collects the single luckiest draw.

This is the opposite of the intuition that careful incremental work is safer
than a scattergun sweep. On a fixed set of tasks, the incremental process fits
harder.

---

## More tasks slow it down without stopping it

```
tasks tuned against    apparent gain after 20 rounds
        48                       +16.5pp
       192                        +8.6pp
       768                        +4.3pp
```

Quadrupling the set halves the damage, which is the same `√n` relationship that
governs the standard error in [page 01](01-standard-error.md). The amount of
luck available to climb is set by how much the pass rate wobbles, and that falls
with the square root of the task count.

It does not reach zero. A larger set is a slower set to overfit, not a set that
cannot be overfitted, and the rounds keep coming.

---

## Why this one behaves unlike other bias

[Page 08](08-where-bias-comes-from.md) defines bias as an error that lands the
same way every repeat, which more data cannot remove. Overfitting fits that
definition against one set of tasks and breaks it against another.

```
rerun on the same tasks             the gain reproduces exactly
run on tasks never tuned against    the gain is absent, or reversed
```

A wrong verifier gives a wrong answer on any tasks you point it at. Overfitting
gives a wrong answer only on the tasks it was fitted to, which makes it the one
source of bias with a direct test: measure the configuration on tasks that were
never in the loop.

That test is also the only thing that detects it. The tuned set agrees with
itself on every rerun, the confidence interval around its pass rate is honest,
and each individual round of tuning was a correct measurement of something.

---

## Holding tasks back

The remedy is a division made before the tuning starts, not a check applied
afterwards.

**A development set** is what you iterate against. Look at it as often as you
like, read its failures, tune against it freely. Its pass rate is not a
performance estimate and should not be quoted as one.

**A held-out set** is what you never tune against. It gives you one honest
number per look.

The division only works if it is made early. Tasks moved into the held-out set
after they have already informed a decision are not held out, because the
configuration has already seen them through you.

### Spending the held-out set

Each look at the held-out set spends part of it, and the cost is paid in the
same currency as the tables above: every time you use it to choose between
candidates, you are selecting on its noise, and it starts becoming a development
set.

Two rules keep it usable:

- Use it to confirm a candidate already chosen on the development set, not to
  pick between candidates. Choosing is what does the damage.
- Count the looks and report the count. A held-out number from the fortieth look
  is not what it was on the first.

Where tasks are cheap to write, retiring the development set periodically and
replacing it achieves the same thing from the other direction, because a fitted
configuration meets tasks it has never been fitted to.

---

## What this is not

**Not contamination.** A model that saw a task during training answers it from
memory, which inflates every configuration equally and is present from the first
run. Overfitting is created by your own iteration and grows with it.
[Page 08](08-where-bias-comes-from.md) covers contamination separately.

**Not a reason to stop iterating.** Iteration is how configurations improve. The
tables above describe what happens when every change is worthless, which is the
extreme case; real tuning mixes genuine gains with fitted ones. The held-out set
is what tells you the ratio.

---

## Related

- [06-statistical-power.md](06-statistical-power.md) — the same selection in a single comparison
- [08-where-bias-comes-from.md](08-where-bias-comes-from.md) — the other errors more data cannot fix
- [scripts/overfitting_simulation.py](scripts/overfitting_simulation.py) — the figures above
