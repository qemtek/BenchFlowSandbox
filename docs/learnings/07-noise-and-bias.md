# Noise and bias

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

The confidence interval reported by `compare-lift` measures noise. It does not
measure bias, so it narrows just as readily around a wrong number as around a
right one.

Figures come from `python docs/learnings/scripts/noise_simulation.py`.

---

## Where the noise comes from

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
error of 6.48 points, larger than the 3.67 that task sampling contributes. That
figure is simulated rather than measured. Running one arm twice over the same
tasks would measure it, and that has not been done here.

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

**How big it is.** Unmeasured here, and it depends entirely on what the tasks
touch. Tasks that call only local, fixed state have almost none. Tasks that
reach a live service have as much as that service has.

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
which set you are measuring. That is bias, covered below.

### The scorer

A model asked to grade the same transcript twice does not always give the same
answer. A program checking the same output twice always does.

**How big it is.** Near zero for programmatic checks. For a model grader,
unmeasured here, and it can be measured directly by grading the same transcripts
twice and counting the disagreements.

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
and none of them is a property of the configuration you meant to test.
`docs/versioning-gaps.md` records which are pinned in this project and which are
not.

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

## Where the bias comes from

Bias has two entry points. Either something other than the change under test
differs systematically between the arms, or the measurement itself is wrong in a
fixed direction. The scorer fault demonstrated above is the second kind.

```
the scorer is wrong           it marks one arm's output right more often
tasks drop out unevenly       the ones that crash are not a random sample
the task set leans            it over-represents one kind of case
the model has seen the task   it answers from memory, not from configuration
the arms ran on different     the stack changed, and the change rode along
stacks                        with the treatment
you picked what to report     the comparison was chosen after its result
                              was known
```

### The scorer is wrong

A check that accepts a format one configuration happens to produce, or rejects
one it does not, credits that arm on every run. The fault does not have to be
large: 5% of tasks was enough to produce the table above.

**How to catch it.** Read the transcripts of tasks that changed hands and
confirm the treatment passed them for the reason you intended. This is the only
reliable check, and a handful of transcripts is usually enough.

**What to do.** Write the check against the task's requirement rather than
against an example answer. Where a model grades, give it the two arms' outputs
without telling it which is which.

### Tasks drop out unevenly

Only tasks scored on both sides can be paired, so a comparison that lost five
tasks to timeouts is a comparison of the 43 that survived. Long, complicated
tasks are the ones that time out, so the surviving set is easier than the set
you chose, and the pass rate you report belongs to that easier set.

**How to catch it.** Compare the task count in the report against the task
count you ran. Any gap is this.

**What to do.** Fix the crashes. Failing that, recompute the delta twice, once
counting every missing rollout as a pass and once as a fail. If the conclusion
survives both, the gap did not cause it.

### The task set leans

A set that over-represents one kind of case answers a question about that case
rather than the one you had in mind. Every bootstrap resample inherits the same
lean, so the interval will be tight around a number that does not generalise.

**How to catch it.** Count your tasks by category and compare against the
mix you meant to test. Nothing in the results will show it.

**What to do.** Choose the set deliberately, in fixed proportions, and report
the proportions alongside the pass rate.

### The model has seen the task

A task drawn from public material may be answered from memory rather than from
the configuration under test. Both arms answer it that way, on every rerun, so
the task contributes nothing except a higher pass rate.

**How to catch it.** Look for tasks that every configuration passes
regardless of how much you degrade the prompt or remove the tools.

**What to do.** Write tasks against private material, and treat a task that
survives having its tools taken away as suspect.

### The arms ran on different stacks

Covered under the stack above. When a model or harness change is aligned with
the arms rather than spread across repeats, it becomes part of the delta you
report, and no amount of extra tasks separates the two.

**What to do.** Run both arms in the same window, against pinned versions.

### You picked what to report

Running several comparisons and writing up the one that came out best makes the
reported number too large, for the same reason a threshold does: the selection
happens on the measurement. [Page 06](06-statistical-power.md) covers the
version of this that a single threshold causes.

**What to do.** Decide what you are testing before running it, report how many
comparisons you ran, and rerun the winner.

---

## More tasks make a bias worse, not better

Take the first source in that list, a scorer that is wrong, and watch what
happens to it as the task set grows.

Both blocks below compare two arms of genuinely equal quality, so the correct
answer in both is a delta of zero.

Both blocks also contain noise, from tasks differing in difficulty and from the
arms disagreeing by chance. Only the second contains a bias: there, the scorer
credits the treatment on 5% of tasks regardless of what either arm did. That
fault lands the same way in every run, which is what makes it a bias and not
noise.

The point of running both is that the noise behaves identically in each. Every
difference between the blocks is the bias.

```
A. noise only: the scorer is working correctly
     48 tasks   delta  -0.0pp   interval width  39.5pp   difference declared  4.4%
    192 tasks   delta  +0.1pp   interval width  19.9pp   difference declared  4.4%
    768 tasks   delta  +0.1pp   interval width  10.0pp   difference declared  5.0%
   3072 tasks   delta  +0.0pp   interval width   5.0pp   difference declared  5.1%

B. noise plus bias: the scorer credits the treatment on 5% of tasks
     48 tasks   delta  +4.8pp   interval width  40.4pp   difference declared  7.1%
    192 tasks   delta  +5.1pp   interval width  20.3pp   difference declared 14.8%
    768 tasks   delta  +5.0pp   interval width  10.2pp   difference declared 47.3%
   3072 tasks   delta  +5.0pp   interval width   5.1pp   difference declared 96.5%
```

Start with the top block, which has noise but no bias. The delta is zero at
every task count, which is correct, because the two arms really are equal. A
difference is declared about 5% of the time at every size, which is the false
alarm rate a 95% interval is designed to have. Adding tasks narrows the
interval and changes nothing else.

Now the bottom block, which has the same noise plus a 5-point bias. Take it one
column at a time.

**The delta column reads +4.8, +5.1, +5.0, +5.0.** The scoring fault is worth 5
points, and it is still worth 5 points after sixty-four times as many tasks.
Averaging does not remove it, because it is not a random error. Every run gets
credited on the same 5% of tasks.

**The width column reads 40.4, 20.3, 10.2, 5.1.** It halves every time the task
count quadruples, exactly as it does in the top block. Width depends on how many
tasks you ran and nothing else, so a fault in the scorer does not slow it down.

**Now put the two together.** The delta stays at 5 points while the interval
around it keeps shrinking. At 48 tasks the interval is 40 points wide, far too
wide to exclude zero, so the fault is usually reported as "could not tell". By
3,072 tasks the interval is 5 points wide, centred on 5, and it no longer
reaches zero at all.

That is the last column. The same fault is called a real improvement 7% of the
time on 48 tasks and 96.5% of the time on 3,072.

More tasks did not move the answer closer to the truth. They made a false answer
look certain.

---

## Telling them apart

Rerun one arm, unchanged, over the same tasks.

```
the number moves       what moved is noise
the number holds       what is left is bias
```

This is the only diagnostic that separates them, and it costs one extra run of
one arm. It is also the measurement [page 01](01-standard-error.md) says has not
been done here, which means the split between the two components in this project
is currently unknown.

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
bootstrap's side.

---

## Which one to suspect first

A result that fails to replicate is usually noise, and the fix is more tasks or
more runs.

A result that replicates cleanly and still seems too good is the one to check
for bias, because replication is exactly what bias does. Before believing a
large delta, read a handful of the transcripts behind the tasks that changed
hands, and confirm the treatment passed them for the reason you intended.

---

## Related

- [02-paired-comparison.md](02-paired-comparison.md) — the two noise sources, and what pairing removes
- [03-bootstrapping.md](03-bootstrapping.md) — what resampling can measure
- [06-statistical-power.md](06-statistical-power.md) — buying your way out of noise
- [scripts/noise_simulation.py](scripts/noise_simulation.py) — the figures above
