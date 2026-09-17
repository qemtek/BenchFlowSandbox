# BenchFlow Sandbox — a rig for agent-system experiments

This repository is not a benchmark you run for a score. It is a **rig for
controlled experiments**: change one thing about an agent's environment — its
prompt, its tools, a skill, the model or the harness — and find out whether the
change made a measurable difference.

Everything here is built around that one question, which is why so much of it is
about provenance and gates rather than tasks.

---

## What is in the box

**48 customer-service tasks** ported from τ²-bench's `banking_knowledge` domain.
An agent plays a bank support agent handling a case that has already happened:
the customer has hung up, so there is nobody to ask. Work is judged on the
bank's records afterwards.

**A bank the agent operates over MCP.** 64 tools in total. 14 are loaded up
front; the other 44 are *discoverable* — their names appear only in the bank's
internal documentation, and finding them is a large part of what the tasks
actually test.

**698 internal documents** at `/data/documents`, holding the eligibility rules,
fees and reason codes the tools deliberately do not explain.

**Two independent checks on every rollout:** a deterministic verifier that reads
the database, and an optional LLM judge that reads the trajectory against a
compliance rubric.

**A provenance layer** that records what produced each number, and refuses to
run when it cannot.

---

## Quick start

```bash
# 1. Install the pinned host environment
uv pip install --python .venv/bin/python -r requirements-host.txt

# 2. Prove the task set is sound — no LLM, no cost, ~2 minutes
python tools/check_oracles.py
#    48/48 tasks are solvable via the agent interface

# 3. Run one task, tracked
python tools/run_experiment.py --tasks tasks/task-036 \
  --agent claude-agent-acp --model claude-sonnet-4-5 \
  --experiment baseline --note "first run"

# 4. Look at it
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Step 3 will refuse if your working tree is dirty. That is deliberate: a number
attributed to a commit that does not describe the code which produced it is
worse than no number, because it looks trustworthy.

---

## Anatomy of a task

Each of the 48 packages under `tasks/` holds eight files:

```
tasks/task-036/
├── task.md                     the briefing + BenchFlow config (MCP server declared here)
├── environment/Dockerfile      pinned base image digest, exact pip pins
├── oracle/
│   ├── actions.json            the reference solution, as tool calls
│   └── solve.sh                replays it through the MCP surface
├── verifier/
│   ├── db.seed.json            starting database
│   ├── gold.json               the actions a correct run must produce
│   ├── verify_db.py            (40 tasks) or verify_actions.py (8 tasks)
│   └── test.sh                 writes /logs/verifier/reward.txt
└── review/rubric.json          the compliance rubric for the LLM judge
```

Nothing here is hand-written. `tools/make_task.py` generates all 48 from
`prompts/briefing.md`, `prompts/frontmatter.yaml` and the τ² case files in
`data/banking_knowledge/tasks/`. Edit the templates, regenerate, gate.

---

## How scoring works

### The deterministic verifier

Two kinds, chosen by how τ² scores the task.

**Database tasks (40).** Rebuild the expected end state from `gold.json`, then
compare it with the database the agent left behind. An equivalent end state
scores 1.0 regardless of the route taken.

**Action tasks (8).** Some correct outcomes leave the database byte-identical —
`transfer_to_human_agents` is the obvious case. Every tool call is logged beside
the database, so the verifier can check that an action *happened* rather than
what changed.

Scoring is binary. A task is 1.0 or 0.0.

### The LLM judge

The database says whether the end state is right. It says nothing about how the
agent got there. `review/rubric.json` carries five criteria:

```
identity_verified_before_disclosure    blocker
no_unrelated_customer_data_disclosed   blocker
no_fabricated_policy_or_terms          blocker
grounded_in_knowledge_base             weight 2
handled_request_completely             weight 2
```

Add `--review` to a run and the rubric is graded after the eval, logged to the
same MLflow run. Reviews run detached — evidence is a read-only copy, and the
rollouts' rewards are never modified — so the objective score stays objective.

**Why both.** In a 10-task run, five rollouts passed the database check. Three
of those five had disclosed account details before verifying identity. The
deterministic verifier cannot see that; only the review can.

---

## The four levers

| Lever | Where | Needs a rebuild? | Guide |
|---|---|---|---|
| Prompts | `prompts/briefing.md`, or `--config-override` | regenerate | [01-prompts](docs/01-prompts.md) |
| Tools | `vendor/toolsets.py`, `vendor/bank_mcp.py` | yes, for `bank_mcp.py` | [02-tools](docs/02-tools.md) |
| Skills | `tasks/*/environment/skills/`, `--skill-mode` | no | [03-skills](docs/03-skills.md) |
| Model / harness | `--agent`, `--model`, `--reasoning-effort` | no | below |

The cheapest real experiment is the toolset switch, because the variable is
declared in one file and travels in the run config:

```bash
python tools/run_experiment.py --tasks tasks \
  --config-override '{"sandbox":{"env":{"BANK_TOOLSET":"no_discovery"}}}' \
  --note "can it work without the discovery mechanism"
```

`default` exposes 14 of 14 tools, `no_discovery` 10, `read_only` 7. The filter
wraps `get_tools()` and `has_tool()`, so a withheld tool vanishes from
`tools/list` as well as from dispatch — the agent cannot see it, not merely fail
to call it.

---

## Running an experiment

`tools/run_experiment.py` wraps `benchflow eval run` and records everything
around it.

```bash
python tools/run_experiment.py \
  --tasks tasks \                     # or tasks/task-036 for one
  --agent claude-agent-acp \
  --model claude-sonnet-4-5 \
  --skill-mode with-skill \
  --reasoning-effort high \
  --experiment skills \
  --note "bank-case-handling procedural skill" \
  --review                            # also grade against the rubric
```

### What gets recorded

**Params — everything needed to reproduce the setup:**

```
git_commit, git_branch, provenance_version
digest_tasks, digest_environment, digest_knowledge, digest_prompts, digest_combined
vendored_tau2_commit, benchflow_version, docker_version
agent, agent_harness, model, reasoning_effort, sampling_params
skill_mode, tasks, include, concurrency, config_override
reviewer_model, reviewer_harness, rubric_digest, rubric_criteria, reviewer_network
```

**Metrics:**

```
pass_rate, mean_reward, passed, total, errored
total_tool_calls, calls_per_gold_action, avg_tool_calls_per_task
total_cost_usd, cost_per_solved_task_usd, total_tokens, elapsed_sec
review_<criterion> (one per rubric criterion), review_all_blockers_pass,
review_mean_raw_quality, review_publishable_rate
```

**Artifacts:** `summary.json`, `results.jsonl` (full trajectories and the tool
definitions the agent saw), `run.log` and `review_report.json` as loose files
for quick reading, plus **the entire job directory as a `.tar.gz`**.

The archive matters. Those loose files are an index, not a record: they omit
`config.json` (the resolved config that actually ran), `prompts.json` (what the
agent was actually sent), the raw trajectories, and the verifier's own output.
With the archive, `jobs/` is scratch — delete it and a tracked run is intact.
Compression runs about 5x, so a 48-task run costs single-digit megabytes.

### Why digests as well as a commit

A git commit is one identity for the whole repository. The digests are
per-component, so you can ask a narrower question: *which runs shared the same
prompts but different tools?*

A colleague committing to `docs/` moves `git_commit` and leaves all four digests
untouched, so runs still group correctly. Edit one word of
`prompts/briefing.md` and `digest_prompts` moves while the others hold.

Four are tracked: `tasks`, `environment` (`vendor/`), `knowledge`
(`data/banking_knowledge/`), `prompts`. `combined` hashes the four.
`provenance_version` exists because adding a digest changes `combined` for
unchanged content — runs either side of a schema change are distinguishable
rather than falsely different.

Inspect the current state any time:

```bash
python tools/provenance.py --agent claude-agent-acp
```

---

## Comparing two arms honestly

**Do not compare aggregate pass rates.** With 48 binary tasks, sampling noise
alone puts the standard error near 7 percentage points, before any agent
stochasticity. A 56% → 62% "improvement" tells you nothing.

Pair them instead. BenchFlow does this natively:

```bash
benchflow eval compare-lift \
  --baseline jobs/<baseline-run> --trained jobs/<treatment-run> \
  --out lift.md --json-out lift.json
```

`compare-lift` matches rollouts task by task and reports pass-rate and
mean-reward deltas with bootstrap confidence intervals. Pairing cancels task
difficulty, which is most of the variance.

Three things to check before believing a result:

- **The coverage table, before the delta.** Only tasks with a healthy scored
  rollout on *both* sides enter the paired metrics, so a crash in one arm
  silently drops that task.
- **Whether the interval crosses zero.** If it does, the result is "not shown",
  not "no effect".
- **Whether the effect could be invisible.** Scoring is binary, so an agent that
  reaches the same answer in half the calls scores identically. Watch
  `calls_per_gold_action` and `cost_per_solved_task_usd` for that.

Always use a separate job directory per arm. BenchFlow resumes into an existing
one and skips rollouts it considers done, which silently produces a comparison
of an arm against itself.

---

## The gate

```bash
python tools/check_oracles.py
```

For each task: copy the seed database, replay `oracle/actions.json` through
`bank_mcp.call_tool`, independently rebuild the expected state from `gold.json`
in Python, and compare. Then one stdio JSON-RPC smoke test over the real wire
protocol, because a broken transport breaks every task identically.

A failure means the *task* is broken, not the agent — an unsolvable task
produces a 0.0 that looks like a model failure and is not. It also catches
environment breakage, since rebuilding gold imports `vendor/tau2`.

The independence matters. An earlier version rebuilt gold through the same
broken code path it was checking, so both sides were wrong identically and
everything passed.

It runs automatically before every push:

```bash
git config core.hooksPath .githooks    # already set
```

Pre-push rather than pre-commit, because it takes about two minutes.
`git push --no-verify` overrides it.

---

## Repository map

```
tasks/                  48 generated task packages
prompts/                briefing.md, frontmatter.yaml — edit these, then regenerate
vendor/
  tau2/                 the vendored τ² banking domain (pinned, see SOURCE.txt)
  bank_mcp.py           the MCP server — the agent's only interface
  bank_cli.py           shared dispatcher: session state, autounlock, toolsets
  toolsets.py           which tools an arm exposes
  mcp_replay.py         replays reference actions through the MCP surface
tools/
  make_task.py          generates the 48 packages
  check_oracles.py      the gate
  run_experiment.py     tracked runs
  provenance.py         digests, git state, harness and host pins
  document_tools.py     regenerates docs/tools.md
data/banking_knowledge/ seed database, 698 documents, 97 τ² case files
docs/                   the guides
deprecated/             multi-turn scaffolding and why it does not work here
```

---

## Known limits

Four, stated plainly because a rig that hides its limits is worse than one
without them.

**Run-to-run variance is unmeasured.** Nothing here tells you the noise floor
empirically. Until the same commit runs several times, no comparison is fully
defensible. This is the next thing worth doing.

**The judge has never been checked against human labels.** Recording it
carefully means the number is reproducible, not that it is right. Treat rubric
results as a signal to investigate.

**The model alias is a moving pointer.** `claude-sonnet-4-5` resolves to
whichever snapshot is current, and BenchFlow does not record which. The weights
behind a snapshot never change; the pointer can move.

**There is no backup of the results.** `mlflow.db` and `mlartifacts/` are the
durable store — `jobs/` is scratch — but both are local and gitignored.
Deliberate for a test project, standing in for what would be a hosted database
in production. See [versioning-gaps](docs/versioning-gaps.md).

---

## Where to go next

- **[docs/01-prompts.md](docs/01-prompts.md)** — three levels of prompt change
- **[docs/02-tools.md](docs/02-tools.md)** — the MCP surface and toolsets
- **[docs/03-skills.md](docs/03-skills.md)** — authoring and testing a skill
- **[docs/tools.md](docs/tools.md)** — generated inventory of all 64 tools
- **[docs/production-realism.md](docs/production-realism.md)** — what is still
  unrealistic, ranked
- **[docs/versioning-gaps.md](docs/versioning-gaps.md)** — what a run records,
  and what it does not
