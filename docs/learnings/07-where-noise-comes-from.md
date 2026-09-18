# Where noise comes from

Two different things make an evaluation result wrong, and they need opposite
responses.

**Noise** moves the number between repeats. Run the same comparison twice and
you get two answers. Averaging more measurements shrinks it, so noise is the
problem that more tasks and more runs solve.

**Bias** moves the number the same way every time. Run the comparison twice and
both answers are wrong by the same amount, in the same direction. No quantity of
extra tasks touches it.

```
noise    moves between repeats        more data shrinks it
bias     the same every repeat        more data does nothing
```

This page covers noise: the five things that vary between repeats, how large
each one is, and what reduces it. [Page 08](08-where-bias-comes-from.md) covers
bias.

The distinction matters because the confidence interval reported by
`compare-lift` measures noise. It does not measure bias, so it narrows just as
readily around a wrong number as around a right one.

---

## The five things that vary

Noise is not one quantity. Five different things change between repeats, they
change for different reasons, and each has its own remedy. Working out which of
them is moving your number is most of the work.

```
the task set     a different set of tasks gives a different pass rate
the agent        the same task passes on one run and fails on the next
the environment  a tool times out, a service answers differently
the scorer       the same transcript is graded pass, then fail
the stack        the model or harness is not the one you ran against before
```

---

### The task set

Tasks differ enormously in difficulty, so a set drawn one way is easier than a
set drawn another way, and the pass rate follows. This is the source the
confidence interval is built to measure.

**How big it is.** Three numbers, because it depends on what is being measured.
On a 48-task set near a 50% pass rate:

```
one arm's pass rate                              standard error  7.2pp
the difference between two arms, by overall rate                 9.88pp
the difference between two arms, task by task                    3.67pp
```

The second line is larger than the first because a comparison contains both
arms' errors, not one. Those errors do not add, because they are independent and
as often cancel as compound, so they combine as:

```
√(7.2² + 7.2²)  =  7.2 × √2  =  10.2pp
```

The 9.88 is that same quantity measured on simulated runs rather than taken from
the formula. [Page 01](01-standard-error.md) derives the first line and the
combination rule; [page 02](02-paired-comparison.md) derives the third.

**What reduces it.**

- Pair. A task's difficulty appears in both arms, so comparing task by task
  subtracts it out, which is the 9.88 to 3.67 drop above. It costs nothing and
  needs only that both arms ran the same tasks. What it leaves behind is the
  3.67: tasks still differ in how much the change helps them, and that part is
  reduced only by running more of them.
- Add tasks. The task count sits under a square root in the formula,
  `SE = √(p(1−p)/n)`, so multiplying the tasks by four halves the error: one
  arm near a 50% pass rate goes from 7.2 points at 48 tasks to 3.6 at 192.
  Every further halving costs four times again.
- Hold the task set fixed across comparisons. A result measured on a set you
  have changed since is not comparable with the one before it, and the change
  looks exactly like an effect.
- Choose the set deliberately rather than by luck, in fixed proportions across
  the categories you care about, so that one run cannot happen to draw an easy
  mix.

### The agent

The same prompt, tools and model produce a different transcript each time, so
the same task passes on one run and fails on the next. Nothing about the
configuration changed.

**How big it is.** The simulation behind page 02 puts it at a paired standard
error of 6.48 points, larger than the 3.67 that task sampling contributes. To
measure it on real runs rather than simulated ones, run one arm twice over the
same tasks and read the spread between the two results.

**What reduces it.**

- Repeat runs, averaged. Averaging `n` runs divides this source by `√n`, on the
  same arithmetic as adding tasks above, so four runs halve it and sixteen
  quarter it. It is the only remedy that works on the whole of this source, and
  the cost is a full extra pass over the task set each time.
- Pin what the harness lets you pin. Sampling temperature and a fixed seed
  remove some of it outright, though not every runtime exposes them; where one
  does not, record that they sat at a default rather than leaving it unstated.
- Pin reasoning effort, or whatever equivalent setting decides how much work the
  agent does. Left unset it takes a default that can change underneath you.

**What does not work.** Pairing. The two arms' randomness is independent, so
there is no shared term to subtract, and a paired comparison is still bounded by
how erratic the agent is.

### The environment

The agent acts on things outside itself. A service is slower on one run than
another, a tool call fails and is retried, a database is in a different state,
a search returns different results. Two runs of the same configuration meet
different worlds.

**How big it is.** It depends entirely on what the tasks touch. Tasks that use
only local, fixed state carry almost none of it. Tasks that reach a live service
carry as much variation as that service has.

To measure it, run the same arm twice over the same tasks against live services,
then twice more against recorded responses. Both pairs contain the agent's own
variation; only the first contains the environment's, so the gap between the two
spreads is what the environment is worth.

**What reduces it.**

- Replay recorded responses instead of calling live services. This removes the
  source rather than averaging it away, and is the largest single win available
  for tasks that reach outward.
- Reset to fixed seed data before every rollout, so a task cannot inherit what
  the previous one left behind.
- Set timeouts long enough that they fire on genuine hangs rather than on a slow
  afternoon, since a timeout is the mechanism that turns this into bias.
- Retry transient failures, and record how many retries each rollout needed. An
  unrecorded retry is indistinguishable from a task that never had trouble.

**When it becomes bias.** The moment failures are not spread evenly across
tasks. Timeouts concentrate on the long tasks, and losing the long tasks changes
which set you are measuring. That is bias, and
[page 08](08-where-bias-comes-from.md) covers it.

### The scorer

A model asked to grade the same transcript twice does not always give the same
answer. A program checking the same output twice always does.

**How big it is.** Near zero for a programmatic check. For a model grader, it is
whatever its disagreement rate turns out to be, which you can measure directly:
grade the same transcripts twice and count how often the two gradings differ.

**What reduces it.**

- Use a programmatic check wherever the task admits one. This takes the source
  to zero rather than reducing it.
- Grade each transcript once and keep the label, rather than regrading whenever
  the comparison is rerun. This stops scorer noise entering repeat runs, though
  it freezes any mistake the grader made rather than correcting it.
- Where a model has to grade, have it grade each transcript several times and
  take the majority, which averages the disagreement down in the same way repeat
  runs average the agent down.
- Measure the grader against itself first, on identical transcripts. Its
  disagreement rate puts a floor under the effect you can resolve, and it is
  cheap to establish.

### The stack

The model behind a floating alias, the harness version, the generation settings
left at a default: all of these can differ between two runs separated in time,
and none of them is a property of the configuration you meant to test. A run
that does not record them cannot be told apart from a run that used different
ones.

**What reduces it.**

- Run both arms in the same window, against the same stack. This costs nothing
  and is the difference between the top and bottom rows of the table below.
- Pin the model to an exact version rather than a floating alias, which can
  change under you between one run and the next.
- Pin the harness version, and record it with the run.
- Record the generation settings. Where the runtime does not expose them,
  record that fact, so the limit is written down rather than looking like an
  oversight.

**When it becomes bias.** This one depends on how the runs were scheduled,
and the distinction matters more here than anywhere else:

```
both arms ran together on one stack    no effect
the stack drifted between repeats      noise
the stack changed between the arms     bias, inseparable from your delta
```

The bottom row is why a baseline from last month is not a baseline. Whatever
changed in the stack since then is now part of your measured delta, and no
amount of extra tasks will separate the two.

---

### The cheapest move against each

```
source           the first thing to do             what it costs
the task set     pair the comparison               nothing
the stack        run both arms in one window       nothing
the scorer       have a program check the answer   task design
the environment  replay recorded responses         setup, paid once
the agent        repeat runs, averaged             four times the rollouts
                                                   to halve it
```

The two free lines are free because they are decisions about how the experiment
is arranged rather than things you buy. They are also the two most often given
away: comparing overall pass rates throws away the first, and reusing a baseline
from a previous month throws away the second.

Only the last line has a price that rises with how much noise you want removed,
which is why the other four are worth clearing first.

---

## The analysis decides how much of it reaches you

The five sources above are properties of the experiment. How much of their
variance reaches your reported interval depends on what you do with the results
afterwards.

```
compared by overall pass rate     standard error  9.88pp
compared task by task             standard error  3.67pp
```

Both lines describe identical runs, from the simulation behind
[page 02](02-paired-comparison.md). The difference is not in the data. Comparing
overall rates treats the two arms as unrelated, so every task's difficulty is
counted as noise twice, once in each arm's rate. Comparing task by task
subtracts it out.

The same choice appears again with repeats: one rollout per task carries the
agent's full run-to-run variation into the result, while averaging four carries
half of it. `compare-lift` pairs by task, so it makes the better choice there.
It takes one rollout per task, so on repeats there is nothing to choose.

An analysis cannot remove noise that the design did not let it see. Pairing only
works because both arms ran the same tasks; had they run different tasks, there
would be nothing to subtract.

---

## What the interval can and cannot see

The bootstrap resamples tasks, so the uncertainty it reports is the uncertainty
that comes from which tasks you ran. That is one source out of the several
above.

```
which tasks are in the set     the interval covers this
the agent between runs         not covered: one run per task is all it sees
the grader                     not covered
every source of bias           not covered, and unaffected by resampling
```

So a narrow interval means the task set was informative. It does not mean the
result is right. [Page 03](03-bootstrapping.md) makes the same point from the
bootstrap's side, and [page 08](08-where-bias-comes-from.md) shows what a narrow
interval around a wrong number looks like.

---

---

## Related

- [01-standard-error.md](01-standard-error.md) — how large the task-sampling term is
- [02-paired-comparison.md](02-paired-comparison.md) — what pairing removes, and what it cannot
- [06-statistical-power.md](06-statistical-power.md) — what buying your way out of noise costs
- [08-where-bias-comes-from.md](08-where-bias-comes-from.md) — the errors more data cannot fix
