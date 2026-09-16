#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call transfer_to_human_agents '{"reason": "unconfirmed_external_communication", "summary": ""}'
