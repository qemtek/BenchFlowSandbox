#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call unlock_discoverable_agent_tool '{"agent_tool_name": "emergency_credit_bureau_incident_transfer_1114"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "emergency_credit_bureau_incident_transfer_1114"}'
bank call transfer_to_human_agents '{"summary": ""}'
