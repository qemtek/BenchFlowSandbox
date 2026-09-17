#!/bin/sh
# Reference solution: the gold actions, replayed through the same MCP
# tool surface the agent is given. Proves the task is reachable.
set -eu

exec python /opt/bank/vendor/mcp_replay.py /oracle/actions.json
