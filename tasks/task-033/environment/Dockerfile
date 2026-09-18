FROM python@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# ripgrep/grep are the agent's knowledge-base search; no embedding API needed.
# curl/xz are here only to fetch Node below, and are left in place because
# BenchFlow's bootstrap probes for them before deciding it has work to do.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ripgrep jq curl ca-certificates xz-utils && \
    rm -rf /var/lib/apt/lists/*

# The agent's own runtime, baked rather than fetched once per rollout.
# BenchFlow installs it inside every container: an apt-get for curl and xz, a
# Node tarball from nodejs.org, then an npm install. Six containers doing that
# at once exhausted the local resolver on 2026-09-18 — nine install failures in
# one pass, one task lost outright.
#
# Shipping Node here skips the first two outright: BenchFlow guards them on
# $BF_NODE_DIR/bin/node existing. The npm install still runs, because its guard
# applies only to unpinned packages and this one is pinned — but every package
# is in the image's npm cache, so with the settings below it is served from
# disk in seconds and never reaches the registry. Verified by running
# BenchFlow's own install command in this image under `--network none`.
#
# The versions and paths come from BenchFlow's agent registry at generation
# time, not from a copy kept here, and `run_experiment.py` refuses a run whose
# image disagrees with the registry it is about to run under.
ENV NPM_CONFIG_PREFER_OFFLINE=true \
    NPM_CONFIG_AUDIT=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_UPDATE_NOTIFIER=false
RUN set -eu; \
    case "$(uname -m)" in \
      x86_64|amd64) arch=x64 ;; \
      aarch64|arm64) arch=arm64 ;; \
      *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;; \
    esac; \
    mkdir -p /opt/benchflow/node; \
    curl -fsSLo /tmp/node.tar.xz \
      "https://nodejs.org/dist/v22.20.0/node-v22.20.0-linux-${arch}.tar.xz"; \
    tar -xJf /tmp/node.tar.xz -C /opt/benchflow/node --strip-components=1 --no-same-owner; \
    rm /tmp/node.tar.xz; \
    export PATH="/opt/benchflow/node/bin:$PATH"; \
    /opt/benchflow/node/bin/npm install -g --prefix /opt/benchflow/js-agents @agentclientprotocol/claude-agent-acp@0.73.0; \
    mkdir -p /opt/benchflow/bin; \
    printf '%s\n' '#!/bin/sh' \
      'exec /opt/benchflow/node/bin/node /opt/benchflow/js-agents/bin/claude-agent-acp "$@"' \
      > /opt/benchflow/bin/claude-agent-acp; \
    chmod +x /opt/benchflow/bin/claude-agent-acp; \
    chmod -R a+rX /opt/benchflow

# Only what the vendored banking domain imports — not tau2's agent/LLM stack.
# Exact versions: an unpinned dependency release would change agent behaviour
# with no trace in any digest.
RUN python -m pip install \
      pydantic==2.13.5 deepdiff==9.1.0 addict==2.4.0 loguru==0.7.3 \
      python-dotenv==1.2.3 toml==0.10.2 PyYAML==6.0.3 docstring_parser==0.18.0

# These COPY sources resolve against the shared build context (--context-root .),
# so vendor/ and the knowledge base exist once in the repo rather than being
# duplicated into all 40 task packages.
# The agent reaches the bank through the MCP server declared in task.md.
# bank_cli.py stays as the shared dispatcher that bank_mcp.py imports for
# session state, autounlock and toolsets — it is no longer on PATH, so there is
# one interface to experiment against instead of two.
COPY vendor /opt/bank/vendor

COPY data/banking_knowledge/documents /data/documents

# The seed database is staged per task: a task with initial_state modifies it,
# so it cannot safely be shared even though these 40 currently all match.
COPY tasks/task-033/verifier/db.seed.json /data/db.json
RUN chmod 777 /data && chmod 666 /data/db.json

ENV BANK_DB=/data/db.json
WORKDIR /app
RUN mkdir -p /app && chmod 777 /app
