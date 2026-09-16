#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Marco Vitiello", "user_id": "mv93f8a7b2", "address": "2847 South Lamar Boulevard, Austin, TX 78704", "email": "marco.vitiello@gmail.com", "phone_number": "512-555-0847", "date_of_birth": "08/22/1993", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"mv93f8a7b2\", \"account_type\": \"checking\", \"account_class\": \"Green Fee-Free Account\"}"}'
