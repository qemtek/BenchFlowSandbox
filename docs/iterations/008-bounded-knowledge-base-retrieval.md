# 008 — Bound knowledge retrieval before the next noise-floor run

Status: applied, awaiting runs  
Date: 2026-09-18  
Touches: `vendor/bank_mcp.py`, `prompts/briefing.seed.md`,
`prompts/frontmatter.yaml`, `tools/make_task.py`, `tools/check_oracles.py`, all
generated task packages  
Moves which digest: `digest_environment`, `digest_tasks`, `digest_prompts`

## The problem

Task 004 passed while taking a pathological route. After one customer lookup
had supplied the evidence needed to transfer the case, the agent made 40
terminal calls searching 698 JSON documents. Its first two searches returned
30,136 and 24,392 characters. The rollout recorded 2,285,709 cache-read tokens
and took 210 seconds.

The full failure analysis is in
[`issues/001-unbounded-knowledge-base-search.md`](../../issues/001-unbounded-knowledge-base-search.md).
The immediate operational consequence is that repeated noise-floor runs are
hitting token limits before the experiment finishes.

The old interface made an imprecise search maximally expensive: matching one
term in a JSON `content` field printed the whole field, and every later model
turn carried that output again.

## The change

Replace agent-facing shell search with two bounded MCP tools:

- `kb_search(query, limit=8)` uses local BM25-style keyword ranking and returns
  at most ten document IDs, titles and 260-character snippets.
- `kb_get(document_id)` returns one exact document selected from those results,
  capped at 8 KiB.

`bank_search` remains unchanged because it searches bank operations rather than
policy documents.

The briefing now requires `kb_search` followed by selective `kb_get`, forbids
terminal/filesystem knowledge-base retrieval, and tells the agent to stop once
it has the evidence needed for the next action. The task image moves the policy
store from the advertised `/data/documents` interface to the MCP server's
`/opt/bank/knowledge` path and stops installing `ripgrep` and `jq`.

The optional skill and review rubric use the same interface, so treatment and
review instructions do not steer the agent back to shell search.

This is bounded keyword RAG, not dense retrieval. The two-stage tool contract
is independent of the ranking algorithm; embeddings or hybrid ranking can be
tested later without changing how the agent retrieves a chosen document.

## Baseline

Observed rollout:

- task: `task-004`
- run: `claude-sonnet-4-6/trial-02/2026-09-18__17-06-39/task-004__da6fffd1`
- verifier reward: 1.0
- tool calls: 42 total, including 40 terminal calls
- provider cache-read tokens: 2,285,709
- agent execution: 210 seconds

The earlier noise-floor measurements are not controls for this change. Both the
prompt and image digest move, so the next noise floor must use fresh repeated
runs from the new task set.

## Prediction

For task 004, the transfer should still pass while using no terminal knowledge
searches, no individual knowledge result above 8 KiB, and no more than four
total tool calls.

Across the noise-floor task set:

- p95 token use per rollout decreases;
- p95 tool-result size decreases;
- fewer runs hit provider token limits;
- deterministic pass rate does not decrease.

The change fails if agents ignore the MCP tools and continue filesystem search,
or if bounded ranking omits documents needed to complete otherwise-solvable
tasks.

## How it is measured

Before paying for a rollout:

```bash
python tools/check_oracles.py
```

The smoke test now requires both KB tools over the real stdio MCP transport,
checks that replacement-card search finds the expected policy, and rejects an
oversized search response.

Then run two fresh, identical noise-floor passes with separate job directories
and the same task subset, model, agent, skill mode and reasoning effort. Compare:

- health coverage and provider-limit errors;
- pass rate and discordant tasks;
- total, cache-read and cache-creation tokens;
- average tool calls per task;
- task-004's trajectory and maximum KB result size.

Do not compare a new pass to a pre-008 run as if only sampling noise changed;
the retrieval environment is intentionally different.

## Result

Awaiting fresh runs.

## Verdict

Pending. Land immediately for the next noise-floor pair because the previous
interface is preventing the measurement from completing; retain only if oracle
coverage and outcome quality remain intact.
