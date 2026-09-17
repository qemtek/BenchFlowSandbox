#!/usr/bin/env python3
"""Compare two tracked arms, and record the comparison as a run of its own.

`benchflow eval compare-lift` already does the statistics: it pairs rollouts by
task, reports pass-rate and mean-reward deltas with bootstrap confidence
intervals, and prints a coverage table. What it does not do is remember. The
delta is the number you cite, and until now it lived in a markdown file on
somebody's laptop while every input to it was pinned in MLflow.

So this adds the two things the comparison needs and BenchFlow has no opinion
about:

**A guard.** Two arms are comparable only if they asked the same questions.
`digest_knowledge` moving means the knowledge base changed underneath, and
pairing by task id then compares two different questions. That is the exact
error the split digests were built to catch, and nothing read them until now.

`digest_tasks` needs a subtler test, because a prompt arm runs two task sets
built from two briefing versions and is *supposed* to move it. So the task sets
are compared with `benchflow tasks overlap`, by task id and by content digest:

    same roster, every digest equal      the task sets are identical
    same roster, every digest differs    a whole-set change; fine when a
                                         whole-set lever explains it
    same roster, some digests differ     a subset of packages was edited, which
                                         no lever does. Refused.
    different roster                     different questions. Refused.

The partial case is the one worth having. A stray regeneration that touched six
packages produces a delta that looks ordinary and is contaminated, and nothing
in the headline number says so.

`--allow-digest-mismatch` overrides and tags the result. Digests that are meant
to move — environment, prompts — are reported as the lever under test.

**A record.** The lift becomes a third MLflow run, with both arms' run ids and
digests as params, the deltas and their intervals as metrics, and `lift.md` /
`lift.json` as artifacts.

    python tools/compare_arms.py --baseline <run-id> --treatment <run-id> \\
        --note "no_discovery toolset"

Job directories are scratch, so an arm whose `jobs/` has been deleted is
recovered from its archived `.tar.gz` in MLflow. A tracked run stays comparable
after the working copy is gone, which is the whole point of archiving it.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
TRACKING_DB = REPO / "mlflow.db"

# Digests that must match for a paired comparison to mean anything, against the
# reason they must. The others (environment, prompts) are the lever.
#
# digest_tasks is deliberately not here. A prompt arm runs two task sets
# generated from two briefing versions, so digest_tasks is *meant* to differ,
# and a flat equality test would refuse the comparison it exists to support.
# What matters is not whether the task sets differ but HOW — see task_set_note.
FIXED_DIGESTS = {
    "digest_knowledge": "the knowledge base the tasks are answered from",
}

# Params worth reporting as "what actually differs between these two arms".
LEVERS = ("model", "agent", "agent_harness", "skill_mode", "reasoning_effort",
          "config_override", "briefing_prompt_uri", "digest_environment",
          "digest_prompts", "benchflow_version", "git_commit")

# A whole-set lever changes every task package, so every digest moves together.
# Anything that moves only some of them was not this.
WHOLE_SET_LEVERS = ("briefing_prompt_uri", "digest_tasks")


def resolve_jobs_dir(client, run, stack: tempfile.TemporaryDirectory,
                     label: str) -> pathlib.Path:
    """The arm's job directory: local if it survives, else from the archive."""
    rel = run.data.params.get("jobs_dir")
    if rel:
        local = REPO / rel
        if local.is_dir() and any(local.iterdir()):
            return local
    archives = [f.path for f in client.list_artifacts(run.info.run_id)
                if f.path.endswith(".tar.gz")]
    if not archives:
        raise SystemExit(
            f"run {run.info.run_id[:8]} has neither a job directory on disk "
            f"({rel or 'no jobs_dir param'}) nor an archived one")
    dest = pathlib.Path(stack.name) / label
    dest.mkdir(parents=True, exist_ok=True)
    path = client.download_artifacts(run.info.run_id, archives[0], str(dest))
    with tarfile.open(path) as tar:
        tar.extractall(dest, filter="data")
    unpacked = [d for d in dest.iterdir() if d.is_dir()]
    if len(unpacked) != 1:
        raise SystemExit(f"unexpected archive layout in {archives[0]}")
    print(f"  recovered {run.info.run_id[:8]} from its archive")
    return unpacked[0]


def check_digests(base, treat, allow_mismatch: bool) -> dict:
    """Refuse a comparison whose measuring stick moved; report the lever."""
    blocking = []
    for param, why in FIXED_DIGESTS.items():
        b, t = base.data.params.get(param), treat.data.params.get(param)
        if b and t and b != t:
            blocking.append(f"{param} differs — {why} changed between the arms")
    if blocking and not allow_mismatch:
        print("Refusing to compare: these arms did not measure the same thing.\n",
              file=sys.stderr)
        for line in blocking:
            print(f"    {line}", file=sys.stderr)
        print("\nPairing by task id compares two different questions. Pass "
              "--allow-digest-mismatch\nto record it anyway; the run is tagged "
              "digests_matched=false and should not be cited.",
              file=sys.stderr)
        raise SystemExit(2)

    moved = {}
    for param in LEVERS:
        b, t = base.data.params.get(param, ""), treat.data.params.get(param, "")
        if b != t:
            moved[param] = f"{b} → {t}"
    return {"blocking": blocking, "moved": moved}


def find_manifest(job_dir: pathlib.Path) -> pathlib.Path | None:
    """The task manifest BenchFlow wrote for this run, if it survives.

    `run_experiment.py` passes --task-manifest-out, so it sits beside the job
    directory. Recovered archives can nest it a level deeper, hence the search.
    """
    direct = job_dir / "task-manifest.json"
    if direct.is_file():
        return direct
    return next(iter(sorted(job_dir.rglob("task-manifest.json"))), None)


def task_set_note(base, treat, base_dir, treat_dir,
                  tmp: pathlib.Path) -> tuple[list[str], list[str], dict]:
    """How the two arms' task sets differ. Returns (blocking, notes, result).

    `benchflow tasks overlap` compares the manifests by task id and by content
    digest, which answers the question a digest equality test cannot: two task
    sets that differ are either the same 48 questions carrying a different
    briefing, or two different sets of questions. Only the first is comparable.

    Three outcomes matter:

      roster differs        different questions; pairing by task id is
                            meaningless, so this always blocks
      every digest differs  a whole-set change. Fine if a whole-set lever
                            explains it, otherwise something unaccounted for
                            rewrote every package
      some digests differ   no whole-set lever does this. A subset of packages
                            was edited, and the comparison is contaminated in a
                            way the headline delta will not show
    """
    left = find_manifest(base_dir)
    right = find_manifest(treat_dir)
    if not (left and right):
        return ([], ["task manifests missing from one or both arms — the task "
                     "sets could not be compared by digest"], {})

    out = tmp / "overlap.json"
    proc = subprocess.run(
        ["benchflow", "tasks", "overlap", str(left), str(right), "--out", str(out)],
        capture_output=True, text=True)
    if not out.is_file():
        return ([], [f"tasks overlap failed: {(proc.stderr or proc.stdout).strip()}"],
                {})
    r = json.loads(out.read_text())

    n_left, n_right = r["left_count"], r["right_count"]
    shared_ids, shared_digests = r["task_id_overlap_count"], r["digest_overlap_count"]
    moved_whole_set = [p for p in WHOLE_SET_LEVERS
                       if base.data.params.get(p) != treat.data.params.get(p)]

    if shared_ids != n_left or shared_ids != n_right:
        return ([f"task rosters differ — {n_left} vs {n_right} tasks, "
                 f"{shared_ids} in common. Pairing by task id compares two "
                 f"different sets of questions"], [], r)

    if shared_digests == n_left:
        return ([], [f"task sets are identical ({n_left} tasks, every digest "
                     f"matches)"], r)

    if shared_digests == 0:
        if moved_whole_set:
            return ([], [f"all {n_left} task packages differ, explained by "
                         + ", ".join(moved_whole_set)], r)
        return ([f"all {n_left} task packages differ and no whole-set lever "
                 f"explains it — {', '.join(WHOLE_SET_LEVERS)} are identical "
                 f"across the arms"], [], r)

    return ([f"{n_left - shared_digests} of {n_left} task packages differ, the "
             f"rest are identical. No whole-set lever does that: a subset was "
             f"edited, so the arms differ by more than the thing under test"],
            [], r)


def lift_metrics(lift: dict) -> dict:
    """The numbers worth plotting, flattened out of lift.json."""
    m = lift.get("metrics") or {}
    out = {
        "paired_count": m.get("paired_count", 0),
        "pass_rate_base": m.get("pass_rate_base") or 0.0,
        "pass_rate_treatment": m.get("pass_rate_trained") or 0.0,
        "pass_rate_delta": m.get("pass_rate_delta") or 0.0,
        "mean_reward_base": m.get("mean_reward_base") or 0.0,
        "mean_reward_treatment": m.get("mean_reward_trained") or 0.0,
        "mean_reward_delta": m.get("mean_reward_delta") or 0.0,
    }
    for name, key in (("pass_rate_delta", "pass_rate_delta"),
                      ("mean_reward_delta", "mean_reward_delta")):
        ci = (m.get("ci") or {}).get(key)
        if ci:
            out[f"{name}_ci_low"] = ci["low"]
            out[f"{name}_ci_high"] = ci["high"]

    # Coverage first, delta second. Only tasks with a healthy scored rollout on
    # both sides enter the paired metrics, so an arm that crashed on six tasks
    # produces a delta over 42 and says so nowhere in the headline number.
    cov = lift.get("coverage") or {}
    for side, label in (("baseline", "base"), ("trained", "treatment")):
        c = cov.get(side) or {}
        out[f"{label}_healthy_rollouts"] = c.get("healthy_rollouts", 0)
        out[f"{label}_excluded_rollouts"] = c.get("excluded_rollouts", 0)
        out[f"{label}_healthy_task_coverage"] = c.get("healthy_task_coverage") or 0.0
    pairing = lift.get("pairing") or {}
    out["base_only_healthy_tasks"] = len(pairing.get("baseline_only_healthy_tasks") or [])
    out["treatment_only_healthy_tasks"] = len(pairing.get("trained_only_healthy_tasks") or [])
    return out


def verdict(metrics: dict) -> str:
    """What the interval licenses you to say, in one line.

    An interval straddling zero does not mean "no difference"; it means the
    experiment could not tell a large improvement from none. Those are
    different claims and the second one is the honest one.
    """
    low = metrics.get("pass_rate_delta_ci_low")
    high = metrics.get("pass_rate_delta_ci_high")
    delta = metrics["pass_rate_delta"]
    if low is None:
        return "no interval — too few paired tasks to bootstrap"
    if low > 0:
        return f"improvement: +{delta:.3f}, 95% CI [{low:+.3f}, {high:+.3f}]"
    if high < 0:
        return f"regression: {delta:.3f}, 95% CI [{low:+.3f}, {high:+.3f}]"
    return (f"undecided: {delta:+.3f}, 95% CI [{low:+.3f}, {high:+.3f}] — "
            f"zero is inside the interval, so this run cannot separate "
            f"'no effect' from a real one")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, help="MLflow run id")
    ap.add_argument("--treatment", required=True, help="MLflow run id")
    ap.add_argument("--experiment", default="comparisons")
    ap.add_argument("--note", default="")
    ap.add_argument("--bootstrap-samples", type=int, default=1000)
    # Pinned, like everything else here: an interval you cannot re-derive is
    # not a recorded result.
    ap.add_argument("--bootstrap-seed", type=int, default=0)
    ap.add_argument("--allow-digest-mismatch", action="store_true")
    args = ap.parse_args()

    import mlflow
    from mlflow.tracking import MlflowClient

    mlflow.set_tracking_uri(f"sqlite:///{TRACKING_DB}")
    client = MlflowClient()
    try:
        base = client.get_run(args.baseline)
        treat = client.get_run(args.treatment)
    except Exception as e:
        print(f"cannot read those runs: {e}", file=sys.stderr)
        return 1

    diffs = check_digests(base, treat, args.allow_digest_mismatch)
    if diffs["moved"]:
        print("levers that differ between the arms:")
        for k, v in diffs["moved"].items():
            print(f"  {k}: {v}")
    else:
        print("warning: nothing differs between these arms except the rollouts",
              file=sys.stderr)

    stack = tempfile.TemporaryDirectory()
    try:
        base_dir = resolve_jobs_dir(client, base, stack, "baseline")
        treat_dir = resolve_jobs_dir(client, treat, stack, "treatment")

        # Before the statistics, establish that the two arms asked the same
        # questions. compare-lift pairs by task id and will happily pair two
        # tasks that share an id and nothing else.
        blocking, notes, overlap = task_set_note(
            base, treat, base_dir, treat_dir, pathlib.Path(stack.name))
        for line in notes:
            print(f"  task sets: {line}")
        if blocking and not args.allow_digest_mismatch:
            print("\nRefusing to compare: these arms did not measure the same "
                  "thing.\n", file=sys.stderr)
            for line in blocking:
                print(f"    {line}", file=sys.stderr)
            print("\nPass --allow-digest-mismatch to record it anyway; the run "
                  "is tagged\ntask_sets_comparable=false and should not be "
                  "cited.", file=sys.stderr)
            raise SystemExit(2)
        for line in blocking:
            print(f"  task sets: OVERRIDDEN — {line}", file=sys.stderr)
        diffs["blocking"].extend(blocking)

        out_dir = pathlib.Path(stack.name) / "lift"
        out_dir.mkdir()
        md, js = out_dir / "lift.md", out_dir / "lift.json"
        cmd = ["benchflow", "eval", "compare-lift",
               "--baseline", str(base_dir), "--trained", str(treat_dir),
               "--out", str(md), "--json-out", str(js),
               "--bootstrap-samples", str(args.bootstrap_samples),
               "--bootstrap-seed", str(args.bootstrap_seed)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if not js.is_file():
            print(proc.stdout + proc.stderr, file=sys.stderr)
            print("compare-lift produced no report", file=sys.stderr)
            return proc.returncode or 1
        lift = json.loads(js.read_text())
        metrics = lift_metrics(lift)

        if mlflow.get_experiment_by_name(args.experiment) is None:
            mlflow.create_experiment(
                args.experiment, artifact_location=f"file://{REPO / 'mlartifacts'}")
        mlflow.set_experiment(args.experiment)
        with mlflow.start_run() as run:
            params = {
                "baseline_run_id": args.baseline,
                "treatment_run_id": args.treatment,
                "bootstrap_samples": args.bootstrap_samples,
                "bootstrap_seed": args.bootstrap_seed,
                "levers_moved": ",".join(diffs["moved"]) or "none",
            }
            for param in ("digest_tasks", "digest_knowledge",
                          "digest_environment", "digest_prompts",
                          "provenance_version"):
                params[f"base_{param}"] = base.data.params.get(param, "")
                params[f"treatment_{param}"] = treat.data.params.get(param, "")
            if overlap:
                # How the task sets relate, as recorded numbers rather than a
                # line of console output nobody kept.
                params["task_ids_shared"] = overlap["task_id_overlap_count"]
                params["task_digests_shared"] = overlap["digest_overlap_count"]
                params["task_count_base"] = overlap["left_count"]
                params["task_count_treatment"] = overlap["right_count"]
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            mlflow.set_tags({
                "note": args.note,
                "digests_matched": str(not diffs["blocking"]).lower(),
                # Whether the two arms asked the same questions, established by
                # `benchflow tasks overlap` rather than by digest equality —
                # a prompt arm changes every task digest on purpose.
                "task_sets_comparable": str(not blocking).lower(),
                # Coverage is a precondition for reading the delta, so it is a
                # tag you can filter on, not a number buried in the report.
                "coverage_complete": str(
                    metrics["base_only_healthy_tasks"] == 0
                    and metrics["treatment_only_healthy_tasks"] == 0).lower(),
                "verdict": verdict(metrics).split(":")[0],
            })
            for f in (md, js):
                mlflow.log_artifact(str(f))
            (REPO / "jobs").mkdir(exist_ok=True)
            report = shutil.copy(md, REPO / "jobs" / "lift.md")

        print()
        print(f"  paired tasks: {metrics['paired_count']:.0f}"
              f"  (baseline-only {metrics['base_only_healthy_tasks']:.0f}, "
              f"treatment-only {metrics['treatment_only_healthy_tasks']:.0f})")
        print(f"  {verdict(metrics)}")
        for line in lift.get("limitations") or []:
            print(f"  note: {line}")
        print(f"\nmlflow run: {run.info.run_id}")
        print(f"report:     {pathlib.Path(report).relative_to(REPO)}")
        return 0
    finally:
        stack.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
