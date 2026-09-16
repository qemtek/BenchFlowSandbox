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
import pathlib
import shlex
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
    """Drive oracle/solve.sh through the CLI, returning any failed steps."""
    db = workdir / "db.json"
    db.write_bytes((pkg / "verifier" / "db.seed.json").read_bytes())
    env = {"BANK_DB": str(db), "PATH": "/usr/bin:/bin", "HOME": str(workdir)}
    failures = []
    for line in (pkg / "oracle" / "solve.sh").read_text().splitlines():
        line = line.strip()
        if not line.startswith("bank"):
            continue
        argv = shlex.split(line)[1:]  # drop the literal "bank"
        proc = subprocess.run(
            [PYTHON, str(VENDOR / "bank_cli.py"), *argv],
            capture_output=True,
            text=True,
            env=env,
        )
        if proc.returncode != 0:
            failures.append(f"{argv[:2]} -> {proc.stderr.strip()[:120]}")
    return failures


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

    print(f"\n{len(ok)}/{len(pkgs)} tasks are solvable via the agent interface")
    if broken:
        print(f"\n{len(broken)} broken task(s) — exclude these from runs:")
        for name, reason, cli in broken:
            print(f"\n  {name}: {reason}")
            for c in cli[:3]:
                print(f"      cli: {c}")
    (REPO / "tools" / "oracle_report.json").write_text(
        json.dumps(
            {"ok": ok, "broken": [{"task": n, "reason": r} for n, r, _ in broken]},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
