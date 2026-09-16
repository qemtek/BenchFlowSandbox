#!/usr/bin/env python3
"""Run a BenchFlow eval and record it in MLflow with full provenance.

Why this exists rather than calling `benchflow eval run` directly: a result is
only meaningful if you can say exactly what produced it. That means the git
commit, the content of the tools and knowledge base, the prompts, and the run
configuration — all pinned, all recorded together.

It refuses to run against a dirty working tree. That is the point: a number
attributed to a commit that does not describe the code which produced it is
worse than no number, because it looks trustworthy.

    python tools/run_experiment.py --tasks tasks/task-036 \\
        --agent claude-agent-acp --model claude-sonnet-4-5 \\
        --experiment baseline --note "first flag-CLI run"

    --allow-dirty   record the dirty file list and run anyway (debugging only;
                    the run is tagged dirty=true and should not be cited)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from provenance import collect  # noqa: E402

MLRUNS = REPO / "mlruns"


def gold_action_count(tasks_path: pathlib.Path) -> int:
    """Total reference actions across the selected tasks — the denominator for
    efficiency (see docs/production-realism.md §1)."""
    golds = (
        [tasks_path / "verifier" / "gold.json"]
        if (tasks_path / "verifier" / "gold.json").is_file()
        else sorted(tasks_path.glob("*/verifier/gold.json"))
    )
    total = 0
    for g in golds:
        try:
            total += len(json.loads(g.read_text()))
        except Exception:
            pass
    return total


def summarise(jobs_dir: pathlib.Path) -> dict:
    """Read BenchFlow's own summary for the most recent job."""
    runs = sorted(
        (p for p in jobs_dir.glob("*/summary.json")),
        key=lambda p: p.stat().st_mtime,
    )
    if not runs:
        return {}
    return json.loads(runs[-1].read_text())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True, help="task dir, or a set root")
    ap.add_argument("--include", action="append", default=[])
    ap.add_argument("--agent", default="claude-agent-acp")
    ap.add_argument("--model", default="claude-sonnet-4-5")
    ap.add_argument("--experiment", default="banking")
    ap.add_argument("--note", default="")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--skill-mode", default="no-skill")
    ap.add_argument("--config-override", default="")
    ap.add_argument("--allow-dirty", action="store_true")
    args = ap.parse_args()

    prov = collect()
    if prov["git"]["dirty"] and not args.allow_dirty:
        print("Refusing to run: the working tree has uncommitted changes.\n",
              file=sys.stderr)
        for f in prov["git"]["dirty_files"]:
            print(f"    ~ {f}", file=sys.stderr)
        print("\nCommit them, or pass --allow-dirty to record an untrusted run.",
              file=sys.stderr)
        return 1

    import mlflow

    mlflow.set_tracking_uri(f"file://{MLRUNS}")
    mlflow.set_experiment(args.experiment)

    tasks_path = REPO / args.tasks if not args.tasks.startswith("/") else pathlib.Path(args.tasks)
    stamp = time.strftime("%Y-%m-%d__%H-%M-%S")
    jobs_dir = REPO / "jobs" / f"mlf-{stamp}"

    cmd = [
        "benchflow", "eval", "run",
        "--tasks-dir", str(tasks_path),
        "--context-root", str(REPO),
        "--agent", args.agent,
        "--model", args.model,
        "--sandbox", "docker",
        "--concurrency", str(args.concurrency),
        "--skill-mode", args.skill_mode,
        "--jobs-dir", str(jobs_dir),
    ]
    for inc in args.include:
        cmd += ["--include", inc]
    if args.config_override:
        cmd += ["--config-override", args.config_override]

    with mlflow.start_run() as run:
        # Params: everything needed to reproduce this run exactly.
        mlflow.log_params({
            "git_commit": prov["git"]["commit"],
            "git_branch": prov["git"]["branch"],
            "digest_environment": prov["digests"]["environment"],
            "digest_knowledge": prov["digests"]["knowledge"],
            "digest_prompts": prov["digests"]["prompts"],
            "digest_combined": prov["digests"]["combined"],
            "vendored_tau2_commit": prov.get("vendored_tau2_commit", ""),
            "agent": args.agent,
            "model": args.model,
            "skill_mode": args.skill_mode,
            "tasks": args.tasks,
            "include": ",".join(args.include) or "all",
            "concurrency": args.concurrency,
            "config_override": args.config_override or "none",
        })
        mlflow.set_tags({
            "dirty": str(prov["git"]["dirty"]).lower(),
            "note": args.note,
        })

        print(f"running: {' '.join(cmd[:6])} …")
        started = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - started

        log_path = jobs_dir / "run.log"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        log_path.write_text(proc.stdout + proc.stderr)

        summary = summarise(jobs_dir)
        golds = gold_action_count(tasks_path)
        tool_calls = summary.get("total_tool_calls") or 0

        metrics = {
            "pass_rate": summary.get("score_ratio", 0.0) or 0.0,
            "mean_reward": summary.get("mean_reward") or 0.0,
            "total": summary.get("total", 0) or 0,
            "passed": summary.get("passed", 0) or 0,
            "errored": summary.get("errored", 0) or 0,
            "total_tool_calls": tool_calls,
            "elapsed_sec": elapsed,
        }
        if golds:
            # Efficiency: how many tool calls per action the task actually needed.
            metrics["calls_per_gold_action"] = tool_calls / golds
        mlflow.log_metrics(metrics)

        for artifact in ("summary.json", "results.jsonl", "run.log"):
            for p in jobs_dir.rglob(artifact):
                mlflow.log_artifact(str(p))
                break

        print(f"\nmlflow run: {run.info.run_id}")
        print(f"jobs dir:   {jobs_dir.relative_to(REPO)}")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
