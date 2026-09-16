#!/bin/bash
# Rebuild the gold database from the reference actions, then compare it with the
# database the agent left behind. Both sides run through the same vendored tools,
# so an equivalent end state scores 1.0 regardless of the route taken.
set -uo pipefail
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

python /verifier/verify_db.py \
    --seed /verifier/db.seed.json \
    --gold /verifier/gold.json \
    --actual "${BANK_DB:-/data/db.json}" \
    --out /logs/verifier
exit $?
