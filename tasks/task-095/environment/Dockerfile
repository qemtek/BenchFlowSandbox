FROM python@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# ripgrep/grep are the agent's knowledge-base search; no embedding API needed.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ripgrep jq && \
    rm -rf /var/lib/apt/lists/*

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
COPY tasks/task-095/verifier/db.seed.json /data/db.json
RUN chmod 777 /data && chmod 666 /data/db.json

ENV BANK_DB=/data/db.json
WORKDIR /app
RUN mkdir -p /app && chmod 777 /app
