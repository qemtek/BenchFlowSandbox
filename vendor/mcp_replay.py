#!/usr/bin/env python3
"""Replay a list of reference actions through the MCP tool surface.

Used by ``oracle/solve.sh`` inside the container and by
``tools/check_oracles.py`` on the host. Both need to prove the same thing: the
reference solution is reachable through the interface the agent actually has.

Before this, the oracle drove ``bank call <op> '<json>'`` — a CLI form the agent
no longer uses. A gate that exercises an interface nobody ships stops testing
what it claims to test, which is the failure we are trying to design out.

Assistant actions go through ``bank_mcp.call_tool``, the exact entry point the
MCP server dispatches to. User actions do not: they model the customer's side of
a dual-control task, the agent can never perform them, and the MCP surface
deliberately exposes only the assistant toolkit. Those replay against the user
toolkit directly, which is honest — they are scene-setting, not agent work.

    python mcp_replay.py actions.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

VENDOR = Path(__file__).resolve().parent
sys.path.insert(0, str(VENDOR))

import bank_cli  # noqa: E402
import bank_mcp  # noqa: E402


def to_mcp(action: dict) -> tuple[str, dict]:
    """Translate one gold action into an MCP tool call.

    tau2 records the 44 specialised operations as a ``call_discoverable_agent_tool``
    wrapper whose ``arguments`` is a JSON *string*. The MCP surface takes an
    object, so unpack it here rather than making every caller know.
    """
    name = action["name"]
    args = dict(action.get("arguments") or {})
    if name == "call_discoverable_agent_tool":
        inner = args.get("arguments") or "{}"
        if isinstance(inner, str):
            inner = json.loads(inner)
        return "bank_call_operation", {
            "operation": args.get("agent_tool_name", ""),
            "arguments": inner,
        }
    return name, args


def replay_user_action(action: dict) -> str:
    """Run an action the customer performs, against the user toolkit."""
    db = bank_cli._load()
    tk = bank_cli._toolkit(db, "user")
    args = action.get("arguments") or {}
    result = tk.use_tool(action["name"], **args)
    bank_cli._save(db)
    bank_cli._save_session(tk)
    bank_cli._log_call("user", action["name"], args)
    return result


def replay(actions: list[dict]) -> list[str]:
    out = []
    for action in actions:
        if action.get("requestor") == "user":
            out.append(replay_user_action(action))
            continue
        name, args = to_mcp(action)
        out.append(bank_mcp.call_tool(name, args))
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: mcp_replay.py <actions.json>", file=sys.stderr)
        return 2
    actions = json.loads(Path(sys.argv[1]).read_text())
    for action, result in zip(actions, replay(actions)):
        text = result if isinstance(result, str) else json.dumps(result, default=str)
        print(f"{action['name']}: {text[:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
