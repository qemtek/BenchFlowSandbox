# Guide: changing the prompt

> **Cost constraint: one task per run.**
> The OpenRouter key has a small monthly cap and a banking task costs roughly
> $0.15. Run a single task with `--tasks-dir tasks/<task-id>` and
> `--concurrency 1`. A full 40-task arm is ~$6 and would exhaust the balance in
> one command. Check `limit_remaining` at `https://openrouter.ai/api/v1/key`
> before and after.


The prompt is what the agent is told before it acts. There are two places to
change it, and which you pick depends on whether the change is part of the
benchmark or part of an experiment.

---

## A. Change the prompt for every task (baked in)

The prompt is generated, not hand-written. `briefing()` in
`tools/make_task.py` builds every task's `task.md` from the tau2 scenario.

```python
def briefing(task: dict) -> str:
    scenario = (task.get("user_scenario") or {}).get("instructions", "").strip()
    ...
```

Edit that function, then regenerate:

```bash
python tools/make_task.py $(cat tools/eligible_ids.txt) --out tasks
```

Use this when the change belongs to the task definition itself — how the work
order is framed, what the bank's policy says, how the tools are introduced.

### Why the framing matters

The first version of this prompt passed tau2's roleplay text through verbatim:

> **Your character:** You are Fatima Al-Hassan, a 31-year-old small business
> owner from Detroit...

The agent read that as a live conversation, replied politely asking the customer
to confirm her identity, and stopped. **Zero tool calls, reward 0.** There was
nobody to reply.

The fix was to frame it as a completed call:

> The call has already taken place... **the customer has hung up and cannot
> answer further questions.** Carry out the customer's request using
> `bank call`. Do not reply conversationally.

Same task, same tools, same model — 26 tool calls and a pass. If you are
flattening a multi-turn benchmark into single-turn, this is the failure to
watch for.

---

## B. Change the prompt for one run (not baked in)

`--config-override` deep-merges a patch into each task's resolved config, with
no file edits:

```bash
benchflow eval run --tasks-dir tasks/task-036 \
  --config-override '{"agent":{"prompt_prefix":"Always search /data/documents before calling a tool."}}' \
  --jobs-dir jobs/with-hint
```

`prompt_prefix` is prepended to every resolved prompt. BenchFlow records the
override **by content hash**, so the run is replayable and the variation is
part of the run's identity rather than a hidden edit.

This is the right mechanism for an experiment: one knob moves, everything else
stays fixed.

### The boundary on prompt_prefix

From the field's own description:

> Intended for generic harness constraints such as benchmark integrity rules;
> **must not contain task-specific solution content.**

So "search the documentation first" is fine. "The tool you need is
`order_replacement_credit_card_7291`" is not — that is leaking the answer, and
any lift you measure is meaningless.

---

## Running a prompt A/B

```bash
# baseline
benchflow eval run --tasks-dir tasks --jobs-dir jobs/prompt-base \
  --agent opencode --model openrouter/anthropic/claude-sonnet-4.5 \
  --concurrency 1

# treatment
benchflow eval run --tasks-dir tasks --jobs-dir jobs/prompt-hint \
  --agent opencode --model openrouter/anthropic/claude-sonnet-4.5 \
  --concurrency 1 \
  --config-override '{"agent":{"prompt_prefix":"..."}}'

# paired comparison with bootstrap CIs
benchflow eval compare-lift --baseline jobs/prompt-base --trained jobs/prompt-hint \
  --out lift.md --json-out lift.json
```

Always use a separate `--jobs-dir` per arm. BenchFlow resumes into an existing
job directory and will skip rollouts it considers already done — which silently
produces a comparison of one arm against itself.
