#!/usr/bin/env python3
"""Score a task on WHICH ACTIONS the agent performed, not on end state.

Some correct outcomes change nothing. `transfer_to_human_agents` is the clearest
case: escalating an unverifiable customer is right, and leaves the database
byte-identical, so an end-state verifier cannot see it at all.

BenchFlow hands the verifier a container rather than a trajectory, so the
actions have to be part of the end state. `bank` appends every successful call
to <db>.calls.jsonl; this reads that log.

An action matches when the tool name matches and every argument the task marked
`compare_args` matches. Extra calls are allowed — the agent may look things up
on the way — but every required action must appear.
"""

import argparse
import json
import sys
from pathlib import Path


def matches(required, actual):
    if required["name"] != actual.get("tool"):
        return False
    want = required.get("arguments") or {}
    got = actual.get("arguments") or {}
    # compare_args restricts which arguments must agree; absent means all of them.
    keys = required.get("compare_args")
    if keys is None:
        keys = list(want)
    return all(str(got.get(k)) == str(want.get(k)) for k in keys)


def run():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--calls", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    gold = json.loads(Path(args.gold).read_text())
    calls_path = Path(args.calls)
    calls = []
    if calls_path.is_file():
        for line in calls_path.read_text().splitlines():
            if line.strip():
                calls.append(json.loads(line))

    checks = []
    for required in gold:
        found = any(matches(required, c) for c in calls)
        checks.append({"action": required["name"], "matched": found})

    matched = sum(1 for c in checks if c["matched"])
    reward = 1.0 if matched == len(checks) and checks else 0.0

    (out / "action_check.json").write_text(json.dumps({
        "action_match": reward == 1.0,
        "action_reward": reward,
        "matched": matched,
        "required": len(checks),
        "checks": checks,
        "calls_seen": len(calls),
    }, indent=2))
    (out / "reward.txt").write_text(("1.0" if reward else "0.0") + "\n")

    for c in checks:
        print(("  OK   " if c["matched"] else "  MISS ") + c["action"])
    print(f"{matched}/{len(checks)} required actions performed ({len(calls)} calls seen)")
    print("PASS" if reward else "FAIL: required actions missing")
    return 0 if reward else 1


if __name__ == "__main__":
    raise SystemExit(run())
