# 002 — Telling the agent what disclosure means

Status: landed, unmeasured
Date: 2026-09-17
Touches: `prompts/briefing.md`, regenerates all 48 `tasks/*/task.md`
Moves which digest: `digest_prompts` and `digest_tasks`
Related: [001](001-identity-blocker-definition.md) changed the same rule on the
judge's side

## The problem

The briefing stated the policy without stating the order it implies:

> Verify the customer's identity before disclosing or changing account
> information, and record it with `log_verification`.

It did not say what counts as disclosure, and the case notes say the customer
has hung up, so there was nobody for the agent to disclose anything to. An
agent reading that sentence had no way to know that the review would be looking
for `log_verification` to precede the first mutating call.

`docs/01-prompts.md` already recorded this as "a known weakness, not yet fixed"
and named it as the obvious first prompt experiment.

## The design question, and how it was settled

Inferring where the disclosure boundary sits could be treated as part of the
capability under test, in which case stating it makes the task easier rather
than fairer, and the honest form would be Level B from `docs/01-prompts.md` — a
second briefing generating its own task set, kept alongside the current one.

It was settled the other way, for one reason: after 001 the rubric states the
required order explicitly, and a task set that scores an ordering it never
states is testing whether the agent can guess the judge. Stating it removes a
hidden requirement rather than an obstacle. The knowledge-base work, the
discovery of the 44 specialised operations and the reason codes are all
untouched, and those are what the tasks are for.

Recorded here rather than left implicit, because it is a judgement call and the
next person has to be able to disagree with it.

## The change

The Bank policy section now gives the sequence: look the customer up, compare
what they said against the record, call `log_verification`, and only then run
anything that changes the bank's records or state an account detail in the
closing report. It also says outright that the lookup is how verification is
performed, so the lookup comes first.

The closing sentence on exception procedures gained four words — "including
where it says identity verification is not required" — which is the case
`task-033` failed on.

No operation, argument or reason code is named, so the boundary in
`docs/01-prompts.md` on solution content holds.

## Baseline

None, and none will be taken.

Isolating this change would mean rollouts at the commit before it and the commit
after, because the briefing is baked into `task.md` at generation time and there
is no run-time switch for it. That is one extra run, plus a second task set or a
checkout, to measure a change whose case does not rest on a number.

The case is consistency: after [001](001-identity-blocker-definition.md) the
rubric states the required order explicitly, and a task set that scores an
ordering it never states is testing whether the agent can guess the judge. The
briefing now states it. That is worth doing whether or not it moves the score.

Measuring it was considered and dropped on 2026-09-17 as not worth the rollouts.
Recorded here so that nobody later reads the absence as an oversight, and so
that no one cites this change as an improvement — it has not been shown to be
one.

## What this costs later

Runs before this commit and runs after it differ in the briefing as well as in
whatever is being tested, so they are not comparable. The baseline for
everything downstream is this commit, not anything earlier.

If the question ever becomes worth a number, the honest form is Level B from
`docs/01-prompts.md`: keep the old briefing as `prompts/briefing-plain.md`,
generate a second task set from it, and run both from one commit.
`briefing_prompt_uri` already distinguishes the arms, which is the part that
would otherwise be missing.

## Result

Not measured, by the decision above. The change is in the tree:
`prompts/briefing.md` edited, all 48 packages regenerated, `check_oracles.py`
prints 48/48 and `smoke: stdio transport OK`.

## Verdict

Landed unmeasured. Treat it as part of the baseline, not as a result.
