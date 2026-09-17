# Deprecated: multi-turn conversational tasks

BenchFlow's user loop is **progressive disclosure, not conversation**. Each round
is a fresh agent process (`connect_as` / `disconnect` per round in
`rollout/_user_loop.py`) that sees only the single string `user.run()` returns.
Workspace and database persist across rounds; the agent's identity, instructions
and conversation memory do not.

We built and ran a multi-turn variant of task_036. The loop worked — three
rounds fired, and withheld facts were released when the agent asked for them —
but the agent lost its role after round 0 and replied:

> I'm OpenCode, a coding assistant... It sounds like you might be trying to
> contact customer support about a credit card.

Rounds 1 and 2 made zero tool calls. Final reward 0.0.

`agent.prompt_prefix` does not fix it: it is applied once to
`self._resolved_prompts` (`rollout/__init__.py:997`), and the user loop bypasses
those entirely (`_user_loop.py:370`). Making this work means authoring each
round's prompt through a `BaseUser` subclass in the SDK, giving up
`benchflow eval run`.

Full analysis below.

These files are kept for reference. The live task set is single-turn only.

---

## Full analysis (2026-09-16)

Moved here from `docs/realism-roadmap.md` when that file was retired: its
three phases were all delivered, and completed plans are what git log is
for. This analysis is not recoverable from the code, so it stays.

### It is declarative, not SDK work

The roadmap originally scoped this as implementing a `BaseUser`. That was wrong.
A `user:` block in `task.md` frontmatter plus a `## user-persona` section is
enough — BenchFlow compiles it into a `DocumentNudgeUser` and runs the loop
itself. Verified:

```
status: supported | kind: scripted-linear | rounds: 6
facts: ('shipping address', 'shipping speed')
```

`model: scripted` needs no LLM for the user side, so a multi-turn run costs the
same as a single-turn one.

### The loop, in four lines

From `benchflow/rollout/_user_loop.py`:

```python
prompt = await user.run(round_num, instruction, round_result)  # :532
if prompt is None: break
await rollout.connect_as(role)                                 # :369
await rollout.execute(prompts=[prompt])                        # :370  agent runs here
await rollout.disconnect()                                     # :372
rewards, out, err = await rollout.soft_verify()                # :392
```

### The blocker: each round is a NEW agent process

`connect_as` / `disconnect` bracket every round, so the agent is destroyed and
recreated. It sees **only the single string `user.run()` returned** — nothing
else carries over.

Round 0 receives the full briefing. Round 1 receives only BenchFlow's fixed
template:

```
Additional user detail for shipping address: Please send the replacement to ...
```

With no role, no tools, and no policy, the agent answered as itself:

> I'm OpenCode, a coding assistant... It sounds like you might be trying to
> contact customer support about a credit card.

Result: rounds 1 and 2 made zero tool calls, final reward 0.0.

### What we author versus what BenchFlow authors

| Thing | Author | Agent sees it |
|---|---|---|
| `## prompt` body (`prompts/briefing-*.md`) | us | round 0 only |
| `## user-persona` + `private_facts` | us | never — drives the simulated user |
| per-round prompt | **BenchFlow** `DocumentNudgeUser` | every round after 0 |

We cannot change the round-1+ prompt; it is a fixed f-string in
`contracts/user.py`.

### The fix that does NOT work

`agent.prompt_prefix` looks like the answer — its description says it is
"prepended to each resolved task prompt". It is not enough. Traced:

```
config.py:571          AgentConfig.prompt_prefix
_setup.py:296          _apply_prompt_prefix()
rollout/__init__.py:997  called ONCE, on self._resolved_prompts
```

The user loop does not use resolved prompts:

```python
await rollout.execute(prompts=[prompt])   # _user_loop.py:370, prompt from user.run()
```

So the prefix decorates round 0 only — the round that already has the briefing.

### Why this is architectural, not a gap

The loop is called *progressive disclosure*, not conversation. From `_types.py`:

> BenchFlow provides **sandbox + instruction + observation** infrastructure. It
> does **not** orchestrate agent-internal loops... BenchFlow scenes define
> *turns* (prompts), not iteration.

`connect_as` / `disconnect` per round is deliberate. Across a round boundary:

- **persists:** workspace, database, files the agent wrote
- **does not persist:** the agent's identity, instructions, conversation memory

Good for "do work → learn more → do more work". Wrong for roleplay.

### What would actually work

1. **Carry context in the fact values** — we control those strings. Ugly, since
   they are meant to be the customer speaking, but needs no SDK.
2. **A `BaseUser` subclass via the SDK** — author every round's prompt directly.
   Means driving rollouts from Python instead of `benchflow eval run`.
3. **A wrapper user** delegating to `DocumentNudgeUser` and prepending a standing
   preamble to each returned prompt. Cleanest, ~15 lines, still SDK-driven.

**Recommendation: park it.** The single-turn arms work and score correctly.
Multi-turn here is information disclosure, not dialogue, and making it
conversational means leaving the CLI behind.

### Also note

The first generated version leaked the withheld work address into the prompt,
because the tau2 scenario spells it out. Multi-turn specs therefore carry an
explicit `opening:` message that replaces the scenario. Always grep the
generated `task.md` for a withheld value before running.
