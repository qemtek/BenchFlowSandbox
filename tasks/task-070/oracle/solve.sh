#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Yuki Nakamura", "user_id": "224959b99e", "address": "3421 Sakura Avenue, Portland, OR 97205", "email": "yuki.nakamura@simba.com", "phone_number": "503-555-0842", "date_of_birth": "05/12/1991", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"224959b99e\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"224959b99e\", \"account_type\": \"business_checking\", \"account_class\": \"Sky Blue\"}"}'
