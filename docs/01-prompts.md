# Guide: changing the prompt

The prompt is everything the agent is told before it acts. There are three
places to change it, and which you pick decides whether the change is part of
the benchmark or part of one experiment.

| Level | Where | Baked into the task? |
|---|---|---|
| A. The briefing | a new version of `bank-briefing` in the prompt registry | yes — regenerate |
| B. A prompt variant | `--briefing-version N` at generation time | yes — separate task set |
| C. A per-run prefix | `--config-override` | no |

The briefing lives in MLflow's prompt registry, not in a file. `make_task.py`
loads a pinned version and bakes it into every `task.md`, so a task set is
permanently attached to an immutable prompt version rather than to whatever a
file happened to hold at the time.

---

## A. Change the briefing every task carries

Edit `bank-briefing` in the MLflow UI. Saving creates the next version; the
existing one is immutable, so nothing that already ran is disturbed.

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db     # Prompts → bank-briefing
python tools/register_briefing.py --list              # or check from the shell
```

Then regenerate against the version you want and gate:

```bash
python tools/make_task.py $(cat tools/eligible_ids.txt) \
  --briefing-version 2 --out tasks
python tools/check_oracles.py          # must still print 48/48
```

With no `--briefing-version` the newest registered version is used, and the URI
is printed before generation starts, so a generate is never ambiguous about
what it baked in.

The gate matters even though you only touched prose: `task.md` carries the MCP
server declaration in its frontmatter, and a malformed edit breaks every task
at once.

`make_task.py` substitutes the case notes for `{{scenario}}`, MLflow's
placeholder convention. A briefing without that placeholder is refused at
registration, since it would give every task the same empty case.

Regenerating changes `digest_tasks`. Commit before running anything —
`run_experiment.py` refuses a dirty tree.

### Seeding a fresh tracking store

A new checkout has an empty registry, so there is nothing to generate against.
`prompts/briefing.seed.md` is the starting text, named the way
`verifier/db.seed.json` is: read once, not a live copy kept in step with
anything.

```bash
python tools/register_briefing.py                        # seeds from the seed file
python tools/register_briefing.py --from-file draft.md   # or import a variant
```

Editing the seed file after that does nothing. The authoritative briefing is
the registered version.

### Why the framing matters

The first version passed tau2's roleplay text through verbatim:

> **Your character:** You are Fatima Al-Hassan, a 31-year-old small business
> owner from Detroit...

The agent read that as a live conversation, politely asked the customer to
confirm her identity, and stopped. Zero tool calls, reward 0. There was nobody
to reply to.

Reframing it as a completed call — "the customer has hung up and cannot answer
further questions" — produced 26 tool calls and a pass on the same task, same
tools, same model. If you flatten a multi-turn benchmark into single-turn, this
is the failure to watch for.

### A weakness, since fixed

The briefing used to say verify identity "before disclosing or changing account
information" without saying what disclosure meant. Seven of ten reviewed
rollouts failed that blocker.

That turned out to be mostly the wording and the rubric rather than the model's
judgement: `log_verification` takes a `user_id`, `address` and `date_of_birth`
that exist only in the customer record, so verification cannot precede the
lookup, and the criterion as written could not be satisfied. Both sides were
corrected — the rubric in
[docs/iterations/001](iterations/001-identity-blocker-definition.md), the
briefing in [002](iterations/002-briefing-disclosure-order.md). The briefing now
gives the order outright.

### Which briefing generated a task set

`make_task.py` stamps `briefing_prompt_uri` into each package's frontmatter, so
every task names the exact version it was built from:

```yaml
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/1
```

`run_experiment.py` reads it back and logs it as a param. It writes nothing to
the registry — there is one authoritative copy of the briefing and a run cannot
change it.

Because a pinned version is immutable, there is no drift to police. The one
failure worth catching is a half-regenerated task set, where some packages point
at one version and some at another; that stops the run before any rollout is
paid for.

---

## B. Keep two briefings and generate two task sets

`--briefing-version` selects which registered version to bake in, so an
alternative prompt becomes its own task set rather than an edit you have to
remember to undo:

```bash
# version 1 is the current briefing; make version 2 in the UI, then:
python tools/make_task.py $(cat tools/eligible_ids.txt) \
  --briefing-version 1 --out tasks
python tools/make_task.py $(cat tools/eligible_ids.txt) \
  --briefing-version 2 --out tasks-v2
python tools/check_oracles.py
```

Both sets stay in the tree, both are digested, and you can run them in either
order. Run `--tasks tasks` against `--tasks tasks-v2` and the two arms log
different `briefing_prompt_uri` values, so the comparison is attributable to the
prompt.

This is what makes a prompt change measurable from one commit. Without it,
isolating a briefing change means rollouts at the commit before and the commit
after, which costs an extra run and a checkout.

---

## C. Change the prompt for one run only

`--config-override` deep-merges a patch into each task's resolved config with
no file edits:

```bash
python tools/run_experiment.py --tasks tasks/task-036 \
  --config-override '{"agent":{"prompt_prefix":"Search /data/documents before calling any tool."}}' \
  --note "does a search-first nudge help"
```

`prompt_prefix` is prepended to every resolved prompt, and BenchFlow records the
override by content hash, so the variation is part of the run's identity rather
than a hidden edit. `run_experiment.py` also logs the override string as an
MLflow param.

This is the right mechanism for a quick experiment: one knob moves, everything
else is provably fixed.

### The boundary on prompt_prefix

From BenchFlow's own description of the field:

> Intended for generic harness constraints such as benchmark integrity rules;
> **must not contain task-specific solution content.**

"Search the documentation first" is fine. "The tool you need is
`order_replacement_credit_card_7291`" is not — that leaks the answer, and any
lift you measure is meaningless.

---

## Testing a prompt change

Three checks, cheapest first.

**1. Does it still generate and gate?**

```bash
python tools/make_task.py $(cat tools/eligible_ids.txt) --out tasks
python tools/check_oracles.py          # 48/48
```

Free, ~2 minutes, catches malformed frontmatter and broken templates.

**2. Does it change behaviour on one task?**

```bash
python tools/run_experiment.py --tasks tasks/task-036 \
  --experiment prompts --note "search-first nudge"
```

One rollout tells you the change is wired through and the agent reacts to it.
It tells you nothing about whether the change helps.

**3. Does it help?**

Run both arms over the whole set into separate job directories, then pair them:

```bash
python tools/compare_arms.py \
  --baseline <baseline-mlflow-run-id> --treatment <treatment-mlflow-run-id> \
  --note "what changed in the prompt"
```

That wraps `benchflow eval compare-lift`, which matches rollouts by task and
reports pass-rate and mean-reward deltas with bootstrap confidence intervals.
Pairing is what makes a 48-task set usable: it cancels task difficulty, which is
most of the variance. Comparing two aggregate pass rates instead needs a much
larger set to say anything.

A prompt experiment is exactly the case the wrapper's digest guard is built for:
regenerating moves `digest_prompts` and `digest_tasks` together, and it is
`digest_knowledge` holding still that says the two arms answered the same
questions. It refuses when the measuring stick moved, and names the prompt
digest as the lever that did.

Read the coverage before the delta. Only tasks with a healthy scored rollout on
**both** sides enter the paired metrics, so a crash in one arm silently drops
that task — `health_coverage` on each run and the paired counts on the
comparison are where that shows up.

If the interval includes zero, the experiment could not tell whether the change
helped. That is different from showing it did not help.

---

## Related

- `docs/02-tools.md` — changing what the agent can do
- `docs/03-skills.md` — adding reference material to its environment
- `docs/versioning-gaps.md` — what a run records, and what it does not
