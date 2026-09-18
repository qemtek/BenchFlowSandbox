#!/usr/bin/env python3
"""Which tasks a per-procedure skill could possibly affect.

A skill about disputes cannot change a task that never files one. Including
those tasks in its comparison adds no effect and the agent's full run-to-run
noise, so the delta shrinks while the interval does not: four flips read as
+23.5pp on the 17 dispute tasks and +8.3pp on all 48, against standard errors
of roughly 6.2pp and 3.67pp. Fewer tasks, stronger signal.

That only holds if the subset is fixed before the run. Choosing "the dispute
tasks" after seeing where a skill helped selects on the outcome and
manufactures the effect. So the label comes from each task's own reference
actions in `verifier/gold.json` — what the task provably requires, decided
without running anything.

An operation in no family is an error rather than a default, because silently
dropping one shrinks a subset without saying so.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Operations are grouped by the procedure a customer case walks through, not
# by the object they touch: a task that files a dispute and one that reads its
# status are the same procedure seen at different points, and a skill about
# disputes speaks to both.
FAMILIES: dict[str, tuple[str, ...]] = {
    "disputes": (
        "file_debit_card_transaction_dispute",
        "file_credit_card_transaction_dispute",
        "get_user_dispute_history",
        "get_debit_dispute_status",
    ),
    "card-lifecycle": (
        "order_debit_card",
        "close_debit_card",
        "freeze_debit_card",
        "unfreeze_debit_card",
        "activate_debit_card",
        "reset_debit_card_pin",
        "order_replacement_credit_card",
        "get_pending_replacement_orders",
        "clear_debit_card_fraud_alert",
        "request_temporary_debit_card_limit_increase",
    ),
    "limit-increases": (
        "submit_credit_limit_increase_request",
        "approve_credit_limit_increase",
        "deny_credit_limit_increase",
        "get_credit_limit_increase_history",
    ),
    "open-close": (
        "open_bank_account",
        "close_bank_account",
        "log_credit_card_closure_reason",
        "get_closure_reason_history",
    ),
    "credits": (
        "apply_savings_account_credit",
        "apply_checking_account_credit",
        "apply_statement_credit",
        "submit_interest_discrepancy_report",
    ),
}

# Reads and lookups every procedure performs. They identify no procedure, so
# they belong to no family — but they are accounted for, which is what lets an
# unrecognised operation be an error.
SHARED_OPERATIONS = frozenset({
    "get_all_user_accounts_by_user_id",
    "get_bank_account_transactions",
    "get_debit_cards_by_account_id",
    "get_payment_history",
    "pay_credit_card_from_checking",
    "transfer_funds_between_bank_accounts",
    "apply_credit_card_account_flag",
    "emergency_credit_bureau_incident_transfer",
    "initial_transfer_to_human_agent",
})

# The smallest subset worth a paired comparison. Below this the bootstrap
# interval spans most of the range whatever the skill does, so a family under
# it is reported as untestable rather than quietly measured.
MIN_TASKS = 8

_SUFFIX = re.compile(r"_\d+$")


def task_operations(task_dir: Path) -> set[str]:
    """The discoverable bank operations a task's reference actions call.

    Names carry a numeric suffix that differs per task package, so it is
    stripped: `close_debit_card_4821` and `close_debit_card_7233` are the same
    operation.
    """
    gold = task_dir / "verifier" / "gold.json"
    if not gold.is_file():
        return set()
    return {
        _SUFFIX.sub("", action["arguments"]["agent_tool_name"])
        for action in json.loads(gold.read_text())
        if action.get("name") == "call_discoverable_agent_tool"
        and isinstance(action.get("arguments"), dict)
        and "agent_tool_name" in action["arguments"]
    }


def classify(tasks_root: Path) -> tuple[dict[str, list[str]], dict[str, set[str]]]:
    """Task ids per family, and every task's operations."""
    per_task = {
        d.name: task_operations(d)
        for d in sorted(tasks_root.glob("task-*"))
        if d.is_dir()
    }
    families = {
        name: sorted(t for t, ops in per_task.items() if ops & set(members))
        for name, members in FAMILIES.items()
    }
    return families, per_task


def unrecognised(per_task: dict[str, set[str]]) -> set[str]:
    known = SHARED_OPERATIONS.union(*(set(v) for v in FAMILIES.values()))
    return {op for ops in per_task.values() for op in ops} - known


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=REPO / "tasks")
    parser.add_argument("--family", help="print this family's task ids, one per line")
    parser.add_argument(
        "--include-flags",
        action="store_true",
        help="with --family, print as run_experiment.py --include flags",
    )
    args = parser.parse_args()

    families, per_task = classify(args.tasks)
    if not per_task:
        raise SystemExit(f"no task packages under {args.tasks}")

    stray = unrecognised(per_task)
    if stray:
        raise SystemExit(
            "operations in no family and not shared: "
            + ", ".join(sorted(stray))
            + "\nAdd each to FAMILIES or SHARED_OPERATIONS in this file. Leaving "
            "one out would shrink a subset without saying so."
        )

    if args.family:
        if args.family not in families:
            raise SystemExit(
                f"no family {args.family!r}; have: {', '.join(families)}"
            )
        ids = families[args.family]
        if args.include_flags:
            print(" ".join(f"--include {t}" for t in ids))
        else:
            print("\n".join(ids))
        return

    total = len(per_task)
    print(f"{'family':<18}{'tasks':>6}{'share':>8}   testable")
    for name, ids in families.items():
        ok = "yes" if len(ids) >= MIN_TASKS else f"no (under {MIN_TASKS})"
        print(f"{name:<18}{len(ids):>6}{len(ids) / total:>7.0%}   {ok}")

    claimed = {t for ids in families.values() for t in ids}
    overlap = sum(
        1 for t in per_task if sum(t in ids for ids in families.values()) > 1
    )
    print()
    print(f"  tasks total:            {total}")
    print(f"  in no family:           {total - len(claimed)}")
    print(f"  in more than one:       {overlap}")
    print(f"\nwrite a subset into a run with:\n"
          f"  python tools/run_experiment.py --tasks tasks "
          f"$(python tools/task_families.py --family disputes --include-flags) …",
          file=sys.stderr)


if __name__ == "__main__":
    main()
