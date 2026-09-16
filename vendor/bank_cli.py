#!/usr/bin/env python3
"""`bank` — the agent's interface to the banking domain.

A generic dispatcher over the vendored tau2 banking toolkits. Every tool the
domain defines is reachable without hand-writing a wrapper per tool:

    bank list                             # every tool, with its signature
    bank show <tool>                      # full docstring for one tool
    bank call <tool> '<json-args>'        # invoke it

State lives in one JSON file (``$BANK_DB``, default /data/db.json). Each call
loads it, runs the tool, and writes it back, so the file on disk is always the
current database. That is what the verifier compares against the gold state.

The agent toolkit and the user toolkit share the database, matching tau2's
dual-control design. ``--as user`` dispatches against the user toolkit.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

VENDOR = Path(__file__).resolve().parent
sys.path.insert(0, str(VENDOR))

from tau2.domains.banking_knowledge.data_model import TransactionalDB  # noqa: E402
from tau2.domains.banking_knowledge.tools import (  # noqa: E402
    KnowledgeTools,
    KnowledgeUserTools,
)
from toolsets import allowed  # noqa: E402

DB_PATH = Path(os.environ.get("BANK_DB", "/data/db.json"))
# Which discoverable tools have been unlocked is toolkit-instance state upstream
# ("Check if the tool was unlocked (in-memory state)"), because tau2 keeps one
# toolkit alive for a whole conversation. Each CLI invocation is a new process,
# so that state has to be persisted next to the database or an unlock would be
# forgotten by the very next command.
SESSION_PATH = DB_PATH.with_name(DB_PATH.stem + ".session.json")
# Tool-call log — see _log_call().
CALLS_PATH = DB_PATH.with_name(DB_PATH.stem + ".calls.jsonl")


def _load() -> TransactionalDB:
    return TransactionalDB.load(str(DB_PATH))


def _save(db: TransactionalDB) -> None:
    db.dump(str(DB_PATH))


def _load_session() -> dict:
    if SESSION_PATH.is_file():
        try:
            return json.loads(SESSION_PATH.read_text())
        except json.JSONDecodeError:
            pass
    return {"agent": {}, "user": {}}


class _Filtered:
    """Wraps a toolkit so withheld tools are invisible and uncallable."""

    def __init__(self, tk, allowed_names: set[str]):
        self._tk = tk
        self._allowed = allowed_names

    def get_tools(self, include=None):
        return {
            k: v for k, v in self._tk.get_tools(include).items()
            if k in self._allowed
        }

    def has_tool(self, name: str) -> bool:
        return name in self._allowed and self._tk.has_tool(name)

    def __getattr__(self, item):
        return getattr(self._tk, item)


def _toolkit(db: TransactionalDB, requestor: str):
    tk = KnowledgeUserTools(db) if requestor == "user" else KnowledgeTools(db)
    session = _load_session()
    tk._agent_discoverable_tools_state = dict(session.get("agent") or {})
    tk._user_discoverable_tools_state = dict(session.get("user") or {})
    # BANK_TOOLSET names a set in toolsets.py; unset means every tool.
    names = allowed(os.environ.get("BANK_TOOLSET"), set(tk.get_tools()))
    return _Filtered(tk, names)


def _log_call(requestor: str, name: str, args: dict) -> None:
    """Append every successful tool call to a log beside the database.

    BenchFlow hands the verifier a container, not a trajectory — `test.sh` can
    only inspect end state. Some tasks are scored on whether an action happened
    rather than on what changed: `transfer_to_human_agents`, for instance, is a
    correct outcome that leaves the database byte-identical. Writing the calls to
    a file makes them part of the end state, so an action verifier can read them.
    """
    record = {"requestor": requestor, "tool": name, "arguments": args}
    with CALLS_PATH.open("a") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def _autounlock(tk, name: str, args: dict) -> None:
    """Unlock a discovered tool on demand, instead of requiring a separate call.

    Upstream makes the agent call `unlock_discoverable_agent_tool` before
    `call_discoverable_agent_tool`. Real systems authorise at call time, and the
    unlock is invisible to scoring — it mutates in-memory toolkit state only, so
    the database hash is identical before and after. Removing the ceremony
    therefore changes no reward, only friction.

    Explicit unlock still works, so the gold replay and oracle are unaffected.
    """
    if name != "call_discoverable_agent_tool":
        return
    tool = args.get("agent_tool_name")
    inner = getattr(tk, "_tk", tk)
    if not tool or not inner.has_discoverable_tool(tool):
        return
    state = inner._agent_discoverable_tools_state
    state.setdefault(tool, {"unlocked_at": "auto", "auto_unlocked": True})


def _save_session(tk) -> None:
    SESSION_PATH.write_text(
        json.dumps(
            {
                "agent": getattr(tk, "_agent_discoverable_tools_state", {}) or {},
                "user": getattr(tk, "_user_discoverable_tools_state", {}) or {},
            },
            indent=2,
            default=str,
        )
    )


def cmd_list(requestor: str) -> int:
    tk = _toolkit(_load(), requestor)
    tools = tk.get_tools()
    print(f"{len(tools)} tools available to '{requestor}':\n")
    for name in sorted(tools):
        tool = tools[name]
        doc = (getattr(tool, "short_desc", "") or "").strip().split("\n")[0]
        fn = (getattr(tool, "openai_schema", None) or {}).get("function", {})
        props = (fn.get("parameters") or {}).get("properties") or {}
        required = set((fn.get("parameters") or {}).get("required") or [])
        sig = ", ".join(p if p in required else f"[{p}]" for p in props)
        print(f"  {name}({sig})\n      {doc[:110]}")
    return 0


def cmd_show(requestor: str, name: str) -> int:
    tk = _toolkit(_load(), requestor)
    tools = tk.get_tools()
    if name not in tools:
        # Discoverable operations are not in get_tools() but are callable via
        # call_discoverable_agent_tool, so `show` must describe them as well.
        inner = getattr(tk, "_tk", tk)
        disc = inner.get_discoverable_tools()
        if name in disc:
            import inspect as _inspect
            fn = disc[name]
            params = [p for p in _inspect.signature(fn).parameters if p != "self"]
            print(f"{name}  (discoverable operation)\n")
            print(_inspect.getdoc(fn) or "")
            print("\ncall it with:")
            print(f"  bank call call_discoverable_agent_tool "
                  f"'{{\"agent_tool_name\": \"{name}\", \"arguments\": "
                  f"\"{{...}}\"}}'")
            print(f"  arguments keys: {', '.join(params)}")
            return 0
        print(f"No such tool: {name!r}. Try `bank list`.", file=sys.stderr)
        return 2
    tool = tools[name]
    schema = getattr(tool, "openai_schema", None)
    if schema:
        # The JSON schema carries description + parameter types + required set,
        # which is everything the agent needs to form a correct call.
        print(json.dumps(schema.get("function", schema), indent=2, default=str))
        return 0
    print(f"{name}\n")
    print((getattr(tool, "short_desc", "") or "").strip())
    print((getattr(tool, "long_desc", "") or "").strip())
    return 0


def cmd_call(requestor: str, name: str, raw_args: str) -> int:
    try:
        args = json.loads(raw_args) if raw_args else {}
    except json.JSONDecodeError as exc:
        print(f"Arguments must be a JSON object: {exc}", file=sys.stderr)
        return 2
    if not isinstance(args, dict):
        print("Arguments must be a JSON object, e.g. '{\"user_id\": \"u1\"}'",
              file=sys.stderr)
        return 2

    db = _load()
    tk = _toolkit(db, requestor)
    if not tk.has_tool(name):
        print(f"No such tool: {name!r}. Try `bank list`.", file=sys.stderr)
        return 2
    _autounlock(tk, name, args)
    try:
        result = tk.use_tool(name, **args)
    except Exception as exc:  # surface domain errors to the agent verbatim
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    # Persist only after a successful call so a failed tool cannot corrupt state.
    _save(db)
    _save_session(tk)
    _log_call(requestor, name, args)
    print(result if isinstance(result, str) else json.dumps(result, default=str))
    return 0


def cmd_search(requestor: str, query: str) -> int:
    """Search the operations registry, including tools not listed by `bank list`.

    The bank exposes a core toolkit plus a larger catalogue of specialised
    operations. Production systems let an agent query a registry for the
    operation it needs rather than hiding schemas in prose, so this returns
    matching names and descriptions from both.

    Finding the operation does NOT tell you how to use it correctly — eligibility
    rules, fees and policy live in /data/documents. Search here to locate the
    operation; read the documentation to perform it properly.
    """
    tk = _toolkit(_load(), requestor)
    inner = getattr(tk, "_tk", tk)
    terms = [t for t in query.lower().split() if t]

    catalogue = {}
    for name, tool in tk.get_tools().items():
        catalogue[name] = (getattr(tool, "short_desc", "") or "").strip()
    for name, fn in inner.get_discoverable_tools().items():
        catalogue[name] = (fn.__doc__ or "").strip().split("\n")[0]

    scored = []
    for name, desc in catalogue.items():
        haystack = f"{name} {desc}".lower().replace("_", " ")
        score = sum(1 for t in terms if t in haystack)
        if score:
            scored.append((score, name, desc))
    # Prefer entries matching every term; fall back to partial matches only when
    # nothing matches fully, so a two-word query does not return half the catalogue.
    full = [h for h in scored if h[0] == len(terms)]
    hits = full or scored
    hits.sort(key=lambda h: (-h[0], h[1]))

    if not hits:
        print(f"No operations match {query!r}. Try fewer or different words.")
        return 0
    print(f"{len(hits)} operation(s) matching {query!r}:\n")
    for _, name, desc in hits[:15]:
        print(f"  {name}\n      {desc[:120]}")
    print(
        "\nUse `bank show <name>` for parameters. Check /data/documents for the "
        "procedure before acting."
    )
    return 0



def _norm(name: str) -> str:
    """Tool names are underscored internally; the CLI accepts dashes too."""
    return name.replace("-", "_")


def _coerce(raw: str, kind):
    """Turn a flag string into the type the tool expects."""
    if kind in (bool, "boolean"):
        return raw.strip().lower() in ("1", "true", "yes", "y")
    if kind in (int, "integer"):
        return int(raw)
    if kind in (float, "number"):
        return float(raw)
    return raw


def _spec_for(tk, name: str):
    """Return (kind, {param: type, ...}, required) for a tool, or None.

    kind is "core" for tools callable directly, "discoverable" for the
    operations reached through call_discoverable_agent_tool.
    """
    import inspect

    inner = getattr(tk, "_tk", tk)
    tools = tk.get_tools()
    if name in tools:
        fn = (getattr(tools[name], "openai_schema", None) or {}).get("function", {})
        props = (fn.get("parameters") or {}).get("properties") or {}
        required = set((fn.get("parameters") or {}).get("required") or [])
        # Keep the whole property schema: it carries the description, any enum
        # of permitted values, and the default. Discarding those was why an
        # agent could call `transfer_to_human_agents` without knowing `reason`
        # had to be one of a fixed set — a correct action scored as a failure.
        return "core", props, required, (fn.get("description") or "")

    disc = inner.get_discoverable_tools()
    if name in disc:
        params, required = {}, set()
        for prm in inspect.signature(disc[name]).parameters.values():
            if prm.name == "self":
                continue
            ann = prm.annotation
            params[prm.name] = ann if ann is not inspect._empty else str
            if prm.default is inspect._empty:
                required.add(prm.name)
        return "discoverable", params, required, (disc[name].__doc__ or "")
    return None


def cmd_tool(requestor: str, name: str, argv: list[str]) -> int:
    """Invoke a tool through named flags: `bank change-user-email --user-id 1 ...`.

    Production CLIs take flags, not a JSON blob. Building the parser from each
    tool's own schema keeps this generic — no per-tool code — while giving the
    agent an interface that looks like every other command-line tool it knows.
    """
    import argparse

    name = _norm(name)
    db = _load()
    tk = _toolkit(db, requestor)
    spec = _spec_for(tk, name)
    if spec is None:
        print(f"No such operation: {name!r}. Try `bank search <words>`.",
              file=sys.stderr)
        return 2
    kind, params, required, description = spec

    parser = argparse.ArgumentParser(
        prog=f"bank {name.replace('_', '-')}",
        description=description.strip()[:600] or None,
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    enums = {}
    for param, pschema in params.items():
        if isinstance(pschema, dict):
            ptype = pschema.get("type", "string")
            choices = pschema.get("enum")
            desc = (pschema.get("description") or "").strip()
            default = pschema.get("default")
        else:  # discoverable tools expose python annotations, not JSON schema
            ptype, choices, desc, default = pschema, None, "", None
        bits = [f"({getattr(ptype, '__name__', ptype)})"]
        if desc:
            bits.append(desc)
        if default is not None:
            bits.append(f"default: {default}")
        if choices:
            enums[param] = list(choices)
            bits.append("one of: " + ", ".join(str(c) for c in choices))
        parser.add_argument(
            "--" + param.replace("_", "-"),
            dest=param,
            required=param in required,
            choices=choices or None,
            help="  ".join(bits),
        )
    try:
        parsed = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 2)

    def kind_of(param):
        s = params[param]
        return s.get("type", "string") if isinstance(s, dict) else s

    args = {
        k: _coerce(v, kind_of(k))
        for k, v in vars(parsed).items()
        if v is not None
    }

    if kind == "discoverable":
        # The underlying tool wants its arguments as a JSON string; that packing
        # is an implementation detail the agent should not have to perform.
        payload = {"agent_tool_name": name, "arguments": json.dumps(args)}
        _autounlock(tk, "call_discoverable_agent_tool", payload)
        try:
            result = tk.use_tool("call_discoverable_agent_tool", **payload)
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        _save(db)
        _save_session(tk)
        _log_call(requestor, name, args)
        print(result)
        return 0

    try:
        result = tk.use_tool(name, **args)
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    _save(db)
    _save_session(tk)
    _log_call(requestor, name, args)
    print(result if isinstance(result, str) else json.dumps(result, default=str))
    return 0


def cmd_hash(requestor: str) -> int:
    print(_toolkit(_load(), requestor).get_db_hash())
    return 0


USAGE = """usage:
  bank list                          list available tools
  bank search <words>                find an operation by what it does
  bank show <tool>                   show one tool's documentation
  bank <operation> --arg value       invoke an operation with flags
  bank call <tool> '<json-args>'     invoke a tool with raw JSON (fallback)
  bank hash                          print the current database hash

  --as user                          use the customer's toolkit instead of the agent's
"""


def main(argv: list[str]) -> int:
    requestor = "assistant"
    if "--as" in argv:
        i = argv.index("--as")
        try:
            requestor = argv[i + 1]
        except IndexError:
            print(USAGE, file=sys.stderr)
            return 2
        del argv[i : i + 2]

    if not argv:
        print(USAGE, file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]

    if cmd == "list":
        return cmd_list(requestor)
    if cmd == "show" and rest:
        return cmd_show(requestor, rest[0])
    if cmd == "call" and rest:
        return cmd_call(requestor, rest[0], rest[1] if len(rest) > 1 else "")
    if cmd == "search" and rest:
        return cmd_search(requestor, " ".join(rest))
    if cmd == "hash":
        return cmd_hash(requestor)
    # Anything else is treated as a tool name with flags.
    return cmd_tool(requestor, cmd, rest)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
