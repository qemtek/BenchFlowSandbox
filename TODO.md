# Next actions

Ordered. Each item says why it comes before the one after it.

Written 2026-09-18, after the first noise floor run
(`b56f9113`, experiment `noise-floor`).

## Where this stands

One arm was run twice over the same 24 tasks with nothing different between
the passes: 3/24 passed the first time, 7/23 the second. Four tasks gave
different answers — `task-012`, `032`, `054`, `075`, all of them fail then
pass — and `task-062` errored in the second pass, so 23 tasks are paired.

That is a spread of 17.9 points between two identical runs. Counting the
errored task as a pass instead of a fail gives 20.8 points, as a fail 16.7, so
the dropout does not change it.

Attributing that to the sources in
[docs/learnings/07](docs/learnings/07-where-noise-comes-from.md):

- **Task set: none of it.** Both passes ran the same 24 tasks, so the term the
  confidence interval measures is absent by construction.
- **The agent: nearly all of it.** The four tasks that changed hands differ in
  what the agent chose to do, not in what happened to it — `task-032` stopped
  after 5 tool calls in the failing pass and used 17 in the passing one. None
  of the four had an infrastructure event, and total effort across all 24 tasks
  was near identical (653 against 640 tool calls).
- **The environment: real, but not in the flips.** The first pass had no
  infrastructure trouble; the second had 9 agent-install failures, 3 ACP
  errors and 3 retries, and ran 50% longer. It cost one task outright.
- **The scorer: none.** Both verifiers are programs. No model has graded
  anything yet.
- **The stack: no evidence of drift.** Both passes logged the same
  `provider_model` and the same wire settings, in one window at one commit.
  `claude-sonnet-4-6` is a floating alias with no dated form, so this is
  "nothing visibly changed" rather than "it could not have".

---

## 1. Bake Node and the agent into the task image

Every rollout installs its own toolchain at start-up: `apt-get` for `curl` and
`xz-utils`, a ~50 MB Node tarball from `nodejs.org`, then
`npm install -g @agentclientprotocol/claude-agent-acp@0.73.0`. Six containers
doing that at once, 24 times a pass, exhausted the local resolver in the second
pass — `Could not resolve 'deb.debian.org'`, then `curl: not found`, then
`rc=127`.

BenchFlow guards both steps: it skips the Node download when
`/opt/benchflow/node/bin/node` exists, and skips the npm install when
`/opt/benchflow/js-agents/bin/claude-agent-acp` exists, because the package
version is pinned. Baking both into `environment/Dockerfile` makes the whole
install a no-op and takes the network out of the rollout path.

This moves `digest_environment` on all 48 tasks. That is free right now,
because no run predating today survives as a baseline, and it will not be free
later.

## 2. A second noise floor measurement

One repeat gives one number, and everything below depends on it. The true
spread could plausibly be 8 points or 25; and all four flips going the same way
is either a 1-in-8 coincidence or an order effect, which one pair of runs
cannot distinguish.

Run after item 1, so the floor describes the environment that later
comparisons will actually run in.

## 3. Redesign iteration 006's comparison

[006](docs/iterations/006-every-request-in-the-briefing.md) predicts at least
three of 24 tasks flipping. Four flip on their own, so that prediction cannot
clear the floor whatever the briefing change does.

The options are more tasks (48 rather than 24), repeated arms averaged, or
both. Page [06](docs/learnings/06-statistical-power.md) prices them; cost it
before buying rollouts.

## 4. Re-derive the failure modes from the fixed task set

[007](docs/iterations/007-per-task-starting-state.md) found that 18 of the 48
tasks were unsolvable until today. Everything this project believes about what
the agent gets wrong was formed by reading failures on the 30 that worked —
including the skill in
[003](docs/iterations/003-bank-case-handling-skill.md) and the briefing wording
in 006. Both inherit a biased sample of failure modes.

---

## Carried, not scheduled

**An ambiguous scoring field.** `task-085` requires
`customer_max_liability_amount = 50` on all three disputes. The documented rule
is $50 within two business days *of the statement* and $500 within 60 days, and
the third dispute was noticed five days after the transaction; the tool's own
docstring adds that the value depends on "reporting timing rules and the
disputed amount", which for a $14.99 charge points lower still. An agent can
reach 500 by careful reasoning and fail the task.

40 of the 48 tasks score by hashing the whole final database, so one wrong
field discards everything else — twelve correct actions on `task-085` thrown
away by the thirteenth. Whether other tasks hang on a similarly ambiguous value
is unchecked.

**Rubric-based scoring.** The review rubric can see an agent that got twelve of
thirteen actions right, where the hash cannot. Parked: the current floor is
being established for the deterministic checks.

**A dated model id.** `claude-sonnet-4-6` publishes no dated form, so the
snapshot is recorded from the capture rather than pinned in the request.

**Contamination.** τ²-bench is public and the model may have trained on it.
Choosing 4.6 over 5 reduces the exposure; nothing here tests for it.
