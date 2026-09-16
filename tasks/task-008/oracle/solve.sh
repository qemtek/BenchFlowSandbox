#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call transfer_to_human_agents '{"reason": "customer_demands_after_unavailable_offer_refusal", "summary": ""}'
