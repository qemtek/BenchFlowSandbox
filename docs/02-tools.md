# Guide: changing the agent's tools

The agent reaches the bank over MCP and nothing else. `vendor/bank_mcp.py` is
the tool surface; each task's `task.md` declares it:

```yaml
sandbox:
  mcp_servers:
    - name: bank
      transport: stdio
      command: python
      args: ['/opt/bank/vendor/bank_mcp.py']
```

17 tools are advertised: the 14-tool core toolkit, plus three that reach the 44
specialised operations.

```
bank_search              find an operation by describing what you want
bank_describe_operation  read its signature: arguments, types, defaults
bank_call_operation      run it
```

`vendor/bank_cli.py` is still in the tree, but it is no longer an interface. It
is the shared dispatcher `bank_mcp.py` imports for session state, autounlock and
toolset filtering, and it is not on `PATH` inside the image.

`docs/tools.md` is the generated inventory of all 64 tools with source
locations. Regenerate it with `python tools/document_tools.py` after any change
here.

---

## A. Change which tools an arm exposes

`vendor/toolsets.py` is the switch. Nothing else needs editing:

```python
TOOLSETS = {
    "default":      None,
    "no_discovery": {"exclude": {"unlock_discoverable_agent_tool", ...}},
    "read_only":    {"include": {"get_current_time", ...}},
}
```

Select one per run — no rebuild, no regeneration:

```bash
python tools/run_experiment.py --tasks tasks \
  --config-override '{"sandbox":{"env":{"BANK_TOOLSET":"no_discovery"}}}' \
  --note "can it work without the discovery mechanism"
```

Add a toolset by adding a key. The filter wraps `get_tools()` and `has_tool()`,
so a withheld tool disappears from `tools/list` as well as from dispatch — the
agent cannot see it, not merely fail to call it.

**This is the cheapest real tools experiment available here**, because the
variable is declared in one file and recorded in the run config.

---

## B. Change what a tool does, or add one

Tool implementations live in `vendor/tau2/domains/banking_knowledge/tools.py`
(agent) and `user_tools.py` (customer). A method decorated `@is_tool` is
exposed; the other methods are internal.

`bank_mcp.py` builds MCP definitions generically from each tool's
`openai_schema`, so a new `@is_tool` method appears in `tools/list` with no
changes to the server.

To add a tool the bank does not have at all — say a document profiler — put it
in `vendor/` and expose it as an MCP tool in `bank_mcp.py`'s `list_tools()` and
`call_tool()`. Then mention it in the briefing: an agent will not use a tool it has not
been told about. That means a new `bank-briefing` version and a regenerate —
see `docs/01-prompts.md`.

**Tool changes need a rebuild.** `vendor/` is copied into the image at build
time, so editing it has no effect until the image rebuilds. Prompt changes ride
on `--config-override` and skills on `--skill-mode`; tool changes do not.

---

## C. Change how the agent searches the knowledge base

tau2 ships this as a designed ladder. The 698 documents in `/data/documents` are
where operations are discovered, and how the agent may search them is a
capability you control:

| Variant | Capability | Needs an API |
|---|---|---|
| Plain | no search | no |
| Grep | keyword search over documents | no |
| Shell | agentic shell search (current setup) | no |
| KB-search | dense vector retrieval | yes — embeddings |

The Dockerfile installs `ripgrep`, giving the shell variant. Remove that line
and the agent falls back to plain `grep`. Dense retrieval needs the retrieval
chain vendored — `vendor/tau2/domains/banking_knowledge/__init__.py` stubs it
out, and `KnowledgeToolsWithKBSearch` needs an embedding model.

Same tasks, same scoring, one variable.

---

## Testing a tool change

**1. Rebuild is implicit, but the gate is not.**

```bash
python tools/check_oracles.py
```

Runs every oracle through `bank_mcp.call_tool` — the exact entry point the
server dispatches to — and finishes with one stdio JSON-RPC smoke test over the
real wire protocol. Must print `48/48` and `smoke: stdio transport OK`.

This is the check that matters most for tool work, because it exercises the tool
layer 48 times without an LLM, for free, in about two minutes. The pre-push hook
runs it too.

**2. Inspect the surface directly.**

```bash
BANK_DB=/tmp/scratch.json python -c "
import sys; sys.path.insert(0,'vendor')
import bank_mcp
print(bank_mcp.call_tool('bank_describe_operation', {'operation':'transfer_to_human_agents'}))"
```

Faster than a rollout for checking that a tool presents itself the way you
intended.

**3. Read what the agent actually did.**

```bash
benchflow eval view jobs/<run>
```

Renders the trajectory as a page, which beats reading `results.jsonl` when you
want to know why a tool change did not land the way you expected.

**4. Then measure.** A job directory per arm — `run_experiment.py` gives each
run its own and refuses a directory that already holds results — then
`tools/compare_arms.py`. A toolset switch moves `digest_environment` and nothing
else, which is exactly what the comparison should report as the lever. See
`docs/01-prompts.md` for the pairing argument.

---

## Two rules learned the hard way

### If the schema declares it, the agent should be able to see it

Three separate bugs came from the same instinct — one generic code path over all
64 tools instead of surfacing what each tool declares.

**Nested JSON arguments.** The old CLI took a raw JSON blob, so calling a
discovered operation meant a JSON string inside a JSON object inside shell
quoting. An agent spent several turns getting the escaping right. MCP takes an
object, which is the whole reason it replaced the CLI.

**Enums discarded.** The flag builder read only `type` from each property,
dropping `description`, `default` and `enum`. `transfer_to_human_agents` showed
`--reason (string)` with no hint that only 19 codes scored. Agents called the
right operation with a thoughtful summary and no reason code, and were marked
wrong. Fixing it flipped task-004 and task-014 from FAIL to PASS.

**Signatures invisible over MCP.** `bank_search` returned argument *names* only
for the 44 discoverable operations. `bank_describe_operation` now returns the
full signature.

What was deliberately *not* fixed: `compare_args` stays invisible, and the tool
description still says the reason codes live in the knowledge base. Finding the
right code still requires reading the documentation — that is the capability
under test. The fixes removed only what was unguessable.

### If a tool keeps state outside the database, persist it

Some toolkit state lives on the object, not in the database. Upstream keeps one
toolkit alive for a whole conversation. When `unlock_discoverable_agent_tool`
marked a tool unlocked in `self._agent_discoverable_tools_state`, a later call
had forgotten, and a correct agent scored 0 after 44 tool calls.

State now persists to `db.session.json` beside the database, and unlocking
happens on demand. Add a stateful tool and you must do the same, or the agent
hits a wall that looks like its own failure.

### A third, found on 2026-09-17

Converting the oracle gate from the CLI to MCP immediately exposed that
`bank_mcp.py` never wrote the tool-call log. All eight ACTION-scored tasks were
unpassable over MCP and had been since the MCP server was written. A gate that
tests an interface nobody ships cannot find this. If you add a code path the
agent uses, make the gate use it too.

---

## Related

- `docs/tools.md` — generated inventory of all 64 tools
- `docs/01-prompts.md` — telling the agent about a tool
- `docs/03-skills.md` — teaching it a procedure instead
