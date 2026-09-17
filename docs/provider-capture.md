# Capturing the provider side of a run

`trajectory/llm_trajectory.jsonl` is BenchFlow's record of every call an agent
makes to the model API: the request, the response, the token usage, and the
model id that answered. It is written by BenchFlow's LiteLLM proxy, which
authenticates upstream with an API key, so it is skipped entirely when the
agent runs on a Claude subscription. BenchFlow states the rule in
`providers/litellm_runtime.py`: the only agents that skip the proxy are those
that cannot be routed through it, meaning `oracle`, which has no model, and
native subscription auth, which has no API key to proxy.

`tools/capture_proxy.py` writes that file for a subscription run. It is not on
by default; pass `--capture-provider` to `run_experiment.py`.

## Why this repository needed it

The gap was invisible until it was measured. `run_experiment.py` began logging
BenchFlow's own coverage counts in September 2026, and the first run reported
`missing_llm_trajectory: 1` out of 1 rollout. Checking earlier job directories
gave the same answer for every run this project had ever done. Nothing broke
that day. The loss was as old as the repository and had never been written
down, which is the failure this repository exists to avoid.

Switching to an API key would close it, and that is the wrong trade here. These
runs are personal testing on a Claude subscription that is already paid for. Two
measured rollouts of one task used about 9,000 and 11,000 output tokens each,
alongside roughly 2 million cache-read tokens, so a full pass over the 48 tasks
extrapolates to something near 500,000 output tokens and 100 million cache-read
tokens. Paying per token for work the subscription already covers, so that a
file gets written, is a bad exchange. The constraint is the subscription, and
the capture has to fit around it.

Two facts made that possible, both established by probe rather than by
argument. Claude Code presents its subscription token when `ANTHROPIC_BASE_URL`
points somewhere other than Anthropic, and it works the same way when handed a
dummy bearer while the real token is attached by the proxy. The first fact makes
capture possible at all. The second is why the capture also takes the
credential out of the sandbox.

The evidence matters most for the levers. This repository changes one thing
about an agent's environment at a time, and three of the five levers, prompts,
tools and skills, are changes to what the agent can see. A rollout records what
the agent did. Only the provider capture records what it was looking at when it
decided.

## What a run without it cannot tell you

Four kinds of evidence exist nowhere else in a rollout:

- The exact context window per turn: the full message array and the tool
  schemas as sent. Every lever this repository varies is a change to what the
  agent can see, and this is the direct record of it.
- Per-call token usage, rather than one total for the rollout.
- Provider failures and retries. A 429 in the middle of a rollout is otherwise
  invisible.
- Which snapshot answered. `provider_model` holds the resolved dated id. With
  no capture there is no dated id anywhere in a rollout, only the alias string
  passed on the command line.

Two BenchFlow commands read that file and nothing else, so both fail without
it: `benchflow train convert`, which builds trainer data, and
`benchflow eval continue`, which resumes a timed-out run by replaying recorded
responses.

## During the run

```
  ┌─ host ─────────────────────────────────────────────────────┐
  │                                                            │
  │  run_experiment.py                                         │
  │      │                                                     │
  │      ├─ starts ──► capture_proxy.py  :8787                 │
  │      │             ├ holds the OAuth token (from .env)     │
  │      │             └ knows one run secret                  │
  │      │                                                     │
  │      └─ benchflow eval run --agent-env …                   │
  │             │                                              │
  │  ┌─ docker sandbox ──────────────────┐                     │
  │  │  Claude Code (the agent)          │                     │
  │  │    ANTHROPIC_BASE_URL=            │                     │
  │  │      host.docker.internal:8787 ───┼──┐                  │
  │  │    ANTHROPIC_AUTH_TOKEN=<secret>  │  │ ① request +      │
  │  │    no real credential             │  │   run secret     │
  │  └───────────────────────────────────┘  │                  │
  │                                         ▼                  │
  │                                  capture_proxy             │
  │                             ② check secret, strip it       │
  │                             ③ attach real OAuth token      │
  │                             ⑤ log request + response ──┐   │
  └────────────────────────────────────│───────────────────│───┘
                                       │ ④                 ▼
                                       ▼            capture.jsonl
                              api.anthropic.com     (whole run, one file)
                                       │
                          SSE streamed straight back to the agent,
                          unbuffered, so the agent sees no change
```

The agent holds a per-run secret rather than the subscription token. The proxy
checks that secret, removes it, and attaches the real credential on the way
upstream. This is the property BenchFlow's own proxy has, where the raw
provider key never reaches the agent, and it is an improvement on the default
subscription path: without it the token is placed inside a container whose
tasks declare `network_mode: public`.

## After the run

```
  capture.jsonl ──► attribute ──► jobs/<run>/…/task-036__abc/
   (33 calls,       matches each      trajectory/llm_trajectory.jsonl
    one stream)     call to its                  │
                    rollout by the               ├─► benchflow train convert
                    <case_notes>                 ├─► benchflow review evidence
                    text in the                  └─► per-call usage, dated
                    request                          model, failures
                         │
                         └─► health.json regenerated
                             missing_llm_trajectory: 1 → 0
```

`health.json` is rewritten with BenchFlow's own writer rather than edited,
because it is produced during the run, before the trajectories exist, so its
`missing_llm_trajectory` count is stale by construction.

## How a call is matched to a rollout

One proxy serves the whole run, and Claude Code has no reason to announce which
task it is working on, so calls carry no rollout id. They are matched by
content: each task's `<case_notes>` block is echoed verbatim in the request body
of every call about that task.

A prefix of that block is not enough. task-045 and task-046 share their opening
word for word and diverge partway through a single utterance, so every prefix
length from 240 to 1000 characters maps both onto one key. The whole block
separates them: across the 48 tasks the full blocks give 48 distinct keys, and
no task's block appears inside another's, which is the condition a substring
match needs. Attribution therefore holds at any concurrency. A time window from
each rollout's `started_at` and `finished_at` is the fallback, used only when
exactly one rollout was running.

## What the proxy will not do

It listens on a port a sandboxed agent can reach, so its scope is fixed rather
than configurable:

- Upstream is hardcoded to `api.anthropic.com`. A client cannot redirect it, so
  the sandbox cannot use it to reach anything else.
- Only `POST /v1/messages*` is served. Everything else is refused.
- A request that does not present the run secret is refused before any upstream
  call is made.
- Credentials are never written to the capture or the logs.

## What it does not fix

Cost. A subscription call carries no price, so `response_cost` is recorded as
null rather than a fabricated zero, and `total_cost_usd` stays at 0.00. What
the capture adds is exact per-call token counts, which is the input an estimate
would need.

## Checking that it worked

```bash
python tools/run_experiment.py --tasks tasks/task-036 --capture-provider \
  --experiment plumbing --note "capture check"
```

Three signals, in increasing strength:

```bash
# 1. the calls were captured at all
wc -l jobs/<run>/capture.jsonl

# 2. BenchFlow agrees the trajectories are present and valid
#    (this metric is logged on the MLflow run as well)
grep missing_llm_trajectory jobs/<run>/**/health.json

# 3. the capture is faithful: one row per exchange, tool calls intact
benchflow train convert jobs/<run> -o /tmp/sft.jsonl --row-mode exchange \
  --manifest /tmp/manifest.json
```

On the first run of task-036 this gave 33 captured calls,
`missing_llm_trajectory` of 0 where every earlier run reported 1, and 33
exported rows of which 32 carried tool calls. The 37 tool calls in the export
match the 37 in the rollout's own `total_tool_calls`, which is what makes the
capture a record of the run rather than a parallel account of it.
