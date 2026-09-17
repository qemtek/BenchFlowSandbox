# Paired comparison

**Running both arms over the same tasks reduces the variance of the difference
between them. It costs nothing extra.**

Figures below come from `python docs/learnings/pairing_simulation.py`.

---

## What varies when you compare two arms

A comparison produces one number: the difference in pass rate. Run the whole
experiment again and that number moves. Three separate things move it, and they
have different remedies.

| Source | What it is | Reduced by |
|---|---|---|
| Task sampling | which tasks ended up in your set | **pairing**, and more tasks |
| Agent behaviour | same arm, same task, different answer | repeat runs, averaged |
| Measurement | the scorer disagreeing with itself | deterministic scoring |

The third is near zero when a program checks the answer, and real when a model
grades it. The first two are the ones you have to manage.

---

## Task sampling

Tasks differ in difficulty. Some are solved by almost any configuration, some by
almost none. That spread is large — usually much larger than the effect you are
testing.

If each arm ran a different set of tasks, the difficulty spread would land
inside the measured difference, and nothing would separate it from a real
effect.

**Pairing removes it by subtracting within each task before averaging.** Run
both arms over the same tasks, then for each task compute:

```
d  =  (did the treatment pass)  −  (did the baseline pass)      +1, 0, or −1
```

A task's difficulty affects both terms equally, so it cancels in the
subtraction. The average of `d` across tasks is the delta. That average equals
the plain difference in pass rates, so the estimate is unchanged — only its
variance falls.

Simulated on 48 tasks with a genuine 7-point effect:

```
both arms on the same 48 tasks      standard error  3.67pp
each arm on a different 48          standard error  9.85pp
                                    reduction         63%
```

---

## Agent behaviour

Rerun one arm, unchanged, over the same tasks, and some tasks flip. This is not
measurement error; the agent genuinely does something different.

Pairing cannot reduce this. The two arms' randomness is independent, so there is
no shared term to subtract out. Holding the task set fixed and varying only the
agent:

```
paired standard error on a fixed task set   6.48pp
```

The same figure with or without pairing.

Only repetition reduces it. Run each arm `n` times and average, and this
component falls by `√n` — four runs to halve it.

---

## What follows

The two sources add together. Pairing removes one and leaves the other
untouched, so a paired comparison is still limited by how erratic the agent is.

**Always pair.** It is free: you were running both arms anyway, and running them
over the same tasks costs nothing.

**Budget for repeats separately.** They are the only thing that touches agent
variance, and they cost rollouts.

**Know which one is limiting you** before spending anything. If the agent is
highly consistent, pairing alone may be enough. If it is erratic, repeats matter
more than adding tasks.

---

## How much pairing buys, in effect size

Pairing's benefit depends on how many tasks the two arms disagree on. On a
48-task set:

```
tasks that differ        standard error    smallest detectable effect
 2 of 48                      3.2pp                   9pp
 4 of 48                      4.6pp                  13pp
 9 of 48                      6.5pp                  18pp
14 of 48                      7.9pp                  22pp

unpaired                      9.9pp                  28pp
```

Read the right-hand column: a change that moves 10% of tasks is detectable
paired and invisible unpaired.

Counter-intuitively, **fewer disagreements is better**. A consistent effect on a
few tasks separates from chance more easily than a scattered one.

These numbers are for a 48-task set with pass rates near 50%. Both columns
shrink with more tasks and with pass rates further from 50%; see
[01-standard-error](01-standard-error.md).

---

## Running it

```bash
benchflow eval compare-lift \
  --baseline jobs/<baseline-run> --trained jobs/<treatment-run> \
  --out lift.md --json-out lift.json
```

It pairs the rollouts by task and puts an interval around the delta; see
[03-bootstrapping](03-bootstrapping.md) for what that interval means.

**Use a separate job directory per arm.** BenchFlow resumes into an existing
directory and skips rollouts it considers done. Point both arms at one and the
second does nothing, leaving you comparing a set of rollouts against itself — a
clean report, a delta near zero, and no error.

**Read the coverage figures before the delta.** Only tasks scored on both sides
get paired. If an arm crashed on five tasks you are comparing 43, not 48, and
crashes cluster on the long, complicated tasks — so the delta quietly describes
an easier subset.

**Some effects cannot appear.** Scoring is pass or fail, so an agent reaching
the same answer in half the steps scores identically. If the change was meant to
improve efficiency rather than correctness, this is the wrong instrument.

---

## Related

- [01-standard-error.md](01-standard-error.md) — where the variance comes from
- [03-bootstrapping.md](03-bootstrapping.md) — how the interval is built
- [pairing_simulation.py](pairing_simulation.py) — the figures above
