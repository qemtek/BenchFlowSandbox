"""Vendored subset of tau2-bench: the banking_knowledge domain only.

Upstream's __init__ imports the runner/orchestrator stack (litellm, fastapi,
uvicorn). Those are unreachable from the domain tools, so this stub keeps the
dependency surface to pydantic/deepdiff/addict/loguru/python-dotenv.
See vendor/SOURCE.txt for the pinned commit.
"""
