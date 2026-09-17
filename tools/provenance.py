#!/usr/bin/env python3
"""Content digests for everything a result depends on.

BenchFlow records a `task_digest` per task, covering the files inside the task
package. Since we moved shared sources out via `--context-root`, that digest no
longer covers what the agent actually runs against:

    covered      task.md, environment/Dockerfile, oracle/, verifier/, review/
    NOT covered  vendor/bank_cli.py, vendor/toolsets.py, the knowledge base

That gap is real. Today's enum fix flipped two tasks from FAIL to PASS without
changing a single `task_digest` — two runs with materially different tool
behaviour looked identical in provenance.

This computes the missing digests so a run can be pinned to the exact code and
data that produced it:

    environment  vendor/ (tool implementation, toolsets, MCP server)
    knowledge    data/banking_knowledge/ (seed db + 698 documents)
    prompts      prompts/ (briefings and frontmatter templates)

Usage:
    python tools/provenance.py            # print the digests
    python tools/provenance.py --json     # machine-readable
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

# Directories whose contents change what a run means, keyed by the name the
# digest is reported under.
TRACKED = {
    "environment": ("vendor", (".py",)),
    "knowledge": ("data/banking_knowledge", (".json",)),
    "prompts": ("prompts", (".md", ".yaml")),
}


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
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if "__pycache__" in path.parts:
            continue
        h.update(str(path.relative_to(root)).encode())
        h.update(path.read_bytes())
        count += 1
    return "sha256:" + h.hexdigest(), count


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

    Returns e.g. "@agentclientprotocol/claude-agent-acp@0.73.0", or "unknown"
    if the registry cannot be read.
    """
    # BenchFlow lives in its own interpreter (uv tool install), so import it
    # there rather than requiring it in ours.
    try:
        bf = shutil.which("benchflow")
        interp = pathlib.Path(bf).read_text().splitlines()[0].lstrip("#!").strip()
        out = subprocess.run(
            [interp, "-c", _HARNESS_PROBE, agent],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or "unknown"
    except Exception:
        return "unknown"


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


def collect(agent: str | None = None) -> dict:
    out = {"git": git_state(), "toolchain": toolchain(), "digests": {}, "file_counts": {}}
    if agent:
        out["agent_harness"] = agent_harness(agent)
    for name, (rel, suffixes) in TRACKED.items():
        digest, count = digest_dir(REPO / rel, suffixes)
        out["digests"][name] = digest
        out["file_counts"][name] = count
    # One digest over the three, so a run can be pinned with a single value.
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
    args = ap.parse_args()
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
    for name in ("environment", "knowledge", "prompts"):
        print(f"{name:13s}{data['digests'][name][:19]}…  "
              f"({data['file_counts'][name]} files)")
    print(f"{'combined':13s}{data['digests']['combined'][:19]}…")
    if "vendored_tau2_commit" in data:
        print(f"{'tau2':13s}{data['vendored_tau2_commit'][:12]}")
    for k, v in data["toolchain"].items():
        print(f"{k:13s}{v[:19] + '…' if v.startswith('sha256:') else v}")
    if "agent_harness" in data:
        print(f"{'harness':13s}{data['agent_harness']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
