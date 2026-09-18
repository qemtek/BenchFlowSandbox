#!/usr/bin/env python3
"""Whether the agent opened a skill, and when.

A skill is offered to Claude Code as a one-line description in the system
prompt; the body arrives only if the model calls the `Skill` tool. Offering a
skill and using one are therefore different events, and a comparison that
assumes they are the same measures the baseline on every rollout that declined.

BenchFlow's `total_skill_invocations` counts ACP events with `kind == "skill"`.
Claude Code emits the load as `kind: "other"`, `title: "Load skill"`, so the
count is zero however many times the skill was opened. Counting the ACP title
instead is also wrong: in the 2026-09-17 with-skill arm it found five of the
six loads, because one rollout's ACP stream omitted a call that the provider
capture recorded.

So this reads the capture. `offered` is the skill listing in the request;
`opened` is a `Skill` tool call in the response; `first_call` is the call that
returned it, which says whether the skill was followed as a procedure or
consulted once the agent was already committed.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Collection, Iterator
from dataclasses import dataclass, field
from pathlib import Path

SKILL_LISTING = "The following skills are available for use with the Skill tool"


@dataclass
class Rollout:
    task: str
    rollout: str
    calls: int = 0
    offered: set[str] = field(default_factory=set)
    opened: list[tuple[int, str]] = field(default_factory=list)

    @property
    def first_call(self) -> int | None:
        return self.opened[0][0] if self.opened else None

    @property
    def names(self) -> list[str]:
        return sorted({name for _, name in self.opened})


def _offered_skills(body: dict) -> Iterator[str]:
    """Skill names from the availability listing, wherever it sits."""
    for block in _text_blocks(body):
        if SKILL_LISTING not in block:
            continue
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("- ") and ":" in line:
                yield line[2:].split(":", 1)[0].strip()


def _text_blocks(body: dict) -> Iterator[str]:
    system = body.get("system")
    if isinstance(system, str):
        yield system
    elif isinstance(system, list):
        for part in system:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                yield part["text"]
    for message in body.get("messages", []):
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            yield content
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    yield part["text"]


def _skill_calls(body: dict) -> Iterator[str]:
    for part in body.get("content", []):
        if not isinstance(part, dict) or part.get("type") != "tool_use":
            continue
        if part.get("name") != "Skill":
            continue
        skill = (part.get("input") or {}).get("skill")
        yield skill if isinstance(skill, str) else "?"


def read_rollout(trajectory: Path, only: Collection[str] | None = None) -> Rollout:
    directory = trajectory.parents[1]
    task = directory.name.split("__")[0]
    roll = Rollout(task=task, rollout=directory.name)
    for index, line in enumerate(trajectory.open(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        roll.calls += 1
        request = (record.get("request") or {}).get("body") or {}
        for name in _offered_skills(request):
            if only is None or name in only:
                roll.offered.add(name)
        response = (record.get("response") or {}).get("body") or {}
        for name in _skill_calls(response):
            if only is None or name in only:
                roll.opened.append((index, name))
    return roll


def read_job(job: Path, only: Collection[str] | None = None) -> list[Rollout]:
    return sorted(
        (read_rollout(p, only) for p in job.rglob("llm_trajectory.jsonl")),
        key=lambda r: r.rollout,
    )


def summarise(rollouts: list[Rollout]) -> dict:
    offered = [r for r in rollouts if r.offered]
    opened = [r for r in rollouts if r.opened]
    positions = [r.first_call for r in opened]
    return {
        "skill_rollouts_total": len(rollouts),
        "skill_rollouts_offered": len(offered),
        "skill_rollouts_opened": len(opened),
        "skill_load_rate": round(len(opened) / len(offered), 3) if offered else 0.0,
        "skill_loads_total": sum(len(r.opened) for r in opened),
        "skill_first_load_call_mean": (
            round(sum(positions) / len(positions), 1) if positions else None
        ),
        "skill_first_load_call_max": max(positions) if positions else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path, help="a jobs/<run> directory")
    parser.add_argument(
        "--skill",
        action="append",
        help="restrict to this skill name; repeatable. Without it every skill "
        "the sandbox offers is counted, including the dozen Claude Code ships "
        "with, which is rarely what you want",
    )
    parser.add_argument("--json", action="store_true", help="summary only, as JSON")
    args = parser.parse_args()

    rollouts = read_job(args.job, set(args.skill) if args.skill else None)
    if not rollouts:
        raise SystemExit(f"no llm_trajectory.jsonl under {args.job}")
    summary = summarise(rollouts)

    if args.json:
        print(json.dumps(summary, indent=2))
        return

    print(f"{'task':<12}{'calls':>6}{'offered':>9}{'opened':>8}{'at call':>9}")
    for r in rollouts:
        at = r.first_call if r.first_call else "-"
        print(
            f"{r.task:<12}{r.calls:>6}{len(r.offered):>9}"
            f"{len(r.opened):>8}{at:>9}"
        )
    print()
    for key, value in summary.items():
        print(f"  {key}: {value}")


def sampling_settings(job_dir: Path) -> dict:
    """What the agent was actually configured to do, read off the wire.

    `--reasoning-effort` is a request to the harness, and when it is not passed
    the run records "harness-default", which says what we did not set rather
    than what happened. The harness's default is not mild: it enables extended
    thinking with a budget of 63999 against a 64000 `max_tokens`, so a run that
    looks unconfigured is in fact running at close to maximum reasoning.

    Comparing two arms at different thinking budgets would be comparing two
    agents, so the value belongs beside the pass rate. It is taken from the
    first captured request, which is the request as the provider received it.
    """
    trajectory = next(job_dir.rglob("llm_trajectory.jsonl"), None)
    if trajectory is None:
        return {}
    for line in trajectory.open():
        if not line.strip():
            continue
        record = json.loads(line)
        body = (record.get("request") or {}).get("body") or {}
        thinking = body.get("thinking") or {}
        out = {
            "provider_model": record.get("provider_model") or "unknown",
            "max_tokens": body.get("max_tokens"),
            "thinking": thinking.get("type") or "absent",
            "thinking_budget_tokens": thinking.get("budget_tokens"),
            "temperature": body.get("temperature"),
            "top_p": body.get("top_p"),
            "top_k": body.get("top_k"),
        }
        # A key the provider was never sent is "unset", not None: the two look
        # the same in MLflow and mean different things.
        return {k: ("unset" if v is None else v) for k, v in out.items()}
    return {}


def bundled_skill_names(tasks_path: Path) -> set[str]:
    """Skill names a task bundle ships, from the directory names on disk.

    The name in the frontmatter is what Claude Code advertises, but the
    directory name is what BenchFlow installs under, and the two are equal for
    every skill it will accept. Reading the directory avoids parsing 48 copies
    of the same file.
    """
    roots = [tasks_path] if (tasks_path / "environment").is_dir() else sorted(
        p for p in tasks_path.glob("*") if (p / "environment").is_dir()
    )
    return {
        d.name
        for root in roots
        for d in (root / "environment" / "skills").glob("*")
        if (d / "SKILL.md").is_file()
    }


if __name__ == "__main__":
    main()
