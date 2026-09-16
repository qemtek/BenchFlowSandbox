#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Jordan Chen", "user_id": "jc61f7a8d2", "address": "4521 Pine Street, Seattle, WA 98101", "email": "jordan.chen@consulting.io", "phone_number": "206-555-0847", "date_of_birth": "03/15/1988", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"jc61f7a8d2\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"jc61f7a8d2\", \"account_type\": \"business_checking\", \"account_class\": \"Navy Blue\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"jc61f7a8d2\", \"account_type\": \"savings\", \"account_class\": \"Silver Plus Account\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "transfer_funds_between_bank_accounts_7291"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "transfer_funds_between_bank_accounts_7291", "arguments": "{\"source_account_id\": \"61c9d8e7f6a5b432\", \"destination_account_id\": \"354e3d677cba2b12\", \"amount\": 150}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "close_bank_account_7392"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_bank_account_7392", "arguments": "{\"account_id\": \"61c9d8e7f6a5b432\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "transfer_funds_between_bank_accounts_7291", "arguments": "{\"source_account_id\": \"61a8b7c6d5e4f321\", \"destination_account_id\": \"354e3d677cba2b12\", \"amount\": 2500}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "transfer_funds_between_bank_accounts_7291", "arguments": "{\"source_account_id\": \"61a8b7c6d5e4f321\", \"destination_account_id\": \"e22d00f03a5d044e\", \"amount\": 1000}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_bank_account_7392", "arguments": "{\"account_id\": \"61a8b7c6d5e4f321\"}"}'
