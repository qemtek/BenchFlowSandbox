#!/usr/bin/env python3
"""Compare the agent's final database against the gold end state.

Gold is built by replaying the task's reference actions onto a fresh copy of
the seed database, using the same toolkit the agent drove. Comparison is by
tau2's own hash (sha256 over the sorted model dump), so any action sequence
producing an equivalent end state passes.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "/opt/bank/vendor")

from tau2.domains.banking_knowledge.data_model import TransactionalDB
from tau2.domains.banking_knowledge.tools import KnowledgeTools, KnowledgeUserTools


def build_gold(seed_path, gold_actions):
    """Replay the reference actions onto a fresh seed database.

    Each toolkit is created ONCE and reused, because some state - notably which
    discoverable tools have been unlocked - lives on the toolkit instance rather
    than in the database. Rebuilding per action would silently drop that state
    and produce a gold end state no agent could match.
    """
    db = TransactionalDB.load(str(seed_path))
    kits = {"assistant": KnowledgeTools(db), "user": KnowledgeUserTools(db)}
    problems = []
    for action in gold_actions:
        tk = kits.get(action.get("requestor", "assistant"), kits["assistant"])
        try:
            tk.use_tool(action["name"], **(action.get("arguments") or {}))
        except Exception as exc:
            problems.append(f"{action['name']}: {type(exc).__name__}: {exc}")
    return db, problems


def run():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--actual", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    actual_path = Path(args.actual)
    if not actual_path.is_file():
        (out / "reward.txt").write_text("0\n")
        print("FAIL: no database at " + str(actual_path), file=sys.stderr)
        return 1

    gold_db, problems = build_gold(
        Path(args.seed), json.loads(Path(args.gold).read_text())
    )

    try:
        actual_db = TransactionalDB.load(str(actual_path))
    except Exception as exc:
        (out / "reward.txt").write_text("0\n")
        print("FAIL: database unreadable: " + str(exc), file=sys.stderr)
        return 1

    gold_hash = gold_db.get_hash()
    actual_hash = actual_db.get_hash()
    match = gold_hash == actual_hash

    (out / "db_check.json").write_text(json.dumps({
        "db_match": match,
        "db_reward": 1.0 if match else 0.0,
        "gold_hash": gold_hash,
        "actual_hash": actual_hash,
        "gold_replay_problems": problems,
    }, indent=2))
    (out / "reward.txt").write_text(("1.0" if match else "0.0") + "\n")

    if problems:
        # A gold that cannot be replayed means the task itself is broken; say so
        # loudly rather than letting it read as an agent failure.
        print("WARNING: gold replay had problems:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)

    print("gold   " + gold_hash)
    print("actual " + actual_hash)
    print("PASS" if match else "FAIL: database end state differs")
    return 0 if match else 1


if __name__ == "__main__":
    raise SystemExit(run())
