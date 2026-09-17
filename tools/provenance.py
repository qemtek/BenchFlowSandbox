#!/usr/bin/env python3
"""Content digests for everything a result depends on.

BenchFlow already digests a task package — `task_digest()`, sha256 over every
file in the directory — and stamps the result into each rollout's `config.json`
and `result.json`, verifies it in `benchflow review --tasks-root`, and pins
dataset releases with it. So `tasks` is not ours to compute: we ask for it
(`benchflow tasks digest tasks/`) and aggregate the per-task digests into one
run-level value. One algorithm, so our number, the per-rollout stamp and any
future `--dataset` pin agree by construction.

What BenchFlow cannot digest is everything outside a task package. We moved the
shared sources out via `--context-root`, so:

    covered by task_digest    task.md, environment/Dockerfile, oracle/,
                              verifier/, review/
    covered by nothing else   vendor/bank_cli.py, vendor/toolsets.py,
                              the knowledge base, the prompt templates

That gap is real. The enum fix on 2026-09-16 flipped two tasks from FAIL to PASS
without changing a single `task_digest` — two runs with materially different
tool behaviour looked identical in provenance. So this module computes the three
digests nobody else will, and delegates the fourth:

    tasks        tasks/ (delegated: aggregate of BenchFlow per-task digests)
    environment  vendor/ (tool implementation, toolsets, MCP server)
    knowledge    data/banking_knowledge/ (seed db + 698 documents)
    prompts      prompts/ (briefings and frontmatter templates)

Nothing here reports "unknown" quietly. A probe that cannot read what it claims
to record raises, and the caller decides whether to run anyway — a field whose
whole purpose is attribution must not degrade into a plausible-looking string.

Usage:
    python tools/provenance.py            # print the digests
    python tools/provenance.py --json     # machine-readable
    python tools/provenance.py --tasks    # the per-task digest map
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import subprocess

REPO = pathlib.Path(__file__).resolve().parent.parent

# Bump when TRACKED changes. `combined` is a hash of the other digests, so
# adding one silently changes it for unchanged content; this makes runs from
# either side of such a change distinguishable instead of falsely different.
# 3: `tasks` moved from our suffix-filtered digest_dir() to BenchFlow's
#    task_digest(), which hashes every file rather than a chosen list of
#    extensions. Same content, different number, so runs either side of the
#    change must not be compared by digest alone.
PROVENANCE_VERSION = 3

# Directories outside every task package whose contents change what a run
# means, keyed by the name the digest is reported under. `tasks` is not here:
# BenchFlow owns that digest (see task_digests below).
TRACKED = {
    "environment": ("vendor", (".py",)),
    "knowledge": ("data/banking_knowledge", (".json",)),
    "prompts": ("prompts", (".md", ".yaml")),
}

TASKS_DIR = "tasks"


class ProvenanceError(RuntimeError):
    """A provenance fact could not be read. Never swallowed silently."""


def digest_dir(root: pathlib.Path, suffixes: tuple[str, ...]) -> tuple[str, int]:
    """sha256 over (relative path, file bytes) for every matching file.

    Paths are included and sorted, so a rename changes the digest and file
    ordering never does.
    """
    h = hashlib.sha256()
    count = 0
    if not root.is_dir():
        return "sha256:" + h.hexdigest(), 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        # Match by suffix, or by full name for extensionless files such as
        # Dockerfile.
        if path.suffix not in suffixes and path.name not in suffixes:
            continue
        if "__pycache__" in path.parts:
            continue
        h.update(str(path.relative_to(root)).encode())
        h.update(path.read_bytes())
        count += 1
    return "sha256:" + h.hexdigest(), count


def benchflow_python() -> str:
    """The interpreter BenchFlow is installed under.

    BenchFlow lives in its own environment (uv tool install), so anything that
    needs to import it runs there rather than forcing it into ours.
    """
    bf = shutil.which("benchflow")
    if not bf:
        raise ProvenanceError("benchflow is not on PATH")
    try:
        shebang = pathlib.Path(bf).read_text().splitlines()[0]
    except (OSError, IndexError) as e:
        raise ProvenanceError(f"cannot read the benchflow launcher: {e}") from e
    return shebang.lstrip("#!").strip()


def task_digests(tasks_dir: pathlib.Path | None = None) -> dict[str, str]:
    """BenchFlow's per-task content digests, as {task_id: digest}.

    `benchflow tasks digest` prints one "<name> <digest>" line per package,
    computed by the same `task_digest()` that stamps every rollout's
    config.json and that the dataset registry pins. Asking for it beats
    recomputing it: a digest that disagrees with the one recorded beside the
    rollout is worse than no digest, and a per-task map says *which* task moved
    where a single directory hash only says that something did.
    """
    root = tasks_dir or (REPO / TASKS_DIR)
    proc = subprocess.run(["benchflow", "tasks", "digest", str(root)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise ProvenanceError(
            f"benchflow tasks digest failed: {proc.stderr.strip() or proc.stdout.strip()}")
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        parts = line.split()
        # A single task directory prints the bare digest, a collection prints
        # "<name> <digest>". Accept both so --tasks tasks/task-036 works.
        if len(parts) == 2 and parts[1].startswith("sha256:"):
            out[parts[0]] = parts[1]
        elif len(parts) == 1 and parts[0].startswith("sha256:"):
            out[root.name] = parts[0]
    if not out:
        raise ProvenanceError(
            f"benchflow tasks digest returned no digests for {root}")
    return out


def aggregate_digest(per_task: dict[str, str]) -> str:
    """One run-level value over the per-task map, for grouping runs in MLflow.

    Ordered by task id and includes the ids, so adding, removing or renaming a
    task moves the aggregate just as editing one does.
    """
    h = hashlib.sha256()
    for name in sorted(per_task):
        h.update(name.encode())
        h.update(b"\x00")
        h.update(per_task[name].encode())
    return "sha256:" + h.hexdigest()


def git_state() -> dict:
    """Commit and cleanliness. A dirty tree means the commit does not describe
    what actually ran, which is the one thing versioning must not allow."""
    def run(*args):
        try:
            return subprocess.run(
                ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
            ).stdout.strip()
        except Exception:
            return ""

    dirty = run("status", "--porcelain")
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(dirty),
        # porcelain is "XY PATH"; split rather than slice, because run()
        # strips the leading status column off the first line.
        "dirty_files": [line.split(maxsplit=1)[-1]
                        for line in dirty.splitlines() if line.strip()][:20],
    }


def toolchain() -> dict:
    """Versions of tools that shape a result but live outside the repo.

    BenchFlow computes the rewards, so an upgrade can move scores with nothing
    in git or any digest to show for it. Same for the Docker engine that builds
    the environment.
    """
    def ver(*cmd):
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, check=True
            ).stdout.strip().splitlines()[0]
        except Exception:
            return "unknown"

    # The host interpreter and its pinned deps run the oracle gate and this
    # script. An empty .venv shadowing an ephemeral uv environment is what broke
    # the gate on 2026-09-17 — invisible to every other digest here.
    lock = REPO / "requirements-host.txt"
    return {
        "benchflow": ver("benchflow", "--version").split()[-1],
        "docker": ver("docker", "version", "--format", "{{.Server.Version}}"),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}."
                  f"{sys.version_info.micro}",
        "host_deps": ("sha256:" + hashlib.sha256(lock.read_bytes()).hexdigest()
                      if lock.is_file() else "unpinned"),
    }


def agent_harness(agent: str) -> str:
    """The exact agent harness package BenchFlow will install for `agent`.

    The model is only half of what produces a rollout; the other half is the
    scaffold around it — its system prompt, tool definitions, and control loop.
    BenchFlow pins that per agent (claude-agent-acp is pinned to a specific
    `@agentclientprotocol/claude-agent-acp` version), so the pin is readable
    rather than guessable. Recording it means a score shift after a BenchFlow
    upgrade can be attributed to the harness instead of the model.

    Returns e.g. "@agentclientprotocol/claude-agent-acp@0.73.0".

    `benchflow agent show` prints the launch path but not the install pin, so
    the registry is the only source and this reads it through BenchFlow's own
    interpreter. That makes it a private-API call: a BenchFlow refactor can
    break it. It raises when it does, rather than returning "unknown" — a run
    that silently records "unknown" for its harness looks recorded and is not.
    """
    interp = benchflow_python()
    proc = subprocess.run([interp, "-c", _HARNESS_PROBE, agent],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise ProvenanceError(
            f"harness probe failed for {agent!r}: {proc.stderr.strip()}")
    pin = proc.stdout.strip()
    if not pin:
        raise ProvenanceError(
            f"the agent registry declares no version-pinned install for {agent!r}")
    return pin


# Runs inside BenchFlow's interpreter. Prints the version-pinned packages in the
# agent's install command, comma-separated.
_HARNESS_PROBE = """
import re, sys
from benchflow.agents.registry import AGENTS, resolve_agent_key
key = resolve_agent_key(sys.argv[1])
cfg = AGENTS[key]
pins = sorted(set(re.findall(
    r"[A-Za-z0-9@/._-]+@[0-9][0-9A-Za-z.+-]*", cfg.install_cmd or "")))
print(",".join(pins))
"""


def collect(agent: str | None = None,
            tasks_dir: pathlib.Path | None = None) -> dict:
    """Everything a run needs pinned, plus a `warnings` list.

    A probe that fails records its failure in `warnings` and leaves the field
    "unknown". Nothing here decides what to do about that; the caller does,
    loudly (run_experiment tags the run and says so on stderr).
    """
    out = {"provenance_version": PROVENANCE_VERSION, "git": git_state(),
           "toolchain": toolchain(), "digests": {}, "file_counts": {},
           "warnings": []}
    if agent:
        try:
            out["agent_harness"] = agent_harness(agent)
        except ProvenanceError as e:
            out["agent_harness"] = "unknown"
            out["warnings"].append(f"agent_harness: {e}")
    # tasks/ is BenchFlow's digest, asked for rather than recomputed.
    try:
        per_task = task_digests(tasks_dir)
        out["task_digests"] = per_task
        out["digests"]["tasks"] = aggregate_digest(per_task)
        out["file_counts"]["tasks"] = len(per_task)
    except ProvenanceError as e:
        out["task_digests"] = {}
        out["digests"]["tasks"] = "unknown"
        out["file_counts"]["tasks"] = 0
        out["warnings"].append(f"digest_tasks: {e}")
    for name, (rel, suffixes) in TRACKED.items():
        digest, count = digest_dir(REPO / rel, suffixes)
        out["digests"][name] = digest
        out["file_counts"][name] = count
    if out["toolchain"]["benchflow"] == "unknown":
        out["warnings"].append("toolchain: benchflow --version is unreadable")
    # One digest over the four, so a run can be pinned with a single value.
    combined = hashlib.sha256()
    for name in sorted(out["digests"]):
        combined.update(out["digests"][name].encode())
    out["digests"]["combined"] = "sha256:" + combined.hexdigest()
    # Which tau2 commit the vendored domain came from.
    src = REPO / "vendor" / "SOURCE.txt"
    if src.is_file():
        for line in src.read_text().splitlines():
            if line.startswith("COMMIT:"):
                out["vendored_tau2_commit"] = line.split(":", 1)[1].strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--agent", help="also report this agent's pinned harness")
    ap.add_argument("--tasks", action="store_true",
                    help="print BenchFlow's per-task digest map and exit")
    args = ap.parse_args()
    if args.tasks:
        print(json.dumps(task_digests(), indent=2))
        return 0
    data = collect(args.agent)
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    g = data["git"]
    print(f"{'git':13s}{g['commit'][:12]} on {g['branch']}"
          f"{'  DIRTY' if g['dirty'] else ''}")
    if g["dirty"]:
        for f in g["dirty_files"]:
            print(f"           ~ {f}")
    units = {"tasks": "packages"}
    for name in ("tasks", *TRACKED):
        print(f"{name:13s}{data['digests'][name][:19]}…  "
              f"({data['file_counts'][name]} {units.get(name, 'files')})")
    print(f"{'combined':13s}{data['digests']['combined'][:19]}…")
    if "vendored_tau2_commit" in data:
        print(f"{'tau2':13s}{data['vendored_tau2_commit'][:12]}")
    for k, v in data["toolchain"].items():
        print(f"{k:13s}{v[:19] + '…' if v.startswith('sha256:') else v}")
    if "agent_harness" in data:
        print(f"{'harness':13s}{data['agent_harness']}")
    for w in data["warnings"]:
        print(f"WARNING      {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
