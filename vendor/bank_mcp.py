#!/usr/bin/env python3
"""MCP server exposing the bank's operations as structured tools.

Phase 3 of docs/realism-roadmap.md. The CLI makes the agent compose JSON inside
shell quoting:

    bank call call_discoverable_agent_tool '{"agent_tool_name":"x","arguments":"{\\"user_id\\": \\"1\\"}"}'

No deployed agent works that way — it calls a tool against a schema. This serves
the same dispatcher over MCP so BenchFlow can wire it in through
``[[sandbox.mcp_servers]]``, giving the agent real tool definitions.

Both interfaces stay available, which makes CLI-versus-MCP a clean experiment:
same tasks, same scoring, one variable.

Speaks MCP over stdio using JSON-RPC 2.0 — stdlib only, no SDK.
"""

from __future__ import annotations

import inspect
import json
import os
import sys
from pathlib import Path

VENDOR = Path(__file__).resolve().parent
sys.path.insert(0, str(VENDOR))

import bank_cli  # noqa: E402  (reuse the dispatcher, session and toolset logic)

PROTOCOL_VERSION = "2024-11-05"


def _core_tools() -> list[dict]:
    """The always-available toolkit, as MCP tool definitions."""
    tk = bank_cli._toolkit(bank_cli._load(), "assistant")
    out = []
    for name, tool in sorted(tk.get_tools().items()):
        fn = (getattr(tool, "openai_schema", None) or {}).get("function", {})
        out.append(
            {
                "name": name,
                "description": (getattr(tool, "short_desc", "") or "").strip(),
                "inputSchema": fn.get("parameters")
                or {"type": "object", "properties": {}},
            }
        )
    return out


def _search_tool() -> dict:
    return {
        "name": "bank_search",
        "description": (
            "Find a bank operation by what it does. The bank runs many more "
            "operations than are listed here; search returns matching names and "
            "descriptions. Finding an operation does not tell you how to use it "
            "correctly — eligibility rules, fees and policy live in "
            "/data/documents."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What you need to do"}
            },
            "required": ["query"],
        },
    }


def _call_discovered_tool() -> dict:
    return {
        "name": "bank_call_operation",
        "description": (
            "Run one of the specialised operations found with bank_search. "
            "Arguments are passed as a plain object, not a string."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "description": "Operation name"},
                "arguments": {
                    "type": "object",
                    "description": "Arguments for the operation",
                },
            },
            "required": ["operation"],
        },
    }


def list_tools() -> list[dict]:
    return _core_tools() + [_search_tool(), _call_discovered_tool()]


def _run_search(query: str) -> str:
    tk = bank_cli._toolkit(bank_cli._load(), "assistant")
    inner = getattr(tk, "_tk", tk)
    terms = [t for t in query.lower().split() if t]
    catalogue = {
        n: (getattr(t, "short_desc", "") or "").strip()
        for n, t in tk.get_tools().items()
    }
    for n, f in inner.get_discoverable_tools().items():
        catalogue[n] = (f.__doc__ or "").strip().split("\n")[0]

    scored = []
    for name, desc in catalogue.items():
        hay = f"{name} {desc}".lower().replace("_", " ")
        s = sum(1 for t in terms if t in hay)
        if s:
            scored.append((s, name, desc))
    full = [h for h in scored if h[0] == len(terms)]
    hits = sorted(full or scored, key=lambda h: (-h[0], h[1]))[:15]
    if not hits:
        return f"No operations match {query!r}."
    lines = [f"{len(hits)} operation(s) matching {query!r}:"]
    for _, name, desc in hits:
        params = ""
        disc = inner.get_discoverable_tools()
        if name in disc:
            keys = [p for p in inspect.signature(disc[name]).parameters if p != "self"]
            params = f"  (arguments: {', '.join(keys)})"
        lines.append(f"  {name}{params}\n      {desc[:140]}")
    lines.append("\nCheck /data/documents for the procedure before acting.")
    return "\n".join(lines)


def call_tool(name: str, arguments: dict) -> str:
    db = bank_cli._load()
    tk = bank_cli._toolkit(db, "assistant")

    if name == "bank_search":
        return _run_search(arguments.get("query", ""))

    if name == "bank_call_operation":
        # The whole point of the MCP surface: take arguments as an object and do
        # the JSON-string packing the underlying tool expects ourselves.
        op = arguments.get("operation", "")
        inner_args = arguments.get("arguments") or {}
        payload = {
            "agent_tool_name": op,
            "arguments": json.dumps(inner_args),
        }
        bank_cli._autounlock(tk, "call_discoverable_agent_tool", payload)
        result = tk.use_tool("call_discoverable_agent_tool", **payload)
        bank_cli._save(db)
        bank_cli._save_session(tk)
        return result

    if not tk.has_tool(name):
        return f"Error: no such tool {name!r}."
    result = tk.use_tool(name, **arguments)
    bank_cli._save(db)
    bank_cli._save_session(tk)
    return result


def respond(rid, result=None, error=None) -> None:
    msg = {"jsonrpc": "2.0", "id": rid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method")
        rid = req.get("id")

        if method == "initialize":
            respond(rid, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "bank", "version": "1.0"},
            })
        elif method == "notifications/initialized":
            continue  # notification: no response
        elif method == "tools/list":
            respond(rid, {"tools": list_tools()})
        elif method == "tools/call":
            params = req.get("params") or {}
            try:
                text = call_tool(params.get("name", ""), params.get("arguments") or {})
                respond(rid, {"content": [{"type": "text", "text": str(text)}]})
            except Exception as exc:
                # Surface domain errors as tool results, not protocol errors, so
                # the agent can read and recover from them.
                respond(rid, {
                    "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                    "isError": True,
                })
        elif rid is not None:
            respond(rid, error={"code": -32601, "message": f"unknown method {method}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
