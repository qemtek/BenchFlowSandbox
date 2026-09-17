#!/usr/bin/env python3
"""Run every task's oracle and confirm it reaches that task's gold state.

This is the gate that catches broken tasks before they cost an agent run. Two
distinct failures show up here:

  unsatisfiable gold — replaying the reference actions raises, so no agent could
                       ever produce the gold end state (e.g. sentinel arguments)
  unreachable gold   — the gold replays fine, but driving the same actions
                       through the `bank` CLI lands somewhere else, meaning the
                       agent-facing interface cannot express the reference
                       solution

A task that passes here is known-solvable; a task that fails here would have
scored 0 for every agent and looked like a model failure.

Usage:  python tools/check_oracles.py [tasks_dir]
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
VENDOR = REPO / "vendor"
PYTHON = sys.executable


import re

# An opaque code used as a gold argument LOOKS like a placeholder, but in this
# domain it can be legitimate: task_005's gold logs "9K2X7M4P1N8Q3R5T6A" into
# every log_verification field, and doc_customer_support_special_support_codes_001
# instructs exactly that for an Account Recovery Bypass Code ("enter the bypass
# code in place of personal information"). Such a value is only suspicious when
# nothing in the knowledge base explains it — so check the documents before
# calling a task broken.
OPAQUE_CODE = re.compile(r"^[A-Z0-9]{12,}$")
DOCUMENTS = REPO / "data" / "banking_knowledge" / "documents"


def _documented(code: str) -> bool:
    """True if the knowledge base explains this code (so an agent could find it)."""
    if not DOCUMENTS.is_dir():
        return False
    return any(code in p.read_text(errors="ignore") for p in DOCUMENTS.glob("*.json"))


def undocumented_opaque_arguments(pkg: pathlib.Path) -> list[str]:
    """Gold arguments that are opaque codes with no supporting documentation."""
    found = []
    for action in json.loads((pkg / "verifier" / "gold.json").read_text()):
        for key, value in (action.get("arguments") or {}).items():
            if isinstance(value, str) and OPAQUE_CODE.match(value):
                if not _documented(value):
                    found.append(f"{action['name']}.{key}={value}")
    return found


def run_oracle(pkg: pathlib.Path, workdir: pathlib.Path) -> list[str]:
    """Replay the oracle's actions through the MCP surface, returning failures.

    In-process rather than over stdio JSON-RPC: this hits ``bank_mcp.call_tool``,
    the exact entry point the server dispatches to, so the tool logic is under
    test 48 times over. The transport is covered separately and once, by
    ``--smoke``, because a broken transport breaks every task identically.
    """
    db = workdir / "db.json"
    db.write_bytes((pkg / "verifier" / "db.seed.json").read_bytes())
    actions = json.loads((pkg / "oracle" / "actions.json").read_text())

    # bank_cli resolves its paths from BANK_DB at import time, so point it at
    # this task's scratch copy before the vendored modules load.
    os.environ["BANK_DB"] = str(db)
    proc = subprocess.run(
        [PYTHON, str(VENDOR / "mcp_replay.py"), str(pkg / "oracle" / "actions.json")],
        capture_output=True, text=True,
        env={**os.environ, "BANK_DB": str(db), "PATH": "/usr/bin:/bin",
             "HOME": str(workdir)},
    )
    if proc.returncode != 0:
        tail = (proc.stderr.strip().splitlines() or [""])[-1]
        names = [a["name"] for a in actions]
        return [f"mcp replay failed over {names[:3]} -> {tail[:140]}"]
    return []


def verify(pkg: pathlib.Path, workdir: pathlib.Path) -> dict:
    """Score the oracle's result with whichever verifier this task uses."""
    if (pkg / "verifier" / "verify_actions.py").is_file():
        return verify_actions(pkg, workdir)
    script = (pkg / "verifier" / "verify_db.py").read_text().replace(
        'sys.path.insert(0, "/opt/bank/vendor")', f'sys.path.insert(0, {str(VENDOR)!r})'
    )
    local = workdir / "verify_local.py"
    local.write_text(script)
    out = workdir / "logs"
    subprocess.run(
        [
            PYTHON, str(local),
            "--seed", str(pkg / "verifier" / "db.seed.json"),
            "--gold", str(pkg / "verifier" / "gold.json"),
            "--actual", str(workdir / "db.json"),
            "--out", str(out),
        ],
        capture_output=True,
        text=True,
    )
    report = out / "db_check.json"
    return json.loads(report.read_text()) if report.is_file() else {}


def verify_actions(pkg: pathlib.Path, workdir: pathlib.Path) -> dict:
    """ACTION-scored tasks are checked against the tool-call log, not end state."""
    out = workdir / "logs"
    subprocess.run(
        [
            PYTHON, str(pkg / "verifier" / "verify_actions.py"),
            "--gold", str(pkg / "verifier" / "gold.json"),
            "--calls", str(workdir / "db.calls.jsonl"),
            "--out", str(out),
        ],
        capture_output=True,
        text=True,
    )
    report = out / "action_check.json"
    if not report.is_file():
        return {}
    data = json.loads(report.read_text())
    # Present the same keys the DB path returns so main() needs no special case.
    return {
        "db_match": data.get("action_match"),
        "gold_replay_problems": [],
        "detail": f"{data.get('matched')}/{data.get('required')} actions",
    }


def smoke_transport(workdir: pathlib.Path) -> list[str]:
    """Exercise the real stdio JSON-RPC transport once.

    run_oracle() calls bank_mcp.call_tool in-process, which tests the tool logic
    48 times but never the wire protocol. A broken transport breaks every task
    identically, so it needs covering once, not once per task.
    """
    db = workdir / "smoke.json"
    db.write_bytes((REPO / "data" / "banking_knowledge" / "db.json").read_bytes())
    env = {**os.environ, "BANK_DB": str(db), "HOME": str(workdir)}
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "bank_search", "arguments": {"query": "close account"}}},
    ]
    proc = subprocess.run(
        [PYTHON, str(VENDOR / "bank_mcp.py")],
        input="\n".join(json.dumps(r) for r in requests) + "\n",
        capture_output=True, text=True, env=env, timeout=120,
    )
    replies = {}
    for line in proc.stdout.splitlines():
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if "id" in msg:
            replies[msg["id"]] = msg

    problems = []
    if 1 not in replies:
        problems.append("initialize returned nothing")
    tools = (replies.get(2, {}).get("result") or {}).get("tools") or []
    names = {t.get("name") for t in tools}
    for required in ("bank_search", "bank_describe_operation", "bank_call_operation"):
        if required not in names:
            problems.append(f"tools/list is missing {required}")
    body = json.dumps((replies.get(3, {}).get("result") or {}))
    if "close_bank_account" not in body:
        problems.append("tools/call bank_search did not find close_bank_account")
    if not problems:
        print(f"  smoke: stdio transport OK ({len(tools)} tools advertised)")
    return problems


def main() -> int:
    root = REPO / (sys.argv[1] if len(sys.argv) > 1 else "tasks")
    pkgs = sorted(p for p in root.iterdir() if (p / "oracle" / "solve.sh").is_file())

    ok, broken = [], []
    for pkg in pkgs:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = pathlib.Path(tmp)
            cli_failures = run_oracle(pkg, workdir)
            report = verify(pkg, workdir)

        match = report.get("db_match") is True
        gold_problems = report.get("gold_replay_problems") or []
        sentinels = undocumented_opaque_arguments(pkg)
        if match and not gold_problems and not sentinels:
            ok.append(pkg.name)
            print(f"  PASS  {pkg.name}")
        else:
            if gold_problems:
                reason = "gold unsatisfiable: " + "; ".join(gold_problems)[:160]
            elif sentinels:
                reason = "gold uses undocumented opaque arguments: " + "; ".join(sentinels)[:160]
            else:
                reason = "oracle does not reach gold"
            broken.append((pkg.name, reason, cli_failures))
            print(f"  FAIL  {pkg.name}  {reason}")

    with tempfile.TemporaryDirectory() as td:
        transport = smoke_transport(pathlib.Path(td))
    for problem in transport:
        print(f"  SMOKE FAIL  {problem}")

    print(f"\n{len(ok)}/{len(pkgs)} tasks are solvable via the agent interface")
    if broken:
        print(f"\n{len(broken)} broken task(s) — exclude these from runs:")
        for name, reason, cli in broken:
            print(f"\n  {name}: {reason}")
            for c in cli[:3]:
                print(f"      mcp: {c}")
    (REPO / "tools" / "oracle_report.json").write_text(
        json.dumps(
            {"ok": ok, "broken": [{"task": n, "reason": r} for n, r, _ in broken]},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
