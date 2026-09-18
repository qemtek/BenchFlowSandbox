# A/B testing and agent evaluation

An A/B test and an agent evaluation ask the same question: is the difference
between these two versions larger than chance would produce? They use the same
statistics to answer it, and the numbers that come out look very different.

This page sets the two side by side, because most written guidance on
experiments is written for A/B tests, and knowing which parts carry over saves
importing advice that does not fit.

---

## The machinery is shared

Both compute a p-value the same way: the chance of a result this extreme if the
two versions are truly equal. Both define power the same way: the chance of
declaring a difference when one of a stated size is really there.

The constant that shows up in [page 01](01-standard-error.md) is the standard
A/B sample-size constant:

```
2.8  =  1.96  +  0.84
         ↑        ↑
    5% false   80% power
      alarm
```

Rearranged, it is the formula behind every A/B sample-size calculator:

```
n per arm  =  2.8² × 2p(1−p) / Δ²
```

Nothing in the theory differs. What differs is the experiment the theory is
applied to.

---

## The one structural difference

An A/B test splits its units. Each user is randomised into one version and sees
only that one.

An evaluation gives every unit to both versions. Each task is run under the
baseline and under the treatment, and the two results sit side by side.

Everything else on this page follows from that one difference.

An A/B test cannot work the second way. A user shown both versions has been
influenced by the first when they reach the second, and the order they saw them
in becomes part of the result. A task carries nothing between runs, so it can be
given to both arms without contaminating either.

---

## What drives the uncertainty in each

```
A/B test, two groups      SE = √( 2p(1−p) / n )      driven by the base rate
evaluation, paired        SE = √( d / n )            driven by disagreement
```

In an A/B test the precision depends on the conversion rate and the sample size,
and on nothing else. You can compute it before launching, knowing only those two
numbers.

In a paired evaluation the base pass rate drops out completely. `d`, the share
of tasks the two arms resolve differently, takes its place. That quantity cannot
be known in advance: a change that flips eight tasks all in one direction is
easy to detect, and a change that churns twenty tasks in both directions is hard
to detect, even though both moved the pass rate by the same amount.

The practical form of this is [page 04](04-the-six-task-floor.md): the floor is
set by the number of tasks that changed hands, not by the size of the task set.
An A/B test has no counterpart, because with tens of thousands of users the
count of discordant pairs is never small, and the pairs are never observed.

---

## Sample sizes side by side

Both from the formulas above, at 80% power and a 5% false alarm rate.

```
A/B test, 50% base rate, two independent groups
   effect  10pp        392 users per arm
   effect   5pp      1,568 users per arm
   effect   1pp     39,200 users per arm

Evaluation, paired, arms disagreeing on 14% of tasks
   effect  10pp        110 tasks
   effect   5pp        439 tasks
```

The eye-catching number in A/B testing is the 39,200, and it is not there
because A/B tests are statistically harder. It is there because a 1-point effect
is thirty-nine times harder to see than a 10-point one, and a product team
chasing a 1% lift in conversion is chasing something worth having.

Set the same effect size against both and the evaluation wins. A 10-point effect
takes 784 users across two groups, or 110 tasks run twice. Pairing is what buys
that, and it is a design the A/B test could not have used.

The 110 is worth holding next to the 48 tasks these pages use as their example.
The reason a 48-task comparison struggles to see a 10-point gain is not that
agent evaluation is peculiar. It is that 48 is well under the 110 the formula
asks for. [Page 06](06-statistical-power.md) simulates the same thing and gets
73.8% power at 96 tasks and 97.8% at 192, which brackets it.

---

## Where the cost sits

Traffic arrives on its own. An A/B test that needs four times the sample runs
for four times as long and costs nothing extra per user, which is why running at
80% power is the normal standard rather than an aspiration.

Rollouts are bought. Each one costs money and wall-clock, and the task set has
to be written by someone before any of it can run. An evaluation at 46% power is
common for that reason, not through carelessness.

Two consequences follow, and both are covered in
[page 06](06-statistical-power.md). A result that clears the threshold at 46%
power overstates its effect by about 1.39 times, so rerunning the winner is a
standing requirement in evaluation and an edge case in A/B testing. And the
pre-launch power calculation, which A/B practitioners treat as routine because
wasted traffic is visible, matters more when the wasted resource is a budget.

---

## What each has to worry about

An A/B test worries about things that come with scale and with people. Users
differ from one another, results are watched continuously so the temptation to
stop early is constant, several metrics are usually tracked at once, and the
effect often differs between segments of the audience.

An evaluation worries about things that come with running a machine on a task.
The agent produces a different transcript each time it is run. Tools and
services behave differently between runs. The scorer may be a model that
disagrees with itself. The model or harness can change between one run and the
next. [Page 07](07-where-noise-comes-from.md) covers all four.

One of those has no A/B equivalent at all. You never rerun a user, so the
question of how much the same unit varies under the same treatment does not
arise. In an evaluation it is a source you have to measure and, from the
simulation behind [page 02](02-paired-comparison.md), the largest one.

The same asymmetry works in the evaluation's favour. Because a task can be run
again, repeat runs are available as a way to buy precision, and an A/B test has
no such lever.

---

## What carries over from A/B practice

**Deciding the comparison before running it.** The reason is identical in both
settings and is arithmetic rather than etiquette.

**Computing the detectable effect first.** An experiment that cannot resolve the
effect you are hoping for will not resolve it, and this is cheaper to discover
before the run than after.

**Correcting for running several comparisons.** Five variants tested at a 5%
false alarm rate give roughly a one in four chance that one of them looks good
by accident, whatever is being tested.

**Holding out data.** A/B testing keeps holdout groups; evaluation needs
held-out tasks, for the reason in [page 09](09-overfitting.md).

**CUPED, in spirit.** The A/B world's main variance-reduction technique uses
each user's earlier behaviour as a stand-in for the pairing it cannot do
directly. An evaluation gets the stronger version for free by running both arms
over the same tasks.

---

## What does not carry over

**Sequential monitoring.** A/B tests are watched while they run and use
always-valid p-values to allow it. An evaluation runs as a batch and is read
once, so the machinery solves a problem it does not have.

**Detecting small effects.** A 1-point effect is routine in A/B testing and out
of reach at any task count an evaluation is likely to run.

**Normal approximations.** They hold comfortably at tens of thousands of users
and break at the disagreement counts a small task set produces, which is why
[page 05](05-mcnemar.md) uses the exact form of the test rather than the
chi-squared one.

**Segment analysis as a default.** Slicing a result by category is cheap when
each slice still holds thousands of units. On a 48-task set, a slice is a
handful of tasks and its interval is wider than the question it was asked to
settle.

---

## Related

- [01-standard-error.md](01-standard-error.md) — where the 2.8 comes from
- [02-paired-comparison.md](02-paired-comparison.md) — what pairing buys, measured
- [05-mcnemar.md](05-mcnemar.md) — the paired test, and why the exact form
- [06-statistical-power.md](06-statistical-power.md) — power, and the cost of running low
