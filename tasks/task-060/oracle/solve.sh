#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Jordan Mitchell", "user_id": "jm60a8b9c2", "address": "4521 Mountain View Drive, Denver, CO 80202", "email": "jordan.mitchell@outlook.com", "phone_number": "303-555-0847", "date_of_birth": "08/22/1989", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"jm60a8b9c2\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"jm60a8b9c2\", \"account_type\": \"savings\", \"account_class\": \"Silver Plus Account\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "close_bank_account_7392"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_bank_account_7392", "arguments": "{\"account_id\": \"58d57780cc15e32d\"}"}'
