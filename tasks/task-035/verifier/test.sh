#!/bin/bash
# Action-scored task: what matters is which operations the agent performed, not
# what changed. See verifier/verify_actions.py.
set -uo pipefail
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

DB="${BANK_DB:-/data/db.json}"
python /verifier/verify_actions.py \
    --gold /verifier/gold.json \
    --calls "${DB%.json}.calls.jsonl" \
    --out /logs/verifier
exit $?
