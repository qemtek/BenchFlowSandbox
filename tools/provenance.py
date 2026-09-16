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
        "dirty_files": [line[3:] for line in dirty.splitlines()][:20],
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

    return {
        "benchflow": ver("benchflow", "--version"),
        "docker": ver("docker", "version", "--format", "{{.Server.Version}}"),
    }


def collect() -> dict:
    out = {"git": git_state(), "toolchain": toolchain(), "digests": {}, "file_counts": {}}
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
    args = ap.parse_args()
    data = collect()
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    g = data["git"]
    print(f"git      {g['commit'][:12]} on {g['branch']}"
          f"{'  DIRTY' if g['dirty'] else ''}")
    if g["dirty"]:
        for f in g["dirty_files"]:
            print(f"           ~ {f}")
    for name in ("environment", "knowledge", "prompts"):
        print(f"{name:9s}{data['digests'][name][:19]}…  "
              f"({data['file_counts'][name]} files)")
    print(f"combined {data['digests']['combined'][:19]}…")
    if "vendored_tau2_commit" in data:
        print(f"tau2     {data['vendored_tau2_commit'][:12]}")
    for k, v in data["toolchain"].items():
        print(f"{k:9s}{v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
