#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Riley Parker", "user_id": "rp65a7b3c4", "address": "3847 Burnside Street, Portland, OR 97214", "email": "riley.parker@gmail.com", "phone_number": "503-555-0293", "date_of_birth": "07/19/1991", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"rp65a7b3c4\", \"account_type\": \"savings\", \"account_class\": \"Green Account\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"rp65a7b3c4\", \"account_type\": \"checking\", \"account_class\": \"Evergreen Account\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "close_bank_account_7392"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_bank_account_7392", "arguments": "{\"account_id\": \"chk_rp65a7b3c4\"}"}'
