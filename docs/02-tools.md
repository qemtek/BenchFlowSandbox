# Guide: changing the agent's tools

> **Cost constraint: one task per run.**
> The OpenRouter key has a small monthly cap and a banking task costs roughly
> $0.15. Run a single task with `--tasks-dir tasks/<task-id>` and
> `--concurrency 1`. A full 40-task arm is ~$6 and would exhaust the balance in
> one command. Check `limit_remaining` at `https://openrouter.ai/api/v1/key`
> before and after.


The agent reaches the bank through one command, `bank`, defined in
`vendor/bank_cli.py` and installed by each task's Dockerfile. Everything the
agent can do to the bank goes through it, so that file is the tool surface.

```
bank list                        every tool, with signature and summary
bank show <tool>                 full JSON schema for one tool
bank call <tool> '<json-args>'   invoke it
bank hash                        current database hash
bank --as user call <tool> ...   the customer's toolkit (dual-control tasks)
```

---

## A. Change which tools exist

`_toolkit()` decides what the agent gets:

```python
def _toolkit(db: TransactionalDB, requestor: str):
    tk = KnowledgeUserTools(db) if requestor == "user" else KnowledgeTools(db)
```

To withhold tools, filter what `get_tools()` returns or subclass
`KnowledgeTools`. To add one, add a method decorated with `@is_tool` — the
dispatcher is generic, so a new tool appears in `bank list` with no CLI changes.

The current agent surface is 14 tools. `KnowledgeTools` has 72 methods; only
the `@is_tool`-decorated ones are exposed.

---

## B. Change how the agent searches the knowledge base

This is the most interesting lever, because tau2 ships it as a designed ladder.
The 698 documents in `/data/documents` are where tool names are discovered, and
how the agent can search them is a capability you control:

| Variant | Capability | Needs an API |
|---|---|---|
| Plain | no search | no |
| Grep | keyword search over documents | no |
| Shell | agentic shell search (current setup) | no |
| KB-search | dense vector retrieval | yes — embeddings |

Today the Dockerfile installs `ripgrep`, giving the shell variant:

```dockerfile
RUN apt-get install -y --no-install-recommends ripgrep jq
```

Remove that line and the agent falls back to plain `grep`. To add dense
retrieval you must also vendor the retrieval chain — see
`vendor/tau2/domains/banking_knowledge/__init__.py`, which currently stubs it
out, and note that `KnowledgeToolsWithKBSearch` needs an embedding model
(`text-embedding-3-large`, or `qwen3-embedding-8b` via OpenRouter).

Same tasks, same scoring, one variable. That is the cleanest tools experiment
available here.

---

## C. Change how tools present themselves

The text of `bank list` and `bank show` is your code, and it measurably affects
behaviour. In one run the agent burned several turns discovering that
`call_discoverable_agent_tool` wants its `arguments` field as a JSON **string**,
not a nested object. Better examples in `cmd_show` would have saved them.

This counts as a tools intervention and is worth testing as one.

---

## Adding a genuinely new tool

To give the agent a capability the bank does not have — say a document
profiler:

1. Write the script, e.g. `vendor/kb_profile.py`
2. Install it in the Dockerfile:
   ```dockerfile
   RUN printf '#!/bin/sh\nexec python /opt/bank/vendor/kb_profile.py "$@"\n' \
       > /usr/local/bin/kb-profile && chmod +x /usr/local/bin/kb-profile
   ```
3. Mention it in the prompt — an agent will not discover an undocumented binary
4. Regenerate and rebuild

---

## Important: tool changes need a rebuild

`vendor/` is copied into the image at build time, so editing `bank_cli.py` has
no effect until the image is rebuilt. Prompt and skill changes can ride on
`--config-override` and `--skill-mode`; tool changes cannot.

Use a fresh `--jobs-dir` for the new arm so BenchFlow doesn't resume the old
rollouts and skip the work.

---

## A caution learned the hard way

Some toolkit state lives on the **object**, not in the database. Upstream keeps
one toolkit alive for a whole conversation; our CLI starts a new process per
command. When `unlock_discoverable_agent_tool` marked a tool unlocked in
`self._agent_discoverable_tools_state`, the next `bank call` had forgotten it,
and a correct agent scored 0 after 44 tool calls.

`bank_cli.py` now persists that state to `db.session.json` beside the database.
**If you add a tool that keeps state outside the DB, persist it the same way** —
otherwise the agent hits a wall that looks like its own failure.


---

## Lesson: a generic tool interface hides what the agent needs

Three separate bugs here came from the same instinct — writing one generic code
path over all 58 tools instead of surfacing what each tool actually declares.

**1. Nested JSON arguments.** `bank call` took a raw JSON blob, so calling a
discovered operation meant a JSON string inside a JSON object inside shell
quotes. An agent spent several turns getting the escaping right. Fixed by
generating flags from each tool's schema.

**2. Toolkit state lost between processes.** `unlock_discoverable_agent_tool`
marked a tool unlocked in memory; the next `bank` process had forgotten. A
correct agent scored 0 after 44 tool calls. Fixed by persisting to
`<db>.session.json`, then removed entirely by unlocking on demand.

**3. Enums discarded from `--help`.** The flag builder read only `type` from
each property, dropping `description`, `default` and `enum`. So
`bank transfer-to-human-agents --help` showed `--reason (string)` with no hint
that only 19 specific codes scored. Agents called the right operation with a
thoughtful summary and no reason code, and were marked wrong.

Measured effect of fixing #3 — same tasks, same agent, same model:

```
task-004   FAIL -> PASS
task-014   FAIL -> PASS
task-008   FAIL -> FAIL   (valid code chosen, but the wrong one)
```

What was deliberately NOT fixed: `compare_args` stays invisible, and the tool
description still says the reason codes live in the knowledge base. Finding the
right code still requires reading the documentation — that is the capability
under test. The fix only removed what was unguessable.

**Rule of thumb:** if the schema declares it, the agent should be able to see
it. A generic dispatcher is cheap to write and expensive for the agent to use.
