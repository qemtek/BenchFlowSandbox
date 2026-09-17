# Guide: changing the prompt

The prompt is everything the agent is told before it acts. There are three
places to change it, and which you pick decides whether the change is part of
the benchmark or part of one experiment.

| Level | Where | Baked into the task? |
|---|---|---|
| A. The briefing | `prompts/briefing.md` | yes — regenerate |
| B. A prompt variant | `BANK_BRIEFING=<file>` at generation time | yes — separate task set |
| C. A per-run prefix | `--config-override` | no |

---

## A. Change the briefing every task carries

`prompts/briefing.md` is the template. `briefing()` in `tools/make_task.py`
fills `{scenario}` from the tau2 case and wraps it in
`prompts/frontmatter.yaml`.

Edit the template, then regenerate and gate:

```bash
$EDITOR prompts/briefing.md
python tools/make_task.py $(cat tools/eligible_ids.txt) --out tasks
python tools/check_oracles.py          # must still print 48/48
```

The gate matters here even though you only touched prose: `task.md` carries the
MCP server declaration in its frontmatter, and a malformed edit breaks every
task at once.

Regenerating changes `digest_prompts` **and** `digest_tasks`, so runs before and
after are correctly marked as different. Commit before running anything —
`run_experiment.py` refuses a dirty tree.

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

### A known weakness, not yet fixed

The briefing says to verify identity "before disclosing or changing account
information" but never says that *reading an account back to the customer*
counts as disclosure. Seven of ten reviewed rollouts failed that blocker. Some
of that is probably our wording rather than the model's judgement, and it is the
obvious first prompt experiment to run.

---

## B. Keep two briefings and generate two task sets

`BANK_BRIEFING` and `BANK_FRONTMATTER` select which template
`tools/make_task.py` reads, so an alternative prompt becomes its own task set
rather than an edit you have to remember to undo:

```bash
cp prompts/briefing.md prompts/briefing-strict.md
$EDITOR prompts/briefing-strict.md

BANK_BRIEFING=briefing-strict.md \
  python tools/make_task.py $(cat tools/eligible_ids.txt) --out tasks-strict
python tools/check_oracles.py
```

Both sets stay in the tree, both are digested, and you can run them in either
order. Use this when the prompt change is large enough that you want to keep
comparing against it later.

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
benchflow eval compare-lift \
  --baseline jobs/<baseline-run> --trained jobs/<treatment-run> \
  --out lift.md --json-out lift.json
```

`compare-lift` matches rollouts by task and reports pass-rate and mean-reward
deltas with bootstrap confidence intervals. Pairing is what makes a 48-task set
usable: it cancels task difficulty, which is most of the variance. Comparing two
aggregate pass rates instead needs a much larger set to say anything.

Read the coverage table before the delta. Only tasks with a healthy scored
rollout on **both** sides enter the paired metrics, so a crash in one arm
silently drops that task.

If the interval includes zero, the experiment could not tell whether the change
helped. That is different from showing it did not help.

---

## Related

- `docs/02-tools.md` — changing what the agent can do
- `docs/03-skills.md` — adding reference material to its environment
- `docs/versioning-gaps.md` — what a run records, and what it does not
