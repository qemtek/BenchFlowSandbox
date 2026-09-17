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
    --trials N      run the same arm N times through BenchFlow's --matrix, one
                    nested MLflow run per trial plus the spread on the parent.
                    The spread is the noise floor: a delta between two arms
                    smaller than it is not evidence.

The boundary with BenchFlow is deliberate and one-directional. BenchFlow owns
the data plane — tasks, rollouts, rewards, digests — and knows nothing about
MLflow. This owns the experimentation plane, and reads only files it asked
BenchFlow to write at paths it chose (`--health-summary-out`, `--run-config-out`,
`--task-manifest-out`, `benchflow review --out-dir`). It recomputes nothing the
data plane already emits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import secrets
import statistics
import subprocess
import sys
import tarfile
import time

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from provenance import (  # noqa: E402
    ProvenanceError,
    agent_harness,
    benchflow_python,
    collect,
)

# MLflow 3.x put the filesystem store into maintenance mode; SQLite is the
# supported local backend and is queryable, which suits comparing arms.
TRACKING_DB = REPO / "mlflow.db"
ARTIFACTS = REPO / "mlartifacts"


def task_dirs(tasks_path: pathlib.Path) -> list[pathlib.Path]:
    """The task packages `--tasks` selects: itself, or its children."""
    if (tasks_path / "task.md").is_file():
        return [tasks_path]
    return sorted(d for d in tasks_path.iterdir()
                  if (d / "task.md").is_file())


def gold_action_count(tasks_path: pathlib.Path,
                      include: list[str]) -> int:
    """Total reference actions across the selected tasks — the denominator for
    efficiency (see docs/production-realism.md §1).

    Raises on a gold file it cannot read. An earlier version swallowed the
    error, which silently changed the denominator of a headline metric: a
    malformed gold.json made the agent look more efficient, not broken.
    """
    dirs = task_dirs(tasks_path)
    if include:
        dirs = [d for d in dirs if d.name in set(include)]
    total = 0
    for d in dirs:
        g = d / "verifier" / "gold.json"
        if not g.is_file():
            raise SystemExit(f"missing gold actions: {g}")
        try:
            total += len(json.loads(g.read_text()))
        except (OSError, ValueError) as e:
            raise SystemExit(f"unreadable gold actions in {g}: {e}") from e
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

    try:
        reviewer_harness = agent_harness(reviewer.get("agent", ""))
    except ProvenanceError as e:
        reviewer_harness = "unknown"
        print(f"  warning: reviewer harness unrecorded — {e}", file=sys.stderr)
    params = {
        "reviewer_agent": reviewer.get("agent", "unknown"),
        "reviewer_model": reviewer.get("model", "unknown"),
        "reviewer_network": reviewer.get("network", "unknown"),
        "reviewer_harness": reviewer_harness,
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


def rel_to_repo(path: pathlib.Path) -> str:
    """Repo-relative where possible, absolute otherwise — never an exception."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict:
    """A file we asked BenchFlow to write, or {} with the absence visible."""
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except ValueError as e:
        print(f"  warning: {path.name} is not valid JSON ({e})", file=sys.stderr)
        return {}


def summarise(job_dir: pathlib.Path) -> dict:
    """BenchFlow's own summary for the single evaluation under `job_dir`.

    The run writes one timestamped directory into a jobs dir we created empty
    and own, so there is exactly one. An earlier version took whichever
    `*/summary.json` had the newest mtime, which is a guess: it is right until
    two runs overlap, and then it is wrong without saying so.
    """
    runs = sorted(job_dir.glob("*/summary.json"))
    if not runs:
        return {}
    if len(runs) > 1:
        raise SystemExit(
            f"{job_dir} holds {len(runs)} evaluations; this wrapper owns one "
            f"job directory per run, so something else wrote here")
    return json.loads(runs[0].read_text())


def health_metrics(job_dir: pathlib.Path) -> tuple[dict, bool]:
    """Coverage counts from the health summary we asked BenchFlow to write.

    The README tells a reader to check coverage before believing a delta. This
    makes that check data on the run instead of an instruction to a human: how
    many rollouts scored, how many produced no tool calls, how many lost their
    LLM trajectory. A pass rate averaged over an arm that quietly lost six
    rollouts has the same problem as a number from a dirty tree — it looks
    trustworthy.
    """
    health = read_json(job_dir / "health.json")
    if not health:
        return {}, False
    total = health.get("total_rows", 0) or 0
    scored = health.get("scored_rows", 0) or 0
    metrics = {
        "health_total_rollouts": total,
        "health_scored_rollouts": scored,
        "health_unscored_rollouts": health.get("unscored_rows", 0) or 0,
        "health_zero_tool_rollouts": health.get("zero_tool_rows", 0) or 0,
        "health_missing_llm_trajectory":
            health.get("missing_llm_trajectory", 0) or 0,
        "health_malformed_llm_trajectory":
            health.get("malformed_llm_trajectory", 0) or 0,
        "health_coverage": (scored / total) if total else 0.0,
    }
    return metrics, bool(total) and scored == total


def start_capture(jobs_dir: pathlib.Path, port: int) -> tuple:
    """Run the capture proxy for this run, and the agent env that reaches it.

    BenchFlow skips its own LiteLLM proxy under subscription auth, so
    `llm_trajectory.jsonl` is never written and with it goes per-call usage,
    the dated snapshot that answered, and the exact context each turn saw.
    `tools/capture_proxy.py` fills that gap for a subscription run.

    The sandbox is handed a per-run secret rather than the real credential:
    the proxy checks it, strips it, and attaches the subscription token on the
    way upstream. That is the property BenchFlow's own proxy has — the raw
    credential never reaches the agent — and it is an improvement on the
    default path, where the token is injected into a container that has open
    network access.
    """
    secret = secrets.token_urlsafe(24)
    capture = jobs_dir / "capture.jsonl"
    proc = subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "capture_proxy.py"),
         "--out", str(capture), "--port", str(port), "--secret", secret,
         "--inject"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    time.sleep(1.0)
    if proc.poll() is not None:
        raise SystemExit(f"capture proxy failed to start:\n{proc.communicate()[0]}")
    # host.docker.internal is how a container reaches the host under Docker
    # Desktop; loopback inside the sandbox is the sandbox itself.
    env_args = [
        "--agent-env", f"ANTHROPIC_BASE_URL=http://host.docker.internal:{port}",
        "--agent-env", f"ANTHROPIC_AUTH_TOKEN={secret}",
    ]
    print(f"capturing provider traffic on :{port} → {capture.name}")
    return proc, capture, env_args


def finish_capture(proc, capture: pathlib.Path, jobs_dir: pathlib.Path) -> None:
    """Stop the proxy, split its capture per rollout, and refresh health.json."""
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    if not capture.is_file():
        print("  capture proxy recorded nothing — did the sandbox reach the "
              "host? (host.docker.internal)", file=sys.stderr)
        return
    subprocess.run(
        [sys.executable, str(REPO / "tools" / "capture_proxy.py"),
         "--out", str(capture), "--attribute", str(jobs_dir)], check=False)
    # health.json was written before the trajectories existed, so its
    # missing_llm_trajectory count is stale by construction. Recompute it with
    # BenchFlow's own writer rather than patching the numbers ourselves.
    for health_file in sorted(jobs_dir.rglob("health.json")):
        recorded = read_json(health_file).get("job_dir")
        if not recorded:
            continue
        subprocess.run(
            [benchflow_python(), "-c",
             "import sys;from pathlib import Path;"
             "from benchflow.eval_artifacts import write_health_summary;"
             "write_health_summary(Path(sys.argv[1]), Path(sys.argv[2]))",
             str(health_file), recorded],
            check=False, capture_output=True)


def selected_tasks(tasks_path: pathlib.Path, include: list[str]) -> list[str]:
    """The task ids this run will evaluate, so the count can be asserted.

    `--expected-tasks` turns a silent partial selection into a failed run: a
    47-task arm compared against a 48-task arm is not a comparison, and nothing
    in the output says which tasks were missing.
    """
    names = [d.name for d in task_dirs(tasks_path)]
    if not names:
        raise SystemExit(f"no task packages under {tasks_path}")
    if include:
        unknown = sorted(set(include) - set(names))
        if unknown:
            raise SystemExit(f"--include names no such task: {', '.join(unknown)}")
        names = [n for n in names if n in set(include)]
    return names


def build_cmd(args, tasks_path: pathlib.Path, jobs_dir: pathlib.Path,
              expected: int) -> list[str]:
    """The `benchflow eval run` invocation, including the artifacts we want.

    Every file this wrapper later reads is one it asked BenchFlow to write, at
    a path it chose. The alternative — reading whatever the run left in the
    directory and taking the newest — is a guess that holds until two runs
    overlap.
    """
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
        # Named outputs rather than salvage. In matrix mode BenchFlow splits
        # each of these per cell (<alias>/trial-NN/<name>), which is why the
        # cell readers below look for the same filenames one level down.
        "--health-summary-out", str(jobs_dir / "health.json"),
        "--run-config-out", str(jobs_dir / "run-config.json"),
        "--task-manifest-out", str(jobs_dir / "task-manifest.json"),
        "--expected-tasks", str(expected),
    ]
    for inc in args.include:
        cmd += ["--include", inc]
    if args.config_override:
        cmd += ["--config-override", args.config_override]
    if args.reasoning_effort:
        cmd += ["--reasoning-effort", args.reasoning_effort]
    if args.trials > 1:
        # Repeats are BenchFlow's job, not a loop around this script: --matrix
        # gives each trial its own job directory, so no trial can resume into
        # another's and be silently compared against itself.
        cmd += ["--matrix", str(jobs_dir / "matrix.yaml"),
                "--trials", str(args.trials)]
    return cmd


def write_matrix(path: pathlib.Path, alias: str, model: str) -> None:
    path.write_text(f"models:\n  {alias}:\n    model: {model}\n")


def run_review(args, cell_dir: pathlib.Path, tasks_path: pathlib.Path) -> dict:
    """Grade `cell_dir`'s rollouts and return the report, or {}.

    `--out-dir` is the point. Without it BenchFlow writes `jobs/review-<ts>/`
    and the caller has to guess which one was its own; the previous version
    globbed every `jobs/review-*` in the repo and took the newest by mtime, so
    a stale directory or a second run in flight would attach another run's
    judge scores to this one, logged as params and looking authoritative.
    """
    rubric = pathlib.Path(args.review_rubric) if args.review_rubric else next(
        iter(sorted(tasks_path.glob("*/review/rubric.json"))
             or [tasks_path / "review" / "rubric.json"]))
    out_dir = cell_dir / "review"
    rcmd = [
        "benchflow", "review", str(cell_dir),
        "--rubric", str(rubric),
        "--agent", args.review_agent,
        "--model", args.review_model,
        "--sandbox", "docker",
        "--concurrency", str(args.concurrency),
        "--tasks-root", str(REPO / "tasks"),
        # The reviewer recomputes each rollout's task_digest against this tree
        # and refuses to admit task evidence that does not match, so the digest
        # BenchFlow stamped at run time is enforced, not just recorded.
        "--out-dir", str(out_dir),
    ]
    if args.review_network == "open":
        rcmd.append("--allow-open-network")
    print(f"reviewing {cell_dir.name} against {rubric.name} …")
    rproc = subprocess.run(rcmd, capture_output=True, text=True)
    (cell_dir / "review.log").write_text(rproc.stdout + rproc.stderr)
    report = read_json(out_dir / "review_report.json")
    if not report:
        print(f"  review produced no report; see {cell_dir.name}/review.log",
              file=sys.stderr)
    return report


def log_cell(mlflow, cell_dir: pathlib.Path, tasks_path: pathlib.Path,
             args, golds: int, elapsed: float | None) -> dict:
    """Log one evaluation's metrics and loose artifacts to the current run.

    `elapsed` is the wrapper's wall clock, which includes the image build. A
    trial inside a matrix has no wall clock of its own, so it passes None and
    takes BenchFlow's own figure for that evaluation.
    """
    summary = summarise(cell_dir)
    if elapsed is None:
        elapsed = summary.get("elapsed_sec") or 0.0
    tool_calls = summary.get("total_tool_calls") or 0

    metrics = {
        "pass_rate": summary.get("score_ratio", 0.0) or 0.0,
        "mean_reward": summary.get("mean_reward") or 0.0,
        "total": summary.get("total", 0) or 0,
        "passed": summary.get("passed", 0) or 0,
        "errored": summary.get("errored", 0) or 0,
        "verifier_errored": summary.get("verifier_errored", 0) or 0,
        "total_tool_calls": tool_calls,
        "elapsed_sec": elapsed,
        # Already computed by BenchFlow; cost per solved task is the
        # number that makes efficiency legible (production-realism §1).
        "total_cost_usd": summary.get("total_cost_usd") or 0.0,
        "total_tokens": summary.get("total_tokens") or 0,
        "total_input_tokens": summary.get("total_input_tokens") or 0,
        "total_output_tokens": summary.get("total_output_tokens") or 0,
        "avg_tool_calls_per_task": summary.get("avg_tool_calls_per_task") or 0.0,
        # The validity flag belongs with the value. Under subscription auth
        # there is no price source, so total_cost_usd is 0.0 meaning
        # "unpriced" rather than "free" — indistinguishable without this.
        "telemetry_coverage": summary.get("telemetry_coverage") or 0.0,
        # Whether the skill was opened at all. Without it, "the skill did not
        # help" and "the agent never read it" are the same number.
        "total_skill_invocations": summary.get("total_skill_invocations") or 0,
    }
    passed = metrics["passed"]
    if passed:
        metrics["cost_per_solved_task_usd"] = metrics["total_cost_usd"] / passed
    if golds:
        # Efficiency: how many tool calls per action the task actually needed.
        metrics["calls_per_gold_action"] = tool_calls / golds

    health, complete = health_metrics(cell_dir)
    metrics.update(health)

    priced = metrics["total_cost_usd"] > 0
    mlflow.set_tags({
        # The dirty-tree rule, applied to outputs: a pass rate averaged over an
        # arm that lost rollouts is still a number, and still looks like one
        # from a whole arm. Tag it so a query can exclude it.
        "coverage_complete": str(complete).lower(),
        "cost_priced": str(priced).lower(),
    })
    if not complete and health:
        print(f"  warning: {metrics['health_unscored_rollouts']:.0f} of "
              f"{metrics['health_total_rollouts']:.0f} rollouts did not score; "
              f"tagged coverage_complete=false", file=sys.stderr)

    # Two levels of artifact, deliberately.
    #
    # Loose files first, so the common ones are one click away in the UI.
    # Log every match rather than the first: a multi-task run writes one
    # results.jsonl per task plus an aggregate, and an earlier `break` kept
    # whichever rglob yielded first and dropped the rest.
    for artifact in ("summary.json", "results.jsonl", "run.log", "health.json",
                     "run-config.json", "task-manifest.json"):
        for f in sorted(cell_dir.rglob(artifact)):
            rel = str(f.parent.relative_to(cell_dir))
            mlflow.log_artifact(str(f),
                                artifact_path=None if rel == "." else rel)

    if args.review:
        report = run_review(args, cell_dir, tasks_path)
        if report:
            rparams, rmetrics = review_metrics(report)
            mlflow.log_params(rparams)
            mlflow.log_metrics(rmetrics)
            mlflow.log_artifact(str(cell_dir / "review" / "review_report.json"))
            metrics.update(rmetrics)

    mlflow.log_metrics(metrics)
    return metrics


def log_trials(mlflow, jobs_dir: pathlib.Path, tasks_path: pathlib.Path,
               args, golds: int, elapsed: float, prov: dict, parent) -> dict:
    """One nested run per trial, and the spread across them on the parent.

    The spread is the point. A 48-task arm has a sampling standard error near
    7 points before the agent's own run-to-run variation, and nothing in a
    single run distinguishes the two. Repeats of an identical arm measure the
    second, which is what tells you whether a delta between two arms is a
    difference or a coin toss.
    """
    matrix = read_json(jobs_dir / "matrix-summary.json")
    cells = matrix.get("runs", [])
    if not cells:
        print("  no matrix summary; trials did not run", file=sys.stderr)
        return {}
    # The run-wide files live at the matrix root rather than in any cell, so
    # the parent carries them; the per-cell ones hang off each nested run.
    for name in ("matrix-summary.json", "matrix.yaml", "task-manifest.json",
                 "run.log"):
        if (jobs_dir / name).is_file():
            mlflow.log_artifact(str(jobs_dir / name))
    pass_rates, rewards, costs = [], [], []
    for cell in cells:
        cell_dir = pathlib.Path(cell["jobs_dir"])
        with mlflow.start_run(nested=True,
                              run_name=f"trial-{cell['trial']:02d}"):
            mlflow.log_params({
                "trial": cell["trial"],
                "matrix_alias": cell["alias"],
                "model": args.model,
                "git_commit": prov["git"]["commit"],
                "digest_combined": prov["digests"]["combined"],
                "parent_run_id": parent.info.run_id,
                "jobs_dir": rel_to_repo(cell_dir),
            })
            m = log_cell(mlflow, cell_dir, tasks_path, args, golds, None)
            pass_rates.append(m.get("pass_rate", 0.0))
            rewards.append(m.get("mean_reward", 0.0))
            costs.append(m.get("total_cost_usd", 0.0))

    metrics = {
        "trials_completed": len(pass_rates),
        "pass_rate_mean": statistics.fmean(pass_rates),
        "pass_rate_min": min(pass_rates),
        "pass_rate_max": max(pass_rates),
        "pass_rate_spread": max(pass_rates) - min(pass_rates),
        "mean_reward_mean": statistics.fmean(rewards),
        "total_cost_usd": sum(costs),
        "elapsed_sec": elapsed,
    }
    if len(pass_rates) > 1:
        # The empirical noise floor: a delta between two arms smaller than
        # this is not evidence of anything.
        metrics["pass_rate_sd"] = statistics.stdev(pass_rates)
    mlflow.log_metrics(metrics)
    return metrics


def briefing_identity(tasks_path: pathlib.Path, selected: list[str]) -> dict:
    """Read which registered briefing these tasks were built from.

    Read-only. The briefing lives in MLflow's prompt registry and `make_task.py`
    pinned a version into every package at generation time, so there is one
    authoritative copy and nothing here can change what ran. This only recovers
    the pointer and logs it against the run.

    The URI names an immutable version, so there is no drift to police -- the
    one failure worth catching is a half-regenerated task set, where some
    packages point at one briefing and some at another.
    """
    uris = {}
    for task_dir in (d for d in task_dirs(tasks_path) if d.name in set(selected)):
        head = (task_dir / "task.md").read_text()[:2000]
        m = re.search(r"^\s+briefing_prompt_uri:\s*(\S+)\s*$", head, re.M)
        uris[task_dir.name] = m.group(1) if m else "unstamped"

    distinct = sorted(set(uris.values()))
    if len(distinct) > 1:
        raise SystemExit(
            "Task set mixes briefings: " + ", ".join(distinct) + "\n"
            "Some packages were generated against a different prompt version. "
            "Regenerate the whole set:\n"
            "  python tools/make_task.py $(cat tools/eligible_ids.txt) --out "
            + tasks_path.name
        )
    uri = distinct[0]
    if uri == "unstamped":
        # Generated before briefings moved into the registry. Say so rather
        # than guessing which prompt it was.
        return {"briefing_prompt_uri": "unstamped"}
    return {
        "briefing_prompt_uri": uri,
        "briefing_prompt_version": uri.rsplit("/", 1)[-1],
    }


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
    # Repeats of one identical arm. The spread across trials is the noise
    # floor: without it, no delta between two runs can be called a difference.
    ap.add_argument("--trials", type=int, default=1,
                    help="run the same arm N times (BenchFlow --matrix), one "
                         "nested MLflow run per trial plus the spread")
    # BenchFlow's ACP runtime sets no temperature/top_p/seed, so reasoning
    # effort is the only generation knob reachable for claude-agent-acp.
    # Left unset it takes an unrecorded default; set it so it is recorded.
    ap.add_argument("--reasoning-effort", default="")
    ap.add_argument("--config-override", default="")
    ap.add_argument("--allow-dirty", action="store_true")
    # Subscription auth means BenchFlow skips its own proxy and writes no
    # llm_trajectory.jsonl. This runs ours instead, so a subscription run keeps
    # the provider-side record — and keeps the credential out of the sandbox.
    ap.add_argument("--capture-provider", action="store_true",
                    help="capture provider traffic through tools/capture_proxy.py")
    ap.add_argument("--capture-port", type=int, default=8787)
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

    tasks_path = (REPO / args.tasks if not args.tasks.startswith("/")
                  else pathlib.Path(args.tasks))
    selected = selected_tasks(tasks_path, args.include)
    golds = gold_action_count(tasks_path, args.include)

    prov = collect(args.agent, tasks_path)
    if prov["git"]["dirty"] and not args.allow_dirty:
        print("Refusing to run: the working tree has uncommitted changes to "
              "files that change what a run means.\n", file=sys.stderr)
        for f in prov["git"]["dirty_files"]:
            print(f"    ~ {f}", file=sys.stderr)
        print("\nCommit them, or pass --allow-dirty to record an untrusted run.",
              file=sys.stderr)
        return 1
    # Uncommitted prose does not change what a run means, so it does not block.
    # It is still recorded: a run that waived something has to say what.
    if prov["git"]["dirty_ignored"]:
        print(f"note: ignoring {prov['git']['dirty_ignored_count']} "
              f"uncommitted documentation file(s); they cannot change a result.",
              file=sys.stderr)
        for f in prov["git"]["dirty_ignored"]:
            print(f"    ~ {f}", file=sys.stderr)
    # A probe that cannot read what it claims to record says so here rather
    # than logging a plausible "unknown" and letting the run look complete.
    for w in prov["warnings"]:
        print(f"warning: provenance incomplete — {w}", file=sys.stderr)

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

    stamp = time.strftime("%Y-%m-%d__%H-%M-%S")
    jobs_dir = REPO / "jobs" / f"mlf-{stamp}"
    # BenchFlow resumes into a job directory that already holds results and
    # skips the rollouts it considers done. That is useful and, for an arm,
    # fatal: the second arm inherits the first one's rollouts and the
    # comparison is of an arm against itself. The README said so; this enforces
    # it, the same way the dirty-tree check enforces the commit rule.
    if jobs_dir.exists() and any(jobs_dir.iterdir()):
        print(f"Refusing to run: {rel_to_repo(jobs_dir)} is not empty.",
              file=sys.stderr)
        return 1
    jobs_dir.mkdir(parents=True, exist_ok=True)

    alias = re.sub(r"[^A-Za-z0-9._-]", "-", args.model)
    if args.trials > 1:
        write_matrix(jobs_dir / "matrix.yaml", alias, args.model)

    cmd = build_cmd(args, tasks_path, jobs_dir, len(selected))

    capture_proc = capture_path = None
    if args.capture_provider:
        capture_proc, capture_path, capture_env = start_capture(
            jobs_dir, args.capture_port)
        cmd += capture_env

    # Before the run starts, so a half-regenerated task set stops the run
    # rather than being discovered after the rollouts are paid for.
    briefing = briefing_identity(tasks_path, selected)

    with mlflow.start_run() as run:
        # Params: everything needed to reproduce this run exactly.
        mlflow.log_params({
            **briefing,
            "git_commit": prov["git"]["commit"],
            "git_branch": prov["git"]["branch"],
            "provenance_version": prov["provenance_version"],
            # tasks is BenchFlow's own task_digest, aggregated over the
            # selected packages — the same value it stamps into every
            # rollout's config.json and that `benchflow review --tasks-root`
            # verifies before admitting a task as evidence.
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
            "expected_tasks": len(selected),
            "concurrency": args.concurrency,
            "trials": args.trials,
            "config_override": args.config_override or "none",
            # The back-pointer. Without it, mapping a directory on disk to the
            # run that produced it is timestamp arithmetic.
            "jobs_dir": rel_to_repo(jobs_dir),
        })
        mlflow.set_tags({
            "dirty": str(prov["git"]["dirty"]).lower(),
            # Prose edits that were waived. A run that ignored something says
            # what it ignored, rather than presenting itself as fully clean.
            "dirty_ignored": ",".join(prov["git"]["dirty_ignored"]) or "none",
            "note": args.note,
            "provenance_complete": str(not prov["warnings"]).lower(),
        })
        (jobs_dir / "mlflow_run_id").write_text(run.info.run_id + "\n")
        digests_path = jobs_dir / "task-digests.json"
        digests_path.write_text(json.dumps(prov.get("task_digests", {}), indent=2))
        mlflow.log_artifact(str(digests_path))

        print(f"running: {' '.join(cmd[:6])} …")
        started = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - started

        log_path = jobs_dir / "run.log"
        log_path.write_text(proc.stdout + proc.stderr)

        # Before any metric is read: attribution writes each rollout's
        # llm_trajectory.jsonl and health.json is recomputed from it, so the
        # coverage numbers logged below describe the run as it now stands.
        if capture_proc is not None:
            finish_capture(capture_proc, capture_path, jobs_dir)

        if args.trials > 1:
            metrics = log_trials(mlflow, jobs_dir, tasks_path, args, golds,
                                 elapsed, prov, run)
        else:
            metrics = log_cell(mlflow, jobs_dir, tasks_path, args, golds,
                               elapsed)

        # Then the whole job directory as one archive. The loose files are an
        # index, not a record: they omit config.json (the resolved config that
        # actually ran, including the task_digest BenchFlow stamped),
        # prompts.json (what the agent was actually sent), the raw
        # trajectories, and the verifier's own output. Without the archive,
        # deleting jobs/ loses exactly the evidence you want when a result
        # surprises you.
        archive = jobs_dir.parent / f"{jobs_dir.name}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(jobs_dir, arcname=jobs_dir.name)
        mlflow.log_artifact(str(archive))
        size_mb = archive.stat().st_size / 1e6
        archive.unlink()
        print(f"  archived job dir: {size_mb:.1f} MB compressed")

        print(f"\nmlflow run: {run.info.run_id}")
        print(f"jobs dir:   {rel_to_repo(jobs_dir)}")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
