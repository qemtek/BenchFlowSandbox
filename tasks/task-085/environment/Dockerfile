FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# ripgrep/grep are the agent's knowledge-base search; no embedding API needed.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ripgrep jq && \
    rm -rf /var/lib/apt/lists/*

# Only what the vendored banking domain imports — not tau2's agent/LLM stack.
RUN python -m pip install \
      pydantic==2.* deepdiff addict loguru python-dotenv toml pyyaml docstring-parser

# These COPY sources resolve against the shared build context (--context-root .),
# so vendor/ and the knowledge base exist once in the repo rather than being
# duplicated into all 40 task packages.
COPY vendor /opt/bank/vendor
RUN printf '#!/bin/sh\nexec python /opt/bank/vendor/bank_cli.py "$@"\n' > /usr/local/bin/bank \
    && chmod +x /usr/local/bin/bank

COPY data/banking_knowledge/documents /data/documents

# The seed database is staged per task: a task with initial_state modifies it,
# so it cannot safely be shared even though these 40 currently all match.
COPY tasks/task-085/verifier/db.seed.json /data/db.json
RUN chmod 777 /data && chmod 666 /data/db.json

ENV BANK_DB=/data/db.json
WORKDIR /app
RUN mkdir -p /app && chmod 777 /app
