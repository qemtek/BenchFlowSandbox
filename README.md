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
  --agent claude-agent-acp --model claude-sonnet-4-6 \
  --experiment baseline --note "first run"

# 4. Look at it
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Step 3 will refuse if your working tree is dirty. That is deliberate: a number
attributed to a commit that does not describe the code which produced it is
worse than no number, because it looks trustworthy.

---

## Anatomy of a task

Each of the 48 packages under `tasks/` holds the same ten files:

```
tasks/task-036/
├── task.md                     the briefing + BenchFlow config (MCP server declared here)
├── environment/
│   ├── Dockerfile              pinned base image digest, exact pip pins
│   └── skills/bank-case-handling/SKILL.md
│                               deployed only under --skill-mode with-skill
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

Nothing here is hand-written. `tools/make_task.py` generates all 48 from the
`bank-briefing` prompt in MLflow's registry, `prompts/frontmatter.yaml` and the
τ² case files in `data/banking_knowledge/tasks/`. Change the source, regenerate,
gate.

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

The two kinds behave differently, and the difference matters when reading a
result.

A **blocker** is judged pass/fail and contributes no points. It acts as a veto.
A **weighted** criterion is scored on a small integer scale and multiplied by
its weight into the points total, so `raw_quality` is
`weighted_points / max_weighted_points`.

`gated_quality` is `raw_quality`, zeroed unless the deterministic verifier
passed *and* every blocker passed. That single number is the combined gate:
conduct and outcome both have to hold.

```
trial       deterministic  blockers   raw    gated
task-032    pass           FAIL       1.0  →  0.0    perfect quality, vetoed
task-008    FAIL           pass       0.75 →  0.0    clean conduct, wrong answer
task-012    pass           pass       1.0  →  1.0    the only combination that survives
```

Add `--review` to a run and the rubric is graded after the eval, logged to the
same MLflow run. Reviews run detached — evidence is a read-only copy, and the
rollouts' rewards are never modified — so the objective score stays objective.

**Why both.** In a 10-task run, five rollouts passed the database check. Three
of those five had disclosed account details before verifying identity. The
deterministic verifier cannot see that; only the review can.

---

## The five levers, and how to change one in isolation

| Lever | Switch | Both arms from one commit? | Rebuild? | Guide |
|---|---|---|---|---|
| Prompt | `--briefing-version N`, or `--config-override` | yes | yes | [01-prompts](docs/01-prompts.md) |
| Tools — which are exposed | `BANK_TOOLSET` via `--config-override` | yes | no | [02-tools](docs/02-tools.md) |
| Tools — what one does | edit `vendor/` | no | yes | [02-tools](docs/02-tools.md) |
| Skills | `--skill-mode` | yes | no | [03-skills](docs/03-skills.md) |
| Model / harness | `--agent`, `--model`, `--reasoning-effort` | yes | no | below |
| Environment | `DOCKERFILE` in `make_task.py`, the knowledge base | no | yes | below |

"Both arms from one commit" is the column that decides what an experiment
costs. A lever behind a flag is two runs from one working tree. A lever baked
into a file needs a second task set, or a checkout — and a checkout means the
arms differ by everything else that changed between those commits too.

Always give each arm its own `--jobs-dir`. BenchFlow resumes into an existing
one and skips rollouts it considers done, which silently compares an arm
against itself.

### The prompt

- **Switch.** Edit `bank-briefing` in the MLflow UI; saving creates the next
  version. Generate a second task set against it:
  `make_task.py … --briefing-version 2 --out tasks-v2`.
- **Arms.** `--tasks tasks` against `--tasks tasks-v2`. Both directories exist
  at once, so no checkout.
- **Recorded as** `briefing_prompt_uri`, `digest_tasks`.
- **Gate.** `check_oracles.py` must print 48/48 — `task.md` carries the MCP
  server declaration, so a malformed edit breaks every task at once.
- **Cheaper variant.** `--config-override '{"agent":{"prompt_prefix":"…"}}'`
  for a per-run nudge, no regeneration. Generic constraints only; task-specific
  solution content makes any lift meaningless.

### The tools

Two levers that get mistaken for each other.

**Which tools are exposed** — the cheapest real experiment here, because the
variable is declared in one file and travels in the run config:

```bash
python tools/run_experiment.py --tasks tasks \
  --config-override '{"sandbox":{"env":{"BANK_TOOLSET":"no_discovery"}}}' \
  --note "can it work without the discovery mechanism"
```

- **Arms.** One commit, no rebuild, no regeneration. `default` exposes 14 of
  14 tools, `no_discovery` 10, `read_only` 7.
- **Recorded as** `config_override`.
- **Why it is honest.** The filter wraps `get_tools()` and `has_tool()`, so a
  withheld tool vanishes from `tools/list` as well as from dispatch — the agent
  cannot see it, not merely fail to call it.

**What a tool does** — editing `vendor/tau2/…/tools.py` or `vendor/bank_mcp.py`:

- **Arms.** No flag exists, so two commits, one run each.
- **Rebuild.** Required. `vendor/` is copied in at build time, so an edit does
  nothing until the image rebuilds.
- **Recorded as** `digest_environment`.
- **Gate.** This is where `check_oracles.py` earns its keep: 48 replays through
  the real dispatch path plus a stdio smoke test, no LLM, about two minutes.

### The skills

- **Switch.** `--skill-mode no-skill` against `--skill-mode with-skill`.
- **Arms.** One commit, no rebuild, no regeneration. The cleanest lever here.
- **Recorded as** `skill_mode`, plus `skill_load_rate` and
  `skill_first_load_call_mean` as metrics. Needs `--capture-provider`.
- **Why the baseline is trustworthy.** Under `no-skill` BenchFlow deletes the
  bundled skills directory from the staged copy and strips its `COPY` lines, so
  a `COPY .` cannot leak it. Honest by construction rather than by trust.
- **Gate.** None. `check_oracles.py` never runs an agent, so this is the one
  lever with no cheap deterministic check. Budget for the rollouts.
- **Trap.** Deploying a skill makes it available, not used. Claude Code shows
  the model the skill's one-line description and reads the body only if the
  model asks; the 2026-09-17 arm offered one in 24 rollouts of 24 and had it
  opened in 6. Read `skill_load_rate` before anything else — below it, "it did
  not help" and "it was never read" are the same number. `total_skill_invocations`
  does not measure this and reads 0 either way.

### The model and harness

- **Switch.** `--agent`, `--model`, `--reasoning-effort`.
- **Arms.** One commit, no rebuild, no regeneration.
- **Recorded as** `agent`, `agent_harness`, `model`, `model_is_alias`,
  `reasoning_effort`, and — from the capture — `provider_model`, `max_tokens`,
  `thinking`, `thinking_budget_tokens`, `temperature`.
- **Trap.** Pass a dated model id. `claude-sonnet-4-6` is an alias, so a run
  recorded under it does not say which weights answered. The runner records
  `model_is_alias` either way, and `--capture-provider` recovers the resolved
  snapshot as `provider_model`, so a run is never silently ambiguous.
- **Trap.** Do not leave effort unset. The harness default enables extended
  thinking with a budget of 63999 against a `max_tokens` of 64000, which is
  close to `max`, and logs only "harness-default" — so a run at near-maximum
  reasoning looks unconfigured. The runner defaults to `medium` instead, and
  records what the provider actually received. Effort belongs with the model:
  two arms at different budgets are two different agents, and at the top of
  the range the agent can reason around a weak prompt, leaving a prompt or
  skill change no headroom to show up in.
- **Related.** `--trials N` reruns one arm through BenchFlow's `--matrix`, one
  nested run per trial, and puts the spread on the parent. That spread is the
  noise floor, and it is still unmeasured here.

### The environment

Three sub-levers, all more expensive than they look.

**The container** — base image, `ripgrep`, `jq`, the pinned pip versions. Edit
the `DOCKERFILE` constant in `make_task.py`, then regenerate. Two commits,
rebuild required, recorded in `digest_tasks` because the Dockerfile lives
inside the package. The base image is pinned by digest rather than tag:
`python:3.12-slim` is mutable and would otherwise change under you.

**How the agent searches the knowledge base** — τ² ships this as a ladder:
plain (no search), grep, shell (current — `ripgrep` is installed), and
KB-search (dense retrieval). Dropping a rung is one line of the Dockerfile.
Dense retrieval needs the retrieval chain vendored;
`vendor/tau2/domains/banking_knowledge/__init__.py` stubs it out.

**The knowledge base itself** — the 698 documents, recorded as
`digest_knowledge`. Handle with care: the documents name the discoverable
operations (`Use open_bank_account_4821`), so careless edits change the answer
key rather than the environment.

### Before you believe a comparison

```bash
python tools/compare_arms.py --baseline <run-id> --treatment <run-id> \
  --note "what moved"
```

It refuses a comparison whose arms did not ask the same questions. `compare-lift`
pairs rollouts by task id and will pair two tasks that share an id and nothing
else, so `compare_arms.py` runs `benchflow tasks overlap` over both runs' task
manifests first: a changed roster is refused, and so is a *subset* of task
packages differing, which no whole-set lever produces and which a stray
regeneration does. A prompt arm changes every task digest on purpose, and that
case is allowed because `briefing_prompt_uri` accounts for it.

---

## BenchFlow's commands, and what the wrapper adds

Everything here runs on BenchFlow. Use its commands directly whenever you are
poking around rather than recording a result:

```bash
benchflow eval run --tasks-dir tasks/task-036 --context-root . \
  --agent claude-agent-acp --model claude-sonnet-4-6 \
  --sandbox docker --jobs-dir jobs/scratch     # a throwaway run

benchflow eval list                            # completed evaluations
benchflow eval metrics --agent claude-agent-acp  # metrics from a jobs dir
benchflow eval view jobs/scratch               # the trajectory, in a browser
benchflow eval compare-lift --baseline A --trained B --out lift.md --json-out lift.json
benchflow review jobs/scratch --rubric tasks/task-036/review/rubric.json
```

`benchflow eval view` is the one to reach for when a result surprises you: it
renders the agent's trajectory as a page, which beats reading `results.jsonl`.

**What `tools/run_experiment.py` adds.** BenchFlow has no tracking layer — no
experiment store, no tags, no notes, and nothing that remembers one run in terms
of another. So the wrapper exists to record a run, not to replace one. It calls
`benchflow eval run` with the arguments above, and around that call it:

- refuses to start on a dirty working tree, or into a job directory that already
  holds results (BenchFlow would resume into it and skip rollouts it considers
  done, silently comparing an arm against itself)
- collects the content digests, the agent harness pin and the host lock, and
  logs them as MLflow params — asking BenchFlow for the task digests rather than
  recomputing them
- asks for the run's own coverage (`--health-summary-out`), resolved config
  (`--run-config-out`) and task manifest (`--task-manifest-out`), logs the
  counts as metrics, and asserts the task count with `--expected-tasks`
- logs pass rate, efficiency, cost and token metrics, each with the flag that
  says whether it is trustworthy
- optionally runs `benchflow review` and folds the judge's per-criterion results
  into the same run
- archives the whole job directory into that run
- with `--capture-provider`, records the provider side of every call, which
  BenchFlow cannot do under subscription auth

Everything the wrapper reads is a file it asked BenchFlow to write, at a path it
chose. That is a deliberate rule: the alternative — reading whatever the run
left in the directory and taking the newest — is a guess that holds until two
runs overlap.

**Repeats.** `--trials N` runs the same arm N times through BenchFlow's
`--matrix`, which gives every trial its own job directory. Each trial becomes a
nested MLflow run; the parent carries `pass_rate_mean`, `pass_rate_sd` and
`pass_rate_spread` across them. That spread is the noise floor, and a delta
between two arms smaller than it is not evidence of anything.

Use `benchflow eval run` when the answer is disposable. Use the wrapper when you
intend to cite the number later.

---

## Running an experiment

```bash
python tools/run_experiment.py \
  --tasks tasks \                     # or tasks/task-036 for one
  --agent claude-agent-acp \
  --model claude-sonnet-4-6 \
  --skill-mode with-skill \
  --reasoning-effort high \
  --experiment skills \
  --note "bank-case-handling procedural skill" \
  --review                            # also grade against the rubric
```

**Pass a dated model id if you want the snapshot pinned.** `claude-sonnet-4-6`
is an alias pointing at whichever snapshot is current, so a run recorded under
it does not say which weights answered. Dated ids pass straight through —
BenchFlow's own default is `claude-haiku-4-5-20251001` — so this is your choice,
not a constraint. The runner prints a note when the model looks like an alias
and records `model_is_alias` either way, so a run is never silently ambiguous.

### What gets recorded

**Params — everything needed to reproduce the setup:**

```
git_commit, git_branch, provenance_version
digest_tasks, digest_environment, digest_knowledge, digest_prompts, digest_combined
briefing_prompt_uri, briefing_prompt_version
vendored_tau2_commit, benchflow_version, docker_version
agent, agent_harness, model, model_is_alias, reasoning_effort
provider_model                      the dated snapshot that answered
max_tokens, thinking,               what the provider was actually sent,
thinking_budget_tokens,             read off the capture rather than from
temperature, top_p, top_k           what we asked the harness for
skill_mode, tasks, include, expected_tasks, concurrency, trials, config_override
jobs_dir                            the back-pointer: which directory produced it
reviewer_model, reviewer_harness, rubric_digest, rubric_criteria, reviewer_network
```

**Tags:** `dirty`, `note`, `provenance_complete` (false when a probe could not
read what it claims to record), `coverage_complete` (false when a rollout did
not score), `cost_priced` (false under subscription auth, where there is no
price source and `total_cost_usd` is 0.0 meaning *unpriced*, not *free*).

**Metrics:**

```
pass_rate, mean_reward, passed, total, errored
total_tool_calls, calls_per_gold_action, avg_tool_calls_per_task
total_cost_usd, cost_per_solved_task_usd, total_tokens, elapsed_sec
review_<blocker>_pass_rate          one per blocker criterion
review_<criterion>_mean_score       one per weighted criterion, on its own scale
review_all_blockers_pass
review_mean_raw_quality             weighted_points / max_weighted_points
review_mean_gated_quality           raw_quality, zeroed unless BOTH the
                                    deterministic verifier and every blocker passed
review_publishable_rate

health_total_rollouts, health_scored_rollouts, health_unscored_rollouts
health_zero_tool_rollouts           rollouts that made no tool call at all
health_missing_llm_trajectory, health_malformed_llm_trajectory
health_coverage                     scored / total — read this before the delta
telemetry_coverage                  whether the token counts can be believed
skill_load_rate                     separates "the skill did not help" from
                                    "the agent never opened it"
skill_first_load_call_mean          followed as a procedure, or consulted
                                    once already committed
total_skill_invocations             BenchFlow's own counter; reads 0 for
                                    Claude Code skills, kept for continuity
verifier_errored

trials_completed, pass_rate_mean, pass_rate_sd    with --trials N
pass_rate_min, pass_rate_max, pass_rate_spread
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
`prompts/frontmatter.yaml` and `digest_prompts` moves while the others hold.

The briefing is not covered by `digest_prompts`, because it is not a file — it
is a pinned version in MLflow's prompt registry, recorded per run as
`briefing_prompt_uri`. That is a stronger identifier than a directory hash: two
briefing variants in the tree would collide in one digest, whereas two versions
never collide.

Four are tracked: `tasks`, `environment` (`vendor/`), `knowledge`
(`data/banking_knowledge/`), `prompts`. `combined` hashes the four.

`tasks` is not ours to compute. BenchFlow digests a task package with
`task_digest()` — sha256 over every file in it — stamps the result into each
rollout's `config.json` and `result.json`, pins dataset releases with it, and
`benchflow review --tasks-root` recomputes it to decide whether a task may be
admitted as evidence. So `provenance.py` asks for it (`benchflow tasks digest
tasks/`, one digest per package, logged as an artifact) and aggregates the map
into `digest_tasks`. One algorithm, so our number, the per-rollout stamp and any
future `--dataset` pin agree by construction. The other three cover what no task
digest can reach: everything we moved out of the task packages via
`--context-root`.
`provenance_version` exists because adding a digest changes `combined` for
unchanged content — runs either side of a schema change are distinguishable
rather than falsely different.

Inspect the current state any time:

```bash
python tools/provenance.py --agent claude-agent-acp
```

---

## Capturing the provider side on a subscription

**Not on by default.** Add `--capture-provider` to a run:

```bash
python tools/run_experiment.py --tasks tasks --capture-provider \
  --experiment baseline --note "with provider capture"
```

### What it is for

BenchFlow writes `trajectory/llm_trajectory.jsonl` — the request and response of
every model call — by routing agents through its LiteLLM proxy. That proxy
authenticates upstream with an API key, so it is skipped entirely under
subscription auth: *"the only agents that skip the proxy are those that
physically cannot be routed through it — oracle (no model) and native
subscription auth (no API key to proxy)"*. The file is simply never written.

Four things go missing with it, and nothing else in the run records them:

- the exact context window per turn — the full message array and tool schemas
  as sent, which is the direct evidence for every lever this rig varies
- per-call token usage, rather than a rollout total
- provider failures and retries — a 429 mid-rollout is otherwise invisible
- **which snapshot answered.** `provider_model` is the resolved dated id. Without
  the capture there is no dated id anywhere in a rollout, only the alias we
  passed

It also blocks `benchflow train convert` outright, and `benchflow eval continue`,
both of which read that file and nothing else.

`tools/capture_proxy.py` fills the gap. Claude Code honours `ANTHROPIC_BASE_URL`
with subscription auth, so the agent's traffic is routed to a local proxy that
forwards verbatim to `api.anthropic.com` and writes the record BenchFlow would
have written.

### What the runner does with it

1. Starts the proxy on `--capture-port` (default 8787) with a per-run secret.
2. Points the sandbox at it — `ANTHROPIC_BASE_URL=http://host.docker.internal:<port>`
   and `ANTHROPIC_AUTH_TOKEN=<run secret>` — via `--agent-env`.
3. Runs the eval. Every call lands in `jobs/<run>/capture.jsonl`.
4. Splits that capture per rollout into `trajectory/llm_trajectory.jsonl`, matching
   calls to rollouts by the `<case_notes>` block echoed in each request. All 48
   task keys are distinct and none contains another, so this holds at any
   concurrency; a time window is the fallback.
5. Regenerates `health.json` with BenchFlow's own writer, so
   `health_missing_llm_trajectory` describes the run as it now stands.

Verified end to end on task-036: 33 exchanges captured, `train convert
--row-mode exchange` wrote 33 rows with 32 carrying tool calls, and the 37 tool
calls in the export match the rollout's own `total_tool_calls` exactly.

### It also takes the credential out of the sandbox

On a normal subscription run the token has to be inside the container for the
agent to authenticate, and these tasks run with `network_mode: public`. With
capture on, the proxy holds the token on the host: the sandbox gets a per-run
secret, the proxy checks it, strips it, and attaches the real credential on the
way upstream. That is the property BenchFlow's own proxy has — the raw
credential never reaches the agent.

The proxy is deliberately narrow, because it listens on a port a sandbox can
reach: upstream is hardcoded, so it cannot be redirected; only `POST
/v1/messages*` is proxied; a request without the run secret is refused before
any upstream call; and credentials are never written to the capture.

**Cost still reads 0.00.** A subscription call carries no price, so
`response_cost` is recorded as null rather than a fabricated zero. What the
capture adds is exact per-call token usage — the input for an estimate, if you
want one.

---

## Comparing two arms honestly

**Do not compare aggregate pass rates.** With 48 binary tasks, sampling noise
alone puts the standard error near 7 percentage points, before any agent
stochasticity. A 56% → 62% "improvement" tells you nothing. Worse, comparing two
arms independently needs a 29-point effect before it can reliably see anything.

Both figures are derived in
[docs/learnings/01-standard-error.md](docs/learnings/01-standard-error.md).

Pair them instead. BenchFlow does this natively:

```bash
benchflow eval compare-lift \
  --baseline jobs/<baseline-run> --trained jobs/<treatment-run> \
  --out lift.md --json-out lift.json --bootstrap-seed 0
```

`compare-lift` matches rollouts task by task and reports pass-rate and
mean-reward deltas with bootstrap confidence intervals. Pairing cancels task
difficulty, which is most of the variance, and roughly halves the effect size
you can detect. The mechanism — only the tasks the two arms *disagree* on carry
information — is in
[docs/learnings/02-paired-comparison.md](docs/learnings/02-paired-comparison.md).

**For a comparison you intend to cite, use the wrapper:**

```bash
python tools/compare_arms.py \
  --baseline <mlflow-run-id> --treatment <mlflow-run-id> \
  --note "no_discovery toolset"
```

It resolves each arm's job directory — from `jobs/` if it is still there, from
the run's archive if it is not, so a comparison survives deleting scratch — runs
`compare-lift` with a pinned bootstrap seed, and records the result as a third
MLflow run: both arms' ids and digests as params, the deltas and their intervals
as metrics, `lift.md` and `lift.json` as artifacts.

It also **refuses to compare arms whose `digest_tasks` or `digest_knowledge`
differ**. Those two are the measuring stick; if they moved, pairing by task id
compares two different questions. Digests that are meant to move — environment,
prompts — are reported as the lever under test rather than blocked. This is what
the split digests were for, and nothing read them until the comparison did.

Three things to check before believing a result. All three are now data on the
run rather than instructions to a reader — `health_coverage` and the
`coverage_complete` tag on each arm, the paired counts on the comparison:

- **The coverage table, before the delta.** Only tasks with a healthy scored
  rollout on *both* sides enter the paired metrics, so a crash in one arm
  silently drops that task. `compare_arms.py` prints how many tasks each arm
  contributed alone and tags the comparison `coverage_complete=false` when
  either number is not zero.
- **Whether zero falls inside the interval.** If it does, "no difference" is
  still a plausible answer, but so is a large improvement. The experiment could
  not tell which, and that is different from showing the change did not help.
- **Whether the effect could be invisible.** Scoring is binary, so an agent that
  reaches the same answer in half the calls scores identically. Watch
  `calls_per_gold_action` and `cost_per_solved_task_usd` for that.

Always use a separate job directory per arm. BenchFlow resumes into an existing
one and skips rollouts it considers done, which silently produces a comparison
of an arm against itself. `run_experiment.py` refuses to start in a job
directory that is not empty, and `--trials` gets its per-trial directories from
BenchFlow's `--matrix`, so neither path can make that mistake by hand.

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

## Changing the evaluation setup

The five levers above are things you change to test an agent. The rubric, the
briefing, a verifier and the metrics change too, and those changes move the
numbers just as much.

Every one of them gets a page in [docs/iterations/](docs/iterations/), written
**before** the change is made:

```
## The problem      what is wrong, with the evidence
## The change       what will be different, exact enough to implement from
## Baseline         the numbers before, and the run they came from
## Prediction       what should happen, stated so that it can fail
## How it is measured   the commands, and what the control arm is
## Result           the numbers after, and the run they came from
## Verdict          landed, reverted, or inconclusive
```

Four rules carry most of the value:

- **One variable per page.** A rubric fix and a briefing fix aimed at the same
  failure are two pages, or neither result is attributable.
- **Predict specifically enough to be wrong.** "Should improve the blocker pass
  rate" cannot fail; "six of the seven failures flip, and task-005 does not"
  can.
- **Re-grade rather than re-run where it applies.** A rubric or reviewer change
  can be measured against archived rollouts with `benchflow review`, at no cost
  in agent rollouts. A briefing, tool or skill change cannot.
- **Measure a control when the instrument is stochastic.** The reviewer is an
  LLM and disagrees with itself, so a new rubric is compared against the old
  rubric re-run on the same rollouts, not against the old report.

`docs/iterations/README.md` holds the full convention and the template.

---

## Repository map

```
tasks/                  48 generated task packages
prompts/
  briefing.seed.md      starting text for an empty registry; read once, not live
  frontmatter.yaml      task config for every task — edit this, then regenerate
vendor/
  tau2/                 the vendored τ² banking domain (pinned, see SOURCE.txt)
  bank_mcp.py           the MCP server — the agent's only interface
  bank_cli.py           shared dispatcher: session state, autounlock, toolsets
  toolsets.py           which tools an arm exposes
  mcp_replay.py         replays reference actions through the MCP surface
tools/
  make_task.py          generates the 48 packages
  register_briefing.py  seeds or imports a briefing into the prompt registry
  check_oracles.py      the gate
  run_experiment.py     tracked runs
  compare_arms.py       records a paired comparison, and guards what it compares
  skill_uptake.py       whether the agent opened the skill it was offered
  task_families.py      which tasks a per-procedure skill could affect
  provenance.py         digests, git state, harness and host pins
  capture_proxy.py      provider-side capture for subscription runs
  document_tools.py     regenerates docs/tools.md
data/banking_knowledge/ seed database, 698 documents, 97 τ² case files
docs/                   the guides
  learnings/            how to tell a result from a coincidence
  iterations/           one page per change to scoring or task text
deprecated/             multi-turn scaffolding and why it does not work here
```

---

## Known limits

Three, stated plainly because a rig that hides its limits is worse than one
without them.

**Run-to-run variance is unmeasured.** Nothing here tells you the noise floor
empirically yet. The mechanism now exists — `run_experiment.py --trials N` runs
one arm N times and records `pass_rate_sd` and `pass_rate_spread` across the
trials — but until it is actually run on a frozen task subset, no comparison is
fully defensible and no scored gate can set a threshold that means anything.
This is the next thing worth doing.

**The judge has never been checked against human labels.** Recording it
carefully means the number is reproducible, not that it is right. Treat rubric
results as a signal to investigate.

**There is no backup of the results.** `mlflow.db` and `mlartifacts/` are the
durable store — `jobs/` is scratch — but both are local and gitignored.
Deliberate for a test project, standing in for what would be a hosted database
in production. See [versioning-gaps](docs/versioning-gaps.md).

---

## Where to go next

- **[docs/learnings/](docs/learnings/)** — how to tell a result from a
  coincidence: standard error, paired comparison, bootstrapping
- **[docs/iterations/](docs/iterations/)** — the log of changes to scoring and
  task text, each with its baseline and its result
- **[docs/01-prompts.md](docs/01-prompts.md)** — three levels of prompt change
- **[docs/02-tools.md](docs/02-tools.md)** — the MCP surface and toolsets
- **[docs/03-skills.md](docs/03-skills.md)** — authoring and testing a skill
- **[docs/tools.md](docs/tools.md)** — generated inventory of all 64 tools
- **[docs/provider-capture.md](docs/provider-capture.md)** — recording what the
  model actually saw, on a subscription
- **[docs/production-realism.md](docs/production-realism.md)** — what is still
  unrealistic, ranked
- **[docs/versioning-gaps.md](docs/versioning-gaps.md)** — what a run records,
  and what it does not
