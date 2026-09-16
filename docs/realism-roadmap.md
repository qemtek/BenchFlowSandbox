# Making the banking tasks a better model of production

> **Cost constraint: one task per run.**
> The OpenRouter key has a small monthly cap and a banking task costs roughly
> $0.15. Run a single task with `--tasks-dir tasks/<task-id>` and
> `--concurrency 1`. A full 40-task arm is ~$6 and would exhaust the balance in
> one command. Check `limit_remaining` at `https://openrouter.ai/api/v1/key`
> before and after.


The τ²-bench banking tasks measure something real — can an agent find the right
operating procedure and execute it correctly — but they wrap it in mechanics no
production system has. This is the plan for closing that gap without redesigning
the tasks themselves.

**The constraint throughout:** task definitions, gold actions, the database and
the scoring stay untouched. Only the layers we own change — the tool interface,
the prompt, and the environment. After each change, `tools/check_oracles.py`
must still report 40/40, which proves scoring is unaffected.

---

## What is artificial today, and what is not

The agent starts with 14 tools. A further 44 are hidden: it must find the tool
name in `/data/documents`, call `unlock_discoverable_agent_tool`, then
`call_discoverable_agent_tool`.

**Artificial:**

- `order_replacement_credit_card_7291` — no real API uses a random numeric
  suffix. It exists so the name cannot be guessed.
- The separate unlock step — real systems authorise at call time.
- Tools hidden behind prose — a real registry exposes schemas programmatically.

**Not artificial:** the underlying capability. The replacement-card document
also carries eligibility rules, shipping fees by card tier, and a policy that
fraud cases get expedited shipping. An agent that guessed the tool name but
skipped the document would ship standard, charge the wrong fee and miss the
fraud guidance. The tool name is a **tripwire proving the agent read the
procedure**.

So the proxy is "did you find the magic string". The capability is "did you
follow the operating procedure". The work below keeps the capability and
replaces the proxy.

---

## Phase 1 — Drop the unlock ceremony

**Status: DONE** — `_autounlock()` in `vendor/bank_cli.py`. Oracle gate 40/40 after.

Unlock is invisible to scoring. Verified directly:

```
hash before unlock:  af324a7d72aced5889daf6cc044e573ad94ffa3bfe7cf65114fd3cfed5daaa48
hash after unlock:   af324a7d72aced5889daf6cc044e573ad94ffa3bfe7cf65114fd3cfed5daaa48
```

It mutates only in-memory toolkit state, never the database. So the CLI can
unlock on demand when a discovered tool is called, and every gold hash stays
identical.

**Why:** removes the least realistic mechanic in the system. Production
authorises at call time. It also removes pure friction — one observed rollout
spent roughly 18 of its 44 tool calls fighting the unlock/call sequence.

**Change:** a few lines in `vendor/bank_cli.py`.

**Risk:** none to scoring, verified above. Gold replay still performs the
explicit unlock, so the reference path is unchanged either way.

---

## Phase 2 — Replace grep-the-manual with a tool registry

**Status: DONE** — `bank search` in `vendor/bank_cli.py`; `bank show` now
resolves discoverable operations too. Oracle gate 40/40 after.

Add a search command over the 44 discoverable tools:

```
bank search "replacement card"    → matching tool names + schemas
```

The agent still has to determine what it needs and search for it — that is the
real capability. What disappears is "did you locate the magic string in prose".

**Why:** this is how MCP tool search and dynamic tool loading actually work, so
it models production rather than proxying it. Large organisations genuinely
cannot fit every internal operation in an agent's context; something must
retrieve the relevant subset.

**Change:** one new command in `vendor/bank_cli.py` searching tool names and
descriptions.

**Tasks unchanged** — the agent still calls the same tool with the same
arguments, so gold hashes hold.

**Worth measuring:** run the current setup against the phase 1+2 version. The
difference tells you how much of the score rested on the tripwire rather than on
procedure-following. That number is the point of doing this.

---

## Phase 3 — Structured tool calls instead of shell JSON

**Status: DONE** — `vendor/bank_mcp.py` (stdio JSON-RPC, stdlib only).
Generated as a parallel arm in `tasks-mcp/` via
`prompts/frontmatter-mcp.yaml` + `prompts/briefing-mcp.md`. Verified to reach
the gold hash through structured calls with no shell quoting.

The agent currently composes this:

```bash
bank call call_discoverable_agent_tool '{"agent_tool_name":"...","arguments":"{\"user_id\": \"890389b165\"}"}'
```

A JSON string inside a JSON object inside shell quoting. No deployed agent works
this way; it calls a tool with a schema. BenchFlow supports that natively
through `[[sandbox.mcp_servers]]`, which maps to ACP specs at runtime.

**Why:** matches how agents are actually deployed, and removes friction we have
already watched cost real tool calls — the agent repeatedly got the nested
escaping wrong before working it out.

**Change:** an MCP server wrapping the same dispatcher. The CLI stays, so both
interfaces exist.

**Bonus:** CLI versus MCP becomes a clean tools experiment in its own right —
same tasks, same scoring, one variable. If escaping friction is costing real
performance, that comparison shows it.

---

## Deferred — worth doing, not as tweaks

### Multi-turn with a user simulator

**Status: ATTEMPTED — loop works, agent loses its role. See findings below.**

The largest realism gap. Real customer service is a conversation; we flattened
it into a briefing where "the customer has hung up and cannot answer further
questions".

This is not a tweak. It needs BenchFlow's `BaseUser` contract
(`benchflow/contracts/user.py`), whose `run(round, instruction, round_result)`
returns the next prompt or `None` to stop — a genuine simulator loop, with the
previous round's trajectory and rewards available.

**Why it is worth real effort:** it would unlock the 49 of 97 tasks currently
out of scope, the ones whose gold actions are performed by the *customer* rather
than the assistant. Those are tau2's dual-control design and cannot be reached
without a simulator.

`DocumentNudgeUser` already ships with persona plus private facts revealed only
when the agent asks — close in shape to tau2's `user_scenario`.

### Injected tool failures

Production tools time out, return stale data, and fail partially. Injecting that
would test recovery behaviour, which nothing here currently measures.

**Deferred because** it changes task difficulty, so scores stop being comparable
with earlier runs. Worth doing as an explicitly separate arm with its own
baseline rather than as a modification to the existing tasks.

---

## Order of work

| Phase | Change | Scoring impact | Effort |
|---|---|---|---|
| 1 | unlock on demand | none (verified) | DONE |
| 2 | `bank search` registry | none | DONE |
| 3 | MCP interface | none | DONE |
| later | multi-turn simulator | unlocks 49 more tasks | large |
| later | injected failures | changes difficulty | medium |

After each phase: `python tools/check_oracles.py` must report 40/40, then run a
single task end to end before moving on.


---

## Running the two arms

Phases 1 and 2 changed `tasks/` in place. Phase 3 produced a parallel arm, so
the comparison is available now:

```bash
# CLI arm
benchflow eval run --tasks-dir tasks --context-root . \
  --agent opencode --model openrouter/anthropic/claude-sonnet-4.5 \
  --jobs-dir jobs/cli --concurrency 1

# MCP arm — same tasks, same scoring, structured tool calls
benchflow eval run --tasks-dir tasks-mcp --context-root . \
  --agent opencode --model openrouter/anthropic/claude-sonnet-4.5 \
  --jobs-dir jobs/mcp --concurrency 1

benchflow eval compare-lift --baseline jobs/cli --trained jobs/mcp \
  --out lift-interface.md --json-out lift-interface.json
```

Task ids match across both arms, so `compare-lift` pairs them correctly.


---

## Multi-turn findings (2026-09-16)

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
