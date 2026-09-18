# Where bias comes from

Two different things make an evaluation result wrong, and only one of them
answers to more data.

**Noise** moves the number between repeats. Run the same comparison twice and
you get two answers. Averaging more measurements shrinks it, so noise is the
problem that more tasks and more runs solve.

**Bias** moves the number the same way every time. Run the comparison twice and
both answers are wrong by the same amount, in the same direction. No quantity of
extra tasks touches it, with one exception noted below: a configuration tuned
against its own task set is wrong only on that set, and fresh tasks expose it.

```
noise    moves between repeats        more data shrinks it
bias     the same every repeat        more data does nothing
```

This page covers bias: where it enters, how to catch each kind, and why adding
tasks makes it worse rather than better. [Page 07](07-where-noise-comes-from.md)
covers noise.

Figures come from `python docs/learnings/scripts/noise_simulation.py`.

---

## The seven sources

Bias arrives by one of three routes. Something other than the change under test
differs between the arms. The measurement itself is wrong in a fixed direction.
Or the result was chosen after somebody had seen it.

```
the scorer is wrong               it marks one arm's output right more often
tasks drop out unevenly           the ones that crash are not a random sample
the task set leans                it over-represents one kind of case
the model has seen the task       it answers from memory, not from configuration
the arms ran on different stacks  the stack change rode along with the treatment
you tuned against the set         the configuration absorbed the set's noise
you picked what to report         the comparison was picked after its result
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

A pass rate is an average over the tasks you ran, weighted by how often each
kind of task appears in the set. If those proportions do not match the
proportions the agent will meet in use, the average is weighted wrongly.

Take a set that is 80% one scenario which in practice occurs 20% of the time,
and suppose the agent passes 90% of that scenario and 50% of everything else:

```
weighted by your set       0.8 × 90  +  0.2 × 50   =  82%
weighted by real usage     0.2 × 90  +  0.8 × 50   =  58%
```

You would report 82% for something that performs at 58%. Every bootstrap
resample draws from the same skewed set, so the interval is tight around the
82 and says nothing about the 58.

The effect on a comparison between two arms is narrower, and worth separating.
If a change helps every scenario equally, the mix cancels and the delta is
correct whatever the proportions. The mix only distorts the delta when the
change helps one scenario more than another, which is common: a change that
gains 10 points on the over-represented scenario and nothing elsewhere reads as
`0.8 × 10 = 8` points on your set, against `0.2 × 10 = 2` in use.

**How to catch it.** Count your tasks by category and compare against the mix
you expect in use. Nothing in the results will show it, and the bootstrap will
not either.

**What to do.** Build the set to the proportions you expect, or keep the set as
it is and reweight the results to those proportions when reporting. Reweighting
needs enough tasks in every category to give each one a usable pass rate, so it
is the cheaper fix only when the small categories are not very small. Report the
proportions alongside the pass rate either way.

### The model has seen the task

A task drawn from public material may be answered from memory rather than from
the configuration under test. Both arms answer it that way, on every rerun, so
the task contributes nothing except a higher pass rate.

**How to catch it.** Look for tasks that every configuration passes
regardless of how much you degrade the prompt or remove the tools.

**What to do.** Write tasks against private material, and treat a task that
survives having its tools taken away as suspect.

### The arms ran on different stacks

A model or harness that changes between runs is a source of noise, covered in
[page 07](07-where-noise-comes-from.md). It turns into bias when the change is
aligned with the arms rather than spread across repeats: then it becomes part of
the delta you report, and no amount of extra tasks separates the two.

**What to do.** Run both arms in the same window, against pinned versions.

### You tuned against the set

Run the evaluation, look at what failed, change the configuration, run it again,
keep what scored better. Each round keeps a change partly because it helped and
partly because it suited these particular tasks, and the second part
accumulates. Twenty rounds of this produce a 16-point gain on the set even when
every change tried is worth nothing.

The only thing that detects it is measuring the configuration on tasks that were
never in the loop, because the tuned set agrees with itself on every rerun.
[Page 09](09-overfitting.md) covers the size of the effect and the held-out set
discipline that prevents it.

### You picked what to report

Running several comparisons and writing up the one that came out best makes the
reported number too large, for the same reason a threshold does: the selection
happens on the measurement. [Page 06](06-statistical-power.md) covers the
version of this that a single threshold causes.

**What to do.** Decide what you are testing before running it, report how many
comparisons you ran, and rerun the winner.

---

## More tasks make a bias worse, not better

Take the first of those seven, a scorer that is wrong, and watch what happens to
it as the task set grows.

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
one arm. Until it has been done, the split between the two is unknown, and a
result can only be reported with the noise it is assumed to carry rather than
the noise it has.

---

## Which one to suspect first

A result that fails to replicate is usually noise, and the fix is more tasks or
more runs.

A result that replicates cleanly and still seems too good is the one to check
for bias, because replication is exactly what bias does. Before believing a
large delta, read a handful of the transcripts behind the tasks that changed
hands, and confirm the treatment passed them for the reason you intended.

---

---

## Related

- [03-bootstrapping.md](03-bootstrapping.md) — why resampling cannot see any of this
- [06-statistical-power.md](06-statistical-power.md) — selection on the result, in its commonest form
- [07-where-noise-comes-from.md](07-where-noise-comes-from.md) — the errors more data does fix
- [scripts/noise_simulation.py](scripts/noise_simulation.py) — the figures above
