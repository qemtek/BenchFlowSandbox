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
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tarfile
import time

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from provenance import agent_harness, collect  # noqa: E402

# MLflow 3.x put the filesystem store into maintenance mode; SQLite is the
# supported local backend and is queryable, which suits comparing arms.
TRACKING_DB = REPO / "mlflow.db"
ARTIFACTS = REPO / "mlartifacts"


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


def review_metrics(report: dict) -> tuple[dict, dict]:
    """Turn a review_report.json into MLflow params and metrics.

    The deterministic verifier and the LLM judge are two halves of one gate, so
    they belong on one run. Until now the judge wrote to a gitignored file and
    nothing linked a review to the rollouts it graded — the judge model and
    rubric were unrecorded, which is the same exposure as an unrecorded model
    version: a judge upgrade moves scores with nothing to show for it.
    """
    reviewer = report.get("reviewer", {}) or {}
    rubric = report.get("rubric", {}) or {}
    trials = [t for t in report.get("trials", []) if t.get("review_valid")]

    params = {
        "reviewer_agent": reviewer.get("agent", "unknown"),
        "reviewer_model": reviewer.get("model", "unknown"),
        "reviewer_network": reviewer.get("network", "unknown"),
        "reviewer_harness": agent_harness(reviewer.get("agent", "")),
        "rubric_criteria": ",".join(rubric.get("criteria", [])),
    }
    rubric_path = rubric.get("path")
    if rubric_path and pathlib.Path(rubric_path).is_file():
        blob = pathlib.Path(rubric_path).read_bytes()
        params["rubric_digest"] = "sha256:" + hashlib.sha256(blob).hexdigest()
        try:
            params["rubric_path"] = str(
                pathlib.Path(rubric_path).relative_to(REPO))
        except ValueError:
            params["rubric_path"] = rubric_path

    metrics = {"reviews_valid": len(trials),
               "reviews_total": len(report.get("trials", []))}
    if not trials:
        return params, metrics

    # Per-criterion result, so a blocker like
    # identity_verified_before_disclosure is plottable across runs rather than
    # buried in a prose summary.
    #
    # The two kinds of criterion are not on the same scale and are not forced
    # onto one. A blocker is judged pass/fail and contributes no points; it acts
    # as a veto on gated_quality. A weighted criterion is scored on a small
    # integer scale and multiplied by its weight into weighted_points.
    #
    # An earlier version divided the mean score by the criterion weight to fake
    # a 0-1 range. That was right only by coincidence: our weighted criteria
    # score 0-2 and weigh 2, so the two happened to cancel. The rubric declares
    # a weight but never declares the score scale, so there is nothing safe to
    # divide by — set weight: 3 and the same code would silently cap at 0.67.
    # Report the mean score as scored, named so the reader knows it is not a
    # rate, and use review_mean_raw_quality for the normalised aggregate.
    for name in rubric.get("criteria", []):
        checks = [t["checks"][name] for t in trials
                  if name in (t.get("checks") or {})]
        judged = [c["outcome"] for c in checks
                  if c.get("outcome") in ("pass", "fail")]
        if judged:
            metrics[f"review_{name}_pass_rate"] = judged.count("pass") / len(judged)
            continue
        scored_c = [c["score"] for c in checks if "score" in c]
        if scored_c:
            metrics[f"review_{name}_mean_score"] = sum(scored_c) / len(scored_c)
            metrics[f"review_{name}_max_score"] = max(scored_c)

    scored = [t.get("scoring") or {} for t in trials]
    metrics["review_all_blockers_pass"] = (
        sum(bool(sc.get("all_blockers_pass")) for sc in scored) / len(scored))
    # raw_quality is weighted_points / max_weighted_points, computed by the
    # reviewer from its own arithmetic — the normalisation to trust.
    metrics["review_mean_raw_quality"] = (
        sum(sc.get("raw_quality") or 0.0 for sc in scored) / len(scored))
    # gated_quality is raw_quality, zeroed unless the deterministic verifier
    # passed AND every blocker passed. This is the combined production gate in
    # one number: conduct and outcome both have to hold.
    metrics["review_mean_gated_quality"] = (
        sum(sc.get("gated_quality") or 0.0 for sc in scored) / len(scored))
    metrics["review_publishable_rate"] = (
        sum(sc.get("decision") == "publishable" for sc in scored) / len(scored))
    return params, metrics


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
    # BenchFlow's ACP runtime sets no temperature/top_p/seed, so reasoning
    # effort is the only generation knob reachable for claude-agent-acp.
    # Left unset it takes an unrecorded default; set it so it is recorded.
    ap.add_argument("--reasoning-effort", default="")
    ap.add_argument("--config-override", default="")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--review", action="store_true",
                    help="grade the rollouts against the rubric and log the "
                         "result to the same MLflow run")
    ap.add_argument("--review-agent", default="claude-agent-acp")
    ap.add_argument("--review-model", default="claude-sonnet-4-5")
    ap.add_argument("--review-rubric", default="",
                    help="default: review/rubric.json from the first task")
    # Subscription auth skips the LiteLLM proxy that the no-internet
    # declaration depends on, so reviewers cannot run isolated under it. Stated
    # as a flag rather than hidden, and the choice is recorded on the run.
    ap.add_argument("--review-network", choices=("open", "isolated"),
                    default="open")
    args = ap.parse_args()

    # An alias like "claude-sonnet-4-5" points at whichever snapshot is current,
    # and BenchFlow records only the string we passed. Dated ids pass straight
    # through — its own default is one — so this is our choice, not a limit of
    # the rig. Say so at the point of choosing rather than in a doc nobody reads
    # mid-run.
    model_is_alias = not re.search(r"-20\d{6}$", args.model)
    if model_is_alias:
        print(f"note: '{args.model}' is an alias, so this run does not record "
              f"which snapshot answered.\n      Pass a dated id "
              f"(e.g. {args.model}-20YYMMDD) to pin it.", file=sys.stderr)

    prov = collect(args.agent)
    if prov["git"]["dirty"] and not args.allow_dirty:
        print("Refusing to run: the working tree has uncommitted changes.\n",
              file=sys.stderr)
        for f in prov["git"]["dirty_files"]:
            print(f"    ~ {f}", file=sys.stderr)
        print("\nCommit them, or pass --allow-dirty to record an untrusted run.",
              file=sys.stderr)
        return 1

    import mlflow

    ARTIFACTS.mkdir(exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{TRACKING_DB}")
    # set_experiment does not take artifact_location; create it explicitly the
    # first time so artifacts land in the repo rather than beside the db.
    if mlflow.get_experiment_by_name(args.experiment) is None:
        mlflow.create_experiment(
            args.experiment, artifact_location=f"file://{ARTIFACTS}"
        )
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
    if args.reasoning_effort:
        cmd += ["--reasoning-effort", args.reasoning_effort]

    with mlflow.start_run() as run:
        # Params: everything needed to reproduce this run exactly.
        mlflow.log_params({
            "git_commit": prov["git"]["commit"],
            "git_branch": prov["git"]["branch"],
            "provenance_version": prov["provenance_version"],
            "digest_tasks": prov["digests"]["tasks"],
            "digest_environment": prov["digests"]["environment"],
            "digest_knowledge": prov["digests"]["knowledge"],
            "digest_prompts": prov["digests"]["prompts"],
            "digest_combined": prov["digests"]["combined"],
            "vendored_tau2_commit": prov.get("vendored_tau2_commit", ""),
            "benchflow_version": prov["toolchain"]["benchflow"],
            "docker_version": prov["toolchain"]["docker"],
            "agent": args.agent,
            # The harness is the other half of the rollout: system prompt,
            # tool definitions, control loop. BenchFlow pins it per agent,
            # so a score shift after a BenchFlow upgrade is attributable.
            "agent_harness": prov.get("agent_harness", "unknown"),
            "model": args.model,
            "model_is_alias": str(model_is_alias).lower(),
            "skill_mode": args.skill_mode,
            "reasoning_effort": args.reasoning_effort or "harness-default",
            # Not settable through BenchFlow for ACP agents; fixed by the
            # harness pin rather than by us.
            "sampling_params": "harness-default (not exposed by ACP runtime)",
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
            # Already computed by BenchFlow; cost per solved task is the
            # number that makes efficiency legible (production-realism §1).
            "total_cost_usd": summary.get("total_cost_usd") or 0.0,
            "total_tokens": summary.get("total_tokens") or 0,
            "total_input_tokens": summary.get("total_input_tokens") or 0,
            "total_output_tokens": summary.get("total_output_tokens") or 0,
            "avg_tool_calls_per_task": summary.get("avg_tool_calls_per_task") or 0.0,
        }
        passed = metrics["passed"]
        if passed:
            metrics["cost_per_solved_task_usd"] = metrics["total_cost_usd"] / passed
        if golds:
            # Efficiency: how many tool calls per action the task actually needed.
            metrics["calls_per_gold_action"] = tool_calls / golds
        mlflow.log_metrics(metrics)

        # Two levels of artifact, deliberately.
        #
        # Loose files first, so the common ones are one click away in the UI.
        # Log every match rather than the first: a multi-task run writes one
        # results.jsonl per task plus an aggregate, and an earlier `break` kept
        # whichever rglob yielded first and dropped the rest.
        for artifact in ("summary.json", "results.jsonl", "run.log"):
            for f in sorted(jobs_dir.rglob(artifact)):
                rel = str(f.parent.relative_to(jobs_dir))
                mlflow.log_artifact(str(f),
                                    artifact_path=None if rel == "." else rel)

        # Then the whole job directory as one archive. Those three files are an
        # index, not a record: they omit config.json (the resolved config that
        # actually ran), prompts.json (what the agent was actually sent), the
        # raw trajectories, and the verifier's own output. Without the archive,
        # deleting jobs/ loses exactly the evidence you want when a result
        # surprises you.
        archive = jobs_dir.parent / f"{jobs_dir.name}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(jobs_dir, arcname=jobs_dir.name)
        mlflow.log_artifact(str(archive))
        size_mb = archive.stat().st_size / 1e6
        archive.unlink()
        print(f"  archived job dir: {size_mb:.1f} MB compressed")

        if args.review:
            rubric = pathlib.Path(args.review_rubric) if args.review_rubric else next(
                iter(sorted(tasks_path.glob("*/review/rubric.json"))
                     or [tasks_path / "review" / "rubric.json"]))
            rcmd = [
                "benchflow", "review", str(jobs_dir),
                "--rubric", str(rubric),
                "--agent", args.review_agent,
                "--model", args.review_model,
                "--sandbox", "docker",
                "--concurrency", str(args.concurrency),
                "--tasks-root", str(REPO / "tasks"),
            ]
            if args.review_network == "open":
                rcmd.append("--allow-open-network")
            print(f"reviewing against {rubric.name} …")
            rproc = subprocess.run(rcmd, capture_output=True, text=True)
            (jobs_dir / "review.log").write_text(rproc.stdout + rproc.stderr)
            reports = sorted(REPO.glob("jobs/review-*/review_report.json"),
                             key=lambda q: q.stat().st_mtime)
            if reports:
                report = json.loads(reports[-1].read_text())
                rparams, rmetrics = review_metrics(report)
                mlflow.log_params(rparams)
                mlflow.log_metrics(rmetrics)
                mlflow.log_artifact(str(reports[-1]))
                metrics.update(rmetrics)
            else:
                print("  review produced no report; see review.log",
                      file=sys.stderr)

        print(f"\nmlflow run: {run.info.run_id}")
        print(f"jobs dir:   {jobs_dir.relative_to(REPO)}")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
