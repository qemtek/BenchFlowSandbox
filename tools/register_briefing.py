#!/usr/bin/env python3
"""Import a briefing into MLflow's prompt registry.

The registry is where briefings live. `make_task.py` loads one by pinned
version and bakes it into each task package, so a task is always attached to an
immutable prompt version rather than to whatever a file happened to contain.

This tool exists for the two moments when text has to get *into* the registry
from outside it:

    bootstrap   a fresh checkout, or a fresh tracking store, has no prompt yet
    import      you drafted a variant somewhere else and want it versioned

Ordinary edits do not go through here. Edit the prompt in the MLflow UI, which
creates the next version directly.

`prompts/briefing.seed.md` is the bootstrap text, named the way
`verifier/db.seed.json` is: a starting point that is read once, not a live copy
that has to be kept in step with anything. Editing it after bootstrap does
nothing, which is the point — there is one authoritative briefing and it is in
the registry.

Usage:
    python tools/register_briefing.py                        # seed the registry
    python tools/register_briefing.py --from-file draft.md   # import a variant
    python tools/register_briefing.py --list                 # what is registered
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
TRACKING_DB = REPO / "mlflow.db"
PROMPT_NAME = "bank-briefing"
SEED = REPO / "prompts" / "briefing.seed.md"


def client():
    import mlflow

    mlflow.set_tracking_uri(f"sqlite:///{TRACKING_DB}")
    return mlflow


def existing_version(text: str):
    """The registered version holding exactly this text, or None.

    Registering identical text again would mint a version number that means
    nothing. A version should mean "a different briefing".
    """
    import mlflow

    try:
        return next(
            (v for v in mlflow.MlflowClient().search_prompt_versions(PROMPT_NAME)
             if v.template == text),
            None,
        )
    except Exception:
        # No prompt of this name yet. Any other failure will resurface on the
        # register call below, where it can be reported against a real action.
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-file", type=pathlib.Path, default=SEED)
    ap.add_argument("--message", default="")
    ap.add_argument("--list", action="store_true",
                    help="show registered versions and exit")
    args = ap.parse_args()

    mlflow = client()
    import mlflow.genai

    if args.list:
        try:
            versions = list(mlflow.MlflowClient().search_prompt_versions(PROMPT_NAME))
        except Exception as e:
            print(f"nothing registered under {PROMPT_NAME}: {e}")
            return 1
        for v in versions:
            print(f"prompts:/{PROMPT_NAME}/{v.version:<4} "
                  f"{hashlib.sha256(v.template.encode()).hexdigest()[:12]}  "
                  f"{v.commit_message or ''}")
        return 0

    if not args.from_file.is_file():
        raise SystemExit(f"no such file: {args.from_file}")
    text = args.from_file.read_text()
    if "{{scenario}}" not in text:
        raise SystemExit(
            f"{args.from_file} has no {{{{scenario}}}} placeholder.\n"
            "make_task.py substitutes the case notes there, so a briefing "
            "without it would give every task the same empty case."
        )

    found = existing_version(text)
    if found:
        print(f"already registered, unchanged: prompts:/{PROMPT_NAME}/{found.version}")
        return 0

    message = args.message or f"imported from {args.from_file.name}"
    version = mlflow.genai.register_prompt(
        name=PROMPT_NAME, template=text, commit_message=message,
        tags={"sha256": hashlib.sha256(text.encode()).hexdigest(),
              "imported_from": str(args.from_file.relative_to(REPO))},
    )
    print(f"registered {version.uri}")
    print(f"generate against it with:\n"
          f"  python tools/make_task.py $(cat tools/eligible_ids.txt) "
          f"--briefing-version {version.version} --out tasks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
